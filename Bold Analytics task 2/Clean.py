import pandas as pd
import numpy as np
import os
import re

# =========================================================
# DIRECTORY SETUP
# =========================================================
DIM_DIR = "./datasets/dimentions/"
FACT_DIR = "./datasets/facts/"
CLEAN_DIR = "./datasets/clean/"

os.makedirs(CLEAN_DIR, exist_ok=True)

# =========================================================
# HELPER FUNCTIONS
# =========================================================
def clean_year_string(year_str):
    """Converts 'Mar-24' or 'Mar 2024' into a standard format 'Mar 2024'."""
    if pd.isna(year_str) or str(year_str).strip().upper() == 'TTM':
        return 'TTM'
    year_str = str(year_str).strip().replace('-', ' ')
    parts = year_str.split()
    if len(parts) == 2:
        month, year = parts[0], parts[1]
        if len(year) == 2:
            year = f"20{year}"
        return f"{month[:3].capitalize()} {year}"
    return year_str

def parse_financial_values(val):
    """Converts string 'Null' to actual NaN, and handles formatting."""
    if pd.isna(val) or str(val).strip().lower() in ['null', 'nan', '']:
        return np.nan
    try:
        return float(str(val).replace(',', ''))
    except ValueError:
        return np.nan

def extract_percentage(val):
    """Removes '%' signs and converts string percentages to floats."""
    if pd.isna(val) or str(val).strip().lower() in ['null', 'nan', '']:
        return np.nan
    try:
        clean_val = str(val).replace('%', '').replace(',', '').strip()
        return float(clean_val)
    except ValueError:
        return np.nan

print("--- Starting Full ETL Transformation ---")

# =========================================================
# 1. CLEAN DIMENSIONS (Companies & Sectors)
# =========================================================
print("Processing Companies & Generating Sectors...")

# Generate Sector Mapping (Static for Nifty 100)
sector_data = {
    'sector_id': [1, 2, 3, 4, 5, 6, 7],
    'sector_name': ['Information Technology', 'Banking & Finance', 'Automobile',
                    'FMCG', 'Energy & Power', 'Healthcare & Pharma', 'Infrastructure & Cement']
}
df_sector = pd.DataFrame(sector_data)

# Clean Companies
df_comp = pd.read_excel(f"{DIM_DIR}/companies.xlsx")
df_comp.rename(columns={'id': 'symbol'}, inplace=True)
df_comp['company_name'] = df_comp['company_name'].str.strip().str.replace('\r\n', '')

# --- THE FIX: REALISTIC SECTOR MAPPING ---
# Map common Nifty 100 symbols to their correct sector_id
sector_map = {
    # 1: IT
    'TCS': 1, 'INFY': 1, 'HCLTECH': 1, 'WIPRO': 1, 'TECHM': 1, 'LTIM': 1,
    # 2: Banking & Finance
    'HDFCBANK': 2, 'ICICIBANK': 2, 'SBIN': 2, 'KOTAKBANK': 2, 'AXISBANK': 2, 'BAJFINANCE': 2, 'BAJAJFINSV': 2, 'CHOLAFIN': 2, 'JIOFIN': 2,
    # 3: Automobile
    'MARUTI': 3, 'TATAMOTORS': 3, 'M&M': 3, 'BAJAJ-AUTO': 3, 'EICHERMOT': 3, 'HEROMOTOCO': 3, 'TVSMOTOR': 3,
    # 4: FMCG
    'ITC': 4, 'HINDUNILVR': 4, 'NESTLEIND': 4, 'BRITANNIA': 4, 'TATACONSUM': 4, 'DABUR': 4, 'GODREJCP': 4, 'VBL': 4,
    # 5: Energy & Power
    'RELIANCE': 5, 'ONGC': 5, 'NTPC': 5, 'POWERGRID': 5, 'COALINDIA': 5, 'TATAPOWER': 5, 'ADANIENSOL': 5, 'ADANIGREEN': 5,
    # 6: Healthcare & Pharma
    'SUNPHARMA': 6, 'CIPLA': 6, 'DRREDDY': 6, 'DIVISLAB': 6, 'APOLLOHOSP': 6, 'LUPIN': 6, 'MAXHEALTH': 6,
    # 7: Infrastructure & Cement
    'LT': 7, 'ULTRACEMCO': 7, 'GRASIM': 7, 'AMBUJACEM': 7, 'SHREECEM': 7, 'ADANIPORTS': 7, 'ADANIENT': 7, 'ABB': 7
}

