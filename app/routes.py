from flask import render_template, jsonify, abort, url_for, redirect, request, flash, render_template_string
from app import app, db, bcrypt, mail
from app.models import Guest, Guestlog, Event, Setting, func
from app.forms import AdminRegistrationForm, AdminLoginForm, GuestRegistrationForm
from flask_mail import  Message
from flask_login import login_user, current_user, logout_user, login_required

from io import BytesIO
import qrcode
import datetime
import uuid
import json

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

@app.route('/login/', methods=['GET', 'POST'])
def login():
    form = AdminLoginForm()
    if form.validate_on_submit():
       guest = Guest.query.filter_by(email=form.email.data).first()
       if guest and bcrypt.check_password_hash(guest.password, form.password.data):
           login_user(guest)           
           return redirect(url_for('dashboard'))
       else:
           flash('Login unsuccessful. Please check email and password', 'danger')
    return render_template('admin_login.html', title='Login Admin', form=form)

@app.route('/registerAdmin/', methods=['GET', 'POST'])
def registerAdmin():
    form = AdminRegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        newAdminGuest = Guest(
            fetUsername=form.fetUsername.data,
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            password=hashed_password
        )
        db.session.add(newAdminGuest)
        db.session.commit()

        flash('Admin added successfully', 'success')
        return redirect(url_for('guests'))
    return render_template('admin_registration.html', title='Register Admin', form=form)

@app.route('/registerGuest/', methods=['GET', 'POST'])
def registerGuest():
    form = GuestRegistrationForm()
    if form.validate_on_submit():        

        newGuest = Guest(
            uuid = request.values.get('uuid'),
            fetUsername=form.fetUsername.data,
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            termsCheck=form.termsCheck.data
        )
        db.session.add(newGuest)
        db.session.commit()

        flash('New Guest Added', 'success')
        return redirect(url_for('guestView', setting=Setting.query.first()))        
    return render_template('guest_registration.html', setting=Setting.query.first(), form = form)


@app.route('/guestView/', methods=['GET', 'POST'])
def guestView():
    form = GuestRegistrationForm()
    if form.validate_on_submit():


        
        newGuest = Guest(
            fetUsername=form.fetUsername.data,
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            termsCheck=form.termsCheck.data,
            
        )
        db.session.add(newGuest)
        db.session.commit()
        sendQRCodeEmail([newGuest.email], newGuest.uuid)
        flash('Guest added successfully', 'success')
        return redirect(url_for('guestView', setting=Setting.query.first(), form=form))

   
    return render_template('guest-view.html', setting=Setting.query.first(), form= form)

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



        return json.dumps(guest.name)
    else:
        return abort(404)




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
                name=request.values.get('name'),
                email=request.values.get('emailAddress'),
                phone=request.values.get('phoneNumber'),
                termsCheck=termsCheckValue,
            )
            db.session.add(newGuest)
            db.session.commit()

            flash('Settings Updated successfully', 'success')
            return redirect(url_for('guests', guests=Guest.query.all()))
        
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
    app.mail.send(msg)



@app.route('/settings/', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        tos = request.values.get('tos')
        tos_updated = request.values.get('tosDate')

        setting = Setting.query.first()

        #setting = Setting.query.filter_by(settingName=settingName).first()
        if setting is None:
            setting = Setting(
                tos=tos,
                tos_updated=tos_updated
            )
            db.session.add(setting)
        else:
            setting.tos = tos
            setting.tos_updated = tos_updated

        db.session.commit()

        flash('Settings Updated successfully', 'success')
        return redirect(url_for('settings'))
    return render_template('settings.html', setting=Setting.query.first())




def generate_uuid():
    return str(uuid.uuid4())


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

