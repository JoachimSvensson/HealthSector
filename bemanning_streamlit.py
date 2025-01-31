import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from data.data_functions import *
from simulation.simulation_models import *
from optimization.optimization import *
import itertools
from datetime import time, timedelta
import warnings

warnings.filterwarnings("ignore")



def bemanningsverktoy(df, tidsperiode, skift, aggregering, visualiseringskolonne):
    kombinert_tabell = df
    try:
        if tidsperiode.lower() == "hele perioden":
            kombinert_tabell = kombinert_tabell
    except:
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
    
    try:
        if tidsperiode.lower() == "hele perioden" and aggregering.lower() == "hele perioden":
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
            # plt.show()
            st.pyplot(plt)

    except:
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
            try:
                plt.title(f"{visualiseringskolonne} for {aggregering} i tidsperioden {start} - {end}", fontsize=14)    
            except:
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
            st.pyplot(plt)
            # plt.show()
        except:
            return df
    return df


@st.cache_data
def oppdater_bemanningsplan(df, bemanningsplan, ppp_df):
    from datetime import time
    bemanningsplan["AntallAnsatte"] = 0
    bemanningsplan["PreDef_PPP"] = 0

    for _, row in df.iterrows():
        start_time = row["Start"]
        end_time = row["End"]
        weeks = [int(w) for w in row["Week"].split("-")]

        for day_idx, day in enumerate(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]):
            employees = row[day]
            if len(ppp_df) > 0:
                ppp = ppp_df.columns[2:-2][day_idx]
                ppp_level = ppp_df.loc[_, ppp]
            for week in weeks:
                if start_time <= end_time:  # Vanlig skift innenfor samme dag
                    mask = (
                        (bemanningsplan["Uke"] == week) &
                        (bemanningsplan["Dag"] == day) &
                        (bemanningsplan["Timer"] >= start_time) &
                        (bemanningsplan["Timer"] < end_time)
                    )
                    bemanningsplan.loc[mask, "AntallAnsatte"] += employees
                    if len(ppp_df) > 0:
                        bemanningsplan.loc[mask, "PreDef_PPP"] += ppp_level

                else:  # Skift som går over til neste dag
                    mask_day1 = (
                        (bemanningsplan["Uke"] == week) &
                        (bemanningsplan["Dag"] == day) &
                        (bemanningsplan["Timer"] >= start_time) &
                        (bemanningsplan["Timer"] < time(23,59, 59))
                    )
                    bemanningsplan.loc[mask_day1, "AntallAnsatte"] += employees
                    if len(ppp_df) > 0:
                        bemanningsplan.loc[mask_day1, "PreDef_PPP"] += ppp_level

                    # Timer fra midnatt til neste skift
                    next_day_idx = (day_idx + 1) % 7  
                    next_day = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][next_day_idx]
                    mask_day2 = (
                        (bemanningsplan["Uke"] == week) &
                        (bemanningsplan["Dag"] == next_day) &
                        (bemanningsplan["Timer"] >= time(0,0)) &
                        (bemanningsplan["Timer"] < end_time)
                    )
                    bemanningsplan.loc[mask_day2, "AntallAnsatte"] += employees
                    if len(ppp_df) > 0:
                        bemanningsplan.loc[mask_day2, "PreDef_PPP"] += ppp_level

    return bemanningsplan

@st.cache_data
def nightshift_weight(row: pd.Series) -> pd.Series:
    import math
    if row["skift_type"] == "natt":
        row["Belegg"] = int(math.ceil(row["Belegg"]*0.25))
    return row

@st.cache_data
def PPP(row: pd.Series) -> int:
    import math
    ppp = round(row['Belegg']/row["AntallAnsatte"], 2)
    return ppp

@st.cache_data
def SkiftIntensitet(row: pd.Series) -> int:
    SI = row['Belegg']/ (row["AntallAnsatte"]*row["PreDef_PPP"])
    return SI

@st.cache_data
def create_quarterly_times_and_update_timer(row):
    times = []
    timer_values = []
    for minute in [0, 15, 30, 45]:
        new_time = row['DatoTid'].replace(minute=minute, second=0)
        times.append(new_time)
        timer_values.append(new_time.time())
    return list(zip(times, timer_values))


dfs_dict = read_folder_to_dfs("./data/timesdata")
fin_data_hourly = create_hourly_obt(dfs_dict)
fin_data_hourly["skift_type"] = fin_data_hourly.apply(add_shift_type, axis=1)
fin_data_hourly.head(10)


fin_data_hourly_med = fin_data_hourly[fin_data_hourly["post"]=="medisinsk"]
fin_data_hourly_kir = fin_data_hourly[fin_data_hourly["post"]=="kirurgisk"]

fin_data_hourly_med["Belegg"] = fin_data_hourly_med.apply(calculate_patients, axis=1)
fin_data_hourly_kir["Belegg"] = fin_data_hourly_kir.apply(calculate_patients, axis=1)

