import matplotlib.pyplot as plt 
import matplotlib.dates as mdates
import seaborn as sns
import pandas as pd 
import numpy as np
import streamlit as st 

class Plotter():
    def __init__(self, all_data):
        data_all = all_data.copy(deep = True)
        self.data_all = data_all
        self.years = list(map(str,sorted(all_data.index.year.unique().tolist())))
        self.FFF = {"Hour of day": ("H", 'getattr(data.index, "hour")', 'list(map(lambda x: f"{str(x).zfill(2)}:00", data.index.tolist()))'),
            "Day of week": ("D", 'getattr(data.index, "day_of_week")',
                            'list(map(lambda x: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][x], data.index.tolist()))'),
            "Day of month": ("D",'getattr(data.index, "day")','data.index.tolist()'),
            "Week of year": ("W",'getattr(getattr(data.index, "isocalendar")(),"week")','data.index.tolist()'),
            "Month of year": ("MS",'getattr(data.index, "month")',
                              'list(map(lambda x: ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"][x-1], data.index.tolist()))'),
            "Hour of week": ("H", '"hour_of_the_week"',
                            '''list(map(lambda x: np.array([[f'{["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][day]}-{str(hour).zfill(2)}' for hour in range(24)] for day in range(7)]).flatten().tolist()[x-1], data.index.tolist()))''')}
        self.F = {"Daily": 24, "Weekly": 24*7*4, "Monthly":24*7*4}
        self.FF = {"Daily": "%Y-%m", "Weekly": "%Y-W%W", "Monthly": "%Y-%m"}
    

    @st.cache_data()
    def plot(_self, frequence, Year_policy, Years, Call_type, Fields):
        if Call_type == "All": Call_type = set(_self.data_all.Call_type.unique().tolist())
        if Years == "All": Years = set(_self.data_all.index.year.unique().tolist())
        filtering = ((_self.data_all.index.year.isin(Years)) & (_self.data_all.Call_type.isin(Call_type)))
        fig, ax = plt.subplots(figsize = (10,4))
        if Year_policy == "Aggregate":
            data = _self.data_all.loc[filtering].resample(_self.FFF[frequence][0]).agg({"Answered" : "sum", "Missed":"sum","Missdialed" : "sum","Calls": "sum", "Waiting_time": "mean", "Call_duration": "mean", "Total_time": "mean"}).copy()
            if frequence == "Hour of week":
                data['hour_of_the_week'] = data.index.dayofweek * 24 + (data.index.hour + 1)
            data = data.groupby(eval(_self.FFF[frequence][1])).agg({"Answered" : "mean", "Missed":"mean","Missdialed" : "sum", "Calls": "mean", "Waiting_time": "mean", "Call_duration": "mean", "Total_time": "mean"})
            for field in Fields:
                ax.plot(eval(_self.FFF[frequence][2]), data[field], label = field.replace("_", " "))
                if frequence == "Hour of week":
                    ax.xaxis.set_ticks(ticks = list(range(0,7*24,7)))
            ax.set_ylabel("Average n. of calls", fontname= "Times New Roman", fontsize = 16, labelpad = 6)
            ax.set_title(f"Average number of calls - {frequence}", fontname= "Times New Roman", fontsize = 18, pad = 10)
            plt.title(f"Average number of calls - {frequence}", fontname= "Times New Roman", fontsize = 18, pad = 10)
        elif Year_policy == "Separate":
            data_agg = _self.data_all.loc[filtering].resample(_self.FFF[frequence][0]).agg({"Answered" : "sum", "Missed":"sum","Missdialed" : "sum","Calls": "sum", "Waiting_time": "mean", "Call_duration": "mean", "Total_time": "mean"}).copy()
            for y in Years:
                data = data_agg.loc[f"{y}"].copy()
                if frequence == "Hour of week":
                    data['hour_of_the_week'] = data.index.dayofweek * 24 + (data.index.hour + 1)
                data = data.groupby(eval(_self.FFF[frequence][1])).agg({"Answered" : "mean", "Missed":"mean","Missdialed" : "sum", "Calls": "mean", "Waiting_time": "mean", "Call_duration": "mean", "Total_time": "mean"})
                for field in Fields:
                    ax.plot(eval(_self.FFF[frequence][2]), data[field], label = f"{y} - {field}".replace("_", " "))
            if frequence == "Hour of week":
                ax.xaxis.set_ticks(ticks = list(range(0,7*24,7)))
            ax.set_ylabel("n. of calls", fontname= "Times New Roman", fontsize = 16, labelpad = 6)
            ax.set_title(f"Number of calls - {frequence}", fontname= "Times New Roman", fontsize = 18, pad = 10)
        ax.set_xlabel(f"{frequence}", fontname= "Times New Roman", fontsize = 16, labelpad = 6)
        ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
        plt.xticks(rotation = 90)
        return fig
    
    @st.cache_data()
    def plot_history(_self, frequence, Years, Call_type, Fields):
        if Call_type == "All": Call_type = set(_self.data_all.Call_type.unique().tolist())
        if Years == "All": Years = set(_self.data_all.index.year.unique().tolist())
        filtering = ((_self.data_all.index.year.isin(Years)) & (_self.data_all.Call_type.isin(Call_type)))
        data = _self.data_all.loc[filtering].resample("H").agg({"Answered" : "sum", "Missed":"sum","Missdialed" : "sum","Calls": "sum", "Waiting_time": "mean", "Call_duration": "mean", "Total_time": "mean"}).copy()
        fig, ax = plt.subplots(figsize = (10,4))
        for field in Fields:
            if field in {"Waiting_time", "Call_duration", "Total_time"}:
                ax.plot(data[field], label = f"{field}")
            else:
                ax.plot(data[field].rolling(_self.F[frequence]).sum(), label = f"{field}")
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=(len(Years)*2*7*24))) 
        ax.xaxis.set_major_formatter(mdates.DateFormatter(_self.FF[frequence]))    
        fig.tight_layout()
        ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
        ax.set_ylabel("n. of calls", fontname= "Times New Roman", fontsize = 16, labelpad = 6)
        ax.set_title(f"Overview", fontname= "Times New Roman", fontsize = 18, pad = 10)
        ax.set_xlabel(f"{frequence} values", fontname= "Times New Roman", fontsize = 16, labelpad = 6)
        plt.xticks(rotation = 45)
        return fig
    
    @st.cache_data()
    def plot_heatmap(_self, Years,Call_type, Field):
        if Call_type == "All": Call_type = set(_self.data_all.Call_type.unique().tolist())
        if Years == "All": Years = set(_self.data_all.index.year.unique().tolist())
        filtering = ((_self.data_all.index.year.isin(Years)) & (_self.data_all.Call_type.isin(Call_type)))
        data = _self.data_all.loc[filtering].resample("H").agg({"Answered" : "sum", "Missed":"sum" ,"Missdialed" : "sum","Calls": "sum", "Waiting_time": "mean", "Call_duration": "mean", "Total_time": "mean"}).copy(deep = True)
        data = pd.DataFrame(data[Field])
        data["DOW"] = data.index.day_of_week
        data["Hour"] = data.index.hour
        data = data.groupby(["Hour", "DOW"], as_index= False).mean()
        data = data.pivot(index = "DOW", columns="Hour", values= Field)
        data.columns = [f"{str(x).zfill(2)}:00" for x in data.columns]
        data.index = [["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][x] for x in data.index]
        fig, ax = plt.subplots(figsize = (16,8))
        sns.heatmap(data, annot = True, fmt=".0f", cmap= sns.color_palette("YlOrBr", as_cmap=True), ax= ax)
        ax.tick_params(labelsize=20)
        plt.xticks(rotation = 425)
        plt.yticks(rotation = 45)
        return fig
    
    @st.cache_data()
    def plot_frequency(_self,s, upper_bound,Call_type, Years):
        if Call_type == "All": Call_type = set(_self.data_all.Call_type.unique().tolist())
        if Years == "All": Years = set(_self.data_all.index.year.unique().tolist())
        filtering = ((_self.data_all.index.year.isin(Years)) & (_self.data_all.Call_type.isin(Call_type)))
        data = _self.data_all.loc[filtering].copy(deep = True)
        data = data.groupby("Waiting_time").agg({"Waiting_time" : "size"}).rename(columns = {"Waiting_time": "Frequency"})
        data["Comulative_Frequency"] = data["Frequency"].cumsum()
        data["Relative_Frequency"] = data["Frequency"] / data["Frequency"].sum()
        data["Relative_Cumulative_Frequency"] = data["Relative_Frequency"].cumsum()
        fig, ax = plt.subplots(figsize = (16,8))
        ax.plot(data["Relative_Frequency"], color = "blue", label = "Relative Frequency")
        ax.plot(data["Relative_Cumulative_Frequency"], color = "orange", label = "Cumulative Relative Frequency")
        ax.vlines(x = s, ymax= data.loc[s,"Relative_Cumulative_Frequency"], ymin = 0, color = "red", linestyles= "dashed")
        ax.scatter(s,data.loc[s,"Relative_Cumulative_Frequency"], color = "red", marker= "*", zorder = 3)
        ax.text(s,data.loc[s,"Relative_Cumulative_Frequency"] + 0.01,f'{int(data.loc[s,"Relative_Cumulative_Frequency"]*100)}%',verticalalignment='bottom', )
        if upper_bound > 71:
            plt.xticks(range(0,upper_bound+1,8))
        else:
            plt.xticks(range(0,upper_bound+1,2))
        plt.yticks(np.linspace(0,1,11,endpoint=True))
        plt.xlim((-1,upper_bound+1))
        ax.tick_params(labelsize=12)
        ax.set_ylabel("Share of Calls", fontname= "Times New Roman", fontsize = 16, labelpad = 6)
        ax.set_title("Response time - Cumulative Frequence Distribution", fontname= "Times New Roman", fontsize = 18, pad = 10)
        ax.set_xlabel("Response time (s)", fontname= "Times New Roman", fontsize = 16, labelpad = 6)
        plt.legend()
        return fig