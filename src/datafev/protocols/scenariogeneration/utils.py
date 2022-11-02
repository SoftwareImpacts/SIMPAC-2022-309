import pandas as pd
from datetime import timedelta
import datetime as dt
import decimal
import matplotlib.pyplot as plt
import matplotlib.ticker as tck
import os


def excel_to_sceneration_input_independent_times(file_path):
    """
    This method converts the excel inputs into inputs suitable for the generate_fleet_data_independent_times function under sceneration.py.

    Parameters
    ----------
    file_path : str
        File path of the Excel input file.

    Returns
    -------
    arr_times_dict : dict
        Arrival times nested dictionary.
        keys: weekend or weekday,
        values: {keys: time identifier, values: time lower bound, time upper bounds and arrival probabilities}.
    dep_times_dict : dict
        Departure times nested dictionary.
        keys: weekend or weekday,
        values: {keys: time identifier, values: time lower bound, time upper bounds and departure probabilities}.
    arr_soc_dict : dict
        SoC nested dictionaries for arrival.
        keys: SoC Identifier, values: SoC Lower Bounds, SOC Upper Bounds and their probabilities.
    dep_soc_dict : dict
        SoC nested dictionaries for departure.
        keys: SoC Identifier, values: SoC Lower Bounds, SOC Upper Bounds and their probabilities.
    ev_dict : dict
        EV nested dictionary.
        keys: EV models, values: their data and probability.

    """

    # Read excel file
    dep_times_df = pd.read_excel(file_path, "DepartureTime")
    arr_times_df = pd.read_excel(file_path, "ArrivalTime")
    arr_soc_df = pd.read_excel(file_path, "ArrivalSoC")
    dep_soc_df = pd.read_excel(file_path, "DepartureSoC")
    ev_df = pd.read_excel(file_path, "EVData")

    # Convert percent probabilities to probabilities between 0 and 1
    arr_times_df["WeekdayArrivalPercentage"] = arr_times_df[
        "WeekdayArrivalPercentage"
    ].div(100)
    arr_times_df["WeekendArrivalPercentage"] = arr_times_df[
        "WeekendArrivalPercentage"
    ].div(100)
    dep_times_df["WeekdayDeparturePercentage"] = dep_times_df[
        "WeekdayDeparturePercentage"
    ].div(100)
    dep_times_df["WeekendDeparturePercentage"] = dep_times_df[
        "WeekendDeparturePercentage"
    ].div(100)
    # Separate weekday and weekend arrival/departure times dataframes, rename WeekdayArrivalPercentage to probability
    weekday_arr_times_df = arr_times_df.filter(
        ["TimeID", "TimeLowerBound", "TimeUpperBound", "WeekdayArrivalPercentage"],
        axis=1,
    )
    weekday_arr_times_df.columns = weekday_arr_times_df.columns.str.replace(
        "WeekdayArrivalPercentage", "Probability"
    )
    weekend_arr_times_df = arr_times_df.filter(
        ["TimeID", "TimeLowerBound", "TimeUpperBound", "WeekendArrivalPercentage"],
        axis=1,
    )
    weekend_arr_times_df.columns = weekend_arr_times_df.columns.str.replace(
        "WeekendArrivalPercentage", "Probability"
    )
    weekday_dep_times_df = dep_times_df.filter(
        ["TimeID", "TimeLowerBound", "TimeUpperBound", "WeekdayDeparturePercentage"],
        axis=1,
    )
    weekday_dep_times_df.columns = weekday_dep_times_df.columns.str.replace(
        "WeekdayDeparturePercentage", "Probability"
    )
    weekend_dep_times_df = dep_times_df.filter(
        ["TimeID", "TimeLowerBound", "TimeUpperBound", "WeekendDeparturePercentage"],
        axis=1,
    )
    weekend_dep_times_df.columns = weekend_dep_times_df.columns.str.replace(
        "WeekendDeparturePercentage", "Probability"
    )
    # Arrival/departure times nested dictionaries
    # keys: weekend or weekday
    # values: {keys: Time Identifier, values: Time Lower Bound, Time Upper Bounds and arrival/departure probabilities}
    arr_times_dict = {}
    weekday_arr_times_df = weekday_arr_times_df.set_index("TimeID")
    arr_times_dict["Weekday"] = weekday_arr_times_df.to_dict(orient="index")
    weekend_arr_times_df = weekend_arr_times_df.set_index("TimeID")
    arr_times_dict["Weekend"] = weekend_arr_times_df.to_dict(orient="index")
    dep_times_dict = {}
    weekday_dep_times_df = weekday_dep_times_df.set_index("TimeID")
    dep_times_dict["Weekday"] = weekday_dep_times_df.to_dict(orient="index")
    weekend_dep_times_df = weekend_dep_times_df.set_index("TimeID")
    dep_times_dict["Weekend"] = weekend_dep_times_df.to_dict(orient="index")

    # Convert percent SoCs to values between 0 and 1
    arr_soc_df["SoCLowerBound"] = arr_soc_df["SoCLowerBound"].div(100)
    arr_soc_df["SoCUpperBound"] = arr_soc_df["SoCUpperBound"].div(100)
    dep_soc_df["SoCLowerBound"] = dep_soc_df["SoCLowerBound"].div(100)
    dep_soc_df["SoCUpperBound"] = dep_soc_df["SoCUpperBound"].div(100)

    # SoC nested dictionaries for both arrival and departure
    # keys: SoC Identifier, values: SoC Lower Bounds, SOC Upper Bounds and their probabilities
    arr_soc_df = arr_soc_df.set_index("SoCID")
    arr_soc_dict = arr_soc_df.to_dict(orient="index")
    dep_soc_df = dep_soc_df.set_index("SoCID")
    dep_soc_dict = dep_soc_df.to_dict(orient="index")

    # EV nested dictionary
    # keys: EV models, values: their data and probability
    ev_df = ev_df.set_index("Model")
    ev_dict = ev_df.to_dict(orient="index")

    return arr_times_dict, dep_times_dict, arr_soc_dict, dep_soc_dict, ev_dict


