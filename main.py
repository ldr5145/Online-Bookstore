import mysql.connector as sqlcon
import db_functionality as db_func
import data_management as data_manage
from flask import Flask, request, render_template, redirect, session, url_for
from decimal import Decimal as decimal

# Remember to set FLASK_APP to main if running for the first time.
# if reinitializing database, visit logout page ("127.0.0.1/logout") to clear session (might improve this)

db_ops = db_func.db_operations('projectdb')
app = Flask(__name__)
app.secret_key = 'top_secret_key'

@app.route("/", methods=["POST", "GET"])
def login():
    creds = {'loginID': '', 'password': ''}
    if 'remember' in session and session['remember']:
        return redirect(url_for('welcome_page'))
    if request.method == "POST":
        creds['loginID'] = request.form['Username']
        creds['password'] = request.form['Password']
        remember_me = True if 'Remember' in request.form else False
        is_manager, valid_login = db_ops.confirm_login(creds)
        if valid_login:
            session['username'] = creds['loginID']
            session['remember'] = remember_me
            session['admin'] = is_manager
            if is_manager:
                return redirect(url_for('manager'))
            return redirect(url_for('welcome_page'))

    return render_template('login.html', developer='Liam Raehsler', posts=creds)


@app.route("/forgot_password", methods=["POST", "GET"])
def forgot():
    if request.method == "POST":
        print(request.form)
    else:
        return render_template('forgot_password.html')


@app.route("/create_account", methods=["POST", "GET"])
def new_account():
    password = password2 = ''
    user_info = {'firstName': '', 'lastname': '', 'phone': '', 'address': '', 'loginID': '', 'password': '',
                 'password2': '', 'salt': '', 'key': ''}
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
        print(result)
        if result['success']:
            print('new account successfully created')
            user_info['salt'], user_info['key'] = db_ops.hash_password(user_info['password'])
            if result['manager']:
                db_ops.add_manager(user_info)
            else:
                db_ops.add_customer(user_info, result['duplicatePhone'])
            return redirect('/')
        else:
            errors = {'errorCodes': result['errorCodes'], 'messages': result['message']}

    return render_template('create_account.html', developer='Liam Raehsler', posts=user_info, errors=errors)


@app.route("/index", methods=["POST", "GET"])
def welcome_page():
    if 'username' not in session:
        return redirect(url_for('login'))

    return render_template('index.html', user=session['username'], developer='Liam Raehsler')

@app.route("/index/manager_dashboard", methods=["POST", "GET"])
def manager():
    if 'username' not in session:
        return redirect(url_for('login'))
    if 'admin' not in session or not session['admin']:
        return redirect(url_for('welcome_page'))
    return render_template('manager_dashboard.html', user=session['username'], developer='Liam Raehsler')

@app.route("/index/manager_dashboard/new_manager", methods=["POST", "GET"])
def register_manager():
    posts = {'loginID': '', 'error':''}
    if 'username' not in session:
        return redirect(url_for('login'))
    if 'admin' not in session or not session['admin']:
        return redirect(url_for('welcome_page'))
    if request.method == "POST":
        if 'enter' in request.form:
            posts['loginID'] = request.form['loginID']
            if db_ops.search_customers(posts['loginID']):
                db_ops.promote_to_manager(posts['loginID'])
                return redirect(url_for('manager'))
            else:
                posts['error'] = 'That account is either already a manager or does not exist in the database.'
        else:
            return redirect(url_for('manager'))
    return render_template('register_manager.html', developer='Liam Raehsler')

