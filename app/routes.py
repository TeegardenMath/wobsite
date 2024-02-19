from flask import (Blueprint, render_template, redirect, url_for)
import os
import psycopg2
from app.forms import TestForm

#create a blueprint
bp = Blueprint('main', __name__, url_prefix='/') 

#create a dictionary, read from .env file
CONNECTION_PARAMETERS = {
    "user": os.environ.get("DB_USER"),
    "password": os.environ.get("DB_PASS"),
    "dbname": os.environ.get("DB_NAME"),
    "host": os.environ.get("DB_HOST"),
}


@bp.route("/", methods=['GET', 'POST'])
def main():

	#this is a list of problems
	problemStatements=["""When \\(a \\ne 0\\), there are two solutions to \(ax^2 + bx + c = 0\) and they are
    $$x = {-b \\pm \\sqrt{b^2-4ac} \\over 2a}.$$""", 
						"Subtract things", 
						"Do math", 
						"What is it", 
						"A question",
						 "Guess"]
	form = TestForm()

	#label the problems
	ii = 0
	for field in form.answers:
		field.label=problemStatements[ii]
		ii+=1


	#form submission stuff
	if form.validate_on_submit():
			#make a connection
			with psycopg2.connect(**CONNECTION_PARAMETERS) as conn:
				#create a cursor
				with conn.cursor() as curs:
					#compile a dictionary of all the answers
					answerlist={}
					problemcounter=1
					problemkeylist="username, email"
					problemkeylist2="'"+form.username.data+"\',\'"+form.email.data+"'"
					for answer in form.answers:
						problemkey = "answer"+str(problemcounter)
						answerlist[problemkey]=answer.answer.data
						#if problemcounter > 1:
						problemkeylist=problemkeylist+","
						problemkeylist2=problemkeylist2+","
						problemkeylist=problemkeylist+problemkey
						problemkeylist2=problemkeylist2+"%("+problemkey+")s"
						problemcounter+=1

					#and now run that sql statement
					sqlstatement="INSERT INTO submissions ("+problemkeylist+") VALUES ("+problemkeylist2+");"
					curs.execute(sqlstatement, answerlist)


					#now actually display it
					return render_template("main.html", form=form)
	else:
		print(form.errors)
	return render_template("main.html", form=form)

@bp.route("/submissions")
def submissions():
	#make a connection
	with psycopg2.connect(**CONNECTION_PARAMETERS) as conn:
		#create a cursor
		with conn.cursor() as curs:
			curs.execute("""
				SELECT id, username, email, answer1, answer2, answer3, answer4, answer5, answer6
				FROM submissions
				ORDER BY id;
				""")
			#fetch the records
			rows = curs.fetchall()
			#return the records
			return render_template("submissions.html", rows=rows)