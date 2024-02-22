from flask import (Blueprint, render_template, redirect, url_for, session, request)
import os, psycopg2, math
from app.forms import create_test_form

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
		maxscore=maxscore+answerKey[i][2]
		if scantron[i] == float(answerKey[i][0]):
			score.append(answerKey[i][2])
		else:
			score.append(0)
		i+=1

	return [score, maxscore]



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
				SELECT problem_id
				FROM problemtest
				WHERE test_id=%s;
				""",[testID])
			problemIDs = curs.fetchall()

			#now we find the problems for those IDs
			curs.execute("""
				SELECT problem, answertype, unit, points
				FROM problems
				WHERE id = ANY(%s);
				""", (problemIDs,))
			#fetch the records
			problemList = curs.fetchall()


	return problemList;
	


# this function takes a submitted form and the ID of the test
# grades it, adds the submission to the database
# and returns a URL to display the results

def gradeTest(form,testID):
	#compile a dictionary of all the answers
	answerlist={}
	scantron=[]
	problemcounter=1
	problemkeylist="username,email"
	problemkeylist2="'"+form.username.data+"\',\'"+form.email.data+"'"
	for answer in form.answers:
		problemkey = "answer"+str(problemcounter)
		answerlist[problemkey]=answer.answer.data
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
	problemkeylist=problemkeylist+",grade, test"
	problemkeylist2=problemkeylist2+","+str(score)+","+testID

	#make a connection
	with psycopg2.connect(**CONNECTION_PARAMETERS) as conn:
		#create a cursor
		with conn.cursor() as curs:

			#and now run that sql statement
			sqlstatement="INSERT INTO submissions ("+problemkeylist+") VALUES ("+problemkeylist2+");"
			curs.execute(sqlstatement, answerlist)

			#redirect on submission success
			return url_for(".submitted",score=score,maxscore=maxScore,results=results)



@bp.route("/")
def main():
	with psycopg2.connect(**CONNECTION_PARAMETERS) as conn:
		#create a cursor
		with conn.cursor() as curs:
			curs.execute("""
				SELECT id, name
				FROM tests
				""")
			testList = curs.fetchall()
	return render_template("main.html", testlist=testList)




@bp.route("/test/<testID>", methods=['GET', 'POST'])
def test(testID):
	problemList = openTest(testID) # [problem, answertype, unit, points]

	#set up the input form
	form = create_test_form(len(problemList))

	#write the problems on the input form
	ii = 0
	for field in form.answers:
		field.label=problemList[ii][0]
		ii+=1

	#form submission stuff
	if form.validate_on_submit():
		urlreturn = gradeTest(form,testID)
		return redirect(urlreturn)
	else:
		print(form.errors)


	### test display stuff ###


	# fetch the test name
	with psycopg2.connect(**CONNECTION_PARAMETERS) as conn:
		#create a cursor
		with conn.cursor() as curs:
			curs.execute("""
				SELECT name
				FROM tests
				WHERE id = %s
				""",[testID])
			testName = curs.fetchall()

	#lists of problem attributes
	pointList=[]
	unitList=[]
	for problem in problemList:
		pointList.append(problem[3])
		unitList.append(problem[2])


	##actually load that page
	return render_template("test.html", form=form, name=testName[0][0], points=pointList, units=unitList)

@bp.route("/highscores", defaults={'testID': 0})
@bp.route("/highscores/<testID>")
def highscores(testID):
	#make a connection
	with psycopg2.connect(**CONNECTION_PARAMETERS) as conn:
		#create a cursor
		with conn.cursor() as curs:
			curs.execute("""
				SELECT username, grade
				FROM submissions
				ORDER BY grade DESC NULLS LAST;
				""")
			#fetch the records
			rows = curs.fetchall()

			curs.execute("""
				SELECT id, name
				FROM tests
				""")
			testList = curs.fetchall()

	return render_template("highscores.html", rows=rows[:10],tests=testList,testID=int(testID))


@bp.route("/submitted")
def submitted():
	score=int(request.args.get("score"))
	maxscore=int(request.args.get("maxscore"))
	results=list(request.args.get("results"))
	roundedperten=math.floor(10*score/maxscore)
	congratslist=["Oof","Oof","Oof","Oof","Better luck next time","Better luck next time","Not so bad","Not too shabby","Nicely done","Awesome job","Fantabulous"]
	return render_template("submitted.html",score=score,maxscore=maxscore,congrats=congratslist[roundedperten],results=results)







