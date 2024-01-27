import pandas as pd 
import os 

# Libraries
import pandas as pd
def clean_police_data(data, name):
    cols_names = ["District", "Call_type", "Date", "Call_start", "Call_answered", "Call_end", "Waiting_time", "Call_duration", "Total_time"]
    cols_types = {"District":str, "Call_type": str, "Waiting_time" : float, "Call_duration": float, "Total_time": float, "Call_start":str, "Call_answered":str, "Call_end": str}
    data = pd.read_csv(f'Data_intermediate\\Police_calls_{name}.csv', sep=',', names= cols_names,dtype = cols_types,engine= "c", skiprows=[0], parse_dates=["Date"])
    # Dataset
    anomalies = data[data["Call_answered"] < data["Call_start"]]
    anomalies = data.loc[data["Total_time"] > 2*60*60].index
    data.loc[anomalies, "Call_duration"] = 0
    data.loc[anomalies,"Total_time"] = data.loc[anomalies,"Call_duration"] + data.loc[anomalies,"Waiting_time"]
    data.loc[(data["Call_answered"] < data["Call_end"]) & (data["Call_end"] < data["Call_start"]) & (data["Call_start"] < "23:00:00") ]
    anomalies = []
    for i,line in data.loc[(data["Call_answered"] < data["Call_end"]) & (data["Call_end"] < data["Call_start"]) & (data["Call_start"] < "23:00:00") ].iterrows():
        anomalies.append(i)
        info = line[["Call_start","Call_answered","Call_end"]].tolist()
        for col in ["Call_start","Call_answered","Call_end"]:
            value = min(info)
            data.loc[i,col] = value
            info.remove(value)

    for index in anomalies:
        data.loc[index, "Waiting_time"] = (pd.to_datetime(data.loc[index, "Call_answered"]) - pd.to_datetime(data.loc[index, "Call_start"])).seconds
        data.loc[index, "Call_duration"] =( pd.to_datetime(data.loc[index, "Call_end"]) - pd.to_datetime(data.loc[index, "Call_answered"])).seconds
        data.loc[index, "Total_time"] = data.loc[index, "Waiting_time"] + data.loc[index, "Call_duration"]

    data.Call_duration.fillna(0, inplace = True)
    data.loc[data.Waiting_time.isnull(), "Waiting_time"] = data.loc[data.Waiting_time.isnull(), "Total_time"]
    data["Answered"] = pd.Series([1] * len(data), name = "Answered", dtype= int) 
    data.loc[data["Call_answered"].isnull(), "Answered"] = 0
    data["Missed"] = (data["Answered"] - 1) **2

    def define_Call_type(original):
        if "112" in original:
            return "112"
        else: 
            return "02800"
    data["Call_type"] = data["Call_type"].apply(lambda otype: define_Call_type(otype))
    data["Date_time"] = pd.to_datetime(data["Date"].astype(str) + " " + data["Call_start"], format = "%Y-%m-%d %H:%M:%S")
    data.drop(columns= "Date", inplace = True)
    data["Missdialed"] = 0
    data.loc[data["Total_time"] <= 3, "Missdialed"] = 1
    data["Calls"] = 1
    data.sort_values(["Date_time", "Call_start", "District","District", "Call_type"]).reset_index(inplace = True, drop = False)
    data.to_csv(f"Data_Cleaned\\{name}_clean.csv", index = False, header = True)

print("Importing files")
def import_file(path):
    file = pd.read_csv(f"{path}", sep = "\t", encoding="utf-16", usecols= ["Distrikt", "CallType", "Dato", "Ring", "Svar", "Avslutt", "Aksesstid(s)", "Taletid(s)", "Totaltid(s)"])
    return file
path1= "Data_Raw"
files = []
for s1_folder in [x for x in os.listdir(f"{path1}") if "." not in x]:
    path2 = path1 + "\\" + s1_folder
    for s2_folder in [x for x in os.listdir(f"{path2}") if "." not in x]:
        path3 = path2 + "\\" + s2_folder
        for file in [x for x in os.listdir(f"{path3}")]:
            file_path = path3 + "\\" + file
            files.append(import_file(file_path))
print("Merging files")
data = pd.concat(files).reset_index(drop = True)
sorost_112 = data.loc[(data["Distrikt"] == "204 Sør-Øst") & (data["CallType"] == "112")]
sorost_02 = data.loc[(data["Distrikt"] == "204 Sør-Øst") & (data["CallType"] == "02800_5")]
innlandet_112 = data.loc[(data["Distrikt"] == "203 Innlandet") & (data["CallType"] == "112")]
innlandet_02 = data.loc[(data["Distrikt"] == "203 Innlandet") & (data["CallType"] == "02800_5")]


innlandet_112.to_csv("Data_Intermediate\\Police_calls_innlandet_112.csv",index = False, header = True) #utf-8, sep = ","
innlandet_02.to_csv("Data_Intermediate\\Police_calls_innlandet_02800.csv",index = False, header = True) #utf-8, sep = ","
sorost_112.to_csv("Data_Intermediate\\Police_calls_sorost_112.csv",index = False, header = True) #utf-8, sep = ","
sorost_02.to_csv("Data_Intermediate\\Police_calls_sorost_02800.csv",index = False, header = True) #utf-8, sep = ","
print("Merging Completed and middle data saved")
print("Cleaning data")
clean_police_data(innlandet_112, "innlandet_112")
clean_police_data(innlandet_02, "innlandet_02800")
clean_police_data(sorost_112, "sorost_112")
clean_police_data(sorost_02, "sorost_02800")
print("Data cleaned and saved")