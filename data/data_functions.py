import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os


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
def opt_dataset(dataset: pd.DataFrame, post: str, weekend: bool = False, predictions: bool = False, year: list = [2024], month: list = None, shift_type: str = None, scenario: str = None) -> pd.DataFrame:
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
        # dataset = dataset[dataset["År"] == year]
        dataset = dataset.query(f"År in {year}")

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
    dataset = dataset[["DatoTid", "Timer", "skift_type", "Antall inn på post", "Belegg"]]

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

############################ Funksjon for å lese inn alle filer fra mappe ############################
def read_folder_to_dfs(folder_path:str, file_extension:str = ".xlsx") -> dict:
    """
    Reads all files with a specific extension from a folder into separate pandas DataFrames.
    
    Parameters:
    - folder_path (str): Path to the folder containing files.
    - file_extension (str): Extension of the files to read. Default is ".csv".
    
    Returns:
    - dict: A dictionary where keys are file names without extensions and values are DataFrames.
    """
    dfs = {}
    
    for filename in os.listdir(folder_path):
        if filename.endswith(file_extension):
            file_path = os.path.join(folder_path, filename)
            df = pd.read_excel(file_path) if file_extension == ".xlsx" else pd.read_csv(file_path)
            file_key = os.path.splitext(filename)[0]
            dfs[file_key] = df
            
    return dfs

############################ Funksjon for å lage timesbasert one big table ############################
def create_hourly_obt(dfs_dict:dict)-> pd.DataFrame:
    """
    Creates hourly dataframes into one big table of all years.
    
    Parameters:
    - dfs_dict (dict): Dictionary containing all dataframes to be transformed
    
    Returns:
    - obt_df: A dataframe containing the transformed dataframes of every year into one big table.
    """
    df_list = []
    for df in dfs_dict:
        dataframe = dfs_dict[df]
        try:
            dataframe = dataframe[dataframe["Timer"].apply(lambda x: not (pd.isna(x) or x == "."))]
        except KeyError:
            dataframe = dataframe[dataframe["Timer (0-23)"].apply(lambda x: not (pd.isna(x) or x == "."))]
        dataframe.reset_index(inplace=True)
        dataframe.drop("index", axis=1, inplace=True)
        try:
            dataframe.rename(columns={"Måned-1":"Måned", "Timer (0-23)":"Timer"}, inplace=True, errors="raise") 
        except:
            pass
        if df[:3] == "med":
            dataframe["post"] = "medisinsk"
        else:
            dataframe["post"] = "kirurgisk"
        df_list.append(dataframe)

    obt_df = pd.concat(df_list, axis=0, ignore_index=True)
    obt_df['helg'] = obt_df['Dato'].dt.weekday.apply(lambda x: 1 if x >= 5 else 0)
    obt_df["År"] = obt_df['Dato'].dt.year
    obt_df["Måned"] = obt_df['Dato'].dt.month_name()
    obt_df["Dag"] = obt_df["Dato"].dt.day_name()
    obt_df["Uke"] = obt_df["Dato"].dt.isocalendar().week
    obt_df["Timer"] = obt_df["Timer"].astype(int) 
    obt_df['DatoTid'] = obt_df['Dato'] + pd.to_timedelta(obt_df['Timer'], unit='h')

    obt_df = obt_df[["År", "Måned", "Uke", "Dag", "DatoTid", "Timer", "post", "helg", "Antall inn på post", "Antall pasienter ut av Post"]]
    obt_df = obt_df.sort_values(by=["DatoTid"]).reset_index()
    obt_df.drop(["index"], axis=1, inplace=True)
    return obt_df

############################ Funksjon for å kalkulere antall pasienter på post pr time ############################
initial_patients = 22
current_patients = initial_patients
previous_year = None 

def calculate_patients(row):
    global current_patients, previous_year
    
    if previous_year is not None and row["År"] != previous_year:
        current_patients = 22
    previous_year = row["År"]

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



