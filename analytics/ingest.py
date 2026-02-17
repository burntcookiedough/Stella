import pandas as pd
import os

def load_data(data_dir: str = "data/raw") -> pd.DataFrame:
    """
    Loads dailyActivity and sleepDay CSVs, merges them on Date, and cleans up column names.
    Expected files: 'dailyActivity_merged.csv', 'sleepDay_merged.csv' under data_dir.
    """
    activity_path = os.path.join(data_dir, "dailyActivity_merged.csv")
    sleep_path = os.path.join(data_dir, "sleepDay_merged.csv")

    if not os.path.exists(activity_path) or not os.path.exists(sleep_path):
        raise FileNotFoundError(f"Missing CSV files in {data_dir}. Ensure dailyActivity_merged.csv and sleepDay_merged.csv exist.")

    # 1. Load Daily Activity
    df_activity = pd.read_csv(activity_path)
    # Convert 'ActivityDate' to datetime
    df_activity['ActivityDate'] = pd.to_datetime(df_activity['ActivityDate'])
    # Rename matching column for merge
    df_activity.rename(columns={'ActivityDate': 'Date'}, inplace=True)

    # 2. Load Sleep Data
    df_sleep = pd.read_csv(sleep_path)
    # Convert 'SleepDay' to datetime (format is often '4/12/2016 12:00:00 AM')
    df_sleep['SleepDay'] = pd.to_datetime(df_sleep['SleepDay'])
    # Normalize to date only (remove time component for merging)
    df_sleep['Date'] = df_sleep['SleepDay'].dt.normalize()
    # Drop original SleepDay column as we have Date
    df_sleep.drop(columns=['SleepDay'], inplace=True)

    # 3. Merge Datasets (Left join on Id and Date to keep all activity records)
    # Using 'Id' (User ID) and 'Date' as keys
    df_merged = pd.merge(df_activity, df_sleep, on=['Id', 'Date'], how='left')

    # 4. Fill NaN for sleep columns (if no sleep record, assume 0 or keep NaN? Let's fill 0 for minutes, but maybe keep NaN for efficiency/records?)
    # For this simplified analysis, let's fill NaNs with 0 to allow calculations, but flag them if needed.
    # Actually, 0 sleep is different from missing data. Let's keep NaNs for now, feature engineering will handle them.
    
    # 5. Standardize Column Names (snake_case)
    df_merged.columns = [c.lower() for c in df_merged.columns]
    
    # Sort by Date
    df_merged.sort_values(by=['id', 'date'], inplace=True)

    print(f"✅ Data Loaded: {len(df_merged)} records from {df_merged['id'].nunique()} users.")
    return df_merged

if __name__ == "__main__":
    # Test run
    try:
        df = load_data("../../Stella/data/raw") # Adjust path for direct run from this file location if needed, but assuming run from root
        print(df.head())
        print(df.columns)
    except Exception as e:
        print(f"Error loading data: {e}")