next_year_med = create_forecast_hourly(fin_data_hourly_med, "medisinsk")
next_year_kir = create_forecast_hourly(fin_data_hourly_kir, "kirurgisk")

next_year = pd.concat([next_year_med, next_year_kir], axis=0).sort_values("DatoTid").reset_index()
next_year.drop(["index"], axis=1, inplace=True)
next_year["skift_type"] = next_year.apply(add_shift_type, axis=1)

fin_data_hourly["Prediksjoner pasientstrøm"] = np.nan
fin_data_hourly["Prediksjoner belegg"] = np.nan

fin_data_hourly = pd.concat([fin_data_hourly_med, fin_data_hourly_kir, next_year], axis=0).sort_values("DatoTid").reset_index()
fin_data_hourly.drop(["index"], axis=1, inplace=True)



fin_med_23 = fin_data_hourly[(fin_data_hourly["År"] == 2023) & (fin_data_hourly["post"] == "medisinsk")]
test = fin_med_23.loc[:, ["DatoTid","Uke", "Dag", "Timer", "Belegg", "skift_type"]]
excel_file = "test_data.xlsx"
df = pd.read_excel(excel_file, sheet_name= 'bemanningsplan', engine='openpyxl')
df = df[df["Aktivering"] == "Aktiv"]
ppp_df = pd.read_excel(excel_file, sheet_name= 'ppp', engine='openpyxl')
ppp_df = ppp_df[ppp_df["Aktivering"] == "Aktiv"]



days_list = df.columns[2:-2].tolist()

week_num = []
for week in df.Week:
    week = str(week)
    for element in week.split("-"):  # Del ukene med komma som separator
        try:
            week_num.append(int(element))
        except:
            pass


dataset_weeks = list(range(min(week_num), max(week_num) + 1))
quarters = [time(hour, minute) for hour in range(24) for minute in (0, 15, 30, 45)]
kombinasjoner = list(itertools.product(dataset_weeks, days_list, quarters))
bemanningsplan = pd.DataFrame(kombinasjoner, columns=["Uke", "Dag", "Timer"])


oppdatert_bemanningsplan = oppdater_bemanningsplan(df, bemanningsplan, ppp_df)


test = test[test.Uke.isin(dataset_weeks)]

test['DatoTid'] = pd.to_datetime(test['DatoTid'])


new_rows = []
for _, row in test.iterrows():
    quarterly_times_and_timers = create_quarterly_times_and_update_timer(row)
    for time, timer in quarterly_times_and_timers:
        new_row = row.copy()
        new_row['DatoTid'] = time
        new_row['Timer'] = timer
        new_rows.append(new_row)

df_quarterly = pd.DataFrame(new_rows)
kombinert_tabell = df_quarterly.merge(oppdatert_bemanningsplan, on=["Uke", "Dag", "Timer"], how="left")


kombinert_tabell = kombinert_tabell.apply(nightshift_weight, axis=1)
kombinert_tabell['Reell_PPP'] = kombinert_tabell.apply(PPP, axis=1)
kombinert_tabell['SI'] = kombinert_tabell.apply(SkiftIntensitet, axis=1)


st.title("Interaktiv Streamlit App for Visualisering")

st.sidebar.header("Velg parametere")

tidsperiode = st.sidebar.selectbox("Velg tidsperiode", options=["hele perioden", "custom"])

if tidsperiode == "custom":
    start_dato = st.sidebar.date_input("Velg startdato", value=kombinert_tabell['DatoTid'].min())
    slutt_dato = st.sidebar.date_input("Velg sluttdato", value=kombinert_tabell['DatoTid'].max())
    
    start_dato = pd.to_datetime(start_dato)
    slutt_dato = pd.to_datetime(slutt_dato)
    tidsperiode = [start_dato, slutt_dato]

    if start_dato > slutt_dato:
        st.sidebar.error("Startdato kan ikke være senere enn sluttdato.")
else:
    start_dato = None
    slutt_dato = None

aggregering = st.sidebar.selectbox("Velg aggregering", options=["hele perioden", "gjennomsnittlig uke", "beste uke", "dårligste uke", 
                                                                "gjennomsnittlig dag", "beste dag", "dårligste dag", 
                                                                "gjennomsnittlig skift", "beste skift", "dårligste skift"])
visualiseringskolonne = st.sidebar.selectbox("Velg visualiseringskolonne", options=["SI", "PreDef_PPP", "Reell_PPP"])
skift = st.sidebar.selectbox("Velg skift", options=["alle skift", "dag", "kveld", "natt"])
df = kombinert_tabell

if st.sidebar.button("Vis plot"):
    df = bemanningsverktoy(df = df, tidsperiode = tidsperiode, skift = skift, aggregering = aggregering, visualiseringskolonne = visualiseringskolonne)