def excel_to_sceneration_input_dependent_times(file_path):
    """
    This method converts the excel inputs into inputs suitable for the generate_fleet_data_dependent_times function under sceneration.py.

    Parameters
    ----------
    file_path : str
        File path of the Excel input file.
        
    Returns
    -------
    times_dict : dict
        Arrival-departure time combinations nested dictionary.
        keys: Arrival-departure time combination identifier, values: time upper and lower bounds.
    arr_dep_times_dict : dict
        Arrival-departure time combinations' probabilities nested dictionary.
        keys: Arrival-departure time combination identifier, values: their probabilities.
    arr_soc_dict : dict
        SoC nested dictionaries for arrival.
        keys: SoC Identifier, values: SoC Lower Bounds, SOC Upper Bounds and their probabilities.
    dep_soc_dict : dict
        SoC nested dictionaries for departure.
        keys: SoC Identifier, values: SoC Lower Bounds, SOC Upper Bounds and their probabilities.
    ev_dict : dict
        EV nested dictionary.
        keys: EV models, values: their data and probability.

    """

    # Read excel file
    times_df = pd.read_excel(file_path, "TimeIDDependentTime")
    arr_dep_times_df = pd.read_excel(file_path, "DependentTime")
    arr_soc_df = pd.read_excel(file_path, "ArrivalSoC")
    dep_soc_df = pd.read_excel(file_path, "DepartureSoC")
    ev_df = pd.read_excel(file_path, "EVData")

    times_df = times_df.set_index("TimeID")
    times_df["TimeLowerBound"] = times_df["TimeLowerBound"].round("S")
    times_df["TimeUpperBound"] = times_df["TimeUpperBound"].round("S")
    times_dict = times_df.T.to_dict("list")
    arr_dep_times_df = arr_dep_times_df.set_index("TimeID")
    arr_dep_times_dict = {}
    for arr_time_id, row in arr_dep_times_df.iterrows():
        id_list = []
        for dep_time_id, probability in row.items():
            id_list.append(arr_time_id)
            id_list.append(dep_time_id)
            id_tuple = tuple(id_list)
            arr_dep_times_dict[id_tuple] = probability
            id_list.clear()

    # Convert percent SoCs to values between 0 and 1
    arr_soc_df["SoCLowerBound"] = arr_soc_df["SoCLowerBound"].div(100)
    arr_soc_df["SoCUpperBound"] = arr_soc_df["SoCUpperBound"].div(100)
    dep_soc_df["SoCLowerBound"] = dep_soc_df["SoCLowerBound"].div(100)
    dep_soc_df["SoCUpperBound"] = dep_soc_df["SoCUpperBound"].div(100)

    # SoC nested dictionaries for both arrival and departure
    # keys: SoC Identifier, values: SoC Lower Bounds, SOC Upper Bounds and their probabilities
    arr_soc_df = arr_soc_df.set_index("SoCID")
    arr_soc_dict = arr_soc_df.to_dict(orient="index")
    dep_soc_df = dep_soc_df.set_index("SoCID")
    dep_soc_dict = dep_soc_df.to_dict(orient="index")

    # EV nested dictionary
    # keys: EV models, values: their data and probability
    ev_df = ev_df.set_index("Model")
    ev_dict = ev_df.to_dict(orient="index")

    return times_dict, arr_dep_times_dict, arr_soc_dict, dep_soc_dict, ev_dict


