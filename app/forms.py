from flask_wtf import FlaskForm
from datetime import datetime
from wtforms.fields import (
    BooleanField, 
    DateField, 
    StringField, 
    SubmitField, 
    TextAreaField, 
    TimeField,
    DecimalField,
    FieldList,
    FormField
)
from wtforms.validators import (
    InputRequired,
    ValidationError,
    Optional,
    Email
)

#check input length
def length(min=-1, max=-1,fieldname="Field"):
    message = '%s must be between %d and %d characters long.' % (fieldname, min, max)

    def _length(form, field):
        l = field.data and len(field.data) or 0
        if l < min or max != -1 and l > max:
            raise ValidationError(message)

    return _length

#check for forbidden characters
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

def normalizeString(sus):
    sus=sus.upper()
    sus=sus.replace("U","V")
    sus=sus.replace("J","I")
    sus=sus.replace("L","I")
    sus=sus.replace("1","I")
    sus=sus.replace("3","E")
    sus=sus.replace("0","O")
    sus=sus.replace("8","B")
    sus=sus.replace("4","A")
    sus=sus.replace("C","K")
    return sus

#profanity filter
def profanityFilter(fieldname="Field"):
    def _profanityFilter(form, field):
        username = field.data
        username=normalizeString(username)
        isProblem = False
        if "FVK" in username:
            isProblem = True
        
        if isProblem:
            raise ValidationError("That username is not available.")

    return _profanityFilter

def numericFilter(fieldname="Field"):
    def _numericFilter(form,field):
        answer=field.data
        if not isfloat(answer):
            raise ValidationError("Please submit a numeric answer.")
    return _numericFilter

#check for floats
def isfloat(num):
    try:
        float(num)
        return True
    except ValueError:
        return False


#this is the basic format for each question's answer field
class AnswerForm(FlaskForm):
    class Meta:
        csrf = False
    answer = StringField('Answer')

def create_test_form(problemList): # problemList = [problem, answertype, unit, points]
    problemCount=len(problemList)
    class TestForm(FlaskForm):
        username = StringField('Username', validators=[InputRequired(),length(min=1,max=50,fieldname="Username"),forbiddenChars("Username"),profanityFilter("Username")])
        email = StringField('Email', validators=[InputRequired(),Email()])
        answers = FieldList(FormField(AnswerForm),min_entries=problemCount) 
        submit = SubmitField('Submit answers')

    specificForm = TestForm()

    ii=0
    for field in specificForm.answers:
        field.label=problemList[ii][0]
        if problemList[ii][1] == "numeric":
            field.answer.validators=[Optional(),numericFilter()]

        ii+=1

    return specificForm






