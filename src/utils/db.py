import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()

class Database:
    def __init__(self):
        self.server = os.getenv('DB_SERVER')
        self.database = os.getenv('DB_DATABASE')
        self.connection_string = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={self.server};DATABASE={self.database};Trusted_Connection=yes;'
    
    def get_connection(self):
        try:
            conn = pyodbc.connect(self.connection_string)
            return conn
        except Exception as e:
            print(f"Veritabanı Hatası: {e}")
            return None

db = Database()