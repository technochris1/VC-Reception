
import os
import sys
from os import environ as env
from dotenv import load_dotenv

import json
import datetime
import re
import logging


from flask import Flask, render_template, request, abort, jsonify
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_sqlalchemy.model import Model
from flask_bcrypt import Bcrypt
from flask_login import LoginManager


from flask_moment import Moment
from flask_mail import Mail, Message

from sqlalchemy.sql import func
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass

from auto_update import Updater





class Base(DeclarativeBase, MappedAsDataclass):
  pass

load_dotenv()

db = SQLAlchemy(model_class=Base)





# create the app
app = Flask(__name__)
app.config.from_object('config.DevelopmentConfig')
admin = Admin(app, name='VC-Admin')
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
moment = Moment(app)
mail = Mail(app)

from app import routes, models

class guestView(ModelView):    
    can_delete = False
    column_hide_backrefs = False
    column_list = ('fetUsername','email','name','phone', 'roles')
    form_columns = ('fetUsername','email','name','phone' ,'roles')
    can_view_details = True
class roleView(ModelView):
    column_hide_backrefs = False    
    column_list = ('name','description', 'permissions', 'guests')
    form_columns = ('name','description', 'permissions', 'guests')

class guestLogView(ModelView):
    can_create = False
    can_edit = False
    can_delete = False



admin.add_view(roleView(models.Role, db.session))
admin.add_view(guestView(models.Guest, db.session))
admin.add_view(guestLogView(models.Guestlog, db.session))
admin.add_view(ModelView(models.Setting, db.session))



migrate = Migrate(app, db)



# one time setup
with app.app_context():
    # Create User to test with
    db.create_all()
    






def reset_logging():
    loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]
    loggers.append(logging.getLogger())
    for logger in loggers:
        handlers = logger.handlers[:]
        for handler in handlers:
            logger.removeHandler(handler)
            handler.close()
        logger.setLevel(logging.NOTSET)
        logger.propagate = True

reset_logging()
logging.basicConfig()

@app.template_filter('utc_to_local')
def utc_to_local(utc_dt):
    return utc_dt.replace(tzinfo=datetime.timezone.utc).astimezone(tz=None)



    