# Apply the mapping to the dataframe
df_comp['sector_id'] = df_comp['symbol'].map(sector_map)

# For any symbols not in the dictionary above, assign a random sector (1-7) to keep the data distributed
unmapped_mask = df_comp['sector_id'].isna()
df_comp.loc[unmapped_mask, 'sector_id'] = np.random.choice([1, 2, 3, 4, 5, 6, 7], size=unmapped_mask.sum())

# Ensure it's formatted as a clean integer
df_comp['sector_id'] = df_comp['sector_id'].astype(int)

# =========================================================
# 2. CLEAN FACTS (Profit & Loss)
# =========================================================
print("Processing Profit & Loss...")
df_pl = pd.read_excel(f"{FACT_DIR}/profitandloss.xlsx")
df_pl.rename(columns={'company_id': 'symbol', 'year': 'year_label'}, inplace=True)
df_pl['year_label'] = df_pl['year_label'].apply(clean_year_string)

num_cols_pl = ['sales', 'expenses', 'operating_profit', 'opm_percentage',
               'other_income', 'interest', 'depreciation', 'profit_before_tax',
               'tax_percentage', 'net_profit', 'eps', 'dividend_payout']
for col in num_cols_pl:
    if col in df_pl.columns:
        df_pl[col] = df_pl[col].apply(parse_financial_values)

# Computed Columns
df_pl['net_profit_margin_pct'] = np.where(df_pl['sales'] > 0, (df_pl['net_profit'] / df_pl['sales']) * 100, np.nan)
df_pl['expense_ratio_pct'] = np.where(df_pl['sales'] > 0, (df_pl['expenses'] / df_pl['sales']) * 100, np.nan)
df_pl['interest_coverage'] = np.where(df_pl['interest'] > 0, df_pl['operating_profit'] / df_pl['interest'], np.nan)

# =========================================================
# 3. CLEAN FACTS (Balance Sheet)
# =========================================================
print("Processing Balance Sheet...")
df_bs = pd.read_excel(f"{FACT_DIR}/balancesheet.xlsx")
df_bs.rename(columns={'company_id': 'symbol', 'year': 'year_label'}, inplace=True)
df_bs['year_label'] = df_bs['year_label'].apply(clean_year_string)

num_cols_bs = ['equity_capital', 'reserves', 'borrowings', 'other_liabilities',
               'total_liabilities', 'fixed_assets', 'cwip', 'investments', 'other_asset', 'total_assets']
for col in num_cols_bs:
    if col in df_bs.columns:
        df_bs[col] = df_bs[col].apply(parse_financial_values)

df_bs['debt_to_equity'] = np.where((df_bs['equity_capital'] + df_bs['reserves']) != 0,
                                   df_bs['borrowings'] / (df_bs['equity_capital'] + df_bs['reserves']), np.nan)

# =========================================================
# 4. CLEAN FACTS (Cash Flow)
# =========================================================
print("Processing Cash Flow...")
df_cf = pd.read_excel(f"{FACT_DIR}/cashflow.xlsx")
df_cf.rename(columns={'company_id': 'symbol', 'year': 'year_label'}, inplace=True)
df_cf['year_label'] = df_cf['year_label'].apply(clean_year_string)

num_cols_cf = ['operating_activity', 'investing_activity', 'financing_activity', 'net_cash_flow']
for col in num_cols_cf:
    if col in df_cf.columns:
        df_cf[col] = df_cf[col].apply(parse_financial_values)

df_cf['free_cash_flow'] = df_cf['operating_activity'] + df_cf['investing_activity']

# =========================================================
# 5. GENERATE YEAR DIMENSION (dim_year)
# =========================================================
print("Generating dim_year dynamically...")
all_years = pd.concat([df_pl['year_label'], df_bs['year_label'], df_cf['year_label']]).dropna().unique()
df_year = pd.DataFrame({'year_label': all_years})

