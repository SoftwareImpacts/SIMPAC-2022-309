# -*- coding: utf-8 -*-
"""
Created on Mon Oct 17 11:39:27 2022

@author: aytugy
"""

import datetime as dt
import protocols.scenariogeneration.read_input as ri
import protocols.scenariogeneration.sceneration as sc

def main(dependent_times=False):
    #TODO: Explain inputs

    same_day_departure_prob = 0.7
    overnight_stay_prob = 0.3
    dep_day_prob_distribution = [same_day_departure_prob, overnight_stay_prob]
    
    if dependent_times is False:
        # independent times
        arr_times_dict, dep_times_dict, arr_soc_dict, dep_soc_dict, ev_dict = \
            ri.excel_to_sceneration_input(file_path='tutorials/scenariogeneration/input_generator.xlsx',
                                          dependent_times=False)

        ev_df = sc.generate_fleet_data(arr_soc_dict=arr_soc_dict, dep_soc_dict=dep_soc_dict, ev_dict=ev_dict,
                                     dep_day_prob_distribution=dep_day_prob_distribution, number_of_evs=5,
                                     startdate=dt.date(2021, 6, 1), enddate=dt.date(2021, 6, 3),
                                     timedelta_in_min=15, diff_arr_dep_in_min=0,
                                     dependent_times=False, arr_times_dict=arr_times_dict,
                                     dep_times_dict=dep_times_dict, times_dict=None, arr_dep_times_dict=None)
    else:
        # dependent times
        times_dict, arr_dep_times_dict, arr_soc_dict, dep_soc_dict, ev_dict = \
            ri.excel_to_sceneration_input(file_path='tutorials/scenariogeneration/input_generator.xlsx',
                                          dependent_times=True)

        ev_df = sc.generate_fleet_data(arr_soc_dict=arr_soc_dict, dep_soc_dict=dep_soc_dict, ev_dict=ev_dict,
                                     dep_day_prob_distribution=dep_day_prob_distribution, number_of_evs=5,
                                     startdate=dt.date(2021, 6, 1), enddate=dt.date(2021, 6, 3),
                                     timedelta_in_min=15, diff_arr_dep_in_min=0,
                                     dependent_times=True, arr_times_dict=None,
                                     dep_times_dict=None, times_dict=times_dict,
                                     arr_dep_times_dict=arr_dep_times_dict)
    
    sc.visualize_statistical_time_generation('output_generator/', ev_df, timedelta_in_min=15)
    
    # Unlocalize datetimes, as Excel does not support datetimes with timezones
    ev_df['ArrivalTime'] = ev_df['ArrivalTime'].dt.tz_localize(None)
    ev_df['DepartureTime'] = ev_df['DepartureTime'].dt.tz_localize(None)
    ev_df.to_excel("output_generator.xlsx")           #:TODO statistical_output is not a good name
    
    sc.output_to_sim_input(ev_df, 'input_simulator.xlsx')
    
if __name__ == "__main__":
    main(dependent_times=False)  #TODO: When I switch to "True" it does not work