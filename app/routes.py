import traceback
from flask import render_template, jsonify, abort, url_for, redirect, request, flash, render_template_string
from app import app, db, bcrypt, mail, login_manager
from app.models import Guest, Guestlog, Event, Setting, func, GuestCredit, CreditTransactionLog   
from app.forms import AdminRegistrationForm, AdminLoginForm, GuestRegistrationForm, AddCreditForm, ChangePasswordForm
from flask_mail import  Message
from flask_login import login_user, current_user, logout_user, login_required
from sqlalchemy import cast, Date, func
from io import BytesIO
import qrcode
from datetime import datetime, timedelta, timezone
from dateutil import tz

import uuid
import json


# @login_manager.unauthorized_handler
# def unauthorized_callback():
#     return redirect('/home?next=' + request.path)




@app.route('/', methods=['GET', 'POST'])
def home():
    form = AdminLoginForm()
    if form.validate_on_submit():
       guest = Guest.query.filter_by(email=form.email.data).first()
       if guest and guest.password and bcrypt.check_password_hash(guest.password, form.password.data):
           login_user(guest)          
           next_page = request.args.get('next') 
           return redirect(next_page) if next_page else redirect(url_for('dashboard'))
       else:
           flash('Login unsuccessful. Please check email and password', 'danger')
    return render_template('home.html', form=form)

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

   
    return render_template('guestView.html', setting=Setting.query.first(), form= form)

@app.route('/registerGuest/', methods=['GET', 'POST'])
def registerGuest():
    form = GuestRegistrationForm()


    if form.validate_on_submit():        

        newGuest = Guest(
            uuid = generate_uuid(),
            fetUsername=form.fetUsername.data,
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            termsCheck=form.termsCheck.data
        )
        db.session.add(newGuest)
        db.session.commit()
        sendQRCodeEmail([newGuest.email], newGuest.uuid)
        flash('New Guest Added', 'success')
        return redirect(url_for('guestView'))        
    return render_template('guest_registration.html', setting=Setting.query.first(), form = form)

@app.route('/preCheckIn/')
@app.route('/preCheckIn/<uuid>')
def preCheckIn(uuid = None):
    print("UUID",uuid)
    settings = Setting.query.first()
    guest = Guest.query.filter_by(uuid = uuid).first()
    
    response = {}
    if(guest):
        print("Guest",guest)        
        visitTime = datetime.datetime.now(datetime.timezone.utc)
        response['guest'] = guest.name       
        response['uuid'] = guest.uuid       


        print("Guest Roles",guest.roles)
        if(guest.roles):
            response['roles'] = ", ".join([role.name for role in guest.roles])
            response['skip_payment'] = any(x.skip_payment_at_checkin == True for x in guest.roles)
            response['skip_tos_update'] = any(x.skip_tos_update_at_checkin == True for x in guest.roles)

        if(guest.lastVisit):
            response['lastCheckin'] = guest.lastVisit.timestamp()
            lastVisit = guest.lastVisit
            lastVisit = lastVisit.replace(tzinfo=datetime.timezone.utc)   
            #checkOutBasedOnTime = settings.checkOutBasedOnTime
            checkInCooldownSeconds = settings.checkInCooldownSeconds     
            if (visitTime - lastVisit).total_seconds() < checkInCooldownSeconds:
                response['checked_in'] = False
                print('Already Checked In')
                response['error'] = "Already Checked In"
                return json.dumps(response)


        guestCredit = GuestCredit.query.filter_by(guest_id=guest.id).first()
        if(guestCredit):
            print("GuestCredit",guestCredit)
            response['generalCredits'] = guestCredit.generalAmount
            response['specialEventCredits'] = guestCredit.specialEventAmount
            response['privateSessionCredits'] = guestCredit.privateSessionAmount
                
        return json.dumps(response)
    else:
        response['error'] = "Invalid QR Code"
        return response
        #return abort(404)