@app.route("/index/manager_dashboard/new_book", methods=["POST", "GET"])
def insert_book():
    book_info = {'ISBN':'', 'title':'', 'authors': '', 'publisher':'', 'lang': '', 'publicationDate':'',
                 'pageCount':'', 'stock': '', 'price': '', 'subject': ''}
    error = ''
    if 'username' not in session:
        return redirect(url_for('login'))
    if 'admin' not in session or not session['admin']:
        return redirect(url_for('welcome_page'))
    if request.method == "POST":
        if 'enter' in request.form:
            book_info['ISBN'] = request.form['ISBN']
            book_info['title'] = request.form['title']
            book_info['authors'] = request.form['authors']
            book_info['publisher'] = request.form['publishers']
            book_info['lang'] = request.form['lang']
            book_info['publicationDate'] = request.form['publicationDate']
            book_info['pageCount'] = request.form['pageCount']
            book_info['stock'] = request.form['stock']
            book_info['price'] = request.form['price']
            book_info['subject'] = request.form['subject']
            author_list = [i for i in book_info['authors'].split('/')]
            if db_ops.insert_book(book_info, author_list):
                return redirect(url_for('manager'))
            else:
                error = 'Some of the information entered is incompatible with the database.'
        else:
            return redirect(url_for('manager'))
    return render_template('insert_book.html', developer='Liam Raehsler', posts=book_info, error=error)

@app.route("/index/manager_dashboard/restock", methods=["POST","GET"])
def restock():
    posts = {'ISBN':'', 'stock':''}
    error = ''
    if 'username' not in session:
        return redirect(url_for('login'))
    if 'admin' not in session or not session['admin']:
        return redirect(url_for('welcome_page'))
    if request.method=="POST":
        if 'enter' in request.form:
            posts['ISBN'] = request.form['ISBN']
            posts['stock'] = request.form['stock']
            if db_ops.restock_book(posts['ISBN'], posts['stock']):
                print("Book successfully restocked.")
                return redirect(url_for('manager'))
            else:
                error = 'that book does not exist in the database.'
        else:
            return redirect(url_for('manager'))
    return render_template('restock.html', developer='Liam Raehsler', posts=posts, error=error)

@app.route("/index/manager_dashboard/book_statistics", methods=["POST", "GET"])
def book_stats():
    posts = {'n': 10, 'startDate': '', 'endDate': '', 'books':[], 'authors':[], 'publishers':[]}
    if 'username' not in session:
        return redirect(url_for('login'))
    if 'admin' not in session or not session['admin']:
        return redirect(url_for('welcome_page'))
    if request.method == "POST":
        if 'enter' in request.form:
            posts['n'] = int(request.form['n'])
            posts['startDate'] = request.form['startDate']
            posts['endDate'] = request.form['endDate']
            posts['books'], posts['authors'], posts['publishers'] = db_ops.get_book_statistics(posts['n'],
                                                                                               posts['startDate'],
                                                                                               posts['endDate'])
        elif 'cancel' in request.form:
            return redirect(url_for('manager'))
    return render_template("book_stats.html", developer='Liam Raehsler', posts=posts)

@app.route("/index/manager_dashboard/customer_statistics", methods=["POST", "GET"])
def customer_stats():
    posts = {'n':10, 'trusted': [], 'useful': []}
    if 'username' not in session:
        return redirect(url_for('login'))
    if 'admin' not in session or not session['admin']:
        return redirect(url_for('welcome_page'))
    if request.method == "POST":
        if 'enter' in request.form:
            posts['n'] = int(request.form['n'])
            posts['trusted'], posts['useful'] = db_ops.get_customer_statistics(posts['n'])
            print(posts)
        elif 'cancel' in request.form:
            return redirect(url_for('manager'))
    return render_template("customer_stats.html", developer='Liam Raehsler', posts=posts)

@app.route("/index/manager_dashboard/return_requests", methods=["POST", "GET"])
def manage_return_requests():
    if 'username' not in session:
        return redirect(url_for('login'))
    if 'admin' not in session or not session['admin']:
        return redirect(url_for('welcome_page'))
    if request.method=="POST":
        if 'approve' in request.form:
            db_ops.update_request_status(request.form['requestID'], request.form['ISBN'], request.form['quantity'], 1)
        else:
            db_ops.update_request_status(request.form['requestID'], request.form['ISBN'], request.form['quantity'], 0)
    posts = db_ops.get_pending_requests()
    return render_template("request_view.html", developer='Liam Raehsler', posts=posts)

