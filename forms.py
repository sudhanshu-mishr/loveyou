from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (
    StringField,
    PasswordField,
    BooleanField,
    SubmitField,
    IntegerField,
    TextAreaField,
)
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    Length,
    Optional,
    NumberRange,
)


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=32)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(
        'Confirm Password', validators=[DataRequired(), EqualTo('password')]
    )
    submit = SubmitField('Create account')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Log in')


class ProfileForm(FlaskForm):
    name = StringField('Name', validators=[Optional(), Length(max=80)])
    age = IntegerField('Age', validators=[Optional(), NumberRange(min=18, max=120)])
    gender = StringField('Gender', validators=[Optional(), Length(max=20)])
    bio = TextAreaField('Bio', validators=[Optional(), Length(max=500)])
    interests = StringField(
        'Interests (comma separated)', validators=[Optional(), Length(max=200)]
    )
    location = StringField('Location', validators=[Optional(), Length(max=120)])
    avatar_file = FileField(
        'Profile photo',
        validators=[Optional(), FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')],
    )
    submit = SubmitField('Save profile')


class MessageForm(FlaskForm):
    body = TextAreaField('Message', validators=[DataRequired(), Length(max=1000)])
    submit = SubmitField('Send')
