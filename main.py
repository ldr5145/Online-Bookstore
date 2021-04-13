import mysql.connector as sqlcon
import db_functionality as db_func
import data_management as data_manage
from flask import Flask, request, render_template

db_ops = db_func.db_operations('projectdb')
app = Flask(__name__)

@app.route("/", methods=["POST", "GET"])
def hello():
    if request.method == "POST":
        print(request.form)
    return render_template('index.html', developer='Liam Raehsler')

@app.route("/forgot_password", methods=["POST", "GET"])
def forgot():
    if request.method == "POST":
        print(request.form)
    else:
        return render_template('forgot_password.html')

@app.route("/create_account", methods=["POST", "GET"])
def new_account():
    password=password2=''
    user_info = {'firstName':'', 'lastname':'', 'phone':'', 'address':'', 'loginID':'', 'password':'', 'password2':''}
    if request.method == "POST":
        print(request.form)
        user_info['firstName'] = request.form['firstName']
        user_info['lastName'] = request.form['lastName']
        user_info['phone'] = request.form['phone']
        user_info['address'] = request.form['address']
        user_info['loginID'] = request.form['loginID']
        user_info['password'] = request.form['password']
        user_info['password2'] = request.form['password2']
        result = db_ops.verify_new_customer_creds(user_info)
        if result['success']:
            print('new account successfully created')
            db_ops.add_customer(user_info, result['duplicatePhone'])
        else:
            errors = [result['errorCodes'], result['message']]
            print(errors)

    return render_template('create_account.html', developer='Liam Raehsler', posts=user_info)
