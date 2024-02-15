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
	form = TestForm()
	if form.validate_on_submit():
			print("validated!")
			#make a connection
			with psycopg2.connect(**CONNECTION_PARAMETERS) as conn:
				#create a cursor
				with conn.cursor() as curs:
					params = {
	    				'username': form.username.data,
	    				'email': form.email.data,
	    				'answer1': form.answer1.data,
	    				'answer2': form.answer2.data,
	    				'answer3': form.answer3.data,
	    				'answer4': form.answer4.data,
	    				'answer5': form.answer5.data,
	    				'answer6': form.answer6.data
					}
					curs.execute("""
						INSERT INTO submissions (username, email, answer1, answer2, answer3, answer4, answer5, answer6)
						VALUES (%(username)s, 
							%(email)s,
							%(answer1)s,
							%(answer2)s,
							%(answer3)s,
							%(answer4)s,
							%(answer5)s,
							%(answer6)s
							);
						""", params)
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