def generate_time_list(time_lowerb, time_upperb, timedelta_in_min, date):
    """
    Generates a datetime list with the given resolution and given date.

    Parameters
    ----------
    time_lowerb : datetime.datetime
        Start datetime.
    time_upperb : datetime.datetime
        End datetime.
    timedelta_in_min : int
        Resolution in minutes.
    date : datetime.datetime
        Date of the datetimes to be returned.

    Returns
    -------
    times : list
        Datetime list.

    """
    times = []
    times_str_list = [
        (time_lowerb + timedelta(hours=timedelta_in_min * i / 60)).strftime("%H:%M:%S")
        for i in range(
            int((time_upperb - time_lowerb).total_seconds() / 60.0 / timedelta_in_min)
        )
    ]
    for time_str in times_str_list:
        temp_time = dt.datetime.strptime(time_str, "%H:%M:%S")
        time = dt.datetime.combine(date, temp_time.time())
        times.append(time)
    return times


def generate_datetime_list(sdate, edate, timedelta_in_min):
    """
    Generates a datetime list with the given resolution.

    Parameters
    ----------
    sdate : TYPE
        Start datetime.
    edate : TYPE
        End datetime.
    timedelta_in_min : int
        Resolution in minutes.

    Returns
    -------
    datetime_lst : TYPE
        Datetime list.

    """
    diff_delta = edate - sdate  # as timedelta
    number_of_ts = int(diff_delta / dt.timedelta(minutes=timedelta_in_min))
    datetime_lst = []
    new_datetime = sdate
    for n in range(0, number_of_ts):
        datetime_lst.append(new_datetime)
        new_datetime = new_datetime + dt.timedelta(minutes=timedelta_in_min)
    return datetime_lst


def drange(x, y, jump):
    """
    Generate a range from x to y with jump spaces.
    
    Parameters
    ----------
    x : numpy.float64
        Start point.
    y : float
        End point.
    jump : str
        Space between generated jumps.

    Yields
    ------
    decimal.Decimal
        Parts in the equal range of the jump between x and y.

    """

    while x < y:
        yield float(x)
        x = decimal.Decimal(x) + decimal.Decimal(jump)


