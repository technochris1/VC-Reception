# project/routes/__init__.py
#from .users import user_bp
#from .posts import posts_bp
# ...
from flask import Blueprint, render_template
profile = Blueprint('profile', __name__)

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

