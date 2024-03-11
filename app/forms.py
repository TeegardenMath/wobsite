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
import math

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

def tfFilter(fieldname="Field"):
    def _tfFilter(form,field):
        answer=field.data
        tfList=["true","t","yes","y","false","f","no","n"]
        answer=answer.casefold()
        if not answer[-1].isalpha():
            answer=answer[:-1]
        if not answer in tfList:
            raise ValidationError("Please answer 'true' or 'false'.")

    return _tfFilter

def numericFilter(fieldname="Field"):
    def _numericFilter(form,field):
        answer=field.data
        if not isfloat(answer):
            raise ValidationError("Please submit a numeric answer.")
    return _numericFilter

def fracFilter(fieldname="Field"):
    def _fracFilter(form,field):
        answer=field.data
        isNumeric=True
        if " " in answer:
            mixedform = answer.split(" ",1)
            mixedform[0]=mixedform[0].strip()
            mixedform[1]=mixedform[1].strip()
            if not isint(mixedform[0]):
                isNumeric=False
            if "-" in mixedform[1]:
                isNumeric=False
            if not "/" in mixedform[1]:
                isNumeric=False
            answer=mixedform[1]
        if "/" in answer:
            fracform=answer.split("/",1)
            fracform[0]=fracform[0].strip()
            fracform[1]=fracform[1].strip()
            if not isfloat(fracform[0]) or not isfloat(fracform[1]):
                isNumeric=False 
            else:
                fracform[0]=float(fracform[0])
                fracform[1]=float(fracform[1])
                if fracform[1] == 0:
                    raise ValidationError("Fractions may not have a denominator of zero.")
                if not isint(fracform[0]) or not isint(fracform[1]):
                    raise ValidationError("Fractions must be in simplest form.")
                if fracform[1]<0 or fracform[1]==1:
                    raise ValidationError("Fractions must be in simplest form.")
                if math.gcd(int(fracform[0]),int(fracform[1]))>1:
                    raise ValidationError("Fractions must be in simplest form.")


        elif not isfloat(answer):
            isNumeric = False

        if not isNumeric:
            raise ValidationError("Please submit a numeric answer.")
    return _fracFilter

#check for floats
def isfloat(num):
    try:
        float(num)
        return True
    except ValueError:
        return False

#check for ints
def isint(num):
    try:
        num = float(num)
    except ValueError:
        return False
    if int(num) == num:
        return True
    else:
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
        if problemList[ii][1] == "tf":
            field.answer.validators=[Optional(),tfFilter()]
        if problemList[ii][1] == "fraction":
            field.answer.validators=[Optional(),fracFilter()]

        ii+=1

    return specificForm