def visualize_statistical_time_generation(file_path, gen_ev_df, timedelta_in_min=15):
    """
    This method visualizes generated distribution of arrival and departure times of the generated fleet behavior.

    Parameters
    ----------
    file_path : str
        The file path for image files to be saved.
    gen_ev_df : pandas.core.frame.DataFrame
        Output data frame from generate_fleet_data function.
    timedelta_in_min : int, optional
        Resolution of the simulation in minutes. The default is 15.

    Returns
    -------
    None.

    """

    # Create times dicts for arrival and departure Keys: All possible time assignments, Values: number of assigned EVs
    current = dt.datetime(2022, 1, 1)  # arbitrary day
    datetime_lst = [
        current + timedelta(minutes=m) for m in range(0, 24 * 60, timedelta_in_min)
    ]
    arr_times_dict = {}
    dep_times_dict = {}
    # Initialize with 0
    for item in datetime_lst:
        arr_times_dict[item.strftime("%H:%M")] = 0
        dep_times_dict[item.strftime("%H:%M")] = 0
    for ev_id, row in gen_ev_df.iterrows():
        for time, value in arr_times_dict.items():
            if time == gen_ev_df.at[ev_id, "ArrivalTime"].strftime("%H:%M"):
                arr_times_dict[time] += 1
        for time, value in dep_times_dict.items():
            if time == gen_ev_df.at[ev_id, "DepartureTime"].strftime("%H:%M"):
                dep_times_dict[time] += 1
    # Plotting
    # Arrival times of EVs
    arr_times = list(arr_times_dict.keys())
    arr_values = list(arr_times_dict.values())
    plt.title("Arrival Times of EVs", size=16)
    plt.xlabel("Time", size=12)
    plt.ylabel("Number of EVs", size=12)
    plt.bar(arr_times, arr_values, color="g", width=0.4)
    plt.gca().yaxis.set_major_locator(tck.MultipleLocator(1))
    plt.gca().xaxis.set_major_locator(tck.MultipleLocator(10))
    plot_name = "arrival_times_of_EVs"
    plot_path = os.path.join(file_path, plot_name)
    plt.savefig(plot_path)
    # Clear memory
    plt.clf()
    # Departure times of EVs
    dep_times = list(dep_times_dict.keys())
    dep_values = list(dep_times_dict.values())
    plt.title("Departure Times of EVs", size=16)
    plt.xlabel("Time", size=12)
    plt.ylabel("Number of EVs", size=12)
    plt.bar(dep_times, dep_values, color="r", width=0.4)
    plt.gca().yaxis.set_major_locator(tck.MultipleLocator(1))
    plt.gca().xaxis.set_major_locator(tck.MultipleLocator(10))
    plot_name = "departure_times_of_EVs"
    plot_path = os.path.join(file_path, plot_name)
    plt.savefig(plot_path)


def output_to_sim_input(sce_output_df, xlfile, dc_power=False):
    """
    This function converts the fleet behavior (generated from statistical data) to the format that could be simulated
    in this simulation framework.

    Parameters
    ----------
    sce_output_df : pandas.core.frame.DataFrame
        Output data frame from generate_fleet_data function.
    xlfile : str
        Desired name of the output excel file.
    dc_power : bool, optional
        This parameter indicates whether dc or ac will be used as charging power in the simulation. 
        The default is False.

    Returns
    -------
    None.

    """

    sim_input_df = pd.DataFrame(
        columns=[
            "Battery Capacity (kWh)",
            "p_max_ch",
            "p_max_ds",
            "Real Arrival Time",
            "Real Arrival SOC",
            "Estimated Departure Time",
            "Target SOC @ Estimated Departure Time",
        ]
    )

    sim_input_df["Battery Capacity (kWh)"] = sce_output_df["BatteryCapacity"].values
    sim_input_df["Real Arrival Time"] = sce_output_df["ArrivalTime"].values
    sim_input_df["Real Arrival SOC"] = sce_output_df["ArrivalSoC"].values
    sim_input_df["Estimated Departure Time"] = sce_output_df["DepartureTime"].values
    sim_input_df["Target SOC @ Estimated Departure Time"] = sce_output_df[
        "DepartureSoC"
    ].values
    if dc_power is False:  # use AC-charging-powers
        sim_input_df["p_max_ch"] = sce_output_df["MaxChargingPower"].values
        sim_input_df["p_max_ds"] = sce_output_df["MaxChargingPower"].values
    else:  # use DC-fast-charging-powers
        sim_input_df["p_max_ch"] = sce_output_df["MaxFastChargingPower"].values
        sim_input_df["p_max_ds"] = sce_output_df["MaxFastChargingPower"].values
    # Simulation input dataframe to excel file
    sim_input_df.to_excel(xlfile)
