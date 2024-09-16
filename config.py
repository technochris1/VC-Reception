import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    DEBUG = False
    TESTING = False

    SERVER_REPO = 'technochris1/VC-Reception'
    APP_VERSION = 'V1.4'
    
    SECRET_KEY = "REPLACE_ME"
    SECURITY_PASSWORD_SALT = "73996734432957991591033005944368149869"
    #SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'empty_database.db')   #Initial Database
    #SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'dev_database.db')   #Development Database
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'database.db')  #Production Database
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True,}

    REMEMBER_COOKIE_SAMESITE = "strict"
    SESSION_COOKIE_SAMESITE = "strict"

    MAIL_SERVER=None
    MAIL_PORT=None
    MAIL_USE_TLS=None
    MAIL_USE_SSL=None
    MAIL_USERNAME=None
    MAIL_PASSWORD=None
    MAIL_DEFAULT_SENDER=None

    SCHEDULER_API_ENABLED = True


class ProductionConfig(Config):
    pass


class DevelopmentConfig(Config):
    DEBUG = True    
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = 'technochris1@gmail.com'
    MAIL_PASSWORD = 'jams vumd ylam chfn'
    MAIL_DEFAULT_SENDER = 'technochris1@gmail.com'

class TestingConfig(Config):
    TESTING = True