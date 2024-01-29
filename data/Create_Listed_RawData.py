import pandas as pd 
import os 

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
            save_to = "List_Raw\\" + file_path.split("\\")[1] + "\\" + "_".join(file_path.split("\\")[2:]).replace(" ", "_").replace("(", "").replace(")", "")
            import_file(file_path).to_csv(save_to, sep = "\t", encoding="utf-16")