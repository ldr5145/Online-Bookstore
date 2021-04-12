import mysql.connector as sqlcon
import db_functionality as db_func
import data_management as data_manage
from flask import Flask, request, render_template

app = Flask(__name__)

@app.route("/")
def hello():
    return 'Hello, World!'
