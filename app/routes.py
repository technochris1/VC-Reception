import traceback
import os, sys
from PIL import Image, ImageOps
from flask import render_template, jsonify, abort, url_for, redirect, request, flash, render_template_string, send_from_directory, make_response, Response
from app import app, db, bcrypt, mail, login_manager, socketio
from app.models import Role, Guest, Guestlog, Event, Setting, func, GuestCredit, CreditTransactionLog, TriggeredEmailEvent, EmailTemplate, EmailLog, MenuFile, MenuItem
from app.forms import AdminRegistrationForm, AdminLoginForm, GuestRegistrationForm, AddPointsForm, AddCreditForm, ChangePasswordForm
from flask_mail import  Message
from flask_login import login_user, current_user, logout_user, login_required
from sqlalchemy import cast, Date,and_, func, or_
from io import BytesIO
import qrcode
from datetime import datetime, timedelta, timezone, time
from dateutil import tz
from werkzeug.utils import secure_filename
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

@app.route('/drinkMenu')
def drinkMenu():

    items = MenuItem.query.filter(MenuItem.type == 'drink').all()
    images = MenuFile.query.all()
    for item in items:
        if item.image_id:
            item.image_path = MenuFile.query.filter(MenuFile.id == item.image_id).first().path


    return render_template('foodMenu.html', items = items)



@app.route('/foodMenu')
def foodMenu():

    items = MenuItem.query.filter(MenuItem.type == 'food').all()
    images = MenuFile.query.all()
    for item in items:
        if item.image_id:
            item.image_path = MenuFile.query.filter(MenuFile.id == item.image_id).first().path


    return render_template('foodMenu.html', items = items)




@app.route("/barView/")
#@login_required
def barView():
    date = datetime.now()

    current_time = datetime.now(tz=tz.tzutc())

    last_24_hours = current_time - timedelta(hours=24)

    return render_template('barView.html', guests_checked_in=Guest.query.filter(Guest.checkedIn ==True).all(),
                           guests_recently_visited=Guest.query.filter(Guest.lastVisit > last_24_hours).all(),
                           guests_total_count=Guest.query.count(),
                           quests_top_5=db.session.query(Guest, func.count(Guestlog.id)).join(Guestlog).group_by(Guest.id).order_by(func.count(Guestlog.id).desc()).limit(5).all(),
                           todaysEvents=Event.query.filter(and_(Event.start <= date.timestamp(), date.timestamp() <= Event.end )).order_by(Event.start).all(),                        
                           
                           #guests_top_5=db.session.query(Guest, func.count(Guestlog)).outerjoin(Guestlog, Guest.id == Guestlog.userID).group_by(Guest.id).order_by(func.count(Guestlog.id).desc()).limit(5).all(),                           
                           )




@app.route("/barView/menuEditor", methods=['GET', 'POST'])
#@login_required
def barMenuEditor():
    images = MenuFile.query.all()
    drinkItems = MenuItem.query.filter(MenuItem.type == 'drink').all()
    foodItems = MenuItem.query.filter(MenuItem.type == 'food').all()

    
    for item in drinkItems:
        if item.image_id:
            item.image_path = MenuFile.query.filter(MenuFile.id == item.image_id).first().path
    for item in foodItems:
        if item.image_id:
            item.image_path = MenuFile.query.filter(MenuFile.id == item.image_id).first().path






    if request.method == 'POST':
        print("form:", request.form)
        newMenuItemFile = MenuItem(
            type = request.form['mode_type'],
            name= request.form['itemName'],
            price= request.form['price'],
            image_id= request.form['options-base']
            )
        print("New Item",newMenuItemFile)
        db.session.add(newMenuItemFile)
        db.session.commit()       

        return redirect(url_for('barMenuEditor', menuFiles= images, food = foodItems, drink = drinkItems))
    elif request.method == 'GET':
        return render_template('barMenuEditor.html', menuFiles= images, food = foodItems, drink = drinkItems)

