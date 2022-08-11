from flask_wtf import FlaskForm
from wtforms import StringField,SubmitField, PasswordField, BooleanField, DateField, SelectField
from wtforms.validators import InputRequired, EqualTo, Length

class RegistrationForm(FlaskForm):
    username = StringField("Please input an username:", validators=[InputRequired()])
    password = PasswordField("Please input a password:", validators=[InputRequired()])
    password2 = PasswordField("Repeat above password:", validators=[InputRequired(), EqualTo("password")])
    realname = StringField("Please enter your full name (Optional):")
    email = StringField("Please enter your email (Optional):")
    address = StringField("Please enter a home address (Optional)")
    Submit = SubmitField("Submit")

class LoginForm(FlaskForm):
    username = StringField("Username:", validators=[InputRequired()])
    password = PasswordField("Password:", validators=[InputRequired()])
    Submit = SubmitField("Submit")

class StockForm(FlaskForm):
    newstock = BooleanField("Please tick to insert new item",default = False)
    itemremoval = BooleanField("Please tick to remove item",default = False)
    stockID = StringField("ID number of stock:")
    stockname = StringField("Name of the item:")
    stocklevel = StringField("Stock level:")
    imagename = StringField("Image name (Format:<imagename.fileformat>):")
    price = StringField("Price of item:")
    description = StringField("Description of item:")
    Submit = SubmitField("Submit")

class UserForm(FlaskForm):
    username = StringField("Please enter the user to find (Username cannot be changed)")
    password = PasswordField("Please add new password")
    modification = BooleanField("Please tick to update users information or insert new user with password")
    removal = BooleanField("Please tick if removing account from database")
    changetype = SelectField("Please enter new account type:", choices=("","admin","standard","None"))
    changename = StringField("Please enter new full name")
    changeaddress = StringField("Please enter new home address")
    changemail = StringField("Please enter new email address")
    Submit = SubmitField("Submit")

class EmailForm(FlaskForm):
    emailbox = StringField("Please enter the message you would like to send:",)
    Submit = SubmitField("Submit")

class CheckoutForm(FlaskForm):
    promotion = StringField("Please enter the promotion code if available (Hint: It is 'Sale'):")
    Submit = SubmitField("Submit")

class PurchaseForm(FlaskForm):
    cardnumber = StringField("Please enter your 16 digit card number:",validators=[InputRequired(),Length(min=16,max=16)])
    datenumber = DateField("Please select your expiry date:",validators=[InputRequired()])
    securitynum = PasswordField("Please enter your 3 digit security code:",validators=[InputRequired(),Length(min=3,max=3)])
    shipaddress = StringField("Please enter your shipping address:",validators=[InputRequired()],default=[])
    cardaddress = StringField("Please enter your billing address:",validators=[InputRequired()])
    addtodata = BooleanField("Would you like your shipping address saved for next time?")
    Submit = SubmitField("Submit")