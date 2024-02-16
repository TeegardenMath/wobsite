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
    Optional,
    Email
)

def length(min=-1, max=-1,fieldname="Field"):
    message = '%s must be between %d and %d characters long.' % (fieldname, min, max)

    def _length(form, field):
        l = field.data and len(field.data) or 0
        if l < min or max != -1 and l > max:
            raise ValidationError(message)

    return _length

def forbiddenChars(fieldname="Field"):
    charlist=['#','&','@','"',"'",'{','}','\\','&','*','?','/','$','!',':',';','+','`','|','=','<','>','(',')']
    badchars=[]
    message = '%s contains the following forbidden characters: ' % (fieldname)

    def _forbiddenChars(form, field):
        username = field.data
        isProblem = False
        for badchar in charlist:
            if badchar in username:
                isProblem = True 
                badchars.append(badchar)
        badcharlist=" ".join(badchars)
        if isProblem:
            raise ValidationError(message+badcharlist)

    return _forbiddenChars

class TestForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(),length(min=1,max=50,fieldname="Username"),forbiddenChars("Username")])
    email = StringField('Email', validators=[InputRequired(),Email()])
    answer1 = DecimalField('Answer', validators=[Optional()])
    answer2 = DecimalField('Answer', validators=[Optional()])
    answer3 = DecimalField('Answer', validators=[Optional()])
    answer4 = DecimalField('Answer', validators=[Optional()])
    answer5 = DecimalField('Answer', validators=[Optional()])
    answer6 = DecimalField('Answer', validators=[Optional()])
    submit = SubmitField('Submit answers')
