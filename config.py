import os

class Config:
    # Flaskのデフォルト設定
    DEBUG = True
    TESTING = False
    SECRET_KEY = os.urandom(24)  # セキュリティキー（セッション用）
    
    # MySQLの接続情報
    MYSQL_HOST = "localhost"
    MYSQL_USER = "your_username"
    MYSQL_PASSWORD = "your_password"
    MYSQL_DB = "ranking_db"

class ProductionConfig(Config):
    DEBUG = False
    MYSQL_HOST = "production_db_host"

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True
