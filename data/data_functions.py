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
    fin_data.rename(columns={"Belegg pr. dag":"Belegg"}, inplace=True, errors="raise")
    return fin_data


############################ Dataset for optimalisering av bemanningsnivå ############################
def opt_dataset(dataset: pd.DataFrame, post: str, weekend: bool = False, predictions: bool = False, year: int = 2024, month: list = None, shift_type: str = None, scenario: str = None) -> pd.DataFrame:
    '''
    Function to extract the dataset to use for the optimization process og optimal staffing levels.

    params:
            dataset: Expected value pandas dataframe. Full dataset to be filtered
            
            post: Expected string value. The post at the hospital to filter on
            
            weekend: Expected boolean value. Default False, if True -> filter dataset by weekend values
            
            predictions: Expected boolean value. Default False, if True -> filter dataset on future forecasted values only
            
            year: Expected value integer. Default value 2024, if else -> filter by year of choice
            
            month: Expected value list. Default is None, if else -> filter by month of choice

            shift_type: Expected value string. Default is None, if else -> filter data by choice of shift type (dag, kveld, natt)
            
            scenario: Expected string value. Default None, if else -> filter values on the scenario of choice

    output: returns a pandas dataframe. 
    '''
    
    if post == "medisinsk":
        dataset = dataset[dataset["post"] == "medisinsk"]
    elif post == "kirurgisk":
        dataset = dataset[dataset["post"] == "kirurgisk"]
    
    if shift_type == "dag":
        dataset = dataset[dataset["skift_type"] == "dag"]
    elif shift_type == "kveld":
        dataset = dataset[dataset["skift_type"] == "kveld"]
    elif shift_type == "natt":
        dataset = dataset[dataset["skift_type"] == "natt"]
    

    if month is None:
        pass
    else:
        dataset = dataset.query(f"Måned in {month}")
    

    if weekend == True:
        dataset = dataset[dataset["helg"] == 1]
    else:
        dataset = dataset[dataset["helg"] == 0]

    if predictions == True:
        dataset = dataset[dataset["År"] == 2025]
        dataset["Antall inn på post"] = dataset["Prediksjoner pasientstrøm"]
        dataset["Belegg"] = dataset["Prediksjoner belegg"]
    else:
        dataset = dataset[dataset["År"] == year]
    
    if scenario == "helligdag":
        dataset["Antall inn på post"] = dataset["Antall inn på post"] + 15
        dataset["Belegg"] = dataset["Belegg"] + 10

    elif scenario == "høytid":
        if dataset["Antall inn på post"] >=2:
            dataset["Antall inn på post"] = dataset["Antall inn på post"] - 2
            dataset["Belegg"] = dataset["Belegg"] - 2

    elif scenario == "ulykke":
        dataset["Antall inn på post"] = dataset["Antall inn på post"] + 15
        dataset["Belegg"] = dataset["Belegg"] + 10

    elif scenario == "krig":
        dataset["Antall inn på post"] = dataset["Antall inn på post"] + 30
        dataset["Belegg"] = dataset["Belegg"] + 30

    # if year == 2024:
    #     dataset["Antall inn på post"] = dataset["Antall inn på post"].fillna(dataset["Prediksjoner pasientstrøm"])
    #     dataset["Belegg"] = dataset["Belegg"].fillna(dataset["Prediksjoner belegg"])
    dataset = dataset.reset_index()
    dataset.drop(["index"], axis=1, inplace=True)
    dataset = dataset[["DatoTid", "Antall inn på post", "Belegg"]]

    return dataset


############################ Dataset for prediksjoner ############################
def create_forecast_dataset(path: str, sheetname_med: str, sheetname_kir: str) -> pd.DataFrame:
    '''
    Function to load and transform the dataset containing the predictions.

    params:
            path: string parameter indicating the location of the excel file with the necessary sheets. 
    
    output: returns a pandas dataframe
    '''
    forecasted_med = pd.read_excel(path, sheet_name=sheetname_med)
    forecasted_kir = pd.read_excel(path, sheet_name=sheetname_kir)

    forecasted_med["post"] = "medisinsk"
    forecasted_kir["post"] = "kirurgisk"
    forecasted_demand = pd.concat([forecasted_med, forecasted_kir], axis=0).sort_values("Dato").reset_index()
    forecasted_demand.drop(["index"], axis=1, inplace=True)
    forecasted_demand['helg'] = forecasted_demand['Dato'].dt.weekday.apply(lambda x: 1 if x >= 5 else 0)
    forecasted_demand = forecasted_demand[forecasted_demand["Prediksjoner pasientstrøm"] >= 0]
    forecasted_demand.rename(columns={"Belegg pr. dag":"Belegg"}, inplace=True, errors="raise")
    return forecasted_demand


