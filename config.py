<<<<<<< HEAD
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'jewel-land-secret-key-2024'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///database.db'
=======
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'jewel-land-secret-key-2024'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///database.db'
>>>>>>> 8be023c312a7e4faaa59bd0f576a847bee82c4f1
    SQLALCHEMY_TRACK_MODIFICATIONS = False