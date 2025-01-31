from flask import Flask, request, jsonify, render_template, session
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
from data.data_functions import *
from simulation.simulation_models import *
from optimization.optimization import *
import itertools
from datetime import time, timedelta
import warnings

warnings.filterwarnings("ignore")


db = SQLAlchemy()
# flask init db
# flask db migrate
# flask db upgrade


app = Flask(__name__, template_folder="templates", static_folder="static")

app.secret_key = 'KPMGs Bemanningslanterne'

# dfs_dict = read_folder_to_dfs("./data/timesdata")
# fin_data_hourly = create_hourly_obt(dfs_dict)
# fin_data_hourly["skift_type"] = fin_data_hourly.apply(add_shift_type, axis=1)
# fin_data_hourly.head(10)


# fin_data_hourly_med = fin_data_hourly[fin_data_hourly["post"]=="medisinsk"]
# fin_data_hourly_kir = fin_data_hourly[fin_data_hourly["post"]=="kirurgisk"]

# fin_data_hourly_med["Belegg"] = fin_data_hourly_med.apply(calculate_patients, axis=1)
# fin_data_hourly_kir["Belegg"] = fin_data_hourly_kir.apply(calculate_patients, axis=1)

# next_year_med = create_forecast_hourly(fin_data_hourly_med, "medisinsk")
# next_year_kir = create_forecast_hourly(fin_data_hourly_kir, "kirurgisk")

# next_year = pd.concat([next_year_med, next_year_kir], axis=0).sort_values("DatoTid").reset_index()
# next_year.drop(["index"], axis=1, inplace=True)
# next_year["skift_type"] = next_year.apply(add_shift_type, axis=1)

# fin_data_hourly["Prediksjoner pasientstrøm"] = np.nan
# fin_data_hourly["Prediksjoner belegg"] = np.nan

# fin_data_hourly = pd.concat([fin_data_hourly_med, fin_data_hourly_kir, next_year], axis=0).sort_values("DatoTid").reset_index()
# fin_data_hourly.drop(["index"], axis=1, inplace=True)



fin_data_hourly = pd.read_csv('fin_data_hourly.csv')
fin_med_24 = fin_data_hourly[(fin_data_hourly["År"] == 2024) & (fin_data_hourly["post"] == "medisinsk")]
test = fin_med_24.loc[:, ["DatoTid","Uke", "Dag", "Timer", "Belegg", "skift_type"]]
excel_file = "test_data.xlsx"
# df = pd.read_excel(excel_file, sheet_name= 'bemanningsplan', engine='openpyxl')
bemanningsplan_df = pd.read_excel(excel_file, sheet_name= 'bemanningsplan (2)', engine='openpyxl')
# df = df[df["Aktivering"] == "Aktiv"]
bemanningsplan_df = bemanningsplan_df[bemanningsplan_df["Navn"] != "Inaktiv"]
ppp_df = pd.read_excel(excel_file, sheet_name= 'ppp', engine='openpyxl')
ppp_df = ppp_df[ppp_df["Aktivering"] == "Aktiv"]
døgnrytme_df = pd.read_excel(excel_file, sheet_name='døgnrytmetabell', engine='openpyxl')




days_list = bemanningsplan_df.columns[2:-2].tolist()
week_num = []

for week in bemanningsplan_df.Week:
    week = str(week)
    for element in week.split("-"): 
        try:
            week_num.append(int(element))
        except:
            pass

dataset_weeks = list(range(min(week_num), max(week_num) + 1))
quarters = [time(hour, minute) for hour in range(24) for minute in (0, 15, 30, 45)]

kombinasjoner = list(itertools.product(dataset_weeks, days_list, quarters))
bemanningsplan = pd.DataFrame(kombinasjoner, columns=["Uke", "Dag", "Timer"])
bemanningsplan['DøgnrytmeAktivitet'] = bemanningsplan.apply(
    lambda row: match_and_add_activity(døgnrytme_df, row), axis=1
)


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
df_quarterly["skift_type"] = df_quarterly.apply(add_shift_type_quarterly, axis=1)
df_full = df_quarterly.merge(bemanningsplan, on=["Uke", "Dag", "Timer"], how="left")
df_full = df_full.apply(nightshift_weight, axis=1)


sheets = pd.read_excel(excel_file, sheet_name= ['bemanningsplan (2)', 'ppp', 'døgnrytmetabell'], engine='openpyxl')
bemanningsplaner = bemanningsplan_df.Navn.unique().tolist()


@app.route('/')
def index():
    return render_template('index.html')



@app.route('/api/get_table', methods=['POST'])
def get_table():
    params = request.json
    sheet_name = params.get('sheet_name', 'bemanningsplan (2)')
    global sheets
    df = sheets.get(sheet_name)
    df_copy = df.copy(deep=True)
    if df_copy is not None:
        df_copy['Start'] = df_copy['Start'].apply(lambda x: x.strftime('%H:%M:%S'))
        df_copy['End'] = df_copy['End'].apply(lambda x: x.strftime('%H:%M:%S'))
        table_data = {
            'headers': df_copy.columns.tolist(),  
            'data': df_copy.values.tolist() 
        }
        return jsonify({'table': table_data})
    else:
        return jsonify({'error': 'Invalid sheet name'}), 400


