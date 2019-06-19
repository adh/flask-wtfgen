from flask import Flask, Blueprint, flash, render_template
from wtforms import StringField, PasswordField, SubmitField, SelectField, \
    TextField, TextAreaField, BooleanField, RadioField, FormField
from wtforms.widgets import TextArea, CheckboxInput, ListWidget, CheckboxInput
from wtforms.ext.sqlalchemy.fields import QuerySelectMultipleField
from wtforms.validators import DataRequired, Required, EqualTo, ValidationError, Email
from flask_wtf import FlaskForm
from flask_wtfgen import VerticalFormView

app = Flask(__name__)

app.config['SECRET_KEY'] = 'foo'

class AuthorForm(FlaskForm):
    name = TextField("Name")
    email = TextField("Email", [Email()])
    affiliation = SelectField("Affiliation", choices=[('0', "None"),
                                                      ('1', "Academic"),
                                                      ('2', "Industry")])

class ArticleForm(FlaskForm):
    title = TextField('Title')
    slug = TextField('Slug', description="Part of article's URL (should be related to title and without special characters)")
    summary = TextAreaField('Summary')
    content = TextAreaField('Content')
    checkbox = BooleanField('Foo?')
    radio = RadioField('Bar', choices=[(i, i) for i in ['A', 'B', 'C']])
    author = FormField(AuthorForm)


@app.route('/', methods=['GET', 'POST'])
def index():
    f = ArticleForm()
    if f.validate_on_submit():
        pass
    return render_template('template.html', f=VerticalFormView()(f))
