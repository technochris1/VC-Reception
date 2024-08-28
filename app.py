import os
import uuid
import json
import datetime
import re



from flask import Flask, render_template, request, abort
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_sqlalchemy.model import Model

from flask_moment import Moment

from flask_mail import Mail, Message

from sqlalchemy.sql import func
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
  pass

db = SQLAlchemy(model_class=Base)

# create the app
app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'technochris1@gmail.com'
app.config['MAIL_PASSWORD'] = 'jams vumd ylam chfn'
app.config['MAIL_DEFAULT_SENDER'] = 'technochris1@gmail.com'

#db.init_app(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
moment = Moment(app)

mail = Mail(app)

@app.route("/")
def dashboard():
    return render_template('index.html')

@app.route('/guests/')
def guests():
    return render_template('guests.html', guests=VcGuest.query.all())

@app.route('/forms/')
def forms():
    return render_template('forms.html')

@app.route('/events/', methods=['GET', 'POST'])
def events():

    if request.method == 'POST':

        newEvent = Event(
            eventName=request.values.get('eventName'),
            eventDescription=request.values.get('eventDescription'),
            eventStartDate= datetime.datetime.strptime(re.sub(r" \((.*?)\)", "", request.values.get('eventStart')), "%a %b %d %Y %H:%M:%S %Z%z"),
            eventEndDate= datetime.datetime.strptime(re.sub(r" \((.*?)\)", "", request.values.get('eventEnd')), "%a %b %d %Y %H:%M:%S %Z%z"),
            eventLocation=request.values.get('eventLocation')
        )
        db.session.add(newEvent)
        db.session.commit()

    return render_template('events.html', events=Event.query.all())

#https://flask-mail.readthedocs.io/en/latest/#
@app.route('/sendEmail/')
def sendEmail():
    msg = Message(
        subject="Hello",
        sender="from@example.com",
        recipients=["cfisk@symtechsolutions.com"],
    )
    mail.send(msg)



# Guest VIEWS

@app.route('/guestView/', methods=['GET', 'POST'])
def guest():
    if request.method == 'POST':
        username = request.values.get('user') # Your form's
        password = request.values.get('pass') # input names
        #your_register_routine(username, password)

        print(request.values.get('emailAddress'))

        existingGuest = db.session.execute(db.select(VcGuest).filter_by(email=request.values.get('emailAddress'))).first()
        print(existingGuest)
        print(request.form)
        if(existingGuest == None):
            termsCheckValue = False
            idCheckValue = False

            if request.form.get('termsCheck') is not None:
                termsCheckValue = True
            if request.form.get('idCheck') is not None:
                idCheckValue = True




            newGuest = VcGuest(
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


        


        return render_template('guest-view.html')
    else:
        # You probably don't have args at this route with GET
        # method, but if you do, you can access them like so:
        #yourarg = flask.request.args.get('argname')
        #your_register_template_rendering(yourarg)
        
        return render_template('guest-view.html')

@app.route('/checkIn/<uuid>')
def checkIn(uuid = None):
    guest = VcGuest.query.filter_by(uuid = uuid).first()
    if(guest):
        guest.lastVisit = func.now()


        return json.dumps(guest.firstName)
    else:
        return abort(404)



def generate_uuid():
    return str(uuid.uuid4())



class VcGuest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String, name="uuid", default=generate_uuid)

    fetUsername = db.Column(db.String(100))
    firstName = db.Column(db.String(100))
    lastName = db.Column(db.String(100))
    email = db.Column(db.String(200), unique=True, nullable=False)
    phone = db.Column(db.String(20))

    termsCheck = db.Column(db.Boolean(), default=False)
    termsDate = db.Column(db.DateTime(timezone=True), server_default=None)
    termsVersion = db.Column(db.String(20))

    idCheck = db.Column(db.Boolean(), default=False)
    idDate = db.Column(db.DateTime(timezone=True), server_default=None)

    lastVisit = db.Column(db.DateTime(timezone=True), server_default=None)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f'<Vc Guest - {self.firstName}>'


class Form(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    formName = db.Column(db.String(100))
    formDescription = db.Column(db.String(200))
    formVersion = db.Column(db.String(20))
    formFile = db.Column(db.String(100))
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f'<Form - {self.formName}>'
    
class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    eventName = db.Column(db.String(100))
    eventDescription = db.Column(db.String(200))
    eventStartDate = db.Column(db.DateTime(timezone=True))
    eventEndDate = db.Column(db.DateTime(timezone=True))
    eventLocation = db.Column(db.String(100))
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f'<Event - {self.eventName}>'
    
class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    settingName = db.Column(db.String(100))
    settingValue = db.Column(db.String(200))

    def __repr__(self):
        return f'<Setting - {self.settingName}>'
    
class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tagName = db.Column(db.String(100))
    tagDescription = db.Column(db.String(200))

    def __repr__(self):
        return f'<Tag - {self.tagName}>'
    


with app.app_context():
    db.create_all()



if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0' )