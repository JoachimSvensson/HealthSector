import pandas as pd 
import datetime
import holidays
import streamlit as st 
import numpy as np 
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

def create_horizon_dates(s_start, horizon, f):
    start_date = pd.to_datetime(s_start, format = "%Y/%m/%d")
    end_date = start_date + datetime.timedelta(weeks= horizon, hours= 23, minutes= 59)
    return pd.date_range(start= start_date, end = end_date, freq= f"{f}min")

def create_horizon_data(dates):
    data = pd.DataFrame(index = dates)
    data["hour"] = data.index.hour
    data["month"] = data.index.month
    data["year"] = data.index.year
    data["day"] = data.index.day
    data["dow"] = data.index.day_of_week +1
    data["minute"] = data.index.minute
    data["Weekend"] = (data["dow"] >5).astype(int)
    data["holiday"] = 0
    
    hol = holidays.Norway(years=data.index.year.unique().tolist())
    translated_holidays = {'Andre påskedag' : "Easter",
    'Andre juledag' : "Christmas",
    'Arbeidernes dag' : "Worker's day",
    'Første juledag' : "Christmas",
    'Kristi himmelfartsdag' : "Easter",
    'Skjærtorsdag' : "Easter",
    'Andre pinsedag' : "Pentecost",
    'Første pinsedag' : "Pentecost",
    'Langfredag' : "Easter",
    'Første nyttårsdag': "New year",
    'Grunnlovsdag' : "Constitution day",
    'Første påskedag' : "Easter"}

    for date, holiday in hol.items():
        data.loc[str(date), "holiday"] = translated_holidays[holiday]
    data.loc[(data["month"] == 12) & (data["day"] == 31), "holiday"] = "New year"
    data.loc[(data["month"] == 12) & (data["day"] >= 21) & (data["day"] <= 28), "holiday"] = "Christmas"

    for holiday in translated_holidays.values():
        data[holiday] = 0
        data.loc[data["holiday"] == holiday, holiday] = 1
    data.drop(columns= "holiday", inplace = True)
    data.dropna(subset= ["day"], inplace = True)
    seasons = {1: "Winter", 2:"Spring", 3: "Summer", 4:"Autumn"}
    months_to_seasons = dict(zip(list(range(1,13)), [1]*2 + [2]*3 + [3]*3 + [4]*3 + [1] *1))
    data["season"] = data.month.apply(lambda x: months_to_seasons[x])
    return data

def create_prediction_output(x,y, type):
    data = pd.DataFrame(index = x)
    data["Predictions"] = (np.round(y.flatten())).astype("int")
    return data

@st.cache_data()
def plot_predictions(show_pred, show_train, show_train_pred, Type, n):
    predictions = st.session_state[f"call_forecast"][n].copy(deep =  True)
    train = pd.DataFrame(st.session_state[f"full_train_dfs_{Type}"][0].copy(deep =  True))
    train_pred = st.session_state[f"Train_pred_{Type}"].copy(deep =  True)
    fig, ax = plt.subplots(figsize = (10,4))
    indeces = []
    if show_pred & (show_train_pred or show_train):
        predictions = predictions.resample("W").mean()
        indeces.extend(predictions.index.tolist())
        if show_train_pred:
            train_pred = train_pred.resample("W").mean() 
            indeces.extend(train_pred.index.tolist())
        if show_train:
            train = train.resample("W").mean()
            indeces.extend(train.index.tolist())
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=24*7*8)) 
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        ax.set_ylabel("Average n. of calls (hourly)", fontname= "Times New Roman", fontsize = 16, labelpad = 6)
        ax.set_title(f"{st.session_state['Data_info'][0]} - {Type} calls: history and forecast", fontname= "Times New Roman", fontsize = 18, pad = 10)
    elif show_pred and not(show_train_pred or show_train):
        predictions = predictions.resample("D").sum()
        indeces = predictions.index.tolist()
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=24*4)) 
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
        ax.set_ylabel("Daily n. of calls", fontname= "Times New Roman", fontsize = 16, labelpad = 6)
        ax.set_title(f"{st.session_state['Data_info'][0]} - {Type} calls: forecast", fontname= "Times New Roman", fontsize = 18, pad = 10)
    elif (not show_pred) & (show_train_pred or show_train):
        if show_train_pred:
            train_pred = train_pred.resample("W").mean() 
            indeces.extend(train_pred.index.tolist())
        if show_train:
            train = train.resample("W").mean()
            indeces.extend(train_pred.index.tolist())
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=24*7*8)) 
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        ax.set_ylabel("Average n. of calls (hourly)", fontname= "Times New Roman", fontsize = 16, labelpad = 6)
        ax.set_title(f"{st.session_state['Data_info'][0]} - {Type} calls: history", fontname= "Times New Roman", fontsize = 18, pad = 10)

    if show_train_pred:
        ax.plot(train_pred.index, train_pred["Predictions"], label = "Training predictions", color = "orange", zorder = 2)
    if show_train:
        ax.plot(train.index, train["Calls"], label = "Actual calls", color = "lightgreen", zorder = 1)
    if show_pred:
        ax.plot(predictions.index, predictions["Predictions"], label = "Predictions", color = "dodgerblue", zorder = 1)

    ax.set_xlim(left= min(indeces) - datetime.timedelta(days = 1), right= max(indeces) + datetime.timedelta(days = 1))
    ax.set_xlabel("Horizon", fontname= "Times New Roman", fontsize = 16, labelpad = 6)
    ax.legend(loc='lower left')
    ax.grid(color='silver', linestyle='dashed', linewidth=0.5)
    if show_train_pred or show_train:
        plt.ylim(bottom=0)
    plt.xticks(rotation = 45)
    return fig
