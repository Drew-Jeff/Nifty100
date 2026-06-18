import pandas as pd
from sqlalchemy import create_engine

DB_USER = "nifty_admin"
DB_PASS = "Nifty100Db"
DB_HOST = "127.0.0.1"
DB_PORT = "5430"
DB_NAME = "nifty100"
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)
CLEAN_DIR = "./datasets/clean"


def load_table(file_name, table_name, is_fact=True):
    file_path = f"{CLEAN_DIR}/{file_name}"
    try:
        print(f"Reading {file_name}...")
        df = pd.read_excel(file_path)

        if is_fact and 'id' in df.columns:
            df = df.drop(columns=['id'])

        print(f"Loading {len(df)} rows into '{table_name}' table...")
        df.to_sql(table_name, engine, if_exists='replace', index=False)
        print(f"Successfully loaded {table_name}\n")
    except Exception as e:
        print(f"Error loading {table_name}: {e}\n")


if __name__ == "__main__":
    print("=== STARTING DATA WAREHOUSE LOAD ===\n")

    print("--- Loading Dimensions ---")
    load_table("dim_company.xlsx", "dim_company", is_fact=False)
    load_table("dim_year.xlsx", "dim_year", is_fact=False)
    load_table("dim_sector.xlsx", "dim_sector", is_fact=False)

    print("--- Loading Facts ---")
    load_table("fact_profit_loss.xlsx", "fact_profit_loss")
    load_table("fact_balance_sheet.xlsx", "fact_balance_sheet")
    load_table("fact_cash_flow.xlsx", "fact_cash_flow")
    load_table("fact_analysis.xlsx", "fact_analysis")
    load_table("fact_pros_cons.xlsx", "fact_pros_cons")
    load_table("fact_documents.xlsx", "fact_documents")

    print("=== WAREHOUSE LOAD COMPLETE ===")