from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, PasswordField, SubmitField, RadioField, BooleanField
from wtforms.validators import InputRequired, NumberRange

# User forms for the User
class RegistrationForm(FlaskForm):
    user_id = StringField("User ID:",
                          validators=[InputRequired()])
    password = PasswordField("Password:",
                             validators=[InputRequired()])
    confirm_password = PasswordField("Confirm Password:",
                             validators=[InputRequired()])
    submit = SubmitField("Register")


class LoginForm(FlaskForm):
    user_id = StringField("User ID:",
                          validators=[InputRequired()])
    password = PasswordField("Password:",
                             validators=[InputRequired()])
    submit = SubmitField("Login")

class DepositForm(FlaskForm):
    deposit = FloatField("",
                         validators=[InputRequired()])
    cancel = SubmitField("Cancel")
    submit = SubmitField("Deposit Funds")
    
class WithdrawForm(FlaskForm):
    withdraw = FloatField("",
                          validators=[InputRequired()])
    cancel = SubmitField("Cancel")
    submit = SubmitField("Withdraw funds")
    
class TransferForm(FlaskForm):
    receiver_user = StringField("",validators=[InputRequired()])
    receiver_iban = StringField("", validators=[InputRequired()])
    transfer = FloatField("",
                          validators=[InputRequired(), NumberRange(min=0.01)])
    confirm_transfer = FloatField("",
                                  validators=[InputRequired(), NumberRange(min=0.01)])
    message = StringField("")
    cancel = SubmitField("Cancel")
    submit = SubmitField("Transfer funds")


class AccountStatusForm(FlaskForm):
    status = RadioField("Account status:", 
    choices = ["Freeze", "Activate"],
    default = "Activate",
    validators = [InputRequired()])
    submit = SubmitField("Confirm")

class DeleteAccountForm(FlaskForm):
    confirm = BooleanField("I understand that this will result in permanent deletion of your account",
                           validators=[InputRequired()])
    submit = SubmitField("Delete Account")


# All admin related forms for ADMIN ONLY
class AdminDeleteAccountForm(FlaskForm):
    submit = SubmitField("Delete Account")

class AdminDepositForm(FlaskForm):
    amount = FloatField("Amount", validators=[InputRequired()])
    submit = SubmitField("Deposit")

class AdminWithdrawForm(FlaskForm):
    amount = FloatField("Amount", validators=[InputRequired()])
    submit = SubmitField("Withdraw")

class FreezeAccountForm(FlaskForm):
    submit = SubmitField("Freeze Account")

class NotifyUserForm(FlaskForm):
    message = StringField("Message", validators=[InputRequired()])
    submit = SubmitField("Send Message")
    
