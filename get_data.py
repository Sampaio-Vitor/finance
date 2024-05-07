import os.path
import pandas as pd
import mysql.connector
import googleapiclient.discovery
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration Constants from .env file
API_KEY = os.getenv('API_KEY')
SAMPLE_SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
SAMPLE_RANGE_NAME = os.getenv('RANGE_NAME')

# MySQL database configuration from .env
MYSQL_CONFIG = {
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'database': os.getenv('DB_NAME'),
    'raise_on_warnings': True
}

def fetch_data_with_api_key():
    """Fetch data from Google Sheets using an API key."""
    try:
        service = googleapiclient.discovery.build('sheets', 'v4', developerKey=API_KEY)
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID, range=SAMPLE_RANGE_NAME).execute()
        values = result.get('values', [])

        if not values:
            print("No data found.")
            return pd.DataFrame()  # Return empty DataFrame if no data found

        # Create DataFrame from fetched values
        df = pd.DataFrame(values, columns=['data', 'compra'])
        return df

    except Exception as e:
        print("Failed to retrieve data:", e)
        return pd.DataFrame()  # Return empty DataFrame on error

def update_mysql_database(new_df):
    """Update MySQL database with new data."""


    # Connect to MySQL database
    cnx = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = cnx.cursor()

    # Fetch existing data from MySQL
    cursor.execute("SELECT data, compra FROM raw")
    existing_data = cursor.fetchall()
    existing_df = pd.DataFrame(existing_data, columns=['data', 'compra'])

    # Determine new data by checking if it's not in existing data
    merged_df = pd.merge(new_df, existing_df, on=['data', 'compra'], how='left', indicator=True)
    new_rows = merged_df[merged_df['_merge'] == 'left_only'].drop('_merge', axis=1)

    if new_rows.empty:
        pass  # No new data to insert
    else:
        # Insert new data into the 'raw' table
        insert_query = "INSERT INTO raw (data, compra) VALUES (%s, %s)"
        for index, row in new_rows.iterrows():
            print("Inserting:", row['data'], row['compra'])
            cursor.execute(insert_query, (row['data'], row['compra']))

        # Commit changes to the database
        cnx.commit()
        print("New data inserted into MySQL database successfully.")

    # Close cursor and connection
    cursor.close()
    cnx.close()

def main():
    df = fetch_data_with_api_key()
    update_mysql_database(df)

if __name__ == "__main__":
    main()