# @app.route('/update_table', methods=['POST'])
# def update_table():
#     data = request.json
#     sheet_name = data.get('sheet', 'bemanningsplan')
#     rows = data.get('rows')

#     if sheet_name not in sheets:
#         return jsonify({'error': 'Invalid sheet name'}), 400

#     df = pd.DataFrame(rows)
#     sheets[sheet_name] = df

#     with pd.ExcelWriter(excel_file, mode='w') as writer:
#         for name, sheet_df in sheets.items():
#             sheet_df.to_excel(writer, sheet_name=name, index=False)
#     return jsonify({'success': True})


@app.route('/api/get_dropdown_values', methods = ["POST"])
def get_dropdown_values():
    global bemanningsplaner
    return jsonify({'plan': bemanningsplaner})



@app.route('/api/get_plot_data', methods=['POST'])
def get_plot_data():

    params = request.json
    tidsperiode = params.get('tidsperiode', 'hele perioden')
    aggregering = params.get('aggregering', 'hele perioden')
    visualiseringskolonne = params.get('visualiseringskolonne', 'SI')
    skift = params.get('skift', 'alle skift')
    start = params.get('start_dato', None)
    end = params.get('slutt_dato', None)
    plan = params.get('plan', "Grunnplan")
    

    global df_full, bemanningsplan_df, ppp_df
    
    uten_ansatte = df_full.copy(deep=True)
    pasient_per_pleier  = ppp_df.copy(deep=True)
    bemanning = bemanningsplan_df.copy(deep=True)
    bemanning = bemanning[bemanning["Navn"] == plan]
    
    oppdatert_bemanningsplan = oppdater_bemanningsplan(bemanning, uten_ansatte, pasient_per_pleier)
    oppdatert_bemanningsplan['Reell_PPP'] = oppdatert_bemanningsplan.apply(PPP, axis=1)
    oppdatert_bemanningsplan['SI'] = oppdatert_bemanningsplan.apply(SkiftIntensitet, axis=1)



    if tidsperiode == "hele perioden":
        kombinert_tabell = oppdatert_bemanningsplan.copy(deep=True)
    else:
        tidsperiode = [start, end]
        tidsperiode = pd.to_datetime(tidsperiode)
        start, end = tidsperiode
        kombinert_tabell = oppdatert_bemanningsplan.copy(deep=True)
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
    
    
    if aggregering == "hele perioden":
        visualisering = kombinert_tabell[visualiseringskolonne].tolist()
        plt.figure(figsize=(20, 8))
        plt.plot(kombinert_tabell["DatoTid"],visualisering, marker='o', color='g', linestyle='-')
        if not start:
            plt.title(f'Variasjon i {visualiseringskolonne} for post hos Finnmarksykehuset gjennom {tidsperiode}')
        else:
            plt.title(f"{visualiseringskolonne} for {aggregering} fra {start} til {end}", fontsize=14)
        plt.xlabel('Tidsperiode')
        plt.ylabel(f'{visualiseringskolonne} (i desimal)')
        plt.grid(True)
        plt.xticks(kombinert_tabell['DatoTid'].dt.date.unique().tolist(), rotation=45)
        plt.tight_layout()
        # plt.show()

    else:
        try:
            df = tabell
            df["Timer"] = pd.to_datetime(df["Timer"], format="%H:%M:%S").dt.time
            df["Minutes"] = df["Timer"].apply(lambda t: t.hour * 60 + t.minute)

            plt.figure(figsize=(12, 6))

            if aggregering in ["gjennomsnittlig uke", "beste uke", "dårligste uke"]:
                for dag in df["Dag"].unique():
                    subset = df[df["Dag"] == dag]
                    plt.plot(subset["Minutes"], subset[visualiseringskolonne], marker="o", label=dag)

            else:
                plt.plot(df["Minutes"], df[visualiseringskolonne], marker="o")

            plt.xlabel("Tid", fontsize=12)
            plt.ylabel(visualiseringskolonne, fontsize=12)
            if "hele perioden" in tidsperiode:
                plt.title(f"{visualiseringskolonne} for {aggregering} over {tidsperiode}", fontsize=14)
            else:
                plt.title(f"{visualiseringskolonne} for {aggregering} fra {start} til {end}", fontsize=14)
            plt.xticks(
                ticks=[i * 60 for i in range(24)],
                labels=[f"{i:02d}:00" for i in range(24)], 
                rotation=45,
                fontsize=10,
            )
            if aggregering in ["gjennomsnittlig uke", "beste uke", "dårligste uke"]:
                plt.legend(title="Dag", fontsize=10)
                
            plt.grid(True, linestyle="--", alpha=0.7)
            plt.tight_layout()
        except:
            pass

    if aggregering != "gjennomsnittlig skift":
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        buf.close()
        plt.close()
        return jsonify({'plot': image_base64})

    else:
        return jsonify({'table': df.to_html(index=False)})



if __name__ == '__main__':
    # app.run(debug=True)
    from werkzeug.serving import run_simple
    run_simple('localhost', 5000, app)
