import os
import uuid
import json

from flask import Flask, render_template, request, abort
from flask_sqlalchemy import SQLAlchemy

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

#db.init_app(app)
db = SQLAlchemy(app)


@app.route("/")
def hello_world():
    return render_template('index.html')




@app.route('/guests/')
def guests():
    return render_template('guests.html')

@app.route('/forms/')
def forms():
    return render_template('forms.html')





@app.route('/guest/', methods=['GET', 'POST'])
def guest():
    if request.method == 'POST':
        username = request.values.get('user') # Your form's
        password = request.values.get('pass') # input names
        #your_register_routine(username, password)

        print(request.values.get('emailAddress'))

        existingGuest = db.session.execute(db.select(VcGuest).filter_by(email=request.values.get('emailAddress'))).first()
        print(existingGuest)
        if(existingGuest == None):
            newGuest = VcGuest(firstName=request.values.get('firstName'),
            lastName=request.values.get('lastName'),
            email=request.values.get('emailAddress'),
            phone=request.values.get('phoneNumber'),
            termsCheck=bool(request.values.get('termsCheck')),
            idCheck=bool(request.values.get('idCheck'))
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
        return json.dumps(guest.firstName)
    else:
        return abort(404)



def generate_uuid():
    return str(uuid.uuid4())



class VcGuest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String, name="uuid", default=generate_uuid)

    firstName = db.Column(db.String(100))
    lastName = db.Column(db.String(100))
    email = db.Column(db.String(200), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    termsCheck = db.Column(db.Boolean(), default=False)
    idCheck = db.Column(db.Boolean(), default=False)

    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f'<Vc Guest - {self.firstName}>'


with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True)