@app.route("/menuImages", methods=['GET', 'POST'])
#@login_required
def menuImages():
    if request.method == 'POST':

        print("form:", request.form)
        f = request.files['file']
        if f:
            #print("File received:", f.filename)
            file_path = os.path.join(app.root_path, 'static', 'menu_files', secure_filename(f.filename))
            
            print("File received:", f.filename, "File path:", file_path)



            newFile = MenuFile(
                fileName = secure_filename(f.filename),    
                path = os.path.join( '../static', 'menu_files', secure_filename(f.filename))
            )
            print("New Check In",newFile)
            db.session.add(newFile)
            db.session.commit()




            
            f.save(file_path)
            # Resize the image
            img = Image.open(file_path)
            #img = img.resize((800, 800), Image.Resampling.LANCZOS)
            img = ImageOps.fit(img, (800,800), Image.Resampling.LANCZOS)
            img.save(file_path)
            #return jsonify({'success': True, 'filename': filename})
            return redirect(url_for('menuImages', menuFiles=MenuFile.query.all()))
            #return render_template('barMenuImages.html', menuFiles=MenuFile.query.all())
    
        return jsonify({'success': False, 'error': 'Invalid file or request method'})
    elif request.method == 'GET':
        return render_template('barMenuImages.html', menuFiles=MenuFile.query.all())

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
        
        sendQRCodeEmailFromUser(newGuest)
        #sendQRCodeEmail([newGuest.email], newGuest.uuid)
        flash('Guest added successfully', 'success')
        return redirect(url_for('guestView', setting=Setting.query.first(), form=form))
    
    date = datetime.now()
    dateMin = datetime.combine(date, time.min)
    tommorow =  date+timedelta(days=1) 
    tommorowDate =  datetime.combine(tommorow, time.max).timestamp()  
    thirtyDays = (date+timedelta(days=30)).timestamp()

    print("Now!",date.timestamp())
    print("Tommorow",tommorow.timestamp())
    print("TommorowDate",tommorowDate)
    
    
    
    upComingEvents  = []
    query = Event.query.filter(and_(Event.start >= tommorowDate, Event.start <= thirtyDays)).order_by(Event.start).all()
    for event in query:
        if event.start > date.timestamp() and event.display == True and event.specialEvent == True:
            upComingEvents.append(event)
    for event in query:
        if event.start > date.timestamp() and event.display == True and event.specialEvent == False:
            upComingEvents.append(event)
   
    return render_template('guestView.html',
                           todaysEvents=Event.query.filter(and_(Event.start <= date.timestamp(), date.timestamp() <= Event.end)).order_by(Event.start).all(),                        
                            upComingEvents=upComingEvents,
                            setting=Setting.query.first(),
                            form= form)

@app.route('/guestView2/', methods=['GET', 'POST'])
def guestView2():

    
    date = datetime.now()
    dateMin = datetime.combine(date, time.min)
    tommorow =  date+timedelta(days=1) 
    tommorowDate =  datetime.combine(tommorow, time.max).timestamp()  
    thirtyDays = (date+timedelta(days=30)).timestamp()

    print("Now!",date.timestamp())
    print("Tommorow",tommorow.timestamp())
    print("TommorowDate",tommorowDate)
    
    
    
    upComingEvents  = []
    query = Event.query.filter(and_(Event.start >= tommorowDate, Event.start <= thirtyDays)).order_by(Event.start).all()
    for event in query:
        if event.start > date.timestamp() and event.display == True and event.specialEvent == True:
            upComingEvents.append(event)
    for event in query:
        if event.start > date.timestamp() and event.display == True and event.specialEvent == False:
            upComingEvents.append(event)






    form = GuestRegistrationForm(request.form)
    print("request",request.method)
    if  form.validate_on_submit():        
        print("dlData",form.dldata.data)
        newGuest = Guest(
            fetUsername=form.fetUsername.data,
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            termsCheck=True,            
            termsDate=datetime.now(timezone.utc)
        )
        db.session.add(newGuest)
        db.session.commit()
        sendQRCodeEmail([newGuest.email], newGuest.uuid)
        flash('Guest added successfully', 'success')
        return redirect(url_for('guestView2',todaysEvents=Event.query.filter(and_(Event.start <= date.timestamp(), date.timestamp() <= Event.end, Event.display == True)).order_by(Event.start).all(),                        
                            upComingEvents=upComingEvents, setting=Setting.query.first(), form=form))
    
   
    return render_template('guestView2.html',
                           todaysEvents=Event.query.filter(and_(Event.start <= date.timestamp(), date.timestamp() <= Event.end, Event.display == True)).order_by(Event.start).all(),                        
                            upComingEvents=upComingEvents,
                            setting=Setting.query.first(),
                            form= form)


@app.route('/guestView/registerGuest', methods=['GET', 'POST'])
def gw_registerGuest():
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
        return redirect(url_for('gw_registerGuest'))        
    return render_template('guest_registration.html', setting=Setting.query.first(), form = form)