############################# Bemanningsverktøyet #############################
def bemanningsverktoy(df, tidsperiode, skift, aggregering, visualiseringskolonne):
    kombinert_tabell = df
    if tidsperiode == "hele perioden":
        kombinert_tabell = kombinert_tabell
    else:
        tidsperiode = pd.to_datetime(tidsperiode)
        start, end = tidsperiode
        kombinert_tabell = kombinert_tabell[(kombinert_tabell["DatoTid"] >= start) & (kombinert_tabell["DatoTid"] <= end)] 
    
    
    if skift != "alle skift":
        skifttype = skift
        kombinert_tabell = kombinert_tabell[kombinert_tabell["skift_type"] == skifttype]   
    else:
        kombinert_tabell = kombinert_tabell
    
    # ukesnivå
    if aggregering == "gjennomsnittlig uke":
        # Average week
        tabell = kombinert_tabell.groupby(["Dag", "Timer"])[visualiseringskolonne].mean().reset_index()
        # result = result.pivot(index="Timer", columns="Dag", values=visualiseringskolonne)
    elif aggregering == "beste uke":
        result = kombinert_tabell.groupby("Uke")[visualiseringskolonne].mean().idxmin()
        tabell = kombinert_tabell[kombinert_tabell["Uke"] == result]
    elif aggregering == "dårligste uke":
        result = kombinert_tabell.groupby("Uke")[visualiseringskolonne].mean().idxmax()
        tabell = kombinert_tabell[kombinert_tabell["Uke"] == result]
    
    # Dagsnivå
    elif aggregering == "gjennomsnittlig dag":
        tabell = kombinert_tabell.groupby("Timer")[visualiseringskolonne].mean().reset_index()
    elif aggregering == "beste dag":
        result = kombinert_tabell.groupby(["Uke","Dag"])[visualiseringskolonne].mean().idxmin()
        tabell = kombinert_tabell[kombinert_tabell[["Uke", "Dag"]].apply(tuple, axis=1) == result]
        if len(tabell) < 80:
            result = kombinert_tabell.groupby(["Uke","Dag"])[visualiseringskolonne].mean().nsmallest(2).idxmax()
            tabell = kombinert_tabell[kombinert_tabell[["Uke", "Dag"]].apply(tuple, axis=1) == result]
    elif aggregering == "dårligste dag":
        result = kombinert_tabell.groupby(["Uke","Dag"])[visualiseringskolonne].mean().idxmax()
        tabell = kombinert_tabell[kombinert_tabell[["Uke", "Dag"]].apply(tuple, axis=1) == result]  
        
    # skift nivå
    elif aggregering == "gjennomsnittlig skift":
        tabell = kombinert_tabell.groupby("skift_type")[visualiseringskolonne].mean().reset_index()
    try:
        if aggregering == "beste skift":
            result = kombinert_tabell.groupby(["Uke","Dag"])[visualiseringskolonne].mean().idxmin()
            tabell = kombinert_tabell[kombinert_tabell[["Uke", "Dag"]].apply(tuple, axis=1) == result]
            if len(tabell) < 15:
                result = kombinert_tabell.groupby(["Uke","Dag"])[visualiseringskolonne].mean().nsmallest(2).idxmax()
                tabell = kombinert_tabell[kombinert_tabell[["Uke", "Dag"]].apply(tuple, axis=1) == result]
        elif aggregering == "dårligste skift":
            result = kombinert_tabell.groupby(["Uke","Dag"])[visualiseringskolonne].mean().idxmax()
            tabell = kombinert_tabell[kombinert_tabell[["Uke", "Dag"]].apply(tuple, axis=1) == result]
    except:
        tabell = None
    
    
    if "hele perioden" in tidsperiode and aggregering == "hele perioden":
        visualisering = kombinert_tabell[visualiseringskolonne].tolist()
        plt.figure(figsize=(20, 8))
        # plt.plot(kombinert_tabell["DatoTid"],needed_nurses_intensity_rounded, marker='o', color='g', linestyle='-')
        plt.plot(kombinert_tabell["DatoTid"],visualisering, marker='o', color='g', linestyle='-')
        plt.title(f'Variasjon i {visualiseringskolonne} for post hos Finnmarksykehuset gjennom tidsperiode')
        # plt.axhline(y=1.0, color="r", linewidth = 2, linestyle = "-")
        plt.xlabel('Tidsperiode')
        plt.ylabel(f'{visualiseringskolonne} (i desimal)')
        plt.grid(True)
        plt.xticks(kombinert_tabell['DatoTid'].dt.date.unique().tolist(), rotation=45)
        plt.tight_layout()
        plt.show()

    else:
        try:
            df = tabell
            # Konverter Timer til datetime.time og deretter til minutter siden midnatt
            df["Timer"] = pd.to_datetime(df["Timer"], format="%H:%M:%S").dt.time
            df["Minutes"] = df["Timer"].apply(lambda t: t.hour * 60 + t.minute)

            # Lag plottet
            plt.figure(figsize=(12, 6))

            if aggregering in ["gjennomsnittlig uke", "beste uke", "dårligste uke"]:
                # Plot en linje for hver dag
                for dag in df["Dag"].unique():
                    subset = df[df["Dag"] == dag]
                    plt.plot(subset["Minutes"], subset[visualiseringskolonne], marker="o", label=dag)

            else:
                plt.plot(df["Minutes"], df[visualiseringskolonne], marker="o")

            # Tilpass aksene
            plt.xlabel("Tid", fontsize=12)
            plt.ylabel(visualiseringskolonne, fontsize=12)
            plt.title(f"{visualiseringskolonne} for {aggregering} over {tidsperiode}", fontsize=14)
            plt.xticks(
                ticks=[i * 60 for i in range(24)],
                labels=[f"{i:02d}:00" for i in range(24)],  # Viser timer fra 00:00 til 23:00
                rotation=45,
                fontsize=10,
            )
            if aggregering in ["gjennomsnittlig uke", "beste uke", "dårligste uke"]:
                plt.legend(title="Dag", fontsize=10)
                
            plt.grid(True, linestyle="--", alpha=0.7)
            plt.tight_layout()
            # plt.show()
        except:
            pass
    # return df




