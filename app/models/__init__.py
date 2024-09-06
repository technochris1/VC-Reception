
from dataclasses import dataclass
import datetime
from tools import generate_uuid
from sqlalchemy.sql import func
#from app import db

from . import db

def init_app(app):
    db.init_app(app)



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

