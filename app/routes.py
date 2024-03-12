from flask import (Blueprint, render_template, redirect, url_for, session, request)
import os, psycopg2, math
from app.forms import create_test_form
from wtforms.validators import (
    InputRequired,
    ValidationError,
    Optional,
    Email
)
from operator import itemgetter

#create a blueprint
bp = Blueprint('main', __name__, url_prefix='/') 

#create a dictionary, read from .env file
CONNECTION_PARAMETERS = {
    "user": os.environ.get("DB_USER"),
    "password": os.environ.get("DB_PASS"),
    "dbname": os.environ.get("DB_NAME"),
    "host": os.environ.get("DB_HOST"),
}



# this function takes a list of answers and a test ID
# and returns a list of 0s and 1s
# to indicate right or wrong answers

def grade(scantron,testID):
	#make a connection
	with psycopg2.connect(**CONNECTION_PARAMETERS) as conn:
		#create a cursor
		with conn.cursor() as curs:
			#first we find the list of problem IDs for this test
			curs.execute("""
				SELECT problem_id
				FROM problemtest
				WHERE test_id=%s;
				""",[testID])
			problemIDs = curs.fetchall()

			#now we find the problems for those IDs
			curs.execute("""
				SELECT answer, answertype, points
				FROM problems
				WHERE id = ANY(%s);
				""", (problemIDs,))
			#fetch the records
			answerKey = curs.fetchall()

	i=0
	score=[]
	maxscore=0
	while i < len(scantron):
		#increment the maximum possible score
		maxscore=maxscore+answerKey[i][2]

		#first, check if there's an answer at all
		if(scantron[i]):

			#handle numeric answers
			if answerKey[i][1] == "numeric":
				if float(scantron[i]) == float(answerKey[i][0]):
					score.append(answerKey[i][2])
				else:
					score.append(0)

			#handle string answers
			if answerKey[i][1] == "string":
				if str(scantron[i]) == str(answerKey[i][0]):
					score.append(answerKey[i][2])
				else:
					score.append(0)

			#handle true-or-false answers
			if answerKey[i][1] == "tf":
				if tfNormalize(str(scantron[i])) == tfNormalize(str(answerKey[i][0])):
					score.append(answerKey[i][2])
				else:
					score.append(0)

			#handle fractional answers
			if answerKey[i][1]=="fraction":
				if fractionFormat(scantron[i])==fractionFormat(answerKey[i][0]):
					score.append(answerKey[i][2])
				else:
					score.append(0)
		else:
			score.append(0) #no answer, no points
		i+=1

	return [score, maxscore]

# this function takes a string indicating true or false
# and normalizes it to a boolean value

def tfNormalize(answer):
	trueList=["true","t","yes","y"]
	falseList=["false","f","no","n"]
	answer=answer.casefold()
	if not answer[-1].isalpha():
		answer=answer[:-1]
	if answer in trueList:
		return True 
	if answer in falseList:
		return False



# this function takes a test ID
# and returns a list of database rows
# with information about the problems in that test

def openTest(testID):
	#make a connection
	with psycopg2.connect(**CONNECTION_PARAMETERS) as conn:
		#create a cursor
		with conn.cursor() as curs:
			#first we find the list of problem IDs for this test
			curs.execute("""
				SELECT problem_id,ordering
				FROM problemtest
				WHERE test_id=%s;
				""",[testID])
			problemIDsAndOrder = curs.fetchall()

			# print(problemIDsAndOrder)

			problemIDs, problemOrder = list(zip(*problemIDsAndOrder))
			problemIDs=list(problemIDs)

			# print(problemIDs)
			#now we find the problems for those IDs
			curs.execute("""
				SELECT problem, answertype, unit, points, image, hint, id
				FROM problems
				WHERE id = ANY(%s);
				""", (problemIDs,))
			#fetch the records
			problemList = curs.fetchall()

	# order the problems correctly
	orderDict=dict(problemIDsAndOrder)
	newProblemList=[]
	for problem in problemList:
		newProblemList.append((orderDict[problem[6]],problem))
	newProblemList=sorted(newProblemList, key=itemgetter(0))
	problemIDs, problemList = list(zip(*newProblemList))

	return problemList;

#this function takes a fraction, mixed number,
#or decimal, and returns a decimal
def fractionFormat(num):
	try:
		#if it's just a float, just use that
		num = float(num)
	except:
		#mixed numbers
		if " " in num:
			mixed=num.split(" ",1)
			mixed[0]=mixed[0].strip()
			mixed[1]=mixed[1].strip()
			num=float(mixed[0])+simpleFraction(mixed[1])
		else:
			num=simpleFraction(num)
	return num


#this function takes a fraction
#and returns a decimal
def simpleFraction(num):
	num=num.split("/",1)
	num[0]=num[0].strip()
	num[1]=num[1].strip()
	num[0]=float(num[0])
	num[1]=float(num[1])
	num = num[0]/num[1]
	return num
	


# this function takes a submitted form and the ID of the test
# grades it, adds the submission to the database
# and returns a URL to display the results