# def oppdater_bemanningsplan(df, bemanningsplan, ppp_df):
#     from datetime import time
#     bemanningsplan["AntallAnsatte"] = 0
#     bemanningsplan["PreDef_PPP"] = 0

#     for _, row in df.iterrows():
#         start_time = row["Start"]
#         end_time = row["End"]
#         weeks = [int(w) for w in row["Week"].split("-")]

#         for day_idx, day in enumerate(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]):
#             employees = row[day]
#             if len(ppp_df) > 0:
#                 ppp = ppp_df.columns[2:-2][day_idx]
#                 ppp_level = ppp_df.loc[_, ppp]
#             for week in weeks:
#                 if start_time <= end_time:  # Vanlig skift innenfor samme dag
#                     mask = (
#                         (bemanningsplan["Uke"] == week) &
#                         (bemanningsplan["Dag"] == day) &
#                         (bemanningsplan["Timer"] >= start_time) &
#                         (bemanningsplan["Timer"] < end_time)
#                     )
#                     bemanningsplan.loc[mask, "AntallAnsatte"] += employees
#                     if len(ppp_df) > 0:
#                         bemanningsplan.loc[mask, "PreDef_PPP"] += ppp_level

#                 else:  # Skift som går over til neste dag
#                     mask_day1 = (
#                         (bemanningsplan["Uke"] == week) &
#                         (bemanningsplan["Dag"] == day) &
#                         (bemanningsplan["Timer"] >= start_time) &
#                         (bemanningsplan["Timer"] < time(23,59, 59))
#                     )
#                     bemanningsplan.loc[mask_day1, "AntallAnsatte"] += employees
#                     if len(ppp_df) > 0:
#                         bemanningsplan.loc[mask_day1, "PreDef_PPP"] += ppp_level

