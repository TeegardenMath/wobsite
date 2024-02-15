from flask import (Blueprint, render_template, redirect, url_for)
import os
import psycopg2

#create a blueprint
bp = Blueprint('main', __name__, url_prefix='/') 


@bp.route("/")
def main():
	return render_template("main.html")