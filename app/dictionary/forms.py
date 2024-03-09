from flask_wtf import FlaskForm
from markupsafe import Markup
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired

class SearchForm(FlaskForm):
    search_label = Markup("Search&nbsp;Terms:")
    search = StringField(label=search_label)
    submit = SubmitField("Search")

class AddTerm(FlaskForm):
    term = StringField('Term:', validators=[DataRequired()])
    definition = TextAreaField('Definition:', validators=[DataRequired()])
    submit = SubmitField('Submit')

class EditTerm(FlaskForm):
    term = StringField('Term:', validators=[DataRequired()])
    definition = TextAreaField('Definition:', validators=[DataRequired()])
    submit = SubmitField('Submit')

