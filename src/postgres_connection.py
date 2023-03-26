import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

dbname = os.getenv("dbname")
user = os.getenv("user")
password = os.getenv("password")
host = os.getenv("host")
port = os.getenv("port")

# Connect to the PostgreSQL database
connection = psycopg2.connect(
    dbname=dbname,
    user=user,
    password=password,
    host=host,
    port=port
)

