from flask_wtf import FlaskForm
from datetime import datetime
from wtforms.fields import (
    BooleanField, 
    DateField, 
    StringField, 
    SubmitField, 
    TextAreaField, 
    TimeField,
    DecimalField
)
from wtforms.validators import (
    InputRequired,
    ValidationError,
    Optional
)


class TestForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired()])
    email = StringField('Email', validators=[InputRequired()])
    answer1 = DecimalField('Answer', validators=[Optional()])
    answer2 = DecimalField('Answer', validators=[Optional()])
    answer3 = DecimalField('Answer', validators=[Optional()])
    answer4 = DecimalField('Answer', validators=[Optional()])
    answer5 = DecimalField('Answer', validators=[Optional()])
    answer6 = DecimalField('Answer', validators=[Optional()])
    submit = SubmitField('Submit answers')
