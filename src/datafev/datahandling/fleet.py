from src.datafev.datahandling.vehicle import ElectricVehicle
import pandas as pd


class EVFleet(object):
    def __init__(self, fleet_id, behavior, sim_horizon):

        self.fleet_id = fleet_id
        self.objects = {}
        self.reserving_at = dict([(t, []) for t in sim_horizon])
        self.incoming_at = dict([(t, []) for t in sim_horizon])
        self.outgoing_at = dict([(t, []) for t in sim_horizon])
        self.outgoing_at[None] = []

        ##################################################################################################
        # Define behavior
        for _, i in behavior.iterrows():

            # Initialization of an EV object
            evID = i["ev_id"]
            bcap = i["Battery Capacity (kWh)"]
            p_max_ch = i["p_max_ch"]
            p_max_ds = i["p_max_ds"]
            ev = ElectricVehicle(evID, bcap, p_max_ch, p_max_ds)

            # Assigning the scenario parameters
            ev.t_res = i["Reservation Time"]
            ev.t_arr_est = i["Estimated Arrival Time"]
            ev.t_dep_est = i["Estimated Departure Time"]
            ev.soc_arr_est = i["Estimated Arrival SOC"]
            ev.soc_tar_at_t_dep_est = i["Target SOC @ Estimated Departure Time"]
            ev.v2g_allow = i["V2G Allowance (kWh)"] * 3600
            ev.t_arr_real = i["Real Arrival Time"]
            ev.soc_arr_real = i["Real Arrival SOC"]
            ev.t_dep_real = i["Real Departure Time"]
            ev.cluster_target = i["Target Cluster"]
            ev.soc[ev.t_arr_real] = ev.soc_arr_real

            self.objects[evID] = ev
            self.reserving_at[ev.t_res].append(ev)
            self.incoming_at[ev.t_arr_real].append(ev)

            if pd.isna(ev.t_dep_real):
                self.outgoing_at[None].append(ev)
            else:
                self.outgoing_at[ev.t_dep_real].append(ev)
        ##################################################################################################

        ##################################################################################################
        # Calculate statistics
        self.presence_distribution = {}
        for t in sim_horizon:
            self.presence_distribution[t] = len(
                behavior[
                    (behavior["Real Arrival Time"] <= t)
                    & (behavior["Real Departure Time"] > t)
                ]
            )
        ##################################################################################################

    def enter_power_soc_table(self, table):
        for ev_id, ev in self.objects.items():
            ev.pow_soc_table = table.loc[ev_id].copy()

    def reserving_vehicles_at(self, ts):
        return self.reserving_at[ts]

    def incoming_vehicles_at(self, ts):
        return self.incoming_at[ts]

    def outgoing_vehicles_at(self, ts):
        return self.outgoing_at[ts]

    def export_results(self, start, end, step, xlfile):

        sim_horizon = pd.date_range(start=start, end=end, freq=step)

        soc = pd.DataFrame(index=sim_horizon)
        g2v = pd.DataFrame(index=sim_horizon)
        v2g = pd.DataFrame(index=sim_horizon)
        status = pd.Series()

        with pd.ExcelWriter(xlfile) as writer:

            for ev_id in sorted(self.objects.keys()):

                ev = self.objects[ev_id]

                soc.loc[:, ev_id] = pd.Series(ev.soc)
                g2v.loc[:, ev_id] = pd.Series(ev.g2v)
                v2g.loc[:, ev_id] = pd.Series(ev.v2g)
                status[ev_id] = ev.admitted

            soc.to_excel(writer, sheet_name="SOC Trajectory")
            g2v.to_excel(writer, sheet_name="G2V Charge")
            g2v.to_excel(writer, sheet_name="V2G Discharge")
            status.to_excel(writer, sheet_name="Admitted")