@app.route('/preCheckIn/')
@app.route('/preCheckIn/<uuid>')
def preCheckIn(uuid = None):
    #print("UUID",uuid)
    settings = Setting.query.first()
    guest = Guest.query.filter_by(uuid = uuid).first()
    response = {}
    todaysEvents = {}
    upComingEvents = {}

    date = datetime.combine(datetime.now(), time.min)
    tommorowDate = (date+timedelta(days=1)).timestamp()

    _todaysEvents=Event.query.filter(and_(Event.start >= date.timestamp(), Event.start <= tommorowDate)).order_by(Event.start).all()  
    for event in _todaysEvents:
        #print("Event",event)
        pass



    
    # thirtyDays = (date+timedelta(days=30)).timestamp()
    # #print("Date",date)
    # upComingEvents  = []
    # query = Event.query.filter(and_(Event.start >= tommorowDate, Event.start <= thirtyDays)).order_by(Event.start).all()
    # #print("Query",query)
    # for event in query:
    #     if event.start > date.timestamp() and event.display == True and event.specialEvent == True:
    #         upComingEvents.append(event)
    # for event in query:
    #     if event.start > date.timestamp() and event.display == True:
    #         upComingEvents.append(event)
    #print("Events",upComingEvents)
   
    
    #                 
    #upComingEvents=upComingEvents
    
    
    if(guest):
        print("Guest",guest)
        visitTime = datetime.now(timezone.utc)
        response['guest'] = guest.fetUsername
        response['name'] = guest.name       
        response['uuid'] = guest.uuid       
        response['checkin_blocked'] = guest.checkin_blocked
        response['termsCheck'] = guest.termsCheck

        if(guest.termsCheck):
            pass
            
        if(guest.checkin_blocked):
            response['error'] = "See Staff for Check In"            
            socketio.emit('user precheckin', response)
            return json.dumps(response)        

        if(guest.checkedIn):
            response['error'] = "Already Checked In"
            socketio.emit('user precheckin', response)
            return json.dumps(response)      

        print("Guest Roles",guest.roles)
        if(guest.roles):
            response['roles'] = ", ".join([role.name for role in guest.roles])
            response['skip_payment'] = any(x.skip_payment_at_checkin == True for x in guest.roles)
            response['skip_tos_update'] = any(x.skip_tos_update_at_checkin == True for x in guest.roles)

        # if(guest.lastVisit):
        #     response['lastCheckin'] = guest.lastVisit.timestamp()
        #     lastVisit = guest.lastVisit
        #     lastVisit = lastVisit.replace(tzinfo=timezone.utc)   
        #     #checkOutBasedOnTime = settings.checkOutBasedOnTime
        #     checkInCooldownSeconds = settings.checkInCooldownSeconds     
        #     if (visitTime - lastVisit).total_seconds() < checkInCooldownSeconds:
        #         response['checked_in'] = False
        #         print('Already Checked In')
        #         response['error'] = "Already Checked In"
        #         socketio.emit('user precheckin', response)
        #         return json.dumps(response)

        guestCredit = GuestCredit.query.filter_by(guest_id=guest.id).first()
        if(guestCredit):
            print("GuestCredit",guestCredit)
            response['points'] = guestCredit.points
            response['generalCredits'] = guestCredit.generalAmount
            response['specialEventCredits'] = guestCredit.specialEventAmount
            response['privateSessionCredits'] = guestCredit.privateSessionAmount
                
        #socketio.emit('user precheckin', response)
        return json.dumps(response)
    else:
        response['error'] = "Invalid QR Code"
        return response
        #return abort(404)

