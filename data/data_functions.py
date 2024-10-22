import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


############################ Datalast og Transformasjoner ############################
def datalast_behandling(path: str) -> pd.DataFrame:
    '''
    Function to load the necessary data and do simple transformations
    
    params:
            path: string parameter indicating the location of the excel file with the necessary sheets. 
    
    output: returns a pandas dataframe
    
    '''
    fin_hf_med = pd.read_excel(path, sheet_name = "medisinsk hammerfest")
    fin_hf_kir_ort = pd.read_excel(path, sheet_name = "kirurgisk hammerfest")

    # post kolonne
    fin_hf_med["post"] = "medisinsk"
    fin_hf_kir_ort["post"] = "kirurgisk"

    # merge and order datasets
    fin_data = pd.concat([fin_hf_med, fin_hf_kir_ort], axis=0).sort_values("Dato").reset_index()
    fin_data.drop(["index"], axis=1, inplace=True)
    fin_data['helg'] = fin_data['Dato'].dt.weekday.apply(lambda x: 1 if x >= 5 else 0)
    return fin_data


############################ Dataset for optimalisering av bemanningsnivå ############################
def opt_dataset(dataset: pd.DataFrame, post: str, weekend: bool = False, predictions: bool = False, year: int = 2024, scenario: str = None) -> pd.DataFrame:
    '''
    Function to extract the dataset to use for the optimization process og optimal staffing levels.

    params:
            dataset: Expected value pandas dataframe. Full dataset to be filtered
            
            post: Expected string value. The post at the hospital to filter on
            
            weekend: Expected boolean value. Default False, if True -> filter dataset by weekend values
            
            predictions: Expected boolean value. Default False, if True -> filter dataset on future forecasted values only
            
            year: Expected value integer. Default value 2024, if else -> filter by year of choice
            
            scenario: Expected string value. Default None, if else -> filter values on the scenario of choice

    output: returns a pandas dataframe. 
    '''
    
    if post == "medisinsk":
        df_fin = dataset[dataset["post"] == "medisinsk"]
    elif post == "kirurgisk":
        df_fin = dataset[dataset["post"] == "kirurgisk"]
    
    if weekend == True:
        df_fin = df_fin[df_fin["helg"] == 1]
    else:
        df_fin = df_fin[df_fin["helg"] == 0]

    if predictions == True:
        df_fin = df_fin[df_fin["År"] == 2025]
        df_fin["Antall inn på post"] = df_fin["Prediksjoner pasientstrøm"]
        df_fin["Belegg pr. dag"] = df_fin["Prediksjoner belegg"]
    else:
        df_fin = df_fin[df_fin["År"] == year]
    
    if scenario == "helligdag":
        df_fin["Antall inn på post"] = df_fin["Antall inn på post"] + 15
        df_fin["Belegg pr. dag"] = df_fin["Belegg pr. dag"] + 10

    elif scenario == "høytid":
        if df_fin["Antall inn på post"] >=2:
            df_fin["Antall inn på post"] = df_fin["Antall inn på post"] - 2
            df_fin["Belegg pr. dag"] = df_fin["Belegg pr. dag"] - 2

    elif scenario == "ulykke":
        df_fin["Antall inn på post"] = df_fin["Antall inn på post"] + 15
        df_fin["Belegg pr. dag"] = df_fin["Belegg pr. dag"] + 10

    elif scenario == "krig":
        df_fin["Antall inn på post"] = df_fin["Antall inn på post"] + 30
        df_fin["Belegg pr. dag"] = df_fin["Belegg pr. dag"] + 30

    if year == 2024:
        df_fin["Antall inn på post"] = df_fin["Antall inn på post"].fillna(df_fin["Prediksjoner pasientstrøm"])
    df_fin = df_fin.reset_index()
    df_fin.drop(["index"], axis=1, inplace=True)
    df_fin = df_fin[["Dato", "Antall inn på post", "Belegg pr. dag"]]

    return df_fin


############################ Dataset for Prediksjoner ############################
def create_forecast_dataset(path: str) -> pd.DataFrame:
    '''
    Function to load and transform the dataset containing the predictions.

    params:
            path: string parameter indicating the location of the excel file with the necessary sheets. 
    
    output: returns a pandas dataframe
    '''
    forecasted_med = pd.read_excel(path, sheet_name="hammerfest_medisinsk")
    forecasted_kir = pd.read_excel(path, sheet_name="hammerfest_kirurgisk")

    forecasted_med["post"] = "medisinsk"
    forecasted_kir["post"] = "kirurgisk"
    forecasted_demand = pd.concat([forecasted_med, forecasted_kir], axis=0).sort_values("Dato").reset_index()
    forecasted_demand.drop(["index"], axis=1, inplace=True)
    forecasted_demand['helg'] = forecasted_demand['Dato'].dt.weekday.apply(lambda x: 1 if x >= 5 else 0)
    forecasted_demand = forecasted_demand[forecasted_demand["Prediksjoner pasientstrøm"] >= 0]
    return forecasted_demand