@app.route("/index/manager_dashboard/remove_user", methods=["POST", "GET"])
def remove_customer():
    posts = {'loginID':'', 'error':''}
    if 'username' not in session:
        return redirect(url_for('login'))
    if 'admin' not in session or not session['admin']:
        return redirect(url_for('welcome_page'))
    if request.method == "POST":
        if 'enter' in request.form:
            posts['loginID'] = request.form['loginID']
            if db_ops.remove_customer(posts['loginID']):
                return redirect(url_for('manager'))
            elif db_ops.is_super_manager(session['username']) and db_ops.remove_manager(posts['loginID']):
                return redirect(url_for('manager'))
            else:
                posts['error'] = """That user does not exist in the database or you are trying to remove a manager and 
                do not have the proper credentials."""
        elif 'cancel' in request.form:
            return redirect(url_for('manager'))
    return render_template("remove_user.html", developer='Liam Raehsler', posts=posts)

@app.route("/index/catalog", methods=["POST", "GET"])
def browse():
    posts = {'results': {}, 'filters': {}, 'filter_semantics': 1, 'startDate': '', 'endDate': '', 'order': 0,
             'descending': 0}
    session.pop('ISBN', None)
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
        posts['filter_semantics'] = request.form['filter_semantics']
        posts['descending'] = request.form['descending']
        posts['title'] = request.form['title']
        posts['author'] = request.form['author']
        posts['language'] = request.form['language']
        posts['publisher'] = request.form['publisher']
        if 'auth_degree' in request.form:
            # user is asking for results by degree of separation
            posts['results'] = db_ops.find_books_by_author_separation(request.form['author_name_degree'],
                                                                      request.form['degree'])
        else:
            # user just wants a plain search
            posts['results'] = db_ops.find_books([request.form['title'], request.form['author'], request.form['language'],
                                                 request.form['publisher']], posts['filters'],
                                                 [posts['startDate'], posts['endDate']], posts['order'], posts['descending'],
                                                 posts['filter_semantics'], session['username'])

    return render_template('browse_books.html', developer='Liam Raehsler', posts=posts)

@app.route("/index/book_info/<isbn>", methods=["POST", "GET"])
def display_book(isbn):
    posts = {'book': (), 'authors': [], 'comments': [], 'loginID': ''}
    n = 20
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == "POST":
        if 'return' in request.form:
            return redirect(url_for('browse'))
        elif 'order' in request.form:
            session['ISBN'] = request.form['ISBN']
            return redirect(url_for('order_book'))
        elif 'rate' in request.form:
            session['ISBN'] = request.form['ISBN']
            return redirect(url_for('rate_book', isbn=isbn))
        elif 'Very useful' in request.form:
            db_ops.update_comment_score(session['username'], request.form['Very useful'], 'veryUseful')
        elif 'Useful' in request.form:
            db_ops.update_comment_score(session['username'], request.form['Useful'], 'useful')
        elif 'Useless' in request.form:
            db_ops.update_comment_score(session['username'], request.form['Useless'], 'useless')
        elif 'enter' in request.form:
            n = int(request.form['n'])
        else:
            book, authors = db_ops.get_single_book_info(request.form['ISBN'])
            posts = {'book': book, 'authors': authors, 'comments': db_ops.get_comments(request.form['ISBN'],n),
                     'loginID': session['username']}
    if isbn:
        book, authors = db_ops.get_single_book_info(isbn)
        posts = {'book': book, 'authors': authors, 'comments': db_ops.get_comments(isbn, n),
                 'loginID': session['username']}
    return render_template('book_info.html', developer='Liam Raehsler', posts=posts)