@app.route('/checkIn/')
@app.route('/checkIn/<uuid>')
@app.route('/checkIn/<uuid>/<method>')
def checkIn( uuid = None,method = None):
    if(uuid is None or method is None):
        return abort(404)
    #settings = Setting.query.first()
    
      
    if(uuid is not None):
        guest = Guest.query.filter_by(id = uuid).first()
        if(guest is None):
            guest = Guest.query.filter_by(uuid = uuid).first()

    todaysEvent=Event.query.filter(and_(Event.start <= datetime.now().timestamp(), datetime.now().timestamp() <= Event.end)).order_by(Event.start).first(),                        
                           
    if(guest):
        visitTime = datetime.now(timezone.utc)
        response = {
                'guest': guest.fetUsername,
                'name': guest.name,
                'checked_in': True,
                'checked_in_at_timestamp': visitTime.timestamp(),
                'payment_method': method
            }
        if(guest.lastVisit):
            response['lastCheckin'] = guest.lastVisit.timestamp()
            lastVisit = guest.lastVisit
            lastVisit = lastVisit.replace(tzinfo=timezone.utc)         

            # checkInCooldownSeconds = settings.checkInCooldownSeconds             
            # if (visitTime - lastVisit).total_seconds() < checkInCooldownSeconds:
            #     response['checked_in'] = False
            #     print('Already Checked In')
            #     #return json.dumps(response)
            #     return redirect(request.args.get('next') )
        
        if(guest.checkedIn):
            response['error'] = "Already Checked In"   
            socketio.emit('user already checked in', response)         
        else:
            guest.lastVisit = visitTime
            guest.checkedIn = True

            newCheckIn = Guestlog(
                checked_in_at = visitTime,    
                userID = guest.id,
                paymentMethod = method
            )

            if(todaysEvent[0]):
                newCheckIn.event = todaysEvent[0]
            else:       
                newCheckIn.event = None

            print("New Check In",newCheckIn.userID,newCheckIn)
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

            socketio.emit('user checked in', response)
	
        next_page = request.args.get('next') 
        return redirect(next_page) if next_page else json.dumps(response)
    else:
        return abort(404)

@app.route('/checkOut/')
@app.route('/checkOut/<id>')
@app.route('/checkOut/<id>/<method>')
def checkOut(id = None, method = None):
    print("Check Out",id,method)
    if(id is None or method is None):
        return abort(404)
    guest = Guest.query.filter_by(id = id).first()
    print("Guest",guest)                    
                           
    if(guest):
        
        
        
        if(guest.checkedIn):
            guest.checkedIn = False
            guest.barStatus = None
            guest.logbook[-1].checked_out_at = datetime.now(timezone.utc)
            guest.logbook[-1].check_out_method = "Manual"

            #log.checked_out_at = datetime.now(timezone.utc)
            #log.check_out_method = "Automatic By Timer" 
            response = {
                'guest': guest.fetUsername,
                'checked_in': guest.checkedIn,
                'checked_in_at_timestamp': datetime.now(timezone.utc).timestamp(),
                'checked_out_at': guest.logbook[-1].checked_out_at.timestamp(),
                'check_out_method': guest.logbook[-1].check_out_method
            }
            socketio.emit('user checked out', response)

        
        db.session.commit()      

        next_page = request.args.get('next') 
        return redirect(next_page) if next_page else json.dumps(True)
        #return json.dumps(True)
    else:
        return abort(404)