@app.route('/checkIn/')
@app.route('/checkIn/<uuid>')
@app.route('/checkIn/<uuid>/<method>')
def checkIn(uuid = None, method = None):
    if(uuid is None or method is None):
        return abort(404)
    settings = Setting.query.first()
    print("Settings,",settings)
    guest = Guest.query.filter_by(uuid = uuid).first()
    if(guest):
        visitTime = datetime.datetime.now(datetime.timezone.utc)
        response = {
                'guest': guest.fetUsername,
                'checked_in': True,
                'checked_in_at_timestamp': visitTime.timestamp(),
                'payment_method': method
            }
        if(guest.lastVisit):
            response['lastCheckin'] = guest.lastVisit.timestamp()
            lastVisit = guest.lastVisit
            lastVisit = lastVisit.replace(tzinfo=datetime.timezone.utc)         

            checkInCooldownSeconds = settings.checkInCooldownSeconds             
            if (visitTime - lastVisit).total_seconds() < checkInCooldownSeconds:
                response['checked_in'] = False
                print('Already Checked In')
                return json.dumps(response)
        
        guest.lastVisit = visitTime
        newCheckIn = Guestlog(
            checked_in_at = visitTime,
            
            checked_in_at_date = visitTime.replace(tzinfo='America/New_York').date(),
            checked_in_at_time = visitTime.replace(tzinfo='America/New_York').time(),
            userID = guest.id,
            paymentMethod = method
        )
        db.session.add(newCheckIn)
        db.session.commit()
        if(method == "credit"):     
            newTransaction = CreditTransactionLog(
                guest=guest.id,
                authorizedSource="Check In via "+method,
                description="Check In via "+method+" - Removed 1 General Credit",
                generalAmountChange=-1,
                specialEventAmountChange=0,
                privateSessionAmountChange=0
            )
            db.session.add(newTransaction)
            db.session.commit()

            guestCredit = GuestCredit.query.filter_by(guest_id=guest.id).first()
            if(guestCredit):
                guestCredit.generalAmount -= 1
                guestCredit.lastUpdate = datetime.datetime.now(datetime.timezone.utc)
                db.session.commit()

        

        
        return json.dumps(response)
    else:
        return abort(404)

@app.route('/generateUUID/')
def generateUUID():
    return jsonify(generate_uuid())

@app.route('/logout/')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/setInitialPassword/', methods=['GET', 'POST'])
def setInitialPassword():
    form = ChangePasswordForm()
    if form.validate_on_submit():
       hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
       guest = Guest.query.filter_by(email=form.email.data).first()
       print("GUEST",guest)
       if guest and not guest.password:    
           guest.password = hashed_password           
           db.session.commit()          
           #next_page = request.args.get('next') 
           return redirect(url_for('dashboard'))
       else:
           flash('Change Password unsuccessful. Please check email', 'danger')
    return render_template('changePassword.html', form=form)

@app.route('/resetPassword/<id>', methods=['GET', 'POST'])
def resetPassword(id):   
    guest = Guest.query.filter_by(id=id).first()
    tempPassword = uuid.uuid4().hex.upper()[0:6] #"temp-password"
    hashed_password = bcrypt.generate_password_hash(tempPassword).decode('utf-8')
    if guest:    
        guest.password = hashed_password           
        db.session.commit()          
        sendPwResetEmail([guest.email], tempPassword)
        flash('Reset Password Successful. Please check email', 'success')
        return redirect(url_for('dashboard'))
    else:
        flash('Change Password unsuccessful, Contact Support.', 'danger')
        return redirect(url_for('dashboard'))
      
@app.route('/changePassword/', methods=['GET', 'POST'])
def changePassword():
    form = ChangePasswordForm()
    if form.validate_on_submit():
       hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
       guest = Guest.query.filter_by(email=form.email.data).first()
       if guest and not guest.password:    
           guest.password = hashed_password           
           db.session.commit()          
           #next_page = request.args.get('next') 
           return redirect(url_for('dashboard'))
       else:
           flash('Change Password unsuccessful. Please check email', 'danger')
    return render_template('changePassword.html', form=form)

