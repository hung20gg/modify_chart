import logging
import requests
import time
import copy

import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

import os
current_dir = os.path.dirname(os.path.abspath(__file__))    
BATCH_SIZE = 32

#=================#
#       RDB       #
#=================#

class PostgresDB:
    """Simple PostgreSQL database utility class."""
    
    def __init__(self, host='localhost', database='postgres', 
                 user='postgres', password='postgres', port='5432'):
        """Initialize PostgreSQL connection."""
        self.logger = logging.getLogger(__name__)
        self.conn_params = {
            'host': host,
            'database': database,
            'user': user,
            'password': password,
            'port': port
        }
        self.connection = None
        self.connect()

    def get_schema(self):
        with open(os.path.join(current_dir, 'schema_description.md'), 'r') as f:
            schema = f.read()
        return schema

    def connect(self):
        """Establish database connection."""
        try:
            self.connection = psycopg2.connect(**self.conn_params)
            self.logger.info(f"Connected to PostgreSQL: {self.conn_params['database']}")
        except Exception as e:
            self.logger.error(f"Connection error: {e}")
            raise
    
    def close(self):
        """Close the database connection."""
        if self.connection:
            self.connection.close()
            self.logger.info("Connection closed")
    
    def execute(self, query, params=None, fetch=True):
        """Execute a SQL query and return results if needed."""
        if not self.connection or self.connection.closed:
            self.connect()
            
        cursor = None
        try:
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            cursor.execute(query, params)
            
            if fetch:
                results = cursor.fetchall()
                if results:
                    df = pd.DataFrame([dict(row) for row in results])
                    return df
                else:
                    # Return empty DataFrame with no columns if no results
                    return pd.DataFrame()
            else:
                self.connection.commit()
                return cursor.rowcount
                
        except Exception as e:
            self.connection.rollback()
            self.logger.error(f"Query error: {e}")
            error_msg = f"Query error: {e}"
            return error_msg
        finally:
            if cursor:
                cursor.close()
    
    def query(self, query, params=None):
        """Execute a SELECT query."""
        return self.execute(query, params, fetch=True)
    
    def add_data(self, table_name, data):
        """Insert a row into a table."""
        columns = list(data.keys())
        placeholders = [f'%({col})s' for col in columns]
        
        query = f"""
        INSERT INTO {table_name} ({', '.join(columns)})
        VALUES ({', '.join(placeholders)})
        """
        
        return self.execute(query, data, fetch=False)
    
    def delete_data(self, table_name, condition, params=None):
        """Delete data from a table based on a condition."""
        query = f"DELETE FROM {table_name} WHERE {condition}"
        return self.execute(query, params, fetch=False)
    
    def create_table_from_csv(self, table_name, csv_file, delimiter=',', 
                              data_types=None, primary_key=None, 
                              if_exists='replace', chunksize=1000):
        """Create a table and import data from a CSV file using pandas.
        
        Args:
            table_name: Name for the new table
            csv_file: Path to CSV file
            delimiter: CSV delimiter character
            data_types: Optional dict mapping column names to SQLAlchemy data types
            primary_key: Optional column name to use as primary key
            if_exists: Strategy when table exists ('fail', 'replace', or 'append')
            chunksize: Rows to write at once (for large files)
        """
        try:
            # Create SQLAlchemy engine for pandas
            engine_url = f"postgresql://{self.conn_params['user']}:{self.conn_params['password']}@{self.conn_params['host']}:{self.conn_params['port']}/{self.conn_params['database']}"
            engine = create_engine(engine_url)
            
            # Read CSV with pandas
            self.logger.info(f"Reading CSV file: {csv_file}")
            df = pd.read_csv(csv_file, delimiter=delimiter)
            df['date'] = pd.to_datetime(df['prd_id'], format='%Y%m%d', errors='coerce')
            
            # Set primary key index if specified
            if primary_key and primary_key in df.columns:
                df.set_index(primary_key, inplace=True)
            
            # Write DataFrame to PostgreSQL
            self.logger.info(f"Writing {len(df)} rows to table {table_name}")
            df.to_sql(
                table_name,
                engine,
                if_exists=if_exists,
                index=primary_key is not None,
                dtype=data_types,
                chunksize=chunksize
            )
            
            self.logger.info(f"Successfully imported data from {csv_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error importing CSV: {e}")
            return False
    
    def __del__(self):
        """Destructor to ensure connection is closed."""
        self.close()


if __name__ == "__main__":
    # Example usage
    db = PostgresDB(host='localhost', database='postgres', user='postgres', password='12345678', port='5432')

    csv_file = os.path.join(current_dir, 'fake_tool.csv')

    # Create table from CSV
    db.create_table_from_csv(
        table_name='fake_tool',
        csv_file=csv_file,
        delimiter=',',
        data_types=None,
        # primary_key='PRD_ID',
        if_exists='replace',
        chunksize=1000
    )