import pandas as pd
import numpy as np
from sqlalchemy import create_engine

# 1. Connect to your PostgreSQL database
# Replace with your actual credentials
engine = create_engine('postgresql://nifty_admin:Nifty100Db@127.0.0.1:5430/nifty100')

# 2. Fetch the existing symbols from your dim_company table
query = "SELECT symbol FROM dim_company"
df_companies = pd.read_sql(query, engine)

# 3. Generate synthetic ML scores (0 to 100)
# We use a normal distribution centered around 65 to make it look realistic
np.random.seed(42)
df_companies['overall_score'] = np.random.normal(loc=65, scale=15, size=len(df_companies))
df_companies['overall_score'] = df_companies['overall_score'].clip(0, 100).astype(int)

# 4. Assign Health Labels based on the project ticket zones
def assign_label(score):
    if score < 35: return 'POOR'
    elif score < 50: return 'WEAK'
    elif score < 70: return 'AVERAGE'
    elif score < 85: return 'GOOD'
    else: return 'EXCELLENT'

df_companies['health_label'] = df_companies['overall_score'].apply(assign_label)

# 5. Batch-insert into the fact_ml_scores table
df_companies.to_sql('fact_ml_scores', engine, if_exists='replace', index=False)

print("Successfully created fact_ml_scores in PostgreSQL!")