@app.route("/events/", methods=['GET', 'POST'])
#@login_required
def events():    
    if request.method == 'POST':        
        print("Start:",request.values.get('eventStart'))
        print("End:",request.values.get('eventEnd'))
        print("Name:",request.values.get('eventName'))
        print("Description:",request.values.get('eventDescription'))
        newEvent = Event(            
            title = request.values.get('eventName'),
            eventDescription = request.values.get('eventDescription'),
            start = request.values.get('eventStart'),
            end = request.values.get('eventEnd'),
            eventLocation = request.values.get('eventLocation'),
            eventCost = request.values.get('eventCost')

        )
        db.session.add(newEvent)
        db.session.commit()
        
        return redirect(url_for('events')) 
    return render_template('events.html', events=Event.query.all())

@app.route("/dashboard/")
#@login_required
def dashboard():

    current_time = datetime.now(tz=tz.tzutc())

    last_24_hours = current_time - timedelta(hours=24)

    return render_template('dashboard.html', guests_checked_in_count=Guest.query.filter(Guest.lastVisit > last_24_hours ).count(),
                           guests_total_count=Guest.query.count(),
                           guests_checked_in=Guest.query.filter(Guest.lastVisit > last_24_hours ).all(),
                           quests_top_5=db.session.query(Guest, func.count(Guestlog.id)).join(Guestlog).group_by(Guest.id).order_by(func.count(Guestlog.id).desc()).limit(5).all(),
                           #guests_top_5=db.session.query(Guest, func.count(Guestlog)).outerjoin(Guestlog, Guest.id == Guestlog.userID).group_by(Guest.id).order_by(func.count(Guestlog.id).desc()).limit(5).all(),                           
                           )

@app.route('/registerAdmin/', methods=['GET', 'POST'])
#@login_required
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

@app.route('/getGuest/')
@app.route('/getGuest/<id>')
def getGuest(id = None):
    data = Guest.query.filter_by(id = id).first()   
    return jsonify(data)

@app.route('/guests/', methods=['GET', 'POST'])
#@login_required
def guests():
    


    if request.method == 'POST':
        termsCheckValue = False


        if request.form.get('termsCheck') is not None:
            termsCheckValue = True
        
        rowID = request.values.get('id')
        print("ROW ID",rowID)
        
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

@app.route('/guestCredit/<id>', methods=['GET', 'POST'])
#@login_required
def guestCredit(id):
    if(id is None):
        return redirect(url_for('guests', guests=Guest.query.all()))
    _guest = Guest.query.filter_by(id=id).first()
    guestCredit = GuestCredit.query.filter_by(guest_id=_guest.id).first()
    print(_guest, guestCredit)
    if(guestCredit is None):
        newCredit = GuestCredit(
                guest=_guest,
                generalAmount=0,
                specialEventAmount=0,
                privateSessionAmount=0,
                lastUpdate = datetime.now(timezone.utc)                
            )
        print("newCredits",newCredit)
        db.session.add(newCredit)
        db.session.commit()
    
    return render_template('guestCredit.html', guest=_guest, guestCredit=GuestCredit.query.filter_by(guest=_guest).first(), guestCreditLog=CreditTransactionLog.query.filter_by(guest=_guest.id).all())

@app.route('/guestCredit/<id>/addCredits', methods=['GET', 'POST'])
#@login_required
def addCredits(id):
    form = AddCreditForm()
    _guest = Guest.query.filter_by(id=id).first()

    if form.validate_on_submit():
        newCreditLogEntry = CreditTransactionLog(
            guest=_guest.id,
            authorizedBy=0,
            authorizedSource=form.authorizedSource.data,
            description=form.description.data,
            generalAmountChange=form.generalAmountChange.data,
            specialEventAmountChange=form.specialEventAmountChange.data,
            privateSessionAmountChange=form.privateSessionAmountChange.data,
        )

        if(newCreditLogEntry.generalAmountChange > 0 or newCreditLogEntry.specialEventAmountChange > 0 or newCreditLogEntry.privateSessionAmountChange > 0):
            guestCredit = GuestCredit.query.filter_by(guest_id=_guest.id).first()
            if(guestCredit):
                guestCredit.generalAmount += newCreditLogEntry.generalAmountChange
                guestCredit.specialEventAmount += newCreditLogEntry.specialEventAmountChange
                guestCredit.privateSessionAmount += newCreditLogEntry.privateSessionAmountChange
                guestCredit.lastUpdate = datetime.now(timezone.utc)
                
            db.session.add(newCreditLogEntry)
            db.session.commit()

        


        #flash('Admin added successfully', 'success')
        return redirect(url_for('guestCredit',form = form, guest=_guest, id=id))
    #return render_template('admin_registration.html', title='Register Admin', form=form)
    return render_template('addCredits.html', form = form, guest=_guest)

