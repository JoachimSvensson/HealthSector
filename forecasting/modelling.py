from xgboost import XGBRegressor
from sklearn.ensemble import ExtraTreesRegressor
from tpot.export_utils import set_param_recursive
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
import datetime 
import pandas as pd 
from sklearn.metrics import mean_absolute_error
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np 

@st.cache_data()
def custom_train_test_split(data, s_start, horizon):
    s_start = pd.to_datetime(s_start, format = "%Y/%m/%d")
    # today = datetime.datetime.today()
    # today = pd.to_datetime("2023-01-01 00:00:00")
    today = s_start
    gap = max((s_start - today).days, 0)
    try:
        from_date = datetime.date(year= today.year - 4, month= today.month, day= today.day)
    except:
        from_date = today - datetime.timedelta(weeks= 52 * 4)
    train_data = data.loc[from_date:today - datetime.timedelta(weeks= horizon, days= gap)]
    y_train = train_data.pop("Calls")
    test_data = data.loc[today - datetime.timedelta(weeks= horizon):]
    y_test = test_data.pop("Calls")
    return train_data, y_train, test_data, y_test

@st.cache_resource()
def xgb_model():
    exported_pipeline = make_pipeline(StandardScaler(),
    XGBRegressor(learning_rate=0.1, max_depth=5, min_child_weight=1, n_estimators=100, n_jobs=1, objective="reg:squarederror", subsample=0.35000000000000003, verbosity=0))
    set_param_recursive(exported_pipeline.steps, 'random_state', 69)
    return exported_pipeline

@st.cache_data()
def extratrees_model():
    params = {"bootstrap" : False, "max_features" : 0.5, "min_samples_leaf" : 3, "min_samples_split" : 6, "n_estimators" : 100} #0.5
    model =  ExtraTreesRegressor(**params)
    return model

# st.cache_resource()
def mae(y, preds):
    return round(mean_absolute_error(y, preds),2)

def mape(y,preds):
    return round((y - preds).div(y).replace([np.inf, -np.inf], 1).abs().sum() / (len(y)), 2)

def wape(y,preds):
    return round((y - preds).abs().sum() / (y.sum()), 2)

def plot_train_results(y_train, y_test, p_train, p_test):
    y_train = pd.DataFrame(y_train).copy(deep = True)
    y_train["predictions"] = p_train.copy()

    y_test = pd.DataFrame(y_test).copy(deep = True)
    y_test["predictions"] = p_test.copy()
    
    y_train = y_train.resample("W").mean()
    y_test = y_test.resample("W").mean()
    
    if y_train.iloc[-1,0] <y_train.Calls.mean():
        y_train.iloc[-1,0] = y_train.Calls.mean()

    if y_train.iloc[-1,1] <y_train.predictions.mean():
        y_train.iloc[-1,1] = y_train.predictions.mean()

    fig, ax = plt.subplots(figsize = (10,4))
    ax.plot(y_train.index, y_train["Calls"], color = "orange", label = "Partial training value")
    ax.plot(y_train.index, y_train["predictions"], color = "red", label = "Paritial training predictions")
    ax.plot(y_test.index, y_test["Calls"], color = "blue", label = "Testing values")
    ax.plot(y_test.index, y_test["predictions"], color = "green", label = "Testing predictions")
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=24*7*8)) 
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.set_xlabel("Horizon", fontname= "Times New Roman", fontsize = 16, labelpad = 6)
    ax.legend(loc='lower left')
    ax.grid(color='silver', linestyle='dashed', linewidth=0.5)
    plt.ylim(bottom=0)
    plt.xticks(rotation = 45)
    return fig


