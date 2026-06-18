import pandas as pd
from sqlalchemy import create_engine, text

# Replace with your actual PostgreSQL credentials
DB_USER = "postgres"
DB_PASS = "yourpassword"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "nifty100"

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)
CLEAN_DIR = "data/clean/"


def setup_schema():
    """Execute the DDL to construct the Star Schema"""
    schema_sql = """
                 DROP TABLE IF EXISTS fact_cash_flow CASCADE;
                 DROP TABLE IF EXISTS fact_balance_sheet CASCADE;
                 DROP TABLE IF EXISTS fact_profit_loss CASCADE;
                 DROP TABLE IF EXISTS dim_company CASCADE;
                 DROP TABLE IF EXISTS dim_sector CASCADE;

                 CREATE TABLE dim_sector \
                 ( \
                     sector_id   SERIAL PRIMARY KEY, \
                     sector_name VARCHAR(100) UNIQUE
                 );

                 CREATE TABLE dim_company \
                 ( \
                     symbol        VARCHAR(50) PRIMARY KEY, \
                     company_name  VARCHAR(255), \
                     sector_id     INT REFERENCES dim_sector (sector_id), \
                     company_logo  TEXT, \
                     website       TEXT, \
                     chart_link    TEXT, \
                     about_company TEXT, \
                     face_value    DECIMAL, \
                     book_value    DECIMAL
                 );

                 CREATE TABLE fact_profit_loss \
                 ( \
                     id                    SERIAL PRIMARY KEY, \
                     symbol                VARCHAR(50) REFERENCES dim_company (symbol), \
                     year_label            VARCHAR(20), \
                     sales                 DECIMAL, \
                     expenses              DECIMAL, \
                     operating_profit      DECIMAL, \
                     opm_percentage        DECIMAL, \
                     net_profit            DECIMAL, \
                     eps                   DECIMAL, \
                     dividend_payout       DECIMAL, \
                     net_profit_margin_pct DECIMAL, \
                     expense_ratio_pct     DECIMAL, \
                     interest_coverage     DECIMAL, \
                     UNIQUE (symbol, year_label)
                 );

                 CREATE TABLE fact_balance_sheet \
                 ( \
                     id             SERIAL PRIMARY KEY, \
                     symbol         VARCHAR(50) REFERENCES dim_company (symbol), \
                     year_label     VARCHAR(20), \
                     equity_capital DECIMAL, \
                     reserves       DECIMAL, \
                     borrowings     DECIMAL, \
                     total_assets   DECIMAL, \
                     debt_to_equity DECIMAL, \
                     UNIQUE (symbol, year_label)
                 );

                 CREATE TABLE fact_cash_flow \
                 ( \
                     id                 SERIAL PRIMARY KEY, \
                     symbol             VARCHAR(50) REFERENCES dim_company (symbol), \
                     year_label         VARCHAR(20), \
                     operating_activity DECIMAL, \
                     investing_activity DECIMAL, \
                     financing_activity DECIMAL, \
                     net_cash_flow      DECIMAL, \
                     free_cash_flow     DECIMAL, \
                     UNIQUE (symbol, year_label)
                 ); \
                 """
    with engine.begin() as conn:
        conn.execute(text(schema_sql))
    print("Schema Built Successfully.")


def load_data():
    """Load clean CSVs into PostgreSQL"""

    # 1. Insert Default Sector (To satisfy Foreign Keys)
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO dim_sector (sector_id, sector_name) VALUES (1, 'General') ON CONFLICT DO NOTHING;"))

    print("Loading Dimensions...")
    df_comp = pd.read_csv(f"{CLEAN_DIR}/dim_company.csv")
    # Only keep columns that exist in the SQL schema
    cols_to_keep = ['symbol', 'company_name', 'sector_id', 'company_logo', 'website', 'chart_link', 'about_company',
                    'face_value', 'book_value']
    df_comp[cols_to_keep].to_sql('dim_company', engine, if_exists='append', index=False)

    print("Loading Facts...")
    df_pl = pd.read_csv(f"{CLEAN_DIR}/fact_profit_loss.csv").drop(columns=['id'], errors='ignore')
    df_pl.to_sql('fact_profit_loss', engine, if_exists='append', index=False)

    df_bs = pd.read_csv(f"{CLEAN_DIR}/fact_balance_sheet.csv").drop(columns=['id'], errors='ignore')
    df_bs.to_sql('fact_balance_sheet', engine, if_exists='append', index=False)

    df_cf = pd.read_csv(f"{CLEAN_DIR}/fact_cash_flow.csv").drop(columns=['id'], errors='ignore')
    df_cf.to_sql('fact_cash_flow', engine, if_exists='append', index=False)

    print("All Data Loaded Successfully into PostgreSQL!")


if __name__ == "__main__":
    setup_schema()
    load_data()