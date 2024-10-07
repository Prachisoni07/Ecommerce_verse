import os
from urllib.parse import quote_plus

# URL encode username and password to avoid special character issues
username = quote_plus("postgres")
password = quote_plus("admin@123")

class Config:
    # Use f-string to correctly format the connection string
    SQLALCHEMY_DATABASE_URI = f'postgresql://{username}:{password}@localhost:5433/app_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = '09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d7e9'

