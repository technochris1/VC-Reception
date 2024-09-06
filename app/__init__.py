from io import BytesIO
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

from flask_moment import Moment
from flask_mail import Mail, Message
import qrcode

from sqlalchemy.sql import func
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass

from auto_update import Updater




class Base(DeclarativeBase, MappedAsDataclass):
  pass

load_dotenv()

db = SQLAlchemy(model_class=Base)




def create_app():
    from . import models, views, services
    # create the app
    app = Flask(__name__)
    app.config.from_object('config')

    models.init_app(app)
    views.init_app(app)
    services.init_app(app)

    admin = Admin(app, name='VC-Admin')
    admin.add_view(ModelView(Guest, db.session))
    

    basedir = os.path.abspath(os.path.dirname(__file__))

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db') # env['SQLALCHEMY_DATABASE_URI']
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = env['SQLALCHEMY_TRACK_MODIFICATIONS']
    app.config['MAIL_SERVER'] = env['MAIL_SERVER']
    app.config['MAIL_PORT'] = env['MAIL_PORT']
    app.config['MAIL_USE_TLS'] = env['MAIL_USE_TLS']
    app.config['MAIL_USE_SSL'] = env['MAIL_USE_SSL']
    app.config['MAIL_USERNAME'] = env['MAIL_USERNAME']
    app.config['MAIL_PASSWORD'] = env['MAIL_PASSWORD']
    app.config['MAIL_DEFAULT_SENDER'] = env['MAIL_DEFAULT_SENDER']

    #db.init_app(app)
    db = SQLAlchemy(app)
    migrate = Migrate(app, db)
    moment = Moment(app)
    mail = Mail(app)

    with app.app_context():
        db.create_all()

    return app




app = create_app()


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

#reset_logging()
#logging.basicConfig()

@app.template_filter('utc_to_local')
def utc_to_local(utc_dt):
    return utc_dt.replace(tzinfo=datetime.timezone.utc).astimezone(tz=None)




def sendQRCodeEmail(recipients, uuid):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(uuid)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    
    print("IMG",img)

    temp = BytesIO()
    temp.name = "QR.png"
    img.save(temp)
    temp.seek(0)

    #qr_image = {'photo': temp.getvalue()}
    #print("IMG",qr_image['photo'])
    
    return sendEmail(recipients, "VC Access - QR Code", "Please find your VC QR code attached", temp.getvalue())


def sendEmail(recipients, subject, message, attachment=None):
    mail = Mail(app)

    print("Attachment",attachment)

    try:
        msg = Message(subject,
                    sender=("VC Front Desk", "VC-Desk@whoknows.com"),
                    recipients=recipients)
        if attachment:
            try:
                
                    msg.attach("registration-qr-code.png", "image/png", attachment)
                    #msg.body = render_template('email.html', message=message, image="cid:qr_image")
                    msg.body = message
            except Exception as e:
                print("send_mail.attachment exception: {}".format(e))
        mail.send(msg)
    except:
        print("send_mail exception:\n{}".format(traceback.format_exc()))
    return


# Guest VIEWS

@app.route('/guestView/', methods=['GET', 'POST'])
def guestView():
    if request.method == 'POST':
        username = request.values.get('user') # Your form's
        password = request.values.get('pass') # input names
        #your_register_routine(username, password)

        print(request.values.get('emailAddress'))

        existingGuest = db.session.execute(db.select(Guest).filter_by(email=request.values.get('emailAddress'))).first()
        print(existingGuest)
        print(request.form)
        if(existingGuest == None):
            termsCheckValue = False
            idCheckValue = False

            if request.form.get('termsCheck') is not None:
                termsCheckValue = True
            if request.form.get('idCheck') is not None:
                idCheckValue = True




            newGuest = Guest(
            fetUsername=request.values.get('fetUsername'),
            firstName=request.values.get('firstName'),
            lastName=request.values.get('lastName'),
            email=request.values.get('emailAddress'),
            phone=request.values.get('phoneNumber'),
            termsCheck=termsCheckValue,
            idCheck=idCheckValue
            )


            db.session.add(newGuest)
            db.session.commit()

            sendQRCodeEmail([newGuest.email], newGuest.uuid)


        


        return render_template('guest-view.html')
    else:
        # You probably don't have args at this route with GET
        # method, but if you do, you can access them like so:
        #yourarg = flask.request.args.get('argname')
        #your_register_template_rendering(yourarg)
        
        return render_template('guest-view.html')

@app.route('/generateUUID/')
def generateUUID():
    return jsonify(generate_uuid())

@app.route('/checkIn/')
@app.route('/checkIn/<uuid>')
def checkIn(uuid = None):
    guest = Guest.query.filter_by(uuid = uuid).first()
    if(guest):

        #visitTime = datetime.datetime.now()
        visitTime = func.now()
        guest.lastVisit = visitTime

        newCheckIn = Guestlog(
            checked_in_at = visitTime,
            userID = guest.id
        )
        db.session.add(newCheckIn)
        db.session.commit()



        return json.dumps(guest.firstName)
    else:
        return abort(404)




    




