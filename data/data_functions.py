import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


############################ Datalast og Transformasjoner ############################
def datalast_behandling(path: str) -> pd.DataFrame:
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
def opt_dataset(dataset: pd.DataFrame, post: str, weekend: bool = False, predictions: bool = False, year: int = 2024) -> pd.DataFrame:
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
    else:
        df_fin = df_fin[df_fin["År"] == year]
    
    df_fin = df_fin.reset_index()
    df_fin.drop(["index"], axis=1, inplace=True)
    df_fin = df_fin[["Dato", "Antall inn på post", "Belegg pr. dag"]]

    return df_fin
