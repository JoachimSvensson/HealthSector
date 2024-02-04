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


def create_staffing_levels_average_week_plot(staffing_levels: pd.DataFrame, month:str, observed_kpi: str):
    
    if month == 'All':
        staffing_levels = staffing_levels
    else:
        staffing_levels = staffing_levels[staffing_levels['Month'] == month]
    staffing_levels.drop('Month',axis=1, inplace=True)


    # Create average week
    staffing_levels = staffing_levels.groupby(staffing_levels.index.dayofweek).mean().round().reset_index(drop =False, names = ["Day", "Hour", "Minute"])
    days = ["Monday ", "Tuesday ", "Wednesday ", "Thursday " , "Friday ", "Saturday ", "Sunday "]
    staffing_levels["Day"] = staffing_levels["Day"].apply(lambda x: days[x])

    # Plotting
    plt.figure(figsize=(10, 6))  # Adjust the figure size as needed

    # Plot the time series
    plt.plot(staffing_levels['Day'], staffing_levels[observed_kpi], label=observed_kpi)

    # Set labels and title
    plt.xlabel('Average Week')
    plt.ylabel(observed_kpi)
    plt.title(f'Time Series Plot of {observed_kpi}')
    plt.ylim(0, staffing_levels[observed_kpi].max() + 5)
    plt.legend()
    plt.show()

