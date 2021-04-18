import mysql.connector as sqlcon
import db_functionality as db_func
import data_management as data_manage
from flask import Flask, request, render_template, redirect, session,url_for
from decimal import Decimal as decimal

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

@app.route("/index/catalog", methods=["POST","GET"])
def browse():
    posts={'results':{}, 'filters':{}, 'startDate':'', 'endDate':'', 'order':'0'}
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == "POST":
        posts['order'] = request.form['order']
        for i in request.form:
            if request.form[i] == 'on':
                # its a filter, add to filters in posts
                posts['filters'][i] = 'on'
                posts['startDate'] = request.form['startDate']
                posts['endDate'] = request.form['endDate']

        posts['results'] = db_ops.find_books(request.form['query'],posts['filters'],
                                             [posts['startDate'], posts['endDate']], posts['order'])
        print(posts['results'])

    return render_template('browse_books.html', developer='Liam Raehsler', posts=posts)

@app.route("/index/book_info", methods=["POST","GET"])
def display_book():
    posts = {'book':(), 'authors':[]}
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == "POST":
        print(request.form)
        book, authors = db_ops.get_single_book_info(request.form['ISBN'])
        posts['book'] = book
        posts['authors'] = authors

    if not posts['book']:
        return redirect(url_for('browse'))
    return render_template('book_info.html', developer='Liam Raehsler', posts=posts)


@app.route("/index/order_book", methods=["POST","GET"])
def order_book():
    order_info={'ISBN':'','quantity': ''}
    error={}
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == "POST":
        order_info['ISBN'] = request.form['ISBN']
        order_info['quantity'] = request.form['quantity']
        valid, price, title, stock = db_ops.valid_book(order_info)
        print(valid, price, title, stock)
        if valid:
            if stock > int(order_info['quantity']):
                if 'order' in request.form:
                    session['order_details'] = {'ISBN': [order_info['ISBN']], 'quantity': [order_info['quantity']],
                                                'loginID': session['username']}
                    return redirect(url_for('confirm_order'))
                else:
                    # will have to add info for what happens when user adds to cart
                    pass
            else:
                if stock:
                    error = ['There are only ' + str(stock) + ' copies of that book left, please reduce your quantity.']
                else:
                    error = ['That book is currently sold out, please try again later.']
        else:
            error = ['That book is not in our database, please try again.']
    return render_template('order_book.html', developer='Liam Raehsler', error_message=error)

@app.route("/index/order_confirm", methods=["POST","GET"])
def confirm_order():
    if 'username' not in session:
        return redirect(url_for('login'))
    if 'order_details' not in session:
        return redirect(url_for('order_book'))
    posts = {'book': [], 'authors': [], 'quantity': session['order_details']['quantity'], 'loginID': session['username'],
             'cumulative_price': [], 'total_price':0.00}
    total_price = 0.0
    for book in session['order_details']['ISBN']:
        book_info, author_info = db_ops.get_single_book_info(book)
        posts['book'].append(book_info)
        posts['authors'].append(author_info)
    for i in range(len(posts['quantity'])):
        cumulative_price = int(posts['quantity'][i])*float(posts['book'][i][7])
        cum_price_str = str("%.2f" % cumulative_price)
        posts['cumulative_price'].append(cum_price_str)
        total_price += cumulative_price
    posts['total_price'] = str("%.2f" % total_price)
    print(posts)
    session.pop('order_details', None)
    return render_template('order_confirm.html', developer='Liam Raehsler', posts=posts)

@app.route("/logout")
def logout():
    session.pop('username', None)
    session.pop('admin', None)
    session.pop('remember', None)
    return redirect(url_for('login'))