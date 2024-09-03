from io import BytesIO
import os
from os import environ as env
from dotenv import load_dotenv
import uuid
import json
import datetime
import re

from dataclasses import dataclass

from flask import Flask, render_template, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_sqlalchemy.model import Model

from flask_moment import Moment
from flask_mail import Mail, Message
import qrcode

from sqlalchemy.sql import func
from sqlalchemy.orm import DeclarativeBase

from auto_update import Updater


class Base(DeclarativeBase):
  pass

load_dotenv()

db = SQLAlchemy(model_class=Base)

# create the app
app = Flask(__name__)

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


@app.template_filter('utc_to_local')
def utc_to_local(utc_dt):
    return utc_dt.replace(tzinfo=datetime.timezone.utc).astimezone(tz=None)


@app.route("/")
def dashboard():

    current_time = datetime.datetime.now(datetime.UTC)

    last_24_hours = current_time - datetime.timedelta(hours=24)

    return render_template('index.html', guests_checked_in_count=Guest.query.filter(Guest.lastVisit > last_24_hours ).count(),
                           guests_total_count=Guest.query.count(),
                           guests_checked_in=Guest.query.filter(Guest.lastVisit > last_24_hours ).all(),
                           quests_top_5=db.session.query(Guest, func.count(Guestlog.id)).join(Guestlog).group_by(Guest.id).order_by(func.count(Guestlog.id).desc()).limit(5).all(),
                           #guests_top_5=db.session.query(Guest, func.count(Guestlog)).outerjoin(Guestlog, Guest.id == Guestlog.userID).group_by(Guest.id).order_by(func.count(Guestlog.id).desc()).limit(5).all(),
                           
                           )


@app.route('/guest/')
@app.route('/guest/<uuid>')
def guest(uuid = None): 
    print("UUID:",uuid)
    result = Guest.query.filter_by(uuid = uuid).first()
    print("Returning User:",result.uuid)
    return jsonify(result)

@app.route('/guests/', methods=['GET', 'POST'])
def guests():
    if request.method == 'POST':
        termsCheckValue = False
        idCheckValue = False


        if request.form.get('termsCheck') is not None:
            termsCheckValue = True
        if request.form.get('idCheck') is not None:
            idCheckValue = True
        
        rowID = request.values.get('dbID')
        print(rowID)
        
        if (rowID):
            print("Updating Row")
            guest = Guest.query.filter_by(id=rowID).first()
            if guest is None:
                return abort(404)
            
            guest.fetUsername=request.values.get('fetUsername')
            guest.firstName=request.values.get('firstName')
            guest.lastName=request.values.get('lastName')
            guest.email=request.values.get('emailAddress')
            guest.phone=request.values.get('phoneNumber')
            guest.termsCheck=termsCheckValue
            guest.idCheck=idCheckValue

            if(guest.uuid != request.values.get('uuid')):
                guest.uuid=request.values.get('uuid')
                #send email for new QR code
                sendQRCodeEmail([guest.email], guest.uuid)


            

            db.session.commit()




        else:
            print("Adding Row")
            newGuest = Guest(
                uuid = request.values.get('uuid'),
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
        
    return render_template('guests.html', guests=Guest.query.all())




@app.route('/logbook/')
def logbook():
    return render_template('logbook.html', guests=Guest.query.all(), log=Guestlog.query.all())
    #return render_template('logbook.html')



@app.route('/forms/')
def forms():
    return render_template('forms.html')

@app.route('/events/', methods=['GET', 'POST'])
def events():

    if request.method == 'POST':

        newEvent = Event(
            eventName=request.values.get('eventName'),
            eventDescription=request.values.get('eventDescription'),
            eventStartDate= int(datetime.datetime.timestamp(datetime.datetime.strptime(re.sub(r" \((.*?)\)", "", request.values.get('eventStart')), "%a %b %d %Y %H:%M:%S %Z%z"))),
            eventEndDate= int(datetime.datetime.timestamp(datetime.datetime.strptime(re.sub(r" \((.*?)\)", "", request.values.get('eventEnd')), "%a %b %d %Y %H:%M:%S %Z%z"))),
            eventLocation=request.values.get('eventLocation')
        )
        db.session.add(newEvent)
        db.session.commit()

    allEvents = Event.query.all()
    

    return render_template('events.html', events=json.dumps(Event.query.all()))

#https://flask-mail.readthedocs.io/en/latest/#
@app.route('/sendEmail/')
def sendEmailRoute():
    msg = Message(
        subject="Hello",
        sender="from@example.com",
        recipients=["cfisk@symtechsolutions.com"],
    )
    mail.send(msg)



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



def generate_uuid():
    return str(uuid.uuid4())


@dataclass
class Guest(db.Model):
    id:int = db.Column(db.Integer, primary_key=True)
    uuid:str  = db.Column(db.String, name="uuid", default=generate_uuid)

    fetUsername:str  = db.Column(db.String(100))
    firstName:str  = db.Column(db.String(100))
    lastName:str  = db.Column(db.String(100))
    email:str  = db.Column(db.String(200), nullable=False)
    phone:str  = db.Column(db.String(20))

    termsCheck:bool = db.Column(db.Boolean(), default=False)
    termsDate = db.Column(db.DateTime(timezone=True), server_default=None)
    termsVersion:str  = db.Column(db.String(20))

    idCheck:bool = db.Column(db.Boolean(), default=False)
    idDate = db.Column(db.DateTime(timezone=True), server_default=None)
    logbook = db.relationship('Guestlog', backref='Guest')

    lastVisit = db.Column(db.DateTime(timezone=True), server_default=None)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

@dataclass
class Guestlog(db.Model):
    id:int = db.Column(db.Integer, primary_key=True)
    checked_in_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

    userID = db.Column(db.Integer, db.ForeignKey('guest.id'))


@dataclass
class Form(db.Model):
    id:int = db.Column(db.Integer, primary_key=True)
    formName:str  = db.Column(db.String(100))
    formDescription:str  = db.Column(db.String(200))
    formVersion:str  = db.Column(db.String(20))
    formFile:str  = db.Column(db.String(100))
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

@dataclass
class Event(db.Model):
    id:int = db.Column(db.Integer, primary_key=True)
    eventName:str = db.Column(db.String(100))
    eventDescription:str = db.Column(db.String(200))
    eventStartDate:int = db.Column(db.Integer, default=int(datetime.datetime.timestamp(datetime.datetime.now())))
    eventEndDate:int = db.Column(db.Integer, default=int(datetime.datetime.timestamp(datetime.datetime.now())))
    eventLocation:str = db.Column(db.String(100))
    #created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())


@dataclass
class Setting(db.Model):
    id:int = db.Column(db.Integer, primary_key=True)
    settingName:str  = db.Column(db.String(100))
    settingValue:str  = db.Column(db.String(200))

   

@dataclass
class Tag(db.Model):
    id:int = db.Column(db.Integer, primary_key=True)
    tagName:str  = db.Column(db.String(100))
    tagDescription:str  = db.Column(db.String(200))



    


with app.app_context():
    db.create_all()



if __name__ == "__main__":
    
    app.run(debug=True, host='0.0.0.0' )
