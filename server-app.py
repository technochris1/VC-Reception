import os
import uuid

from flask import Flask, render_template
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


@app.route('/guest/')
@app.route('/guest/<guid>')
def hello(guid=None):
    return render_template('guest-view.html', guid=guid)



def generate_uuid():
    return str(uuid.uuid4())

class VcGuest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String, name="uuid", default=generate_uuid)

    firstname = db.Column(db.String(100))
    lastname = db.Column(db.String(100))
    email = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    age = db.Column(db.Integer)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    bio = db.Column(db.Text)

    def __repr__(self):
        return f'<Vc Guest - {self.firstname}>'


with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True)