@app.route("/index/book_info/rate_book/<isbn>", methods=["POST","GET"])
def rate_book(isbn):
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == "POST":
        if 'confirm' in request.form:
            comment_info = {'score': request.form['user_rating'], 'ISBN': isbn,
                            'loginID': session['username'], 'message': ''}
            if 'message' in request.form:
                comment_info['message'] = request.form['message']
            exit_code = db_ops.add_comment(comment_info)
            if exit_code:
                print("New comment created.")
            else:
                print("Comment updated.")
            return redirect(url_for('display_book', isbn=isbn))
        elif 'cancel' in request.form:
            return redirect(url_for('display_book', isbn=isbn))
    return render_template("rate_book.html", developer='Liam Raehsler')

@app.route("/index/order_book", methods=["POST", "GET"])
def order_book():
    session.pop('order_details', None)
    order_info = {'ISBN': '', 'quantity': ''}
    error = {}
    posts = {'ISBN':''}
    if 'username' not in session:
        return redirect(url_for('login'))
    if 'ISBN' in session:
        posts['ISBN'] = session['ISBN']
        session.pop('ISBN', None)
        return render_template('order_book.html', developer='Liam Raehsler', posts=posts)
    if request.method == "POST":
        order_info['ISBN'] = request.form['ISBN']
        order_info['quantity'] = request.form['quantity']
        if not order_info['ISBN'] or not order_info['quantity']:
            error = ['You must enter a value in all fields']
        else:
            valid, price, title, stock = db_ops.valid_book(order_info)
            if valid:
                if stock >= int(order_info['quantity']):
                    if 'order' in request.form:
                        session['order_details'] = {'ISBN': [order_info['ISBN']], 'quantity': [order_info['quantity']],
                                                    'loginID': session['username']}
                        return redirect(url_for('confirm_order'))
                    else:
                        if 'cart' in session:
                            cart = session['cart']
                            if order_info['ISBN'] in session['cart']['ISBN']:
                                element = session['cart']['quantity'][session['cart']['ISBN'].index(order_info['ISBN'])]
                                val = int(element) + int(order_info['quantity'])
                                cart['quantity'][session['cart']['ISBN'].index(order_info['ISBN'])] = str(val)
                                session['cart'] = cart
                            else:
                                cart['ISBN'].extend([order_info['ISBN']])
                                cart['quantity'].extend([order_info['quantity']])
                                session['cart'] = cart
                        else:
                            session['cart'] = {'ISBN': [order_info['ISBN']], 'quantity': [order_info['quantity']],
                                               'loginID': session['username']}
                        return redirect(url_for('cart_confirm'))

                else:
                    if stock:
                        error = [
                            'There are only ' + str(stock) + ' copies of that book left, please reduce your quantity.']
                        posts['ISBN'] = request.form['ISBN']
                    else:
                        error = ['That book is currently sold out, please try again later.']
            else:
                error = ['That book is not in our database, please try again.']
    return render_template('order_book.html', developer='Liam Raehsler', error_message=error, posts=posts)


@app.route("/index/order_confirm", methods=["POST", "GET"])
def confirm_order():
    if 'username' not in session:
        return redirect(url_for('login'))
    if 'order_details' not in session:
        return redirect(url_for('order_book'))
    if request.method == "POST":
        if 'confirm' in request.form:
            db_ops.order_book(session['order_details'])
            session.pop('order_details', None)
            session.pop('cart', None)
            return redirect(url_for('order_successful'))
        elif 'cancel' in request.form:
            session.pop('order_details', None)
            return redirect(url_for('cart_confirm'))
        else:
            session.pop('order_details', None)
            return redirect(url_for('order_book'))
    posts = {'book': [], 'authors': [], 'quantity': session['order_details']['quantity'],
             'loginID': session['username'],
             'cumulative_price': [], 'total_price': 0.00}
    total_price = 0.0
    for book in session['order_details']['ISBN']:
        book_info, author_info = db_ops.get_single_book_info(book)
        posts['book'].append(book_info)
        posts['authors'].append(author_info)
    for i in range(len(posts['quantity'])):
        cumulative_price = int(posts['quantity'][i]) * float(posts['book'][i][7])
        cum_price_str = str("%.2f" % cumulative_price)
        posts['cumulative_price'].append(cum_price_str)
        total_price += cumulative_price
    posts['total_price'] = str("%.2f" % total_price)
    return render_template('order_confirm.html', developer='Liam Raehsler', posts=posts)