@app.route('/logbook/')
#@login_required
def logbook():
    dates = []
    response = [
            # {"date":"2021-01-01", "events": [{Guestlog Item}]},
            # {"date":"2021-01-01", "events": [{Guestlog Item}]}            
        ]
    
    distinct_dates = db.session.query(Guestlog.checked_in_at).order_by(Guestlog.checked_in_at.desc()).all()
    #print("Distinct:",distinct_dates)
    for date in distinct_dates:
        dateItem = date[0]
        
        dateItem = dateItem.replace(tzinfo=tz.tzutc())
        dateItem = dateItem.astimezone(tz.tzlocal())
        if dateItem.date() not in dates:
            dates.append(dateItem.date())


        #print("Date",dateItem.date())
        #dateObj = datetime.strptime(date[0], '%Y-%m-%d')
        #dateObjEnd = dateObj+timedelta(days=1)






        
        #response.append({"date": date[0], "events": Guestlog.query.filter(func.date(Guestlog.checked_in_at).between(dateObj, dateObjEnd)).all()})
    print("Distinct:",dates)
    for date in dates:
        response.append({"date": date, "events": Guestlog.query.filter(func.date(Guestlog.checked_in_at).between(date, date + timedelta(days=1))).all()})

    return render_template('logbook.html', distinct=response ,guests=Guest.query.all(), log=Guestlog.query.all())
    #return render_template('logbook.html')

@app.route('/credits/', methods=['GET', 'POST'])
#@login_required
def credits():
    return render_template('credits.html', guests=Guest.query.all(), guestCreds=GuestCredit.query.all(), guestCreditLog=CreditTransactionLog.query.all())
    #return render_template('logbook.html')

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
#@login_required
def settings():
    if request.method == 'POST':


        pay_cashappBool = False
        pay_venmoBool = False
        pay_paypalBool = False
        pay_creditBool = False


        if request.form.get('pay_cashapp') is not None:
            pay_cashappBool = True
        if request.form.get('pay_venmo') is not None:
            pay_venmoBool = True
        if request.form.get('pay_paypal') is not None:
            pay_paypalBool = True
        if request.form.get('pay_credit') is not None:
            pay_creditBool = True





        tos = request.values.get('tos')
        

        setting = Setting.query.first()

        #setting = Setting.query.filter_by(settingName=settingName).first()
        if setting is None:
            setting = Setting(
                tos=tos,

                show_credit=pay_creditBool,
                show_cashapp=pay_cashappBool,
                show_paypal=pay_paypalBool,
                show_venmo=pay_venmoBool
                
            )
            db.session.add(setting)
        else:
            setting.tos = tos
            setting.show_credit=pay_creditBool
            setting.show_cashapp=pay_cashappBool
            setting.show_paypal=pay_paypalBool
            setting.show_venmo=pay_venmoBool
            

        db.session.commit()

        flash('Settings Updated successfully', 'success')
        return redirect(url_for('settings', setting=Setting.query.first()))
    return render_template('settings.html', setting=Setting.query.first())







def generate_uuid():
    return str(uuid.uuid4())

def sendPwResetEmail(recipients, pw=None):   
    if(pw):
        return sendEmail(recipients=recipients,subject="VC Access - Password Reset", message="Please Use this password to Login: "+ pw)

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
        msg.body = message
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

