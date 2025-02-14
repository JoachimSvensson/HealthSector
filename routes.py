from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_bcrypt import Bcrypt
from flask_login import login_user, logout_user, current_user, login_required
from models import *
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
from data.data_functions import *
from simulation.simulation_models import *
from optimization.optimization import *
import itertools
from datetime import time, timedelta
import sqlite3
import warnings
from secret_info import password_key_admin, password_key_users


warnings.filterwarnings("ignore")

password_key_users = 'ifargotoFsserGelpE!.-_-|§'
password_key_admin = 'draagkaBlaakSretsiniM#45!==?;-.'
bcrypt = Bcrypt()


def register_routes(app,db):
    from datetime import time, timedelta


    UPLOAD_FOLDER = "./data/timesdata"
    os.makedirs(UPLOAD_FOLDER, exist_ok=True) 
    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


    database_path = './instance/bemanningslanternenDB.db'
    conn = sqlite3.connect(database_path)

    bemanningsplan_query = "SELECT * FROM bemanningsplan"
    ppp_query = "SELECT * FROM ppp"

    bemanningsplan_df = pd.read_sql_query(bemanningsplan_query, conn)
    bemanningsplan_df = bemanningsplan_df[bemanningsplan_df["Navn"] != "Inaktiv"]

    ppp_df = pd.read_sql_query(ppp_query, conn)
    ppp_df = ppp_df[ppp_df["Navn"] != "Inaktiv"]

    conn.close()


    bemanningsplan_df['Start'] = bemanningsplan_df['Start'].apply(remove_microseconds)
    bemanningsplan_df['End'] = bemanningsplan_df['End'].apply(remove_microseconds)

    ppp_df['Start'] = ppp_df['Start'].apply(remove_microseconds)
    ppp_df['End'] = ppp_df['End'].apply(remove_microseconds)
    


    days_list = bemanningsplan_df.columns[3:-4].tolist()
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
    døgnrytme_df = None
    df_quarterly = None
    df_full = None
    sykehus = None
    post = None


    @app.route('/api/recalculate_hospital_data', methods=["GET", "POST"])
    @login_required
    def recalculate_hospital_data():
        import os
        if request.method == "GET":
            return render_template("recalculate_hospital_data.html")
        elif request.method == "POST":
            from db_tabell_last import csv_tabell_last_til_db
            try:
                if "file" not in request.files:
                    return jsonify({"message": "Ingen fil mottatt"}), 400
                
                file = request.files["file"]
                filename = file.filename
                name_only, extension = os.path.splitext(filename)


                filename = f"{post}_{name_only}_{sykehus}{extension}"


                file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                file.save(file_path)


                dfs_dict = read_folder_to_dfs("./data/timesdata")
                fin_data_hourly = create_hourly_obt(dfs_dict)
                fin_data_hourly["skift_type"] = fin_data_hourly.apply(add_shift_type, axis=1)

                fin_data_hourly_med = fin_data_hourly[fin_data_hourly["post"]=="medisinsk"]
                fin_data_hourly_kir = fin_data_hourly[fin_data_hourly["post"]=="kirurgisk"]

                fin_data_hourly_med["Belegg"] = fin_data_hourly_med.apply(calculate_patients, axis=1)
                fin_data_hourly_kir["Belegg"] = fin_data_hourly_kir.apply(calculate_patients, axis=1)

                fin_data_hourly = pd.concat([fin_data_hourly_med, fin_data_hourly_kir], axis=0).sort_values("DatoTid").reset_index()
                fin_data_hourly.drop(["index"], axis=1, inplace=True)

                fin_data_hourly.to_csv('fin_data_hourly.csv', index=False)

                database_path = './instance/bemanningslanternenDB.db'
                csv_path = 'fin_data_hourly.csv'

                csv_tabell_last_til_db(csv_file=csv_path, table_name='sykehusdata', db_path=database_path)
                print("Data importert vellykket!")

                return jsonify({"message": f"Fil '{filename}' lagret!", "file_path": file_path, 'success': True}), 200
            except Exception as e:
                return jsonify({"message": f"Feil: {str(e)}", 'success': False}), 500


    @app.route('/', methods=["GET", "POST"])
    def index():
        if request.method == "GET":
            return render_template('login.html')
        elif request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")
            stay = request.form.get("stay")
            description = request.form.get("description")

            if password == password_key_users or password == password_key_admin:
                user = User.query.filter_by(username=username).first()
                if user:
                    session["password"] = password
                    login_user(user)
                    return redirect(url_for("choose_department"))
                else:
                    hashed_password = bcrypt.generate_password_hash(password)
                    user= User(username=username, password=hashed_password, stay=stay, description=description)

                    db.session.add(user)
                    db.session.commit()
                    user = User.query.filter(User.username == username).first()

                    if bcrypt.check_password_hash(user.password, password):
                        session["password"] = password
                        login_user(user)
                        return redirect(url_for("choose_department"))
            else:
                return "Failed to log you in"


    @app.route("/logout/")
    @login_required
    def logout():
        logout_user()
        return redirect(url_for("index"))


    @app.route('/choose_department')
    @login_required
    def choose_department():
        return render_template('choose_department.html')


    @app.route('/api/go_to_main', methods=["POST"])
    @login_required
    def go_to_main():

        params = request.json
        nonlocal df_quarterly, df_full, bemanningsplan, døgnrytme_df, sykehus, post
        sykehus = params.get('sykehus')
        post = params.get('post')

        database_path = './instance/bemanningslanternenDB.db'
        conn = sqlite3.connect(database_path)
        
        sykehus_query = "SELECT * FROM sykehusdata"
        fin_data_hourly = pd.read_sql_query(sykehus_query, conn)

        døgnrytmeplan_query = "SELECT * FROM døgnrytmeplan"
        døgnrytme_df = pd.read_sql_query(døgnrytmeplan_query, conn)
        døgnrytme_df['Start'] = døgnrytme_df['Start'].apply(remove_microseconds)
        døgnrytme_df['End'] = døgnrytme_df['End'].apply(remove_microseconds)
        
        conn.close()

        if session["password"] == password_key_admin and sykehus == '' and post == '':
            sykehusdata_valg = fin_data_hourly[(fin_data_hourly["År"] == 2024)]
        elif sykehus != '' and post != '':
            sykehusdata_valg = fin_data_hourly[(fin_data_hourly["År"] == 2024) & (fin_data_hourly["sykehus"] == sykehus) & (fin_data_hourly["post"] == post)]
        else:
            return jsonify({'failed': True})

        sykehusdata_final = sykehusdata_valg.loc[:, ["DatoTid","Uke", "Dag", "Timer", "Belegg", "skift_type", "sykehus", "post"]]       

        sykehusdata_final = sykehusdata_final[sykehusdata_final.Uke.isin(dataset_weeks)]
        sykehusdata_final['DatoTid'] = pd.to_datetime(sykehusdata_final['DatoTid'])
        if session["password"] == password_key_admin:
            døgnrytme_df = døgnrytme_df
        elif sykehus != '' and post != '':
            døgnrytme_df = døgnrytme_df[(døgnrytme_df["sykehus"] == sykehus) & (døgnrytme_df["post"] == post)]
        else:
            døgnrytme_df = døgnrytme_df
        bemanningsplan = pd.DataFrame(kombinasjoner, columns=["Uke", "Dag", "Timer"])
        if session["password"] == password_key_admin:
            sykehus_post_kombinasjoner = bemanningsplan_df[["sykehus", "post"]].drop_duplicates()

            n = len(sykehus_post_kombinasjoner)
            df_duplisert_bemanning = pd.concat([bemanningsplan] * n, ignore_index=True)
            df_duplisert_bemanning = df_duplisert_bemanning.reset_index(drop=True)

            n = len(bemanningsplan)
            df_duplisert_kombos = pd.concat([sykehus_post_kombinasjoner] * n, ignore_index=True)
            df_duplisert_kombos = df_duplisert_kombos.sort_values(by=["sykehus", "post"]).reset_index(drop=True)

            bemanningsplan = pd.concat([df_duplisert_bemanning, df_duplisert_kombos], axis=1)
        else:
            bemanningsplan["sykehus"] = sykehus 
            bemanningsplan["post"] = post

        bemanningsplan['DøgnrytmeAktivitet'] = bemanningsplan.apply(
            lambda row: match_and_add_activity(døgnrytme_df, row), axis=1
        )

        new_rows = []
        for _, row in sykehusdata_final.iterrows():
            quarterly_times_and_timers = create_quarterly_times_and_update_timer(row)
            for time, timer in quarterly_times_and_timers:
                new_row = row.copy()
                new_row['DatoTid'] = time
                new_row['Timer'] = timer
                new_rows.append(new_row)

        df_quarterly = pd.DataFrame(new_rows)
        df_quarterly["skift_type"] = df_quarterly.apply(add_shift_type_quarterly, axis=1)
        df_full = df_quarterly.merge(bemanningsplan, on=["Uke", "Dag", "Timer", "sykehus", "post"], how="left")
        df_full = df_full.apply(nightshift_weight, axis=1)
        if session["password"] == password_key_admin:
            if df_full.empty or df_full is None:
                return jsonify({'admin': True, 'success': False, 'message': 'Something went wrong, necessary table is created'}), 400
            else:
                return jsonify({'admin': True, 'success': True})
        else:
            if df_full.empty or df_full is None:
                return jsonify({'success': False, 'message': 'Something went wrong, necessary table is created'}), 400
            else:
                return jsonify({'success': True})

    
    @app.route('/main')
    @login_required
    def main():
        return render_template('index.html')


    @app.route('/faq')
    @login_required
    def faq():
        return render_template('faq.html')


    @app.route('/api/get_table', methods=['POST'])
    @login_required
    def get_table():
        params = request.json
        sheet_name = params.get('sheet_name', 'bemanningsplan')

        database_path = './instance/bemanningslanternenDB.db'
        conn = sqlite3.connect(database_path)
        query = f"SELECT * FROM {sheet_name}"
        df = pd.read_sql_query(query, conn)
        df_copy = df.copy(deep=True)
        conn.close()

        if sykehus == '' and post == '':
            df_copy = df_copy
        else:
            df_copy = df_copy[(df_copy["sykehus"] == sykehus) & (df_copy["post"] == post)]
        
        if df_copy is not None:
            table_data = {
                'headers': df_copy.columns.tolist(),  
                'data': df_copy.values.tolist() 
            }
            return jsonify({'table': table_data})
        else:
            return jsonify({'error': 'Invalid sheet name'}), 400


    @app.route('/update_table', methods=['POST'])
    @login_required
    def update_table():
        data = request.json
        sheet_name = data.get('sheet', 'bemanningsplan') 
        rows = data.get('rows', []) 
        if not rows:
            return jsonify({'success': False, 'message': 'No data provided'}), 400

        table_class = None
        if sheet_name == "bemanningsplan":
            table_class = Bemanningsplan
        elif sheet_name == "ppp":
            table_class = PPP
        elif sheet_name == "døgnrytmeplan":
            table_class = Døgnrytmetabell
        else:
            return jsonify({'success': False, 'message': 'Invalid table name'}), 400
        
        if sykehus != '' and post != '':
            db.session.query(table_class).filter(
                table_class.sykehus == sykehus,
                table_class.post == post
            ).delete(synchronize_session=False)
        else:
            db.session.query(table_class).delete()

        for row in rows:
            new_entry = table_class(**row) 
            db.session.add(new_entry)

        db.session.flush()
        db.session.commit()

        if sheet_name == "døgnrytmeplan":
            nonlocal bemanningsplan, df_quarterly, df_full
            conn = sqlite3.connect(database_path)
            døgnrytmeplan_query = f"SELECT * FROM døgnrytmeplan"
            døgnrytme_df = pd.read_sql_query(døgnrytmeplan_query, conn)
            conn.close()
            if session["password"] == password_key_admin:
                døgnrytme_df = døgnrytme_df
            elif sykehus != '' and post != '':
                døgnrytme_df = døgnrytme_df[(døgnrytme_df["sykehus"] == sykehus) & (døgnrytme_df["post"] == post)]
            else:
                døgnrytme_df = døgnrytme_df
            
            døgnrytme_df['Start'] = døgnrytme_df['Start'].apply(remove_microseconds)
            døgnrytme_df['End'] = døgnrytme_df['End'].apply(remove_microseconds)

            bemanningsplan['DøgnrytmeAktivitet'] = bemanningsplan.apply(
            lambda row: match_and_add_activity(døgnrytme_df, row), axis=1
            )

            df_full = df_quarterly.merge(bemanningsplan, on=["Uke", "Dag", "Timer", "sykehus", "post"], how="left")
            df_full = df_full.apply(nightshift_weight, axis=1)

        return jsonify({'success': True})


    @app.route('/api/get_dropdown_values', methods = ["POST"])
    @login_required
    def get_dropdown_values():
        database_path = './instance/bemanningslanternenDB.db'
        conn = sqlite3.connect(database_path)
        query = f"SELECT * FROM bemanningsplan"
        df = pd.read_sql_query(query, conn)
        conn.close()
        if sykehus == '' and post == '':
            df = df
        else:
            df = df[(df["sykehus"] == sykehus) & (df["post"] == post)]
        bemanningsplaner = df.Navn.unique().tolist()
        sykehus_valg = df.sykehus.unique().tolist()
        post_valg = df.post.unique().tolist()
        return jsonify({'plan': bemanningsplaner, 'sykehus':sykehus_valg, 'post': post_valg})


    @app.route('/api/get_plot_data', methods=['POST'])
    @login_required
    def get_plot_data():

        params = request.json
        tidsperiode = params.get('tidsperiode', 'hele perioden')
        dag = params.get('dag', 'hele perioden')
        aggregering = params.get('aggregering', 'hele perioden')
        visualiseringskolonne = params.get('visualiseringskolonne', 'SI')
        skift = params.get('skift', 'alle skift')
        start = params.get('start_dato', None)
        end = params.get('slutt_dato', None)
        plan = params.get('plan', "Grunnplan")
        sykehus_plot_valg = params.get('sykehus', "hammerfest")
        post_plot_valg = params.get('post', "medisinsk")
        
        conn = sqlite3.connect(database_path)
        bemanningsplan_query = "SELECT * FROM bemanningsplan"
        ppp_query = "SELECT * FROM ppp"
        
        bemanningsplan_df = pd.read_sql_query(bemanningsplan_query, conn)
        bemanningsplan_df = bemanningsplan_df[bemanningsplan_df["Navn"] != "Inaktiv"]

        ppp_df = pd.read_sql_query(ppp_query, conn)
        ppp_df = ppp_df[ppp_df["Navn"] != "Inaktiv"]

        conn.close()


        bemanningsplan_df['Start'] = bemanningsplan_df['Start'].apply(remove_microseconds)
        bemanningsplan_df['End'] = bemanningsplan_df['End'].apply(remove_microseconds)

        ppp_df['Start'] = ppp_df['Start'].apply(remove_microseconds)
        ppp_df['End'] = ppp_df['End'].apply(remove_microseconds)

        if session["password"] == password_key_admin:
            bemanningsplan_df = bemanningsplan_df
            ppp_df = ppp_df
        else:
            bemanningsplan_df = bemanningsplan_df[(bemanningsplan_df["sykehus"] == sykehus) & (bemanningsplan_df["post"] == post)]        
            ppp_df = ppp_df[(ppp_df["sykehus"] == sykehus) & (ppp_df["post"] == post)]

        uten_ansatte = df_full.copy(deep=True)
        uten_ansatte = uten_ansatte[(uten_ansatte["sykehus"] == sykehus_plot_valg) & (uten_ansatte["post"] == post_plot_valg)]
        pasient_per_pleier  = ppp_df.copy(deep=True)
        pasient_per_pleier  = pasient_per_pleier[(pasient_per_pleier["Navn"] == plan) & (pasient_per_pleier["sykehus"] == sykehus_plot_valg) & (pasient_per_pleier["post"] == post_plot_valg)]
        bemanning = bemanningsplan_df.copy(deep=True)
        bemanning = bemanning[(bemanning["Navn"] == plan) & (bemanning["sykehus"] == sykehus_plot_valg) & (bemanning["post"] == post_plot_valg)]

        if df_full.empty or bemanning.empty:
            return jsonify({'failed': True})

        oppdatert_bemanningsplan = oppdater_bemanningsplan(bemanning, uten_ansatte, pasient_per_pleier)
        oppdatert_bemanningsplan['Reell_PPP'] = oppdatert_bemanningsplan.apply(PPP, axis=1)
        oppdatert_bemanningsplan['SI'] = oppdatert_bemanningsplan.apply(SkiftIntensitet, axis=1)


        print(oppdatert_bemanningsplan)
        if tidsperiode == "hele perioden":
            kombinert_tabell = oppdatert_bemanningsplan.copy(deep=True)
        else:
            tidsperiode = [start, end]
            tidsperiode = pd.to_datetime(tidsperiode)
            start, end = tidsperiode
            kombinert_tabell = oppdatert_bemanningsplan.copy(deep=True)
            kombinert_tabell = kombinert_tabell[(kombinert_tabell["DatoTid"] >= start) & (kombinert_tabell["DatoTid"] <= end)] 
        
        if dag != "All":
            kombinert_tabell = kombinert_tabell[kombinert_tabell["Dag"] == dag]
        else:
            kombinert_tabell = kombinert_tabell

        if skift != "alle skift":
            skifttype = skift
            kombinert_tabell = kombinert_tabell[kombinert_tabell["skift_type"] == skifttype]   
        else:
            kombinert_tabell = kombinert_tabell
        
        # ukesnivå
        if aggregering == "gjennomsnittlig uke":
            # Average week
            tabell = kombinert_tabell.groupby(["Dag", "Timer"])[visualiseringskolonne].mean().reset_index()
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
        print(tabell)

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

