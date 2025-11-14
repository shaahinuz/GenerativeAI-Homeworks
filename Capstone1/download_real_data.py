"""
Download Real CDC Health Data

This script downloads genuine health survey data from the CDC's 2014 study.
Downloads 253,680 patient survey responses - this may take a minute.
"""

import sqlite3
from ucimlrepo import fetch_ucirepo

print("Downloading CDC Diabetes Health Indicators dataset...")
print("Source: CDC Behavioral Risk Factor Surveillance System (BRFSS) 2014")
print("This will take approximately one minute...")

# Download from the UCI Machine Learning Repository
cdc_diabetes = fetch_ucirepo(id=891)

# Get the data (features are health indicators, target is diabetes status)
X = cdc_diabetes.data.features
y = cdc_diabetes.data.targets

# Combine everything into one table
df = X.copy()
df['Diabetes_binary'] = y

print(f"\nSuccessfully downloaded {len(df):,} patient records")
print(f"Found {len(df.columns)} health indicators")
print(f"\nAvailable columns:")
for col in df.columns:
    print(f"  - {col}")

# Create the SQLite database
print("\nCreating database: diabetes_health.db")
conn = sqlite3.connect("diabetes_health.db")

# Save all the data to the database
df.to_sql('patient_health_data', conn, if_exists='replace', index=False)

# Add additional database features
cursor = conn.cursor()

# Add unique patient ID column
cursor.execute("ALTER TABLE patient_health_data ADD COLUMN patient_id INTEGER")
cursor.execute("UPDATE patient_health_data SET patient_id = rowid")

# Create pre-computed views for common queries
# These improve query performance for frequently asked questions

# View 1: Diabetes statistics grouped by age
cursor.execute("""
    CREATE VIEW diabetes_by_age AS
    SELECT
        Age as age_group,
        COUNT(*) as total_patients,
        SUM(Diabetes_binary) as diabetic_patients,
        ROUND(AVG(Diabetes_binary) * 100, 2) as diabetes_rate_pct,
        ROUND(AVG(BMI), 1) as avg_bmi,
        ROUND(AVG(HighBP) * 100, 1) as high_bp_pct
    FROM patient_health_data
    GROUP BY Age
    ORDER BY Age
""")

# View 2: Health metrics grouped by general health rating
cursor.execute("""
    CREATE VIEW health_risk_summary AS
    SELECT
        GenHlth as general_health_rating,
        COUNT(*) as patient_count,
        ROUND(AVG(BMI), 1) as avg_bmi,
        ROUND(AVG(HighBP) * 100, 1) as high_bp_rate,
        ROUND(AVG(HighChol) * 100, 1) as high_cholesterol_rate,
        ROUND(AVG(Diabetes_binary) * 100, 2) as diabetes_rate
    FROM patient_health_data
    GROUP BY GenHlth
    ORDER BY GenHlth
""")

conn.commit()

# Display database contents
print(f"\nDatabase created successfully")
print(f"\nDatabase contents:")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
for table in cursor.fetchall():
    print(f"  Table: {table[0]}")

cursor.execute("SELECT name FROM sqlite_master WHERE type='view'")
views = cursor.fetchall()
if views:
    print(f"\nPre-computed views:")
    for view in views:
        print(f"  View: {view[0]}")

# Display summary statistics
cursor.execute("SELECT COUNT(*) FROM patient_health_data")
total = cursor.fetchone()[0]

cursor.execute("SELECT SUM(Diabetes_binary) FROM patient_health_data")
diabetic = cursor.fetchone()[0]

cursor.execute("SELECT AVG(BMI) FROM patient_health_data")
avg_bmi = cursor.fetchone()[0]

print(f"\nDataset statistics:")
print(f"  Total Patients: {total:,}")
print(f"  With Diabetes: {diabetic:,} ({diabetic/total*100:.1f}%)")
print(f"  Average BMI: {avg_bmi:.1f}")

conn.close()

print("\nSetup complete. Database is ready to use.")
print(f"\nTo start the application, run: streamlit run app.py")
print(f"\nData source: CDC BRFSS 2014 (253,680 patient records, 21 health indicators)")
