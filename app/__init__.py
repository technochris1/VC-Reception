
import os
import sys
from os import environ as env
# from dotenv import load_dotenv

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
#from flask_apscheduler import APScheduler
from flask_moment import Moment
from flask_mail import Mail, Message

from sqlalchemy.sql import func
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass

#from auto_update import Updater





class Base(DeclarativeBase, MappedAsDataclass):
  pass

# load_dotenv()

db = SQLAlchemy(model_class=Base)





# create the app
app = Flask(__name__)
app.config.from_object('config.DevelopmentConfig')
admin = Admin(app, name='VC-Admin')
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'home' 
login_manager.login_message_category = "info"
moment = Moment(app)
mail = Mail(app)

# initialize scheduler
#scheduler = APScheduler()
# if you don't wanna use a config, you can set options here:
# scheduler.api_enabled = True
#scheduler.init_app(app)
#scheduler.start()


from app import routes, models

class guestView(ModelView):    
    can_delete = False
    column_hide_backrefs = False
    column_list = ('fetUsername', 'uuid', 'email', 'name', 'phone', 'roles')
    form_columns = ('fetUsername', 'uuid', 'email', 'password', 'name', 'phone' ,'roles','allow_qrcode_refresh')
    can_view_details = True

class roleView(ModelView):
    column_hide_backrefs = False    
    column_list = ('name','description', 'permissions', 'guests', 'skip_payment_at_checkin', 'allow_password_reset','allow_login_to_backoffice')
    form_columns = ('name','description', 'permissions', 'guests', 'skip_payment_at_checkin', 'allow_password_reset','allow_login_to_backoffice')

class guestLogView(ModelView):
    can_create = False
    can_edit = False
    can_delete = False
    column_sortable_list = ('userID', 'checked_in_at','paymentMethod')

class guestCreditsView(ModelView):
    can_create = False
    can_edit = False
    can_delete = False
    column_hide_backrefs = False
    column_list = ('guest', 'generalAmount')
    column_sortable_list = ('guest', 'generalAmount')

class creditTransactionLogView(ModelView):
    can_create = False
    can_edit = False
    can_delete = False
    column_hide_backrefs = False
    column_list = ('timestamp', 'guest', 'authorizedBy', 'authorizedSource', 'generalAmountChange', 'description')
    column_sortable_list = ('timestamp', 'guest', 'authorizedBy', 'authorizedSource', 'generalAmountChange', 'description')



admin.add_view(guestView(models.Guest, db.session))
admin.add_view(guestCreditsView(models.GuestCredit, db.session))
admin.add_view(guestLogView(models.Guestlog, db.session))
admin.add_view(creditTransactionLogView(models.CreditTransactionLog, db.session))
admin.add_view(roleView(models.Role, db.session))
#admin.add_view(ModelView(models.Setting, db.session))



migrate = Migrate(app, db)



# one time setup
with app.app_context():
    pass
    
    #db.create_all()

    # settings = models.Setting.query.first()
    # if(settings is None):
    #     settings = models.Setting()
    #     settings.tos = "Contained Herewithin; a Contract entered into between and Vikings Castle LLC© on this , day of , # RELEASE OF LIABILITY FOR In exchange for attendance and participation in the event organized by Vikings Castle LLC© of Seaford DE, and/or use of the property, facilities and services of Vikings Castle, I agree for myself and only for myself, to the following: 1. I agree to observe and obey all posted rules and warnings, and further agree to follow any oral instructions or directions given by Vikings Castle, or the employees, representatives, or agents of Vikings Castle. 2. I recognize that there are certain inherent risks associated with the event I am attending and participating in and I assume full responsibility for personal injury to myself, and further release and discharge Vikings Castle, including it's Owner/s and staff, for injury, loss, or damage arising out of my participation in the event, whether caused by the fault of myself of myself or other parties. 3. I agree to pay for all damages to the facilities and/or property of Vikings castle caused by my negligent, reckless, or willful actions. 4. Any legal or equitable claim that may arise from participation in the above shall be resolved under Delaware law. 5. I agree and acknowledge that I am under no pressure or duress to sign this agreement and that I have been given reasonable opportunity to review it before signing. I further agree and acknowledge that I am free to have my own legal counsel review this agreement if I SO desire. I HAVE READ THE CONTAINED HEREWITHIN AND ACKNOWLEDGE THAT UNDER PENALTY AND PURGERY IN DUE COURSE OF LAW THAT ALL INFORMATION CONTAINED HEREIN; IS VOLUNTARY. THAT BY MY SIGNATURE BELOW I ACKNOWDLEDGE THAT I AM 21 YEARS OF AGE OR OLDER AND THAT I VOLUNTAIRLY SURRENDER CERTAIN LEGAL RIGHTS OF MY OWN FREE WILL THIS DOCUMENT IS GOOD FOR THE LENGTH OF 1 YEAR OF SIGNED. FETLIFE SCREEN NAME PRINT LEGAL NAME SIGNATURE AND DATE"
    #     settings.checkInCooldownSeconds = 60

    #     #models.db.session.add(settings)
        

    

    # guest = models.Guest.query.first()
    # if(guest is None):
    #     guest = models.Guest()
    #     guest.uuid = '1'
    #     guest.fetUsername = 'demoFetlifeUsername'
    #     guest.name = 'demoName'
    #     guest.email = 'demoEmail@demoEmail.com'
    #     guest.phone = '1234567890'
    #     guest.password = bcrypt.generate_password_hash('1').decode('utf-8')
    #     guest.termsCheck = True
    #     guest.termsDate = datetime.datetime.now()

    #     #models.db.session.add(guest)
        

    
    #db.session.commit()





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
logging.basicConfig()
logging.getLogger('sqlalchemy').setLevel(logging.ERROR)


@app.template_filter('check_role_allow_password_reset')
def check_role_allow_password_reset(guest):   
    return any(x.allow_password_reset == True for x in guest.roles)

# @app.template_filter('check_role_allow_qrcode_refresh')
# def check_role_allow_qrcode_refresh(guest):   
#     if guest and guest.roles:
#         return any(x.allow_qrcode_refresh == True for x in guest.roles)
#     else:
#         return False
    
@app.template_filter('utc_to_local')
def utc_to_local(utc_dt):
    return utc_dt.replace(tzinfo=datetime.timezone.utc).astimezone(tz=None)



    