#                     # Timer fra midnatt til neste skift
#                     next_day_idx = (day_idx + 1) % 7  
#                     next_day = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][next_day_idx]
#                     mask_day2 = (
#                         (bemanningsplan["Uke"] == week) &
#                         (bemanningsplan["Dag"] == next_day) &
#                         (bemanningsplan["Timer"] >= time(0,0)) &
#                         (bemanningsplan["Timer"] < end_time)
#                     )
#                     bemanningsplan.loc[mask_day2, "AntallAnsatte"] += employees
#                     if len(ppp_df) > 0:
#                         bemanningsplan.loc[mask_day2, "PreDef_PPP"] += ppp_level

#     return bemanningsplan


def oppdater_bemanningsplan(df, bemanningsplan, ppp_df):
    from datetime import time
    bemanningsplan["AntallAnsatte"] = 0
    bemanningsplan["PreDef_PPP"] = 0

    days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    for index, row in df.iterrows():
        start_time = row["Start"]
        end_time = row["End"]
        weeks = [int(w) for w in row["Week"].split("-")]

        for day_idx, day in enumerate(days_of_week):
            employees = row[day]
            if len(ppp_df) > 0:
                ppp = ppp_df.columns[3:-2][day_idx]
                ppp_level = ppp_df.loc[index, ppp]

            mask = (bemanningsplan["Dag"] == day) & (bemanningsplan["Uke"].isin(weeks))

            # Convert start_time and end_time to datetime for comparison
            start_datetime = pd.to_datetime(f"2000-01-01 {start_time}", format="%Y-%m-%d %H:%M:%S")
            end_datetime = pd.to_datetime(f"2000-01-01 {end_time}", format="%Y-%m-%d %H:%M:%S")

            if start_datetime <= end_datetime:
                # When the shift is within the same day
                mask = mask & (bemanningsplan["Timer"].between(start_datetime.time(), (end_datetime - pd.Timedelta(seconds=1)).time()))
            else:
                # For shifts that go over midnight
                mask1 = mask & (bemanningsplan["Timer"].between(start_datetime.time(), time(23, 59, 59)))
                mask2 = mask & (bemanningsplan["Timer"].between(time(0, 0), end_datetime.time()))
                mask = mask1 | mask2

            bemanningsplan.loc[mask, "AntallAnsatte"] += employees
            if len(ppp_df) > 0:
                bemanningsplan.loc[mask, "PreDef_PPP"] += ppp_level

    return bemanningsplan



# def oppdater_bemanningsplan(df, bemanningsplan, ppp_df):
#     from datetime import time
#     bemanningsplaner = df.Navn.unique().tolist()
#     for plan in bemanningsplaner:
#         bemanningsplan[f"{plan}_AntallAnsatte"] = 0
#         bemanningsplan[f"{plan}_PreDef_PPP"] = 0
#         df_test = df[df["Navn"] == plan]
#         for _, row in df_test.iterrows():
#             start_time = row["Start"]
#             end_time = row["End"]
#             weeks = [int(w) for w in row["Week"].split("-")]

#             for day_idx, day in enumerate(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]):
#                 employees = row[day]
#                 if len(ppp_df) > 0:
#                     ppp = ppp_df.columns[2:-2][day_idx]
#                     ppp_level = ppp_df.loc[_, ppp]
#                 for week in weeks:
#                     if start_time <= end_time:  # Vanlig skift innenfor samme dag
#                         mask = (
#                             (bemanningsplan["Uke"] == week) &
#                             (bemanningsplan["Dag"] == day) &
#                             (bemanningsplan["Timer"] >= start_time) &
#                             (bemanningsplan["Timer"] < end_time)
#                         )
#                         bemanningsplan.loc[mask, f"{plan}_AntallAnsatte"] += employees
#                         if len(ppp_df) > 0:
#                             bemanningsplan.loc[mask, f"{plan}_PreDef_PPP"] += ppp_level

