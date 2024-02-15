import pandas as pd
from pyworkforce.queuing import MultiErlangC
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np


st.cache_data()
def compute_staffing_levels(demand, aht, interval, asa, shrinkage, service_level, max_occupancy):
   
    param_grid = {
        "transactions": demand, 
        "aht": aht, 
        "interval": interval, 
        "asa": asa, 
        "shrinkage": shrinkage        
    }
   
    multi_erlang = MultiErlangC(param_grid=param_grid, n_jobs=-1)
    required_positions_scenarios = {"service_level": service_level, "max_occupancy": max_occupancy}
    positions_requirements = multi_erlang.required_positions(required_positions_scenarios)
    df = pd.DataFrame.from_dict(positions_requirements)
    df.index = demand.index
    staffing_levels = pd.concat([demand, df], axis=1)
    staffing_levels.columns = ["Number of surgeries", "Raw Staffing Level", "Staffing Level",
                               "Service Level (%)", "Occupancy (%)", "Waiting Probability (%)"]
    
    percentage_columns = ["Service Level (%)", "Occupancy (%)", "Waiting Probability (%)"]
    
    pd.options.display.float_format = '{:,.2f}'.format
    
    staffing_levels[percentage_columns] = staffing_levels[percentage_columns].apply(lambda x: x*100)
    staffing_levels = staffing_levels.round(2)
    return staffing_levels


def create_staffing_levels_average_week_plot(staffing_levels: pd.DataFrame, month:str, observed_kpi: str, aggregation_level: str = 'year'):
    
    if month == 'All':
        staffing_levels = staffing_levels
    else:
        staffing_levels = staffing_levels[staffing_levels['Month'] == month]


    if aggregation_level != 'year':
        staffing_levels = staffing_levels[staffing_levels.columns.tolist()[:-1]]
        # Create average week
        staffing_levels = staffing_levels.groupby(staffing_levels.index.dayofweek).mean().round().reset_index(drop =False, names = ["Day", "Hour", "Minute"])
        days = ["Monday ", "Tuesday ", "Wednesday ", "Thursday " , "Friday ", "Saturday ", "Sunday "]
        staffing_levels["Day"] = staffing_levels["Day"].apply(lambda x: days[x])

        # Plotting
        plt.figure(figsize=(20, 12))  # Adjust the figure size as needed

        # Plot the time series
        plt.plot(staffing_levels['Day'], staffing_levels[observed_kpi], label=observed_kpi)

        # Set labels and title
        plt.xlabel('Average Week')
        plt.ylabel(observed_kpi)
        plt.title(f'Time Series Plot of {observed_kpi}')
        plt.ylim(0, staffing_levels[observed_kpi].max() + 1)
        plt.legend()
        plt.show()
        
    else:

        plt.figure(figsize=(30, 18))

        # Assuming you have lists of days and corresponding values
        days = [str(date) for date in staffing_levels.index]
        handling_times = [0.5,3,7,24,72]
        for i in handling_times:
            values = staffing_levels[f'{observed_kpi} ({i})']  # Corresponding values
            # Assuming you have a list of months (e.g., "Jan", "Feb", etc.)
            months = staffing_levels['Month (72)']  # List of months corresponding to each day
            # Plotting
            color = plt.cm.viridis((i%13 * 20))
            plt.plot(np.arange(len(days)), values, label = f'{observed_kpi} ({i})', color=color)

        plt.xlabel('Days & Months of Year')
        plt.ylabel(f'{observed_kpi}')
        plt.title(f'Time Series Plot of {observed_kpi}')
        month_ticks = [days.index(day) for day in days if day[8:10] == '01']  # Index of the first day of each month
        month_labels = [months[days.index(day)] for day in days if day[8:10] == '01']  # Corresponding month labels

        plt.xticks(month_ticks, month_labels, rotation=45)  # Setting ticks and labels to show each month
        legend = plt.legend()
        for line, text in zip(legend.get_lines(), legend.get_texts()):
            text.set_color(line.get_color())
        plt.show()