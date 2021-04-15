import mysql.connector as sqlcon
import db_functionality as db_func
import data_management as data_manage
from flask import Flask, request, render_template, redirect, session,url_for

db_ops = db_func.db_operations('projectdb')
app = Flask(__name__)
app.secret_key = 'top_secret_key'

@app.route("/", methods=["POST", "GET"])
def login():
    creds = {'loginID': '', 'password':''}
    if 'remember' in session and session['remember']:
        return redirect(url_for('welcome_page'))
    if request.method == "POST":
        creds['loginID'] = request.form['Username']
        creds['password'] = request.form['Password']
        remember_me = True if 'Remember' in request.form else False
        is_manager, valid_login = db_ops.confirm_login(creds)
        print(is_manager, valid_login)
        if valid_login:
            session['username'] = creds['loginID']
            session['admin'] = is_manager
            session['remember'] = remember_me
            return redirect(url_for('welcome_page'))

    return render_template('login.html', developer='Liam Raehsler',posts=creds)

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
    errors = []
    if request.method == "POST":
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
            return redirect('/')
        else:
            errors = {'errorCodes':result['errorCodes'], 'messages':result['message']}
            print(errors)

    return render_template('create_account.html', developer='Liam Raehsler', posts=user_info, errors=errors)

@app.route("/index", methods=["POST","GET"])
def welcome_page():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == "POST":
        print(request.form)
    return render_template('index.html', user=session['username'], developer='Liam Raehsler')

@app.route("/logout")
def logout():
    session.pop('username', None)
    session.pop('admin', None)
    session.pop('remember', None)
    return redirect(url_for('login'))