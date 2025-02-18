
import os
import sys
import atexit
from os import environ as env
# from dotenv import load_dotenv

import json
from datetime import datetime, timezone, time
import pytz

import re
import logging
import gevent
from gevent import monkey
monkey.patch_all()


from flask import Flask, render_template, request, abort, jsonify
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_sqlalchemy.model import Model
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_socketio import SocketIO
from flask_moment import Moment
from flask_mail import Mail, Message
from flask_apscheduler import APScheduler
from apscheduler.schedulers.background import BackgroundScheduler


from sqlalchemy.sql import func
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass

#from auto_update import Updater




class Base(DeclarativeBase, MappedAsDataclass):
  pass

# load_dotenv()

db = SQLAlchemy(model_class=Base)





# create the app
app = Flask(__name__)
#app.config.from_object('config.DevelopmentConfig')
#app.config.from_object('config.ProductionConfig')


#print(os.environ)
print("VC_SYSTEM: ",os.environ.get('VC_SYSTEM'))
if os.environ.get('VC_SYSTEM') == None:
    #print('VC_SYSTEM not set in environment variables, please set it to "SERVER", exiting...')
    #sys.exit()

    print('VC_SYSTEM not set in environment variables, please set it to "SERVER", continuing with DevelopmentConfig...')    
    app.config.from_object('config.DevelopmentConfig')
    
elif os.environ.get('VC_SYSTEM') == 'SERVER':    
    app.config.from_object('config.ProductionConfig')
else:
    app.config.from_object('config.DevelopmentConfig')

print(app.config['MAIL_USERNAME'])


app.config['SCHEDULER_API_ENABLED'] = True

admin = Admin(app, name='VC-Admin')
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'home' 
login_manager.login_message_category = "info"
moment = Moment(app)
mail = Mail(app)

socketio = SocketIO(app)



if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':  
    # initialize scheduler
    scheduler = APScheduler()
    # if you don't wanna use a config, you can set options here:
    # scheduler.api_enabled = True

    @scheduler.task('cron', id='list_jobs_every_min', minute='*', misfire_grace_time=3600)
    def list_jobs():
        #print('Job 2 (Every Min) executed')
        print("ALL Jobs:",scheduler.get_jobs())


    @scheduler.task('cron', id='checkin_cleanup', minute='*', misfire_grace_time=3600)
    def checkin_cleanup():
        with app.app_context():
            from app import routes
            routes.checkin_cleanup()

    scheduler.init_app(app)
    scheduler.start()
    #atexit.register(lambda: scheduler.shutdown())


from app import routes, models

class guestView(ModelView):    
    can_delete = True
    column_hide_backrefs = False
    #column_sortable_list = ('fetUsername', 'email','name','phone','checkedIn','roles')
    column_list = ('checkin_blocked','fetUsername', 'uuid', 'email', 'name', 'phone', 'roles', 'checkedIn')
    form_columns = ('checkin_blocked','fetUsername', 'uuid', 'email', 'password', 'name', 'phone' ,'roles','allow_qrcode_refresh', 'checkedIn')
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
    #can_edit = False
    #can_delete = False
    column_hide_backrefs = False
    column_list = ('guest', 'points', 'generalAmount', 'specialEventAmount', 'privateSessionAmount')
    column_sortable_list = ('guest',)

class creditTransactionLogView(ModelView):
    can_create = False
    #can_edit = False
    #can_delete = False
    column_hide_backrefs = False
    column_list = ('timestamp', 'guest', 'authorizedBy', 'authorizedSource', 'pointChange', 'generalAmountChange', 'description')
    column_sortable_list = ('timestamp', 'guest', 'authorizedBy', 'authorizedSource', 'pointChange', 'generalAmountChange', 'description')

#class eventsView(ModelView):   
    #column_hide_backrefs = False
    #column_list = ('title', 'eventDescription', 'start', 'end', 'addons')

class addonView(ModelView):   
    column_hide_backrefs = False
    column_list = ('title', 'description', 'guests', 'cost')


admin.add_view(guestView(models.Guest, db.session))
admin.add_view(guestCreditsView(models.GuestCredit, db.session))
admin.add_view(guestLogView(models.Guestlog, db.session))
admin.add_view(creditTransactionLogView(models.CreditTransactionLog, db.session))
admin.add_view(roleView(models.Role, db.session))
admin.add_view(ModelView(models.Event, db.session))
admin.add_view(addonView(models.Addon, db.session))
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
        
    # guestLog = models.Guestlog.query.all()
    # if(guestLog is not None):
    #     for log in guestLog:
    #         #print(log.checked_in_at)
    #         if(log.checked_in_at):
    #             log.checked_in_at_local = log.checked_in_at.replace(tzinfo=timezone.utc).astimezone(tz=None)
    #             db.session.commit()





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

@app.template_filter('get_general_credits') 
def get_general_credits(credit):   
    return sum(x.generalAmount for x in credit)

@app.template_filter('get_special_event_credits')
def get_special_event_credits(credit):   
    return sum(x.specialEventAmount for x in credit)

@app.template_filter('get_private_session_credits')
def get_private_session_credits(credit):   
    return sum(x.privateSessionAmount for x in credit)

@app.template_filter('check_role_skip_payment_at_checkin')
def check_role_skip_payment_at_checkin(guest):   
    return any(x.skip_payment_at_checkin == True for x in guest.roles)

@app.template_filter('not_check_role_skip_payment_at_checkin')
def not_check_role_skip_payment_at_checkin(guest):   
    return not any(x.skip_payment_at_checkin == True for x in guest.roles)

# @app.template_filter('check_role_allow_qrcode_refresh')
# def check_role_allow_qrcode_refresh(guest):   
#     if guest and guest.roles:
#         return any(x.allow_qrcode_refresh == True for x in guest.roles)
#     else:
#         return False
    
@app.template_filter('utc_to_local')
def utc_to_local(utc_dt):
    return utc_dt.replace(tzinfo=datetime.timezone.utc).astimezone(tz=None)

@app.template_filter('timestamp_to_date_min_time')
def timestamp_to_date_min_time(timestamp):
    return datetime.combine(datetime.fromtimestamp(timestamp), time.min)

@app.template_filter('timestamp_to_date_str')
def timestamp_to_date_str(timestamp):
    return datetime.fromtimestamp(timestamp).strftime('%Y/%m/%d')

@app.template_filter('timestamp_to_time_str')
def timestamp_to_time_str(timestamp):
    return datetime.fromtimestamp(timestamp).strftime('%H:%M')

@app.template_filter('timestamp_to_time_str_ampm')
def timestamp_to_time_str_ampm(timestamp):
    return datetime.fromtimestamp(timestamp).strftime('%I:%M %p')

@app.template_filter('timestamp_to_str')
def timestamp_to_str(timestamp):
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M')

@app.template_filter('timestamp_to_str_ampm')
def timestamp_to_str_ampm(timestamp):
    return datetime.fromtimestamp(timestamp).strftime('%m/%d %I:%M %p')
    

@app.template_filter('guests_to_str')
def guests_to_str(guests):
    print(len(guests))
    return ','.join([x.fetUsername for x in guests if x])


