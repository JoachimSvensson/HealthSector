import pandas as pd
from pyworkforce.queuing import MultiErlangC
import streamlit as st

st.cache_data()
def compute_staffing_levels(demand, aht, planning_period, asa, shrinkage, service_level, max_occupancy, Type):
   
    param_grid = {
        "transactions": demand.Predictions, 
        "aht": aht, 
        "interval": planning_period, 
        "asa": asa, 
        "shrinkage": shrinkage        
    }
   
    multi_erlang = MultiErlangC(param_grid=param_grid, n_jobs=-1)
    required_positions_scenarios = {"service_level": service_level, "max_occupancy": max_occupancy}
    positions_requirements = multi_erlang.required_positions(required_positions_scenarios)
    df = pd.DataFrame.from_dict(positions_requirements)
    df.index = demand.index
    staffing_levels = pd.concat([demand, df], axis=1)
    
    staffing_levels.columns = ["Number of Calls", "Raw Staffing Level", "Staffing Level",
                               "Service Level (%)", "Occupancy (%)", "Waiting Probability (%)"]
    
    percentage_columns = ["Service Level (%)", "Occupancy (%)", "Waiting Probability (%)"]
    
    pd.options.display.float_format = '{:,.2f}'.format
    
    staffing_levels[percentage_columns] = staffing_levels[percentage_columns].apply(lambda x: x*100)
    staffing_levels = staffing_levels.round(2)
    staffing_levels["call_type"] = Type
    return staffing_levels
