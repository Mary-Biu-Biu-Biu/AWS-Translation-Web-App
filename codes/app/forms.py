# We may need to import more validators, documentation on this is included on README file!
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from app.models import *


class DetectForm(FlaskForm):
    picture = FileField('Add An Image', validators=[DataRequired(),FileAllowed(['jpg', 'png', 'jpeg'])])
    # content = TextAreaField('Content')
    language = SelectField(u'Language', choices=[('null','Choose target language'),
        ('zh', 'Chinese'), 
        ('nl', 'Dutch'), 
        ('fr', 'French'),
        ('de', 'German'),
        ('el', 'Greek'),
        ('ja', 'Japanese'),
        ('ko', 'Korean')
        ])
    submit = SubmitField('Upload')


class TranscribeForm(FlaskForm):
    audio = FileField('Add An Audio', validators=[DataRequired(),FileAllowed(['mp3', 'mp4', 'wav'])])
    title = StringField("Title (should be unique)", validators=[DataRequired()])
    submit = SubmitField('Create')

class SignUpForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=4, max=20)])
    confirmed_password = PasswordField("Confirm Password", validators=[DataRequired(), Length(min=4, max=20), EqualTo("password")])
    submit = SubmitField("Sign Up")

    def validate_email(self, email):
        # if email is already used for signup, throw an error etc
        customer = Customer.query.filter_by(email=email.data).first()
        if customer:
            raise ValidationError("The email is already in use. Please use another email.")

# Login form
class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=4, max=20)])
    remember = BooleanField("Keep me logged in?")
    submit = SubmitField('Login')

# job form
class JobForm(FlaskForm):

    language = SelectField(u'Language', choices=[('null','Choose target language to translate...'),
        ('zh', 'Chinese'), 
        ('nl', 'Dutch'), 
        ('fr', 'French'),
        ('de', 'German'),
        ('el', 'Greek'),
        ('ja', 'Japanese'),
        ('ko', 'Korean')
        ])
    contentTest = TextAreaField('Content')
    submit = SubmitField('Confirm')

class GetFileForm(FlaskForm):
    submit = SubmitField('Download .txt File')