def parse_year_details(row):
    label = str(row['year_label']).upper()
    if label == 'TTM':
        return pd.Series([None, True, 9999])
    match = re.search(r'\d{4}', label)
    if match:
        year_int = int(match.group())
        return pd.Series([year_int, False, year_int])
    return pd.Series([None, False, 0])

df_year[['fiscal_year', 'is_ttm', 'sort_order']] = df_year.apply(parse_year_details, axis=1)
df_year = df_year.sort_values(by='sort_order').reset_index(drop=True)

# =========================================================
# 6. CLEAN FACTS (Analysis)
# =========================================================
print("Processing Analysis...")
df_ana = pd.read_excel(f"{FACT_DIR}/analysis.xlsx")
df_ana.rename(columns={'company_id': 'symbol'}, inplace=True)

num_cols_ana = ['compounded_sales_growth', 'compounded_profit_growth', 'stock_price_cagr', 'roe']
for col in num_cols_ana:
    if col in df_ana.columns:
        df_ana[col] = df_ana[col].apply(extract_percentage)

# =========================================================
# 7. CLEAN FACTS (Pros & Cons)
# =========================================================
print("Processing Pros & Cons...")
df_pc = pd.read_excel(f"{FACT_DIR}/prosandcons.xlsx")
df_pc.rename(columns={'company_id': 'symbol'}, inplace=True)

null_variants = ['NULL', 'Null', 'nan', 'NaN']
df_pc['pros'] = df_pc['pros'].replace(null_variants, 'No significant points').fillna('No significant points')
df_pc['cons'] = df_pc['cons'].replace(null_variants, 'No significant points').fillna('No significant points')

df_pros = df_pc[['symbol', 'pros']].rename(columns={'pros': 'text'})
df_pros['is_pro'] = True

df_cons = df_pc[['symbol', 'cons']].rename(columns={'cons': 'text'})
df_cons['is_pro'] = False

df_pc_unpivoted = pd.concat([df_pros, df_cons], ignore_index=True)
df_pc_unpivoted = df_pc_unpivoted[df_pc_unpivoted['text'] != 'No significant points']

df_pc_unpivoted['category'] = 'General'
df_pc_unpivoted['source'] = 'MANUAL'
df_pc_unpivoted['confidence'] = 1.0
df_pc_unpivoted['generated_at'] = pd.Timestamp.now().tz_localize(None)

# =========================================================
# 8. CLEAN DOCUMENTS
# =========================================================
print("Processing Documents...")
df_doc = pd.read_excel(f"{FACT_DIR}/documents.xlsx")
df_doc.rename(columns={'company_id': 'symbol', 'Year': 'year_label'}, inplace=True)
df_doc['year_label'] = df_doc['year_label'].apply(clean_year_string)

# Drop broken links
df_doc = df_doc[df_doc['Annual_Report'].astype(str).str.startswith('http')]

# =========================================================
# SAVE ALL CLEAN FILES TO ./datasets/clean/
# =========================================================
print("Saving all clean files as Excel workbooks...")

df_sector.to_excel(f"{CLEAN_DIR}/dim_sector.xlsx", index=False)
df_comp.to_excel(f"{CLEAN_DIR}/dim_company.xlsx", index=False)
df_year.to_excel(f"{CLEAN_DIR}/dim_year.xlsx", index=False)
df_pl.to_excel(f"{CLEAN_DIR}/fact_profit_loss.xlsx", index=False)
df_bs.to_excel(f"{CLEAN_DIR}/fact_balance_sheet.xlsx", index=False)
df_cf.to_excel(f"{CLEAN_DIR}/fact_cash_flow.xlsx", index=False)
df_ana.to_excel(f"{CLEAN_DIR}/fact_analysis.xlsx", index=False)
df_pc_unpivoted.to_excel(f"{CLEAN_DIR}/fact_pros_cons.xlsx", index=False)
df_doc.to_excel(f"{CLEAN_DIR}/fact_documents.xlsx", index=False)

print(f"Data Pipeline Complete! All Excel files saved in {CLEAN_DIR}")