#                     else:  # Skift som går over til neste dag
#                         mask_day1 = (
#                             (bemanningsplan["Uke"] == week) &
#                             (bemanningsplan["Dag"] == day) &
#                             (bemanningsplan["Timer"] >= start_time) &
#                             (bemanningsplan["Timer"] < time(23,59, 59))
#                         )
#                         bemanningsplan.loc[mask_day1, f"{plan}_AntallAnsatte"] += employees
#                         if len(ppp_df) > 0:
#                             bemanningsplan.loc[mask_day1, f"{plan}_PreDef_PPP"] += ppp_level

#                         # Timer fra midnatt til neste skift
#                         next_day_idx = (day_idx + 1) % 7  
#                         next_day = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][next_day_idx]
#                         mask_day2 = (
#                             (bemanningsplan["Uke"] == week) &
#                             (bemanningsplan["Dag"] == next_day) &
#                             (bemanningsplan["Timer"] >= time(0,0)) &
#                             (bemanningsplan["Timer"] < end_time)
#                         )
#                         bemanningsplan.loc[mask_day2, f"{plan}_AntallAnsatte"] += employees
#                         if len(ppp_df) > 0:
#                             bemanningsplan.loc[mask_day2, f"{plan}_PreDef_PPP"] += ppp_level

#     return bemanningsplan




def nightshift_weight(row: pd.Series) -> pd.Series:
    import math
    row["Belegg"] = int(math.ceil(row["Belegg"]*(row["DøgnrytmeAktivitet"]/10)))
    return row

def PPP(row: pd.Series) -> int:
    import math
    try:
        ppp = round(row['Belegg']/row["AntallAnsatte"], 2)
    except ZeroDivisionError:
        ppp = row["Belegg"]
    return ppp

def SkiftIntensitet(row: pd.Series) -> int:
    try:
        SI = row['Belegg']/ (row["AntallAnsatte"]*row["PreDef_PPP"])
    except ZeroDivisionError:
        SI = 0
    return SI

def create_quarterly_times_and_update_timer(row):
    times = []
    timer_values = []
    for minute in [0, 15, 30, 45]:
        new_time = row['DatoTid'].replace(minute=minute, second=0)
        times.append(new_time)
        timer_values.append(new_time.time())
    return list(zip(times, timer_values))

def add_shift_type_quarterly(row):
    from datetime import datetime
    morning_start = datetime.strptime("07:15:00", "%H:%M:%S").time()
    afternoon_start = datetime.strptime("14:45:00", "%H:%M:%S").time()
    evening_start = datetime.strptime("21:45:00", "%H:%M:%S").time()
    
    row_time = row["Timer"]

    # Sammenligning
    if morning_start < row_time <= afternoon_start:
        shift_type = "dag"
    elif afternoon_start < row_time <= evening_start:
        shift_type = "kveld"
    else: 
        shift_type = "natt"
        
    return shift_type

# def match_and_add_activity(df, row):
#     # row["Timer"] = str(row["Timer"])
#     # df['End'] = df['End'].astype(str)
#     matching_rows = df[
#         (df['Start'] <= row["Timer"]) & 
#         (row["Timer"] <= df['End'])
#     ]
    
#     if not matching_rows.empty:
#         return matching_rows.iloc[0]['Aktivitet']
#     else:
#         return None
    

def match_and_add_activity(df, row):
    import numpy as np
    start_times = df['Start'].values
    end_times = df['End'].values
    timer = row["Timer"]

    matching_condition = (start_times <= timer) & (timer <= end_times)
    matching_rows = df[matching_condition]

    if not matching_rows.empty:
        return matching_rows.iloc[0]['Aktivitet']
    return None




def remove_microseconds(time_str):
    from datetime import datetime
    time_obj = datetime.strptime(time_str, '%H:%M:%S.%f').time()
    return time_obj # .strftime('%H:%M:%S')