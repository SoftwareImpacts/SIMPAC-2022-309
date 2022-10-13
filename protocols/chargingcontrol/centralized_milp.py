import pandas as pd
from algorithms.multicluster.rescheduling_milp import reschedule

def charging_protocol(system,ts, t_delta, horizon, solver, penalty_parameters):

    schedule_horizon = pd.date_range(start=ts, end=ts + horizon, freq=t_delta)
    opt_horizon = list(range(len(schedule_horizon)))
    opt_step    = t_delta.seconds

    powlimits = {}
    powlimits['P_CC_up_lim']  = {}
    powlimits['P_CC_low_lim'] = {}
    powlimits['P_CC_vio_lim'] = {}
    powlimits['P_CS_up_lim']  = dict(enumerate(system.upper_limit[schedule_horizon[:-1]].values))
    powlimits['P_CS_low_lim'] = dict(enumerate(system.lower_limit[schedule_horizon[:-1]].values))

    evdata = {}
    evdata['P_EV_pos_max'] = {}
    evdata['P_EV_neg_max'] = {}
    evdata['charge_eff'] = {}
    evdata['discharge_eff'] = {}
    evdata['battery_cap'] = {}
    evdata['target_soc'] = {}
    evdata['departure_time'] = {}
    evdata['initial_soc'] = {}
    evdata['minimum_soc'] = {}
    evdata['maximum_soc'] = {}
    evdata['location'] = {}

    clusters=[]

    rho_y  = {}
    rho_eps= {}

    for cc_id in system.clusters.keys():

        cluster=system.clusters[cc_id]

        if cluster.number_of_connected_chargers(ts) > 0:

            clusters.append(cc_id)
            powlimits['P_CC_up_lim'][cc_id]  = dict(enumerate(cluster.upper_limit[schedule_horizon[:-1]].values))
            powlimits['P_CC_low_lim'][cc_id] = dict(enumerate(cluster.lower_limit[schedule_horizon[:-1]].values))
            powlimits['P_CC_vio_lim'][cc_id] = cluster.violation_tolerance
            rho_y[cc_id]=penalty_parameters['rho_y'][cc_id]
            rho_eps[cc_id]= penalty_parameters['rho_eps'][cc_id]
            
            for cu_id, cu in cluster.chargers.items():

                ev = cu.connected_ev

                if ev != None:

                    sch_inst = cu.active_schedule_instance
                    cu_sch   = cu.schedule_soc[sch_inst]
                    cu_sch   = cu_sch.reindex(schedule_horizon)
                    cu_sch   = cu_sch.fillna(method="ffill")

                    p_ev_pos_max = min(ev.p_max_ch, cu.p_max_ch)
                    p_ev_neg_max = min(ev.p_max_ds, cu.p_max_ds)

                    ev_id = ev.vehicle_id
                    evdata['battery_cap'][ev_id] = ev.bCapacity
                    evdata['departure_time'][ev_id] = (ev.t_dep_est - ts) / t_delta
                    evdata['initial_soc'][ev_id] = ev.soc[ts]
                    evdata['minimum_soc'][ev_id] = ev.minSoC
                    evdata['maximum_soc'][ev_id] = ev.maxSoC
                    evdata['target_soc'][ev_id] = cu_sch[ts + horizon]
                    evdata['charge_eff'][ev_id] = cu.eff
                    evdata['discharge_eff'][ev_id] = cu.eff
                    evdata['P_EV_pos_max'][ev_id] = p_ev_pos_max
                    evdata['P_EV_neg_max'][ev_id] = p_ev_neg_max
                    evdata['location'][ev_id] = (cc_id, cu_id)

    if len(evdata['battery_cap'])>0:

        p_schedule, s_schedule= reschedule(solver, opt_step, opt_horizon, powlimits, evdata, clusters, rho_y, rho_eps)

        for cc_id in system.clusters.keys():
            for cu_id in system.clusters[cc_id].chargers.keys():
                cu = system.clusters[cc_id].chargers[cu_id]
                if cu.connected_ev != None:
                    ev_id = cu.connected_ev.vehicle_id
                    cu.supply(ts, t_delta, p_schedule[ev_id][0])