############################ Dataset for timesbaserte prediksjoner ############################
def create_forecast_hourly(data: pd.DataFrame, post: str) -> pd.DataFrame:
    use_poisson = True 
    variability_factor = 0.05

    # Create a DataFrame to hold the next year's dates
    next_year = pd.DataFrame({
        'Dato': pd.date_range('2025-01-01', '2025-10-15', freq='H').date,
        'Timer': pd.date_range('2025-01-01', '2025-10-15', freq='H').hour,
    })

    next_year['Dato'] = pd.to_datetime(next_year['Dato'].astype(str) + ' ' + next_year['Timer'].astype(str) + ':00:00')
    next_year['Dato'] = next_year['Dato'].dt.strftime('%Y-%m-%d %H:%M:%S')
    next_year['Dato'] = pd.to_datetime(next_year['Dato'])

    next_year['Predicted Demand'] = np.nan
    next_year['Predicted Belegg'] = np.nan

    for i, row in next_year.iterrows():
        historical_row = data[
            (data['DatoTid'] == row['Dato'] - pd.DateOffset(years=1)) &
            (data['Timer'] == row['Timer'])
        ]
        if not historical_row.empty:
            base_demand = historical_row['Antall inn på post'].values[0]
            base_belegg = historical_row['Belegg'].values[0]
            
            # Apply random variability
            if use_poisson:
                predicted_demand = np.random.poisson(base_demand * (1 + variability_factor))
                predicted_belegg = np.random.poisson(base_belegg * (1 + variability_factor))
            else:
                predicted_demand = np.random.normal(base_demand, base_demand * variability_factor)
                predicted_belegg = np.random.normal(base_belegg, base_belegg * variability_factor)
            
            next_year.at[i, 'Predicted Demand'] = max(0, predicted_demand)  # non-negative demand
            next_year.at[i, 'Predicted Belegg'] = max(0, predicted_belegg)  # non-negative demand

    next_year["Predicted Demand"].fillna(1.0, inplace=True)
    next_year["Predicted Belegg"].fillna(1.0, inplace=True)
    next_year["post"] = post
    next_year.rename(columns={"Dato": "DatoTid", "Predicted Demand":"Prediksjoner pasientstrøm", "Predicted Belegg": "Prediksjoner belegg"}, inplace=True, errors="raise")
    next_year = next_year[["DatoTid", "Timer", "Prediksjoner pasientstrøm", "Prediksjoner belegg", "post"]]

    next_year['helg'] = next_year['DatoTid'].dt.weekday.apply(lambda x: 1 if x >= 5 else 0)

    next_year["År"] = next_year['DatoTid'].dt.year
    next_year["Måned"] = next_year['DatoTid'].dt.month_name()
    next_year["Dag"] = next_year["DatoTid"].dt.day_name()
    next_year["Uke"] = next_year["DatoTid"].dt.isocalendar().week
    next_year["Timer"] = next_year["Timer"].astype(int) 
    return next_year



############################ Dataset for timesbaserte analyser ############################
def create_hourly_dataframe(path_med: str, path_kir: str) -> pd.DataFrame:
    hf_med_time = pd.read_excel(path_med, sheet_name="Results")
    hf_kir_time = pd.read_excel(path_kir, sheet_name="Results")

    hf_med_time = hf_med_time[hf_med_time["Timer"].apply(lambda x: not (pd.isna(x) or x == "."))]
    hf_med_time.reset_index(inplace=True)
    hf_med_time.drop("index", axis=1, inplace=True)

    hf_kir_time = hf_kir_time[hf_kir_time["Timer"].apply(lambda x: not (pd.isna(x) or x == "."))]
    hf_kir_time.reset_index(inplace=True)
    hf_kir_time.drop("index", axis=1, inplace=True)

    hf_med_time["post"] = "medisinsk"
    hf_kir_time["post"] = "kirurgisk"


    fin_data = pd.concat([hf_med_time, hf_kir_time], axis=0).sort_values("Dato").reset_index()
    fin_data.drop(["index"], axis=1, inplace=True)
    fin_data['helg'] = fin_data['Dato'].dt.weekday.apply(lambda x: 1 if x >= 5 else 0)

    fin_data["År"] = fin_data['Dato'].dt.year
    fin_data["Måned"] = fin_data['Dato'].dt.month_name()
    fin_data["Dag"] = fin_data["Dato"].dt.day_name()
    fin_data["Uke"] = fin_data["Dato"].dt.isocalendar().week
    fin_data["Timer"] = fin_data["Timer"].astype(int) 
    fin_data['DatoTid'] = fin_data['Dato'] + pd.to_timedelta(fin_data['Timer'], unit='h')

    fin_data = fin_data[["År", "Måned", "Uke", "Dag", "DatoTid", "Timer", "post", "helg", "Antall inn på post", "Antall pasienter ut av Post"]]
    fin_data.sort_values(by=["DatoTid"], inplace=True)
    fin_data = fin_data.reset_index()
    fin_data.drop(["index"], axis=1, inplace=True)

    


    return fin_data


############################ Funksjon for å kalkulere antall pasienter på post pr time ############################
initial_patients = 0
current_patients = initial_patients

def calculate_patients(row):
    global current_patients
    current_patients += row["Antall inn på post"] - row["Antall pasienter ut av Post"]
    current_patients = max(0, current_patients)
    
    return current_patients


############################ Funksjon for å definere skift type ############################
def add_shift_type(row):
    if 6 < row["Timer"] <= 14:
        shift_type = "dag"
    elif 14 < row["Timer"] <= 22:
        shift_type = "kveld"
    else: 
        shift_type = "natt"
        
    return shift_type