def gradeTest(form,testID):
	#check what answer types to expect
	with psycopg2.connect(**CONNECTION_PARAMETERS) as conn:
		#create a cursor
		with conn.cursor() as curs:
			#first we find the list of problem IDs for this test
			curs.execute("""
				SELECT problem_id
				FROM problemtest
				WHERE test_id=%s;
				""",[testID])
			problemIDs = curs.fetchall()

			#now we find the problems for those IDs
			curs.execute("""
				SELECT answertype
				FROM problems
				WHERE id = ANY(%s);
				""", (problemIDs,))
			#fetch the records
			typeList = curs.fetchall()

	#compile a dictionary of all the answers
	answerlist={}
	scantron=[]
	problemcounter=1
	problemkeylist="username,email"
	problemkeylist2="'"+form.username.data+"\',\'"+form.email.data+"'"
	for answer in form.answers:
		problemkey = "answer"+str(problemcounter)
		print("grading")

		#convert answers into appropriate format
		thisAnswer=answer.answer.data
		expectedType = typeList[problemcounter-1][0]
		if thisAnswer:
			if expectedType == "numeric":
				thisAnswer=float(thisAnswer)
			elif expectedType == "string" or expectedType == "tf":
				thisAnswer=str(thisAnswer)
			elif expectedType == "fraction":
				thisAnswer=fractionFormat(thisAnswer)
			answerlist[problemkey]=thisAnswer
		else:
			answerlist[problemkey]=None


		problemkeylist=problemkeylist+","
		problemkeylist2=problemkeylist2+","
		problemkeylist=problemkeylist+problemkey
		problemkeylist2=problemkeylist2+"%("+problemkey+")s"
		scantron.append(answer.answer.data)
		problemcounter+=1

	#this gives us a list of 0s and 1s
	scannedTest = grade(scantron,testID)
	results=scannedTest[0]
	maxScore=scannedTest[1]

	#add them up for total score
	score=sum(results)

	#concatenate them into a string to pass in url
	results = "".join(str(x) for x in results)

	#format them for postgres queries
	problemkeylist=problemkeylist+",grade, test, maxscore"
	problemkeylist2=problemkeylist2+","+str(score)+","+str(testID)+","+str(maxScore)

	#make a connection
	with psycopg2.connect(**CONNECTION_PARAMETERS) as conn:
		#create a cursor
		with conn.cursor() as curs:

			#and now run that sql statement
			sqlstatement="INSERT INTO submissions ("+problemkeylist+") VALUES ("+problemkeylist2+");"
			curs.execute(sqlstatement, answerlist)

			#redirect on submission success
			return url_for(".submitted",score=score,maxscore=maxScore,results=results,username=form.username.data,testID=testID)


def existsVisibly(testID):
	with psycopg2.connect(**CONNECTION_PARAMETERS) as conn:
		with conn.cursor() as curs:
			curs.execute("""
				SELECT visible
				FROM tests
				WHERE id=%s;
				""",[testID])
			isVisible = curs.fetchall()

	if len(isVisible) == 0 or not isVisible[0][0]:
		return False
	return True

### HERE BEGINNETH THE LIST OF ROUTES ###


@bp.route("/")
def main():
	with psycopg2.connect(**CONNECTION_PARAMETERS) as conn:
		#create a cursor
		with conn.cursor() as curs:
			curs.execute("""
				SELECT id, name, testgroup_id, visible, description
				FROM tests
				""")
			testList = curs.fetchall()

			curs.execute("""
				SELECT id, name, visible
				FROM testgroups
				""")
			testgroups = curs.fetchall()

	# format the descriptions so javascript can access them
	descriptionList=[]
	nameList=[]
	for test in testList:
		if test[4]==None:
			descriptionList.append("No description available")
		else:
			descriptionList.append(test[4])
		title=test[1]
		if ":" in title:
			titleList=(title.split(":"))
			title=":<br>".join(titleList)

		nameList.append(title)

	return render_template("main.html", testlist=testList, testgroups=testgroups, descriptionlist=descriptionList,namelist=nameList)




@bp.route("/test/<int:testID>", methods=['GET', 'POST'])
def test(testID):
	#first, check if there's even a test at that ID

	if not existsVisibly(testID):
		return render_template("notest.html")


	#now, get underway
	problemList = openTest(testID) # [problem, answertype, unit, points, image, hint]

	#set up the input form
	form = create_test_form(problemList)

	#form submission stuff
	if form.validate_on_submit():
		urlreturn = gradeTest(form,testID)
		return redirect(urlreturn)
	else:
		print(form.errors)


	### test display stuff ###

	with psycopg2.connect(**CONNECTION_PARAMETERS) as conn:
		#create a cursor
		with conn.cursor() as curs:
			# fetch the test name
			curs.execute("""
				SELECT name, rules_id, calculators
				FROM tests
				WHERE id = %s
				""",[testID])
			testInfo = curs.fetchall()
			testName=testInfo[0][0]
			rulesID=testInfo[0][1]
			calculatorsAllowed=testInfo[0][2]

			#and the test rules
			if rulesID:
				curs.execute("""
					SELECT rules_text
					FROM rules
					WHERE id = %s
					""",[rulesID])
				testRules = curs.fetchall()[0][0]
			else:
				testRules=False


	#lists of problem attributes
	pointList=[]
	unitList=[]
	imageList=[]
	hintList=[]
	for problem in problemList:
		pointList.append(problem[3])
		unitList.append(problem[2])
		if problem[4]:
			imageList.append(problem[4])
		else:
			imageList.append(False)
		if problem[5]:
			hintList.append(problem[5])
		else:
			hintList.append(False)


	##actually load that page
	return render_template("test.html", form=form, name=testName, points=pointList, units=unitList, images=imageList, hints=hintList, rules=testRules, calculators=calculatorsAllowed)

