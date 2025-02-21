import sqlite3
import pandas as pd
import warnings
from secret_info import DATABASE_URI
import psycopg2
from sqlalchemy import create_engine

warnings.filterwarnings("ignore")


def csv_tabell_last_til_db(csv_file, table_name, db_path):
    conn = psycopg2.connect(db_path)
    engine = create_engine(db_path)

    df = pd.read_csv(csv_file)
    df.columns = df.columns.str.replace(" ", "_")
    
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM {table_name}")

    df.to_sql(table_name, engine, if_exists='append', index=False, method="multi")

    cursor.close()
    conn.close()




def excel_tabell_last_til_db(excel_file, sheet_name, table_name, db_path):
    conn = psycopg2.connect(db_path)
    engine = create_engine(db_path)
    df = pd.read_excel(excel_file, sheet_name, engine='openpyxl')
    
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM {table_name}")

    df.to_sql(table_name, engine, if_exists='append', index=False, method="multi")

    cursor.close()
    conn.close()



if __name__ == "__main__":
    
    # database_path = './instance/bemanningslanternenDB.db'
    database_path = DATABASE_URI
    csv_path = 'fin_data_hourly.csv'
    excel_path = "test_data.xlsx"

    try:
        sheet_name_bemanningsplan = 'bemanningsplan (2)'
        sheet_name_ppp = 'ppp'
        sheet_name_døgnrytme = 'døgnrytmetabell'

        csv_tabell_last_til_db(csv_file=csv_path, table_name='sykehusdata', db_path=database_path)
        excel_tabell_last_til_db(excel_file=excel_path, sheet_name= sheet_name_bemanningsplan, table_name='bemanningsplan', db_path=database_path)
        excel_tabell_last_til_db(excel_file=excel_path, sheet_name= sheet_name_ppp, table_name='ppp', db_path=database_path)
        excel_tabell_last_til_db(excel_file=excel_path, sheet_name= sheet_name_døgnrytme, table_name='døgnrytmeplan', db_path=database_path)
        
        print("Data importert vellykket!")
    
    except Exception as e:
        print(f'En uventet feil oppsto: {e}')


