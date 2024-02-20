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

def grade(scantron):
	with open('app/problembank/answerlist1.txt') as f:
		answerKey = f.read().splitlines()

	i=0
	score=[]
	while i < len(scantron):
		if scantron[i] == float(answerKey[i]):
			score.append(1)
		else:
			score.append(0)
		i+=1

	return score



@bp.route("/", methods=['GET', 'POST'])
def main():

	#take the problem statements from external file
	with open('app/problembank/problemlist1.txt') as f:
		problemStatements = f.read().splitlines()

	form = create_test_form(len(problemStatements))

	#label the problems
	ii = 0
	for field in form.answers:
		field.label=problemStatements[ii]
		ii+=1


	#form submission stuff
	if form.validate_on_submit():

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
			results = grade(scantron)

			#add them up for total score
			score=sum(results)

			#concatenate them into a string to pass in url
			results = "".join(str(x) for x in results)

			#format them for postgres queries
			problemkeylist=problemkeylist+",grade"
			problemkeylist2=problemkeylist2+","+str(score)

			#make a connection
			with psycopg2.connect(**CONNECTION_PARAMETERS) as conn:
				#create a cursor
				with conn.cursor() as curs:

					#and now run that sql statement
					sqlstatement="INSERT INTO submissions ("+problemkeylist+") VALUES ("+problemkeylist2+");"
					curs.execute(sqlstatement, answerlist)

					#redirect on submission success
					return redirect(url_for(".submitted",score=score,maxscore=problemcounter-1,results=results))
	else:
		print(form.errors)
	return render_template("main.html", form=form)


@bp.route("/highscores")
def highscores():
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
			#return the records
			return render_template("highscores.html", rows=rows[:10])

@bp.route("/submitted")
def submitted():
	score=int(request.args.get("score"))
	maxscore=int(request.args.get("maxscore"))
	results=list(request.args.get("results"))
	roundedperten=math.floor(10*score/maxscore)
	congratslist=["Oof","Oof","Oof","Oof","Better luck next time","Better luck next time","Not so bad","Not too shabby","Nicely done","Awesome job","Fantabulous"]
	return render_template("submitted.html",score=score,maxscore=maxscore,congrats=congratslist[roundedperten],results=results)







