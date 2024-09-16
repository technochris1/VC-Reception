
from dataclasses import dataclass
import datetime

from sqlalchemy.sql import func
from app import app, db, login_manager
from flask_login import UserMixin



guest_role = db.Table('guest_roles',
                    db.Column('guest_id', db.Integer, db.ForeignKey('guest.id')),
                    db.Column('role_id', db.Integer, db.ForeignKey('role.id'))
                    )


@dataclass
class Role(db.Model):
    id:int = db.Column(db.Integer, primary_key=True)
    name:str  = db.Column(db.String(100))
    description:str  = db.Column(db.String(200))
    permissions:str  = db.Column(db.String(200))
    skip_payment_at_checkin:bool = db.Column(db.Boolean(), default=False)
    skip_tos_update_at_checkin:bool = db.Column(db.Boolean(), default=False)
    allow_login_to_backoffice:bool = db.Column(db.Boolean(), default=False)
    allow_password_reset:bool = db.Column(db.Boolean(), default=False)
    notify_staff_on_checkin:bool = db.Column(db.Boolean(), default=False)
    auto_checkout_on_event_end:bool = db.Column(db.Boolean(), default=False)

    def __str__(self):
        return f'{self.name}'

    def __repr__(self):
        return f'{self.name}'

@login_manager.user_loader
def load_user(user_id):
    return Guest.query.get(int(user_id))



@dataclass
class Guest(db.Model, UserMixin):
    id:int = db.Column(db.Integer, primary_key=True)
    uuid:str  = db.Column(db.String, unique=True, name="uuid")

    fetUsername:str  = db.Column(db.String(100) )
    name:str  = db.Column(db.String(100), nullable=False)
    email:str  = db.Column(db.String(200), unique=True, nullable=False)
    phone:str  = db.Column(db.String(20))

    password:str  = db.Column(db.String(255))
    roles = db.relationship('Role', backref=db.backref('guests'), secondary=guest_role)

    termsCheck:bool = db.Column(db.Boolean(), default=False)
    termsDate = db.Column(db.DateTime(timezone=True), server_default=None)
    
    credit = db.relationship('GuestCredit',backref='guest')

    logbook = db.relationship('Guestlog', backref='guest')
    

    lastVisit = db.Column(db.DateTime(timezone=True), server_default=None)
    lastCheckOut = db.Column(db.DateTime(timezone=True), server_default=None)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())


    def __str__(self):
        return f'{self.name}'

    def __repr__(self):
        return f'Guest(\'{self.name}\')'

@dataclass
class Guestlog(db.Model):
    id:int = db.Column(db.Integer, primary_key=True)
    checked_in_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    userID = db.Column(db.Integer, db.ForeignKey('guest.id'))
    paymentMethod:str  = db.Column(db.String(100))


@dataclass
class GuestCredit(db.Model):
    id:int = db.Column(db.Integer, primary_key=True)
    lastUpdate = db.Column(db.DateTime(timezone=True), server_default=None)

    guest_id = db.Column(db.Integer, db.ForeignKey('guest.id'), nullable=False)    
    #guest = db.relationship('Guest' ,back_populates='credit')

    generalAmount:int  = db.Column(db.Integer, nullable=False, default=0)
    specialEventAmount:int  = db.Column(db.Integer, nullable=False, default=0)
    privateSessionAmount:int  = db.Column(db.Integer, nullable=False, default=0)

    def __str__(self):
        return f'{self.id}:{self.guest_id}:{self.generalAmount}'

    def __repr__(self):
        return f'{self.id}'


@dataclass
class CreditTransactionLog(db.Model):
    id:int = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime(timezone=True), server_default=func.now())
    guest = db.Column(db.Integer,  db.ForeignKey('guest.id'), nullable=False)
    authorizedSource:str  = db.Column(db.String(100), nullable=False)    
    authorizedBy  = db.Column(db.Integer, db.ForeignKey('guest.id'))
    generalAmountChange:int  = db.Column(db.Integer, nullable=False)
    specialEventAmountChange:int  = db.Column(db.Integer, nullable=False)
    privateSessionAmountChange:int  = db.Column(db.Integer, nullable=False)
    description:str  = db.Column(db.String(200), nullable=False)
    

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
    tos:str  = db.Column(db.String())
    tos_updated:str = db.Column(db.String(100))

    

    checkInCooldownSeconds:int = db.Column(db.Integer, default=60)
    checkOutBasedOnTime:bool = db.Column(db.Boolean(), default=True)
    checkOutTime:datetime = db.Column(db.DateTime(timezone=True), server_default=None)
    checkOutBasedOnEventEndTime:bool = db.Column(db.Boolean(), default=False)


    show_cashapp:bool = db.Column(db.Boolean(), default=True)
    show_paypal:bool = db.Column(db.Boolean(), default=True)
    show_venmo:bool = db.Column(db.Boolean(), default=True)
    show_cash:bool = db.Column(db.Boolean(), default=True)
    show_credit:bool = db.Column(db.Boolean(), default=False)

@dataclass
class Tag(db.Model):
    id:int = db.Column(db.Integer, primary_key=True)
    tagName:str  = db.Column(db.String(100))
    tagDescription:str  = db.Column(db.String(200))