@bp.route("/highscores", defaults={'testID': 0})
@bp.route("/highscores/<int:testID>")
def highscores(testID):
	scoreRatioList=[]

	if int(testID)>0 and not existsVisibly(testID):
		return render_template("notest.html")
	#make a connection
	with psycopg2.connect(**CONNECTION_PARAMETERS) as conn:
		#create a cursor
		with conn.cursor() as curs:

			# first we handle the overall list
			if testID == 0:

				# retrieve the list of submissions
				curs.execute("""
					SELECT username, grade, test, maxscore
					FROM submissions
					ORDER BY grade DESC NULLS LAST;
					""")
				rows = curs.fetchall()

				# isolate a list of the test IDs
				# then use it to calculate percentage scores
				testIDList=[]
				for i in range (0,10):
					testIDList.append(rows[i][2])
					scoreRatio=rows[i][1]/rows[i][3]
					scoreRatio=scoreRatio*100
					scoreRatio=math.floor(scoreRatio)
					scoreRatioList.append(scoreRatio)

				#now we need to sort the rows by percentage score
				newScoreList=[]
				for index,ratio in enumerate(scoreRatioList):
					newScoreList.append((ratio,rows[index]))

				newScoreList=sorted(newScoreList, key=itemgetter(0),reverse=True)
				scoreRatioList, rows = list(zip(*newScoreList))


				# print (testIDList)
				curs.execute("""
					SELECT id,name
					FROM tests
					WHERE id = ANY(%s);
					""", (testIDList,))

				nameKey = curs.fetchall()
				nameKey = dict(nameKey)
				graphdata=False
			else:
				# now we're doing individual tests
				curs.execute("""
					SELECT username, grade
					FROM submissions
					WHERE test = %s
					ORDER BY grade DESC NULLS LAST;
					""",[testID])

				rows = curs.fetchall()
				nameKey=False

				#format for graph display
				graphdata=[["username","grade"]]
				for row in rows:
					graphdata.append([row[0],row[1]])
			#fetch the records
			

			curs.execute("""
				SELECT id, name
				FROM tests
				""")
			testList = curs.fetchall()

	print(graphdata)

	return render_template("highscores.html", 
		rows=rows[:10],
		tests=testList,
		testID=int(testID),
		namekey=nameKey,
		scoreratiolist=scoreRatioList,
		graphdata=graphdata)


@bp.route("/submitted")
def submitted():
	score=int(request.args.get("score"))
	maxscore=int(request.args.get("maxscore"))
	results=list(request.args.get("results"))
	username=str(request.args.get("username"))
	testID=int(request.args.get("testID"))
	roundedperten=math.floor(10*score/maxscore)
	congratslist=["Oof","Oof","Oof","Oof","Better luck next time","Better luck next time","Not so bad","Not too shabby","Nicely done","Awesome job","Fantabulous"]
	with psycopg2.connect(**CONNECTION_PARAMETERS) as conn:
		#create a cursor
		with conn.cursor() as curs:
			curs.execute("""
				SELECT name
				FROM tests
				WHERE id = %s
				""",[testID])
			testName = curs.fetchall()

				# fetch results from test for score distribution
			curs.execute("""
				SELECT username, grade
				FROM submissions
				WHERE test = %s
				ORDER BY grade DESC NULLS LAST;
				""",[testID])
			rows = curs.fetchall()

	#format for graph display
	graphdata=[["username","grade"]]
	for row in rows:
		graphdata.append([row[0],row[1]])

	return render_template("submitted.html",score=score,maxscore=maxscore,congrats=congratslist[roundedperten],results=results,username=username,testID=testID,testname=testName[0][0],graphdata=graphdata)

@bp.route("/trophy")
def trophy():
	score=int(request.args.get("score"))
	maxscore=int(request.args.get("maxscore"))
	username=str(request.args.get("username"))
	testID=int(request.args.get("testID"))
	with psycopg2.connect(**CONNECTION_PARAMETERS) as conn:
		#create a cursor
		with conn.cursor() as curs:
			curs.execute("""
				SELECT name
				FROM tests
				WHERE id = %s
				""",[testID])
			testName = curs.fetchall()

	return render_template("trophy.html",score=score,maxscore=maxscore,username=username,testID=testID,testname=testName[0][0])