@app.route("/index/order_confirm/successful")
def order_successful():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('order_successful.html', developer='Liam Raehsler')

@app.route("/index/my_orders", methods=["POST","GET"])
def my_orders():
    if 'username' not in session:
        return redirect(url_for('login'))

    posts = db_ops.get_user_orders(session['username'])
    if not posts:
        return render_template('my_orders_empty.html')
    return render_template('my_orders.html', developer='Liam Raehsler', posts=posts)

@app.route("/index/my_cart", methods=["POST", "GET"])
def cart_confirm():
    session.pop('order_details', None)
    # FIX MISTAKE, cart stays if user does not press remember me and someone else signs in!!
    if 'username' not in session:
        return redirect(url_for('login'))
    if 'cart' not in session:
        return redirect(url_for('empty_cart'))
    if request.method == "POST":
        if 'checkout' in request.form:
            session['order_details'] = {'ISBN': session['cart']['ISBN'], 'quantity': session['cart']['quantity'],
                                        'loginID': session['username']}
            return redirect(url_for('confirm_order'))
            # remember to pop cart later once user confirms order!
        elif 'clear' in request.form:
            session.pop('cart', None)
            return redirect(url_for('empty_cart'))
        else:
            return redirect(url_for('order_book'))

    cart = {'book': [], 'authors': [], 'quantity': session['cart']['quantity']}
    for book in session['cart']['ISBN']:
        book_info, author_info = db_ops.get_single_book_info(book)
        cart['book'].append(book_info)
        cart['authors'].append(author_info)
    return render_template('my_cart.html', developer='Liam Raehsler', cart=cart)


@app.route("/index/cart_confirm/empty")
def empty_cart():
    if 'username' not in session:
        return redirect(url_for('login'))
    if 'cart' in session:
        return redirect(url_for('cart_confirm'))
    return render_template('empty_cart.html', developer='Liam Raehsler')

@app.route("/index/return_request", methods=["GET", "POST"])
def return_request():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == "POST":
        db_ops.request_return(request.form['orderID'], str(request.form['ISBN']), request.form['quantity'])
        return redirect(url_for('my_requests'))
    posts = db_ops.get_user_orders(session['username'])
    return render_template("return_request.html", developer='Liam Raehsler', posts=posts)

@app.route("/index/return_request/my_requests", methods=["POST", "GET"])
def my_requests():
    if 'username' not in session:
        return redirect(url_for('login'))
    posts = db_ops.get_return_requests(session['username'])
    return render_template("my_requests.html", developer='Liam Raehsler', posts=posts)

@app.route("/index/customer_archives", methods=["GET","POST"])
def customer_search():
    error = ''
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == "POST":
        searched_name = request.form['loginID']
        if db_ops.search_customers(searched_name):
            return redirect(url_for('customer_profile', loginID=searched_name))
        else:
            error = "That user does not exist in the database."
    return render_template("customer_search.html", developer='Liam Raehsler', error_message=error)

@app.route("/index/customer_profile/<loginID>", methods=["POST","GET"])
def customer_profile(loginID):
    if 'username' not in session:
        return redirect(url_for('login'))
    if not db_ops.search_customers(loginID):
        return redirect(url_for('customer_search'))
    if request.method == "POST":
        db_ops.update_trust_status(session['username'], loginID,
                                   'TRUSTED' if 'trust' in request.form else 'UNTRUSTED')
    posts = {'loginID': session['username'], 'info': db_ops.get_basic_userinfo(loginID, session['username'])}
    return render_template("customer_profile.html", developer='Liam Raehsler', posts=posts)

@app.route("/logout")
def logout():
    session.clear()
    # session.pop('username', None)
    # session.pop('admin', None)
    # session.pop('remember', None)
    return redirect(url_for('login'))
