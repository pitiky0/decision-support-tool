import sqlalchemy as sa
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Email
from app import db
from app.models import User
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo

class LoginForm(FlaskForm):
    email = StringField('Email Address:', validators=[DataRequired(message="Please enter your email address"),
                                                      Email(message="Please enter a valid email address")])
    password = PasswordField('Password:', validators=[DataRequired(message="Please enter your password")])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Login')

class SignupForm(FlaskForm):
    full_name = StringField('Full Name:', validators=[DataRequired()])
    email = StringField('Email Address:', validators=[DataRequired(message="Please enter your email address"),
                                                      Email(message="Please enter a valid email address")])
    password = PasswordField('Password:', validators=[
        DataRequired(message="Please enter a password"),
        Length(min=8, message="Password must be at least 8 characters long")
    ])
    confirm_password = PasswordField('Confirm Password:', validators=[
        DataRequired(message="Please confirm your password"),
        EqualTo('password', message="Passwords must match")
    ])

    department = SelectField('Department:', choices=[
        ('IE', 'Industrial Engineering'),
        ('Logistics', 'Logistic'),
        ('Process', 'Process'),
        ('C&P', 'Cutting and Preparation'),
        ('Reliability', 'Reliability'),
        ('Production', 'Production'),
        ('Finance', 'Finance'),
        ('Quality', 'Quality')
    ], validators=[DataRequired()])

    workplace = StringField('Workplace in The Company:', validators=[DataRequired()])
    terms = BooleanField('I agree to the terms and conditions', validators=[DataRequired()])

    submit = SubmitField('Create Account')

    def validate_email(self, email):
        user = db.session.scalar(sa.select(User).where(
            User.email == email.data))
        if user is not None:
            raise ValidationError('Please use a different email address.')

class ForgotPasswordForm(FlaskForm):
    email = StringField('Email Address:', validators=[DataRequired(message="Please enter your email address"),
                                                      Email(message="Please enter a valid email address")])
    submit = SubmitField('Send Reset Link')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password:', validators=[
        DataRequired(message="Please enter a password"),
        Length(min=8, message="Password must be at least 8 characters long")
    ])
    confirm_password = PasswordField('Confirm Password:', validators=[
        DataRequired(message="Please confirm your password"),
        EqualTo('password', message="Passwords must match")
    ])
    submit = SubmitField('Reset Password')
