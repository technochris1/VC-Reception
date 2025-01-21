from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, IntegerField
from wtforms.validators import DataRequired, Email, Length, ValidationError, EqualTo
from app.models import Guest

# class GuestRegistrationForm(FlaskForm):
#     fetUsername = StringField('First Name', validators=[DataRequired()])
#     name = StringField('Last Name', validators=[DataRequired()])
#     email = StringField('Email', validators=[DataRequired(), Email()])
#     phone = StringField('Phone Number', validators=[DataRequired()])

#     termsCheck = BooleanField('I agree to the terms and conditions', validators=[DataRequired()])    
#     submit = SubmitField('Sign Up')

class AdminLoginForm(FlaskForm):
    
    email = StringField('Email', validators=[DataRequired(), Email()])    
    password = StringField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')



class ChangePasswordForm(FlaskForm):
    
    email = StringField('Email', validators=[DataRequired(), Email()])    
    password = StringField('Password', validators=[DataRequired()])
    submit = SubmitField('Change Password')

    
    
    
   

class GuestRegistrationForm(FlaskForm):

    dldata= StringField('DL Data')

    fetUsername = StringField('Fet/Fetlife Username')
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number')

    termsCheck = BooleanField('I agree to the terms and conditions', validators=[DataRequired()])    
    submit = SubmitField('Sign Up')

    def validate_email(self, email):
        user = Guest.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already in use. Please choose another email address.')



class AdminRegistrationForm(FlaskForm):
    fetUsername = StringField('Fetlife Username')
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number')

    password = StringField('Password', validators=[DataRequired()])
    confirmPassword = StringField('Confirm Password', validators=[DataRequired(), EqualTo('password')])

    termsCheck = BooleanField('I agree to the terms and conditions')    
    submit = SubmitField('Sign Up')

    def validate_email(self, email):
        user = Guest.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already in use. Please choose another email address.')

class AddCreditForm(FlaskForm):
    authorizedSource:str  = StringField('Authorized Source', validators=[DataRequired()]) 
    description = StringField('Description', validators=[DataRequired()])
    generalAmountChange = IntegerField('General Admission Credits', default=0)
    specialEventAmountChange = IntegerField('Special Event Credits', default=0)
    privateSessionAmountChange = IntegerField('Private Session Credits', default=0)
    submit = SubmitField('Add Credit')

class SettingsForm(FlaskForm):
    tos:str  = StringField('Terms of Service', validators=[DataRequired()])
    pay_cashapp:bool = BooleanField('Pay with Cashapp')
    pay_venmo:bool = BooleanField('Pay with Venmo')
    pay_paypal:bool = BooleanField('Pay with Paypal')
    pay_credit:bool = BooleanField('Pay with Credit System')