@app.route('/checkInCleanup/')
def checkin_cleanup():

    print("Check In Cleanup @ " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    todays_events = Event.query.filter(and_(Event.end <= datetime.now().timestamp(), datetime.now().timestamp() <= (Event.end  + 600))).order_by(Event.start).all()
    for event in todays_events:
        print("Event",event)
        for log in event.guestlogs:
            #print("Guest Log:",log.userID)
            if log.checked_out_at is None:
                log.checked_out_at = datetime.now(timezone.utc)
                log.check_out_method = "Automatic By Timer"
                guest = Guest.query.filter_by(id = log.userID).first()   
                print("Guest:",guest,"CheckedIn?", guest.checkedIn)             
                if guest.checkedIn:
                    guest.checkedIn = False
                    guest.barStatus = None
                    response = {
                        'guest': guest.fetUsername,
                        'checked_in': guest.checkedIn,
                        'checked_in_at_timestamp': datetime.now(timezone.utc).timestamp(),
                        'checked_out_at': guest.logbook[-1].checked_out_at,
                        'check_out_method': guest.logbook[-1].check_out_method
                    }
                    socketio.emit('user checked out', response)
                db.session.commit()
            
    if(Setting.query.first().membership_role):
        guests = Guest.query.filter( and_(Guest.roles.contains(Setting.query.first().membership_role), Guest.membershipEmailSent == False, Guest.membershipStart, Guest.membershipStart <= (datetime.now() - timedelta(minutes=2)))).all() #
        for guest in guests:
            print("Membership Guest",guest, guest.membershipStart.timestamp(), (datetime.now() - timedelta(minutes=1)).timestamp())
            #guest.membershipEmailSent = True
            
            #db.session.commit() 
             
            roleInitializedEvents = TriggeredEmailEvent.query.filter(TriggeredEmailEvent.roleInitializeTriggered == True).all()
            for event in roleInitializedEvents:
                print("Role Event - User Checked Out", event)
                for emailTemplate in event.emailTemplates:
                    print("Email Template", emailTemplate)
                    #sendEmail(recipients, subject, message, attachment=None):
                    emailSent = sendEmail([guest.email], emailTemplate.templateSubject, emailTemplate.templateBody)
                    guest.membershipEmailSent = emailSent
                    newEmailLog = EmailLog(
                        
                        emailTemplate=emailTemplate.id,
                        emailRecipient = guest.email,
                        emailSubject=emailTemplate.templateSubject,
                        emailBody=emailTemplate.templateBody
                    )
                    db.session.add(newEmailLog)
                    db.session.commit()
                #if emailEvent.

    else:
        print("Membership Role Not Set!")

    

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

@app.route("/events/", methods=['GET', 'POST', 'DELETE'])
@app.route('/events/<id>', methods=['DELETE'])
#@login_required
def events(id = None):
    if request.method == 'DELETE':
        print("Request",request.values)       
        print("ID:",id)
        if(id):
            event = Event.query.filter_by(id=id).first()
            if event is None:
                return abort(404)
            
            db.session.delete(event)
            db.session.commit()
            return redirect(url_for('events'))
    if request.method == 'POST': 
        print("Request",request.values)       
        print("ID:",request.values.get('eventId'))
        print("Start:",request.values.get('eventStart'))
        print("End:",request.values.get('eventEnd'))
        print("Name:",request.values.get('eventName'))
        print("Description:",request.values.get('eventDescription'))
        print("PrePay:",  False if request.values.get('prepay') == None else True)
        print("Display:",  False if request.values.get('display')== None else True)
        print("Special Event:",  False if request.values.get('specialevent')== None else True)
        print("Banner Image:",request.values.get('bannerImage'))

        if(request.values.get('eventId')):
            event = Event.query.filter_by(id=request.values.get('eventId')).first()
            if event is None:
                return abort(404)
            event.specialEvent= False if request.values.get('specialevent') == None else True
            event.prepay= False if request.values.get('prepay') == None else True
            event.display= False if request.values.get('display') == None else True
            event.title=request.values.get('eventName')
            event.eventDescription=request.values.get('eventDescription')
            DateStart = datetime.strptime(request.values.get('eventStart'), '%Y-%m-%d %H:%M')
            DateEnd = datetime.strptime(request.values.get('eventEnd'), '%Y-%m-%d %H:%M')
            event.start=DateStart.timestamp()
            event.end=DateEnd.timestamp()
            event.eventLocation=request.values.get('eventLocation')
            event.eventCost=request.values.get('eventCost')
            event.image=request.values.get('bannerImage')

            db.session.commit()
            return redirect(url_for('events'))
        else:
            DateStart = datetime.strptime(request.values.get('eventStart'), '%Y-%m-%d %H:%M')
            DateEnd = datetime.strptime(request.values.get('eventEnd'), '%Y-%m-%d %H:%M')
            newEvent = Event(            
                specialEvent= False if request.values.get('specialevent') == None else True,
                prepay= False if request.values.get('prepay') == None else True,
                display= False if request.values.get('display') == None else True,
                title = request.values.get('eventName'),
                eventDescription = request.values.get('eventDescription'),                
                start=DateStart.timestamp(),
                end=DateEnd.timestamp(),
                # start = request.values.get('eventStart'),
                # end = request.values.get('eventEnd'),
                eventLocation = request.values.get('eventLocation'),
                eventCost = request.values.get('eventCost'),
                image = request.values.get('bannerImage')
            )
            db.session.add(newEvent)
            db.session.commit()
            
            return redirect(url_for('events')) 
    return render_template('events.html', events=Event.query.all())

@app.route("/dashboard/")
#@login_required
def dashboard():
    date = datetime.now()
    tommorowDate = (date+timedelta(days=1)).timestamp()
    thirtyDays = (date+timedelta(days=30)).timestamp()

    current_time = datetime.now(tz=tz.tzutc())

    last_24_hours = current_time - timedelta(hours=24)

    return render_template('dashboard.html', guests_checked_in=Guest.query.filter(Guest.checkedIn ==True).all(),
                           guests_recently_visited=Guest.query.filter(Guest.lastVisit > last_24_hours).all(),
                           guests_total_count=Guest.query.count(),
                           quests_top_5=db.session.query(Guest, func.count(Guestlog.id)).join(Guestlog).group_by(Guest.id).order_by(func.count(Guestlog.id).desc()).limit(5).all(),
                           todaysEvents=Event.query.filter(and_(Event.start <= date.timestamp(), date.timestamp() <= Event.end )).order_by(Event.start).all(),                        
                           
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

@app.route('/setGuestBarState/', methods=['POST'])
@app.route('/setGuestBarState/<id>/<state>', methods=['POST'])
def setGuestBarState(id=None, state=None):
    if(id is not None or state is not None):
        guest = Guest.query.filter_by(id=id).first()
        if guest:
            guest.barStatus = state
            db.session.commit()

            barStatus = {
                'guestId': guest.id,
                'barStatus': guest.barStatus
            }
            socketio.emit('user barstatus changed', barStatus)
            return json.dumps(True)
        else:
            return abort(404)

@app.route('/getGuest/')
@app.route('/getGuest/<id>')
def getGuest(id = None):
    data = Guest.query.filter_by(id = id).first()   
    #data['roleIDS'] = str({index: value for index, value in enumerate(data.roles)})
    #print(",".join(str(element.id) for element in data.roles))
    print({index: value for index, value in enumerate(data.roles)})
    #jsonData = jsonify(data = data, roles = {index: value for index, value in enumerate(data.roles)})
    jsonData = jsonify(data = data, userRoles = data.roles, membershipRole = Setting.query.first().membership_role)
    print("data.role", jsonData)
    return jsonData
    #return Response(json.dumps(data),  mimetype='application/json')

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
            
            print("GuestData",request.values.get('btnradio'))
            if(request.values.get('btnradio') == "member"):
                if(Setting.query.first().membership_role not in guest.roles):                    
                    guest.roles.append(Setting.query.first().membership_role)
                    guest.membershipStart = datetime.now()
                    guest.membershipEnd = None
                    guest.membershipEmailSent = False
                    guest.membershipEmailSentDate = None


            if(request.values.get('btnradio') == "nonmember"):
                if(Setting.query.first().membership_role in guest.roles):
                    guest.roles.remove(Setting.query.first().membership_role)
                    guest.membershipStart = None
                    guest.membershipEnd = datetime.now()
                    guest.membershipEmailSent = False
                    guest.membershipEmailSentDate = None
            





            guest.fetUsername=request.values.get('fetUsername')
            guest.name=request.values.get('name')
            
            guest.phone=request.values.get('phoneNumber')
            guest.termsCheck=termsCheckValue

            if(guest.uuid != request.values.get('uuid') or guest.email != request.values.get('emailAddress')):
                guest.uuid=request.values.get('uuid')
                guest.email=request.values.get('emailAddress')                          
                #send email for new QR code
                #sendQRCodeEmail([guest.email], guest.uuid)
                sendQRCodeEmailFromUser(guest)


            

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
        
    return render_template('guests.html', guests=Guest.query.all(), settings = Setting.query.first(), roles = Role.query.all(), guestVisitLog=Guestlog.query.all(), guestVisitCounts=Guestlog.query.with_entities(Guestlog.userID, func.count(Guestlog.id)).group_by(Guestlog.userID).all())

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
    
    return render_template('guestCredit.html',settings=Setting.query.first(), guest=_guest, guestCredit=GuestCredit.query.filter_by(guest=_guest).first(), guestCreditLog=CreditTransactionLog.query.filter_by(guest=_guest.id).all())


@app.route('/guestCredit/<id>/addPoints', methods=['GET', 'POST'])
#@login_required
def addPoints(id):
    form = AddPointsForm()
    _guest = Guest.query.filter_by(id=id).first()

    if form.validate_on_submit():
        newCreditLogEntry = CreditTransactionLog(
            guest=_guest.id,
            authorizedBy=0,
            authorizedSource=form.authorizedSource.data,
            description=form.description.data,
            pointChange=form.pointChange.data,
        )

        if(newCreditLogEntry.pointChange > 0 ):
            guestCredit = GuestCredit.query.filter_by(guest_id=_guest.id).first()
            if(guestCredit):
                guestCredit.points += newCreditLogEntry.pointChange
                guestCredit.lastUpdate = datetime.now(timezone.utc)
                
            db.session.add(newCreditLogEntry)
            db.session.commit()

        


            flash('Points added successfully', 'success')
        else:
            flash('Points must be greater than 0', 'danger')
        return redirect(url_for('guestCredit',form = form, guest=_guest, id=id))
    #return render_template('admin_registration.html', title='Register Admin', form=form)
    return render_template('addPoints.html', form = form, guest=_guest)


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

@app.route('/guestCredit/<id>/upgradePoints', methods=['GET', 'POST'])
#@login_required
def upgradePoints(id):
    _guest = Guest.query.filter_by(id=id).first()
    guestCredit = GuestCredit.query.filter_by(guest_id=_guest.id).first()

    if(guestCredit):
        newCreditLogEntry = CreditTransactionLog(
            guest=_guest.id,
            authorizedBy=0,
            description="Upgrade Points To Credit",
            authorizedSource="Upgrade Points To Credit",
            pointChange=  -Setting.query.first().points_per_credit,
            generalAmountChange=1,
        )

        if(guestCredit.points >= Setting.query.first().points_per_credit):      
        
            guestCredit.points -= Setting.query.first().points_per_credit
            guestCredit.generalAmount += 1
            guestCredit.lastUpdate = datetime.now(timezone.utc)

                
            db.session.add(newCreditLogEntry)
            db.session.commit()


    


            flash('Points Upgraded to Credit successfully', 'success')
        else:
            flash('Points must be at least '+str(Setting.query.first().points_per_credit)+' or greater.', 'danger')
    return redirect(url_for('guestCredit', guest=_guest, id=id))







@app.route('/logbook/')
#@login_required
def logbook():
    dates = []
    localDates = []
    response = [
            # {"date":"2021-01-01", "events": [{Guestlog Item}]},
            # {"date":"2021-01-01", "events": [{Guestlog Item}]}            
        ]
    
    #all_dates = db.session.query(Guestlog.checked_in_at_local).order_by(Guestlog.checked_in_at_local.desc()).all()
    all_dates = db.session.query(Guestlog.checked_in_at).order_by(Guestlog.checked_in_at.desc()).all()
    print("All Dates:", all_dates)
    events = []
    for date in all_dates:
        
        dateItem = date[0]
         #.replace(tzinfo=tz.tzutc()).astimezone(tz.tzlocal())
        #print("DateItem",date)
       


        if dateItem is not None and dateItem.date() not in dates:
            dates.append(dateItem.date())
            localDates.append(dateItem.replace(tzinfo=timezone.utc).astimezone(tz=None).date())


        #
        #dateObj = datetime.strptime(date[0], '%Y-%m-%d')
        #dateObjEnd = dateObj+timedelta(days=1)






        
        #response.append({"date": date[0], "events": Guestlog.query.filter(func.date(Guestlog.checked_in_at).between(dateObj, dateObjEnd)).all()})
    print("Distinct Dates:",dates)
    i = 0
    for date in dates:

        
        
        #events = Guestlog.query.filter(func.date(Guestlog.checked_in_at_local) == date).all()
        events = Guestlog.query.filter(func.date(Guestlog.checked_in_at) == date).all()
       # date.replace(tzinfo=timezone.utc).astimezone(tz=None)
        print("Date:",localDates[i], events)
        response.append({"date": localDates[i], "events": events })
        i += 1

    return render_template('logbook.html', distinct=response ,guests=Guest.query.all(), log=Guestlog.query.all(), events=Event.query.all())
    #return render_template('logbook.html')

@app.route('/credits/', methods=['GET', 'POST'])
#@login_required
def credits():
    return render_template('credits.html', guests=Guest.query.all(), guestCreds=GuestCredit.query.all(), guestCreditLog=CreditTransactionLog.query.all())
    #return render_template('logbook.html')

@app.route('/saveEmailTemplate/', methods=['POST'])
def saveEmailTemplate():
    if request.method == 'POST':
        jsonData = request.get_json()
        print(jsonData['emailTemplateName'])
        print(jsonData['emailSubject'])
        print(jsonData['emailMessage'])
              
        
        newEmailTemplate = EmailTemplate(
            templateName=jsonData['emailTemplateName'],
            templateSubject=jsonData['emailSubject'],
            templateBody=jsonData['emailMessage'],
        )
        db.session.add(newEmailTemplate)
        db.session.commit()
        
    return jsonify(success=True)

@app.route('/notificationEmailer/', methods=['GET', 'POST'])
#@login_required
def emailer(): 


    if request.method == 'POST':
        #print("Request",request.values)       
        #print("Emails:",request.values.getlist('emails'))
        #print("Subject:",request.values.get('subject'))
        #print("Message:",request.values.get('message'))
        #print("Recipients:",request.values.get('recipients').split(','))
        try:
            msg = Message(request.values.get('subject'),
                        sender=("VC Front Desk", "VC-Desk@whoknows.com"),
                        cc=request.values.getlist('emails'))
            #msg.body = request.values.get('message')        
            msg.html = request.values.get('message')
            mail.send(msg)
            #return render_template('email.html', guests=Guest.query.all(), roles = Role.query.all())
            flash('Email Send to: '+str(request.values.getlist('emails')), 'success')
            return redirect(url_for('emailer'))
        except:
            print("send_mail exception:\n{}".format(traceback.format_exc()))
        #return
 

        
    return render_template('email.html', guests=Guest.query.all(), roles = Role.query.all())




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

        req_dl = False
        opt_bartip = False
        pay_cashappBool = False
        pay_venmoBool = False
        pay_paypalBool = False
        pay_creditBool = False

        if request.form.get('req_dl') is not None:
            req_dl = True    

        if request.form.get('opt_bartip') is not None:
            opt_bartip = True
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
                
                req_dl=req_dl,
                show_bartip=opt_bartip,
                show_credit=pay_creditBool,
                show_cashapp=pay_cashappBool,
                show_paypal=pay_paypalBool,
                show_venmo=pay_venmoBool,
                points_per_credit=request.form.get('pointpercredit')
                
            )
            db.session.add(setting)
        else:
            setting.tos = tos
            setting.req_dl = req_dl
            setting.show_bartip = opt_bartip
            setting.show_credit=pay_creditBool
            setting.show_cashapp=pay_cashappBool
            setting.show_paypal=pay_paypalBool
            setting.show_venmo=pay_venmoBool
            setting.points_per_credit=request.form.get('pointpercredit')
            

        db.session.commit()

        flash('Settings Updated successfully', 'success')
        return redirect(url_for('settings', setting=Setting.query.first()))
    return render_template('settings.html', setting=Setting.query.first())







def generate_uuid():
    return str(uuid.uuid4())

def sendPwResetEmail(recipients, pw=None):   
    if(pw):
        return sendEmail(recipients=recipients,subject="VC Access - Password Reset", message="Please Use this password to Login: "+ pw)


def sendQRCodeEmailFromUser(user):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(user.uuid)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    
    print("IMG",img)

    temp = BytesIO()
    temp.name = "QR.png"
    img.save(temp)
    temp.seek(0)

    print("User",user)

    #qr_image = {'photo': temp.getvalue()}
    #print("IMG",qr_image['photo'])
    
    # return sendEmail(
    #     user.recipients, 
    #     "VC Access Code", 
    #     "Please find your VC QR code attached", 
    #     temp.getvalue())

    try:
        msg = Message("VC Access - Password Reset",
                    sender=("VC Front Desk", app.config['MAIL_USERNAME']),
                    recipients=[user.email])
        #msg.body = message
        msg.body = 'Hello '+user.name+',\nYou or someone else has requested that a new password be generated for your account. If you made this request, then please follow this link:'
        msg.html = render_template('qrEmail.html' )
        #msg.attach('header.gif','image/gif',open(join(mail_blueprint.static_folder, 'header.gif'), 'rb').read(), 'inline', headers=[['Content-ID','<Myimage>'],])
        script_directory = os.path.dirname(os.path.abspath(sys.argv[0])) 
        #print(script_directory)
        #print("LOGO",open(os.path.join(script_directory, 'app\\static\\VC_logo_dark.png')).read())

        attachmentHeadersA = { "Content-ID": "<vclogo>" }
        msg.attach('vclogo.png','image/png',open(os.path.join(script_directory, 'app\\static\\VC_logo_dark.png'), 'rb').read(), 'inline', headers=attachmentHeadersA)
        attachmentHeadersB = { "Content-ID": "<qrcode>" }
        msg.attach('qrcode.png','image/png',temp.getvalue(), 'inline', headers=attachmentHeadersB)
        msg.attach('qrcode.png','image/png',temp.getvalue())


        mail.send(msg)
    except:
        print("send_mail exception:\n{}".format(traceback.format_exc()))
    return



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
    
    return sendEmail(recipients, "VC Access Code", "Please find your VC QR code attached", temp.getvalue())

def sendEmail(recipients, subject, message, attachment=None):
    

    #print("Attachment",attachment)

    try:
        msg = Message(subject,
                    sender=("VC Front Desk", "VC-Desk@whoknows.com"),
                    recipients=recipients)
        msg.body = message
        if attachment:
            try:            
                msg.attach("registration-qr-code.png", "image/png", attachment)
                msg.body = message
            except Exception as e:
                print("send_mail.attachment exception: {}".format(e))
        mail.send(msg)
        return True
    except:
        print("send_mail exception:\n{}".format(traceback.format_exc()))
        return False
    
 
