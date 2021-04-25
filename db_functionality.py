import mysql.connector as sqlcon
import datetime
import re
import os
import hashlib


class db_operations:
    def __init__(self, db_name):
        self.db = sqlcon.connect(
            host="localhost",
            user="root",
            passwd="password",
            auth_plugin="mysql_native_password",
        )
        self.cursor = self.db.cursor()
        self.cursor.execute("CREATE DATABASE IF NOT EXISTS %s" % db_name)
        self.db.database = db_name
        self.db_name = db_name

    def init_db(self):
        """Initialize the database for use.
         Usage: db_operations.init_db()
         This should be a single-use function as any calls to it after the first one on the same database
         will throw errors, since it is creating the database tables that will be manipulated in the other
         functions.
        """
        print("Initializing database...", end='')
        self.cursor.execute("DROP DATABASE %s" % self.db.database)
        self.__init__(self.db_name)
        self.cursor.execute("USE %s" % self.db.database)

        # Book
        self.cursor.execute(
            """CREATE TABLE Book (
            ISBN VARCHAR(13),
            title VARCHAR(300) COLLATE utf8_general_ci,
            publisher VARCHAR(100) COLLATE utf8_general_ci,
            lang VARCHAR(40),
            publicationDate DATE,
            pageCount SMALLINT CHECK(pageCount >= 0),
            stock SMALLINT CHECK(stock >= 0),
            price DECIMAL(5,2),
            subject VARCHAR(100),
            avg_rating DECIMAL(4,2) CHECK(avg_rating <= 10.00),
            total_rating_score INT DEFAULT 0,
            num_ratings INT DEFAULT 0,
            PRIMARY KEY (ISBN))""")

        # Author
        self.cursor.execute(
            """CREATE TABLE Author (
            ID INT AUTO_INCREMENT,
            name VARCHAR(200) COLLATE utf8_general_ci,
            lang VARCHAR(40),
            PRIMARY KEY (ID))""")

        # CustomerPersonal
        self.cursor.execute(
            """CREATE TABLE CustomerPersonal (
            phone CHAR(10),
            address VARCHAR(300) NOT NULL,
            PRIMARY KEY (phone))""")

        # CustomerCredentials
        self.cursor.execute(
            """CREATE TABLE CustomerCredentials (
            loginID VARCHAR(30),
            firstName VARCHAR(50) NOT NULL,
            lastName VARCHAR(50) NOT NULL,
            salt VARBINARY(32) NOT NULL,
            pass_key VARBINARY(32) NOT NULL,
            phone CHAR(10) NOT NULL,
            PRIMARY KEY (loginID),
            FOREIGN KEY (phone) REFERENCES CustomerPersonal(phone)
            ON UPDATE CASCADE ON DELETE RESTRICT)""")

        # ManagerPersonal
        self.cursor.execute(
            """CREATE TABLE ManagerPersonal (
            phone CHAR(10),
            address VARCHAR(300) NOT NULL,
            PRIMARY KEY (phone))""")

        # ManagerCredentials
        self.cursor.execute(
            """CREATE TABLE ManagerCredentials (
            loginID VARCHAR(30),
            managerID INT UNIQUE NOT NULL AUTO_INCREMENT,
            firstName VARCHAR(50),
            lastName VARCHAR(50),
            salt VARBINARY(32) NOT NULL,
            pass_key VARBINARY(32) NOT NULL,
            phone  CHAR(10) NOT NULL,
            PRIMARY KEY (loginID),
            FOREIGN KEY (phone) REFERENCES ManagerPersonal(phone)
            ON UPDATE CASCADE ON DELETE RESTRICT)""")

        # Comment
        self.cursor.execute(
            """CREATE TABLE Comment (
            commentID INT AUTO_INCREMENT,
            ISBN VARCHAR(13) NOT NULL,
            loginID VARCHAR(30) NOT NULL,
            score TINYINT NOT NULL,
            message TEXT,
            veryUseful INT DEFAULT 0,
            useful INT DEFAULT 0,
            useless INT DEFAULT 0,
            avg_usefulness DECIMAL (3,2),
            commentDate DATETIME,
            PRIMARY KEY (commentID),
            FOREIGN KEY (ISBN) REFERENCES Book(ISBN)
            ON UPDATE RESTRICT ON DELETE CASCADE,
            FOREIGN KEY (loginID) REFERENCES CustomerCredentials(loginID)
            ON UPDATE CASCADE ON DELETE CASCADE)""")

        # OrderLog
        self.cursor.execute(
            """CREATE TABLE OrderLog (
            orderNumber INT AUTO_INCREMENT,
            loginID VARCHAR(30) NOT NULL,
            orderDate DATE,
            PRIMARY KEY (orderNumber),
            FOREIGN KEY (loginID) REFERENCES CustomerCredentials(loginID)
            ON UPDATE CASCADE)""")

        # Return Request
        self.cursor.execute(
            """CREATE TABLE ReturnRequest (
            requestID INT,
            managerLoginID VARCHAR(30),
            orderNumber INT NOT NULL,
            requestDate DATE,
            ISBN INT,
            quantity SMALLINT,
            PRIMARY KEY (requestID),
            FOREIGN KEY (managerLoginID) REFERENCES ManagerCredentials(loginID)
            ON UPDATE CASCADE,
            FOREIGN KEY (orderNumber) REFERENCES OrderLog(orderNumber)
            ON UPDATE RESTRICT ON DELETE CASCADE)""")

        # HasKeyword
        self.cursor.execute(
            """CREATE TABLE HasKeyword (
            ISBN VARCHAR(13),
            word VARCHAR(50) COLLATE utf8_general_ci,
            PRIMARY KEY (ISBN, word),
            FOREIGN KEY (ISBN) REFERENCES Book(ISBN)
            ON UPDATE RESTRICT ON DELETE CASCADE)""")

        # Wrote
        self.cursor.execute(
            """CREATE TABLE Wrote (
            authorID INT,
            ISBN VARCHAR(13),
            PRIMARY KEY (authorID, ISBN),
            FOREIGN KEY (authorID) REFERENCES Author(ID)
            ON UPDATE RESTRICT ON DELETE RESTRICT,
            FOREIGN KEY (ISBN) REFERENCES Book(ISBN)
            ON UPDATE RESTRICT ON DELETE CASCADE)""")

        # ProductOf
        self.cursor.execute(
            """CREATE TABLE ProductOf (
            ISBN VARCHAR(13),
            orderNumber INT,
            quantity SMALLINT CHECK(quantity > 0),
            PRIMARY KEY (ISBN, orderNumber),
            FOREIGN KEY (ISBN) REFERENCES Book(ISBN)
            ON UPDATE RESTRICT ON DELETE CASCADE,
            FOREIGN KEY (orderNUmber) REFERENCES OrderLog(orderNumber)
            ON UPDATE RESTRICT ON DELETE CASCADE)""")

        # Trusts
        self.cursor.execute(
            """CREATE TABLE Trusts (
            loginID VARCHAR(30),
            otherLoginID VARCHAR(30) CHECK(loginID<>otherLoginID),
            trustStatus VARCHAR(9) CHECK(trustStatus = 'TRUSTED' OR trustStatus = 'UNTRUSTED'),
            PRIMARY KEY (loginID, otherLoginID),
            FOREIGN KEY (loginID) REFERENCES CustomerCredentials(loginID)
            ON UPDATE CASCADE ON DELETE CASCADE,
            FOREIGN KEY (otherLoginID) REFERENCES CustomerCredentials(loginID)
            ON UPDATE CASCADE ON DELETE CASCADE)""")

        # Rates
        self.cursor.execute(
            """CREATE TABLE Rates (
            loginID VARCHAR(30),
            commentID INT,
            rating VARCHAR(10) NOT NULL,
            PRIMARY KEY (loginID, commentID),
            FOREIGN KEY (loginID) REFERENCES CustomerCredentials(loginID)
            ON UPDATE CASCADE ON DELETE CASCADE,
            FOREIGN KEY (commentID) REFERENCES Comment(commentID)
            ON UPDATE RESTRICT ON DELETE CASCADE)"""
        )

        print("done")

    def populate_tables(self, data_book, data_author, datafile_name, initial_stock=20):
        """Populate relevant tables with formatted data stored in dictionary structures.
        The data will already be properly formatted in dictionary form (retrieved from a
        .csv file), so this function takes the pre-formatted data and stores it in Book and
        Author tables, since those should be populated upon initialization."""

        print("\nPopulating book table with input data from", datafile_name, "...", end='')
        count = 0
        failed_books = []
        for book in data_book:
            try:
                date = datetime.datetime.strptime(book[7], '%m/%d/%Y').date()
                t = (book[0], book[1], book[8], book[3], date,
                     int(book[4]), initial_stock, book[9])
                self.cursor.execute(
                    """INSERT INTO book (ISBN, title, publisher, lang, publicationDate, pageCount, stock, price) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""", t)
            except Exception as e:
                count = count + 1
                failed_books.append(t[1])
        if failed_books:
            print("\nSome books were not added to the database because they had an invalid format:")
            for book in failed_books:
                print(book)
        print("\nTotal books not included in database: ", count)
        self.cursor.execute(
            """SELECT COUNT(*)
            FROM book""")
        num_successful = self.cursor.fetchall()
        print(num_successful[0][0], "books successfully inserted into table \"Book\".")
        self.db.commit()
        print("done")
        # Now we populate authors. First need to get all ISBNs of books that were added to the book table
        print("\nAdding authors to \"Author\" table...", end='')
        self.cursor.execute("SELECT ISBN FROM Book")
        list_books = [book[0] for book in self.cursor.fetchall()]

        for author in data_author:
            self.cursor.execute("INSERT INTO author (name) VALUES (%s)", (author,))
            self.db.commit()
            for book in data_author[author]:
                if book in list_books:
                    self.cursor.execute("SELECT ID FROM author WHERE name = %s", (author,))
                    auth_id = self.cursor.fetchone()[0]
                    self.cursor.execute("INSERT IGNORE INTO wrote VALUES (%s,%s)", (auth_id, book))
                    self.db.commit()
        print("done")
        # Finally, populate HasKeyword table. For now just add words in title and author names
        print("\nGenerating keywords for \"HasKeyword\" table...", end='')
        for book in list_books:
            self.cursor.execute("SELECT title from book WHERE ISBN = %s", (book,))
            keywords = [i[0].split(' ') for i in self.cursor.fetchall()]
            self.cursor.execute("SELECT name FROM author A, wrote W WHERE A.ID = W.authorID AND W.ISBN = %s", (book,))
            authors = [i[0].split(' ') for i in self.cursor.fetchall()]

            keywords.extend(authors)
            for word_subset in keywords:
                for word in word_subset:
                    if not word.isspace() and word:
                        self.cursor.execute("INSERT IGNORE INTO HasKeyword VALUES(%s,%s)", (book, word))
                        self.db.commit()
        print("done")

    def hash_password(self, password):
        salt = os.urandom(32)
        key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return salt, key

    def verify_new_customer_creds(self, info):
        """Function to take the information entered by a new customer and check its validity.
                A valid set of credentials should exhibit the following qualities:
                    1. Username is not already present in the database
                    2. All fields are not empty (all information is required)
                    3. both of the passwords entered match each other exactly
                    4. All other database integrity constraints are met
                        (names are not too long, phone number is 10 digits, etc...)
                    5. Type requirements are met (phone is an integer, password does not have spaces or any other
                        invalid characters, etc...)

                    2 and 5 can be handled in html restraints, 1 3 and 5 should be checked here.
            Returns a result dictionary, containing an overall success boolean (set to True if the customer was
            successfully added to the database and False otherwise), a list of error codes, and a list of
            error messages that will be displayed on the user interface if invalid data is entered."""

        result = {'success': True, 'message': [], 'errorCodes': [], 'duplicatePhone': False, 'manager': False}

        # Valid password check
        if not (info['password'] == info['password2']):
            result['success'] = False
            result['errorCodes'].append(1)
            result['message'].append('Passwords must match.')

        # valid phone number check
        if not re.match(r'^[2-9][0-9]+$', info['phone']):
            result['success'] = False
            result['errorCodes'].append(2)
            result['message'].append('Phone number must be a valid, 10-digit number.')

        # need to check if any users exist (if not, make this one a manager)
        self.cursor.execute("""SELECT COUNT(*) FROM managercredentials""")
        result_query = self.cursor.fetchone()
        print(result_query[0])
        if result_query[0]:
            # unique customer username check
            self.cursor.execute("SELECT COUNT(*) FROM customercredentials WHERE loginID = %s", (info['loginID'],))
            if self.cursor.fetchone()[0] != 0:
                result['success'] = False
                result['errorCodes'].append(3)
                result['message'].append('That username is taken, please select another.')

            # if phone number is already taken, the address should also be the same
            self.cursor.execute("SELECT * FROM customerpersonal WHERE phone = %s", (info['phone'],))
            for entry in self.cursor.fetchall():
                if entry[1] != info['address']:
                    result['success'] = False
                    result['errorCodes'].append(4)
                    result['message'].append('That phone number is already taken. Each phone number can only be'
                                             ' used by one address.')
                    break
                result['duplicatePhone'] = True
            self.cursor.execute("SELECT * FROM managerpersonal WHERE phone = %s", (info['phone'],))
            for entry in self.cursor.fetchall():
                if entry[1] != info['address']:
                    result['success'] = False
                    result['errorCodes'].append(4)
                    result['message'].append('That phone number is already taken. Each phone number can only be'
                                             ' used by one address.')
                    break
        else:
            result['manager'] = True
        return result

    def add_customer(self, info, dup):
        """Take in a (valid) set of new user information and insert properly into the database."""
        if not dup:
            self.cursor.execute("INSERT INTO customerpersonal VALUES (%s,%s)", (int(info['phone']), info['address']))

        self.cursor.execute("INSERT INTO customercredentials VALUES (%s,%s,%s,%s,%s,%s)",
                            (info['loginID'], info['firstName'], info['lastName'], info['salt'],
                             info['key'], int(info['phone'])))
        self.db.commit()

    def add_manager(self, info):
        """Take in a (valid) set of user information and create a new manager. Also need to check if the user is
        currently a customer, and remove the user if so."""
        self.cursor.execute("""SELECT COUNT(*) FROM managerpersonal WHERE phone=%s""", (int(info['phone']),))
        if not self.cursor.fetchone()[0]:
            self.cursor.execute("""INSERT INTO managerpersonal VALUES (%s,%s)""", (int(info['phone']), info['address']))
        self.cursor.execute("""INSERT INTO managercredentials (loginID, firstName, lastName, salt, pass_key, phone)
        VALUES (%s,%s,%s,%s,%s,%s)""", (info['loginID'], info['firstName'], info['lastName'], info['salt'],
                            info['key'], int(info['phone'])))

        self.db.commit()
        self.cursor.execute("""SELECT COUNT(*) FROM customercredentials WHERE loginID=%s""", (info['loginID'],))
        result = self.cursor.fetchone()
        if result[0]:
            self.cursor.execute("""DELETE FROM customerCredentials WHERE loginID=%s""", (info['loginID'],))
            self.db.commit()
            self.cursor.execute("""SELECT COUNT(*) FROM customerCredentials WHERE phone=%s""", (int(info['phone'])))
            phone_count = self.cursor.fetchone()
            if not phone_count[0]:
                self.cursor.execute("""DELETE FROM customerPersonal WHERE phone=%s""", (int(info['phone'],)))
                self.db.commit()

    def confirm_login(self, info):
        """Given a username and a password, confirm whether it is a valid account and check if it is a customer or
        a manager. NOTE: managers and customers are intentionally separated, so a manager's account won't be found
        in customer, and vice versa. Therefore, we can return a definitive result on the first hit but need to check
        both tables if we miss the first search."""
        manager = False
        valid_user = False
        self.cursor.execute("SELECT salt, pass_key FROM customercredentials WHERE loginID=%s",
                            (info['loginID'],))

        password_entered = info['password']
        key = b''
        salt = b''
        for user in self.cursor.fetchall():
            salt = user[0]
            key = user[1]

        self.cursor.execute("SELECT salt, pass_key FROM managercredentials WHERE loginID=%s",
                            (info['loginID'],))

        for user in self.cursor.fetchall():
            manager = True
            salt = user[0]
            key = user[1]

        new_key = hashlib.pbkdf2_hmac('sha256', password_entered.encode('utf-8'), salt, 100000)
        if key == new_key:
            valid_user = True

        return manager, valid_user

    def valid_book(self, info):
        """Given an ISBN, find the book in the database and return the price, a boolean indicating whether or not
        it exists, and the stock. NOTE: we need to return the stock because if the stock is 0 but we found the book
        we want to output a different message"""
        self.cursor.execute("SELECT ISBN, title, price, stock FROM book WHERE ISBN=%s", (info['ISBN'],))
        for book in self.cursor.fetchall():
            return True, float(book[2]), book[1], book[3]
        return False, 0, 0, 0

    def find_books(self, query, filters, dates, order, descending, semantics):
        """Given a query entered by the user, return all books that match the search. Results must
        satisfy the provided filters. I will be making the result a dict so that duplicates are avoided.
        Also, because I may need to sort all of the books by a certain value, each filter check will
        add a subsection of the query and only one query will be executed at the end so that all of the results
        can be ordered together."""
        print(descending)
        if int(semantics):
            # OR semantics
            conjunction = ' UNION '
        else:
            # AND semantics
            conjunction = ' INTERSECT '
        results = {}
        query_sections = ''
        args = []
        # we don't want all filters off, because that would throw a SQL error. So if user does not select
        # any filters, we will assume they want all results.
        if not filters:
            filters['title_filt'] = 'on'
            filters['author_filt'] = 'on'
            filters['lang_filt'] = 'on'
            filters['publisher_filt'] = 'on'

        # go through each active filter and do a query based on that filter, then append results to the final
        # return value
        if 'title_filt' in filters and query[0]:
            query_sections += "SELECT * FROM book WHERE title LIKE %s"
            args.append('%' + query[0] + '%')

        if 'author_filt' in filters and query[1]:
            if query_sections:
                query_sections += conjunction
            query_sections += """SELECT B.ISBN, title, publisher, B.lang, publicationDate, pageCount, 
            stock, B.price, B.subject, avg_rating, total_rating_score, num_ratings FROM book B, author A, wrote W 
            WHERE W.ISBN = B.ISBN AND W.authorID = A.ID AND A.name LIKE %s"""
            args.append('%' + query[1] + '%')

        if 'lang_filt' in filters and query[2]:
            if query_sections:
                query_sections += conjunction
            query_sections += "SELECT * FROM book WHERE lang LIKE %s"
            args.append('%' + query[2] + '%')

        if 'publisher_filt' in filters and query[3]:
            if query_sections:
                query_sections += conjunction
            query_sections += "SELECT * FROM book WHERE publisher LIKE %s"
            args.append('%' + query[3] + '%')

        # if the query is empty, that means they did not fill out any of the forms for filters they wanted.
        if not query_sections:
            return results
        # determine ordering method
        if order == '0':
            query_sections += " ORDER BY publicationDate"
        elif order == '1':
            query_sections += "ORDER BY avg_rating"

        # if descending is true, add descending specification
        if int(descending):
            query_sections += " DESC"

        # execute final constructed query and store results in a dict
        self.cursor.execute(query_sections, args)
        books = self.cursor.fetchall()
        for book in books:
            if str(book[0]) not in results:
                cur_authors = []
                results[str(book[0])] = book
                # now we need to find all the authors of this book so we can display them
                self.cursor.execute("""SELECT name FROM author A, wrote W, book B WHERE A.ID = W.authorID AND
                W.ISBN = B.ISBN AND B.ISBN = %s""", (book[0],))
                for author in self.cursor.fetchall():
                    cur_authors.append(author[0])
                results[str(book[0])] = [results[str(book[0])], cur_authors]
        return results

    def get_single_book_info(self, isbn):
        """Given an ISBN number of a book, retrieve the entire tuple of that book as well as the authors."""
        self.cursor.execute("SELECT * FROM book WHERE ISBN=%s", (isbn,))
        books = self.cursor.fetchall()
        for book in books:
            authors = []
            self.cursor.execute("""SELECT name FROM Author A, Wrote W, Book B WHERE A.ID = W.authorID AND
            W.ISBN = B.ISBN AND B.ISBN = %s""", (isbn,))
            for auth in self.cursor.fetchall():
                authors.append(auth[0])
        return book, authors

    def order_book(self, order_details):
        """Given the order details of a certain order, place the order. Need to add the order to the order log and
        remove the books ordered from stock."""
        order_date = datetime.date.today()
        self.cursor.execute("INSERT INTO orderlog (loginID, orderDate) VALUES (%s, %s)",
                            (order_details['loginID'], order_date))
        order_id = self.cursor.lastrowid
        for i in range(len(order_details['ISBN'])):
            self.cursor.execute("INSERT INTO productof Values (%s, %s, %s)",
                                (order_details['ISBN'][i], order_id, order_details['quantity'][i]))
            self.cursor.execute("UPDATE book SET stock=stock-%s WHERE ISBN=%s",
                                (order_details['quantity'][i], order_details['ISBN'][i]))
        self.db.commit()
        return True

    def get_user_orders(self, loginID):
        """Given a unique login ID, find the details about all of the orders associated with that user and return in a
        single data structure. Note: only need the order number, title/quantity of books, and date. Order results by
        date from newest to oldest."""
        order_details = {}
        self.cursor.execute("""SELECT orderNumber, orderDate FROM orderlog WHERE loginID=%s 
        ORDER BY orderDate DESC, orderNumber DESC""", (loginID,))
        for order in self.cursor.fetchall():
            order_details[str(order[0])] = {'title': [], 'quantity': []}
            # this line only needs to execute once, but its easier to do it like this.
            order_details[str(order[0])]['date'] = order[1]
            self.cursor.execute("""SELECT ISBN FROM orderlog O INNER JOIN productof P ON O.orderNumber = P.orderNumber
            WHERE O.orderNumber=%s""", (order[0],))
            for book in self.cursor.fetchall():
                self.cursor.execute("""SELECT title, quantity FROM book B, productof P, orderlog O WHERE P.ISBN=%s
                AND P.orderNumber = O.orderNumber AND P.ISBN = B.ISBN AND O.orderNumber = %s""", (book[0], order[0]))
                for details in self.cursor.fetchall():
                    title = details[0]
                    quantity = details[1]
                    order_details[str(order[0])]['title'].append(title)
                    order_details[str(order[0])]['quantity'].append(quantity)
        return order_details

    def add_comment(self, comment_info):
        """Add a new comment from a particular user to a particular book. Since only one comment per user per
        book is allowed, this function first checks if this user has already commented on the book. If not, can just
        add a new comment. Otherwise, update the original comment since users are allowed to update their own
        comments."""
        self.cursor.execute("""SELECT commentID, score FROM comment WHERE loginID = %s AND ISBN = %s""",
                            (comment_info['loginID'], comment_info['ISBN']))
        result = self.cursor.fetchall()
        if result:
            # found a comment, need to update it
            self.cursor.execute("""UPDATE comment SET score=%s, message=%s WHERE commentID=%s""",
                                (comment_info['score'], comment_info['message'], result[0][0]))
            self.cursor.execute("""UPDATE book SET total_rating_score=total_rating_score+%s WHERE ISBN=%s""",
                                (int(comment_info['score']) - result[0][1], comment_info['ISBN']))
            return_code = 0
        else:
            # no comment found, create a new one
            self.cursor.execute("""INSERT INTO comment (ISBN, loginID, score, message, commentDate)
             VALUES (%s,%s,%s,%s,%s)""", (comment_info['ISBN'], comment_info['loginID'], comment_info['score'],
                                          comment_info['message'], datetime.datetime.now()))
            self.cursor.execute("""UPDATE book SET total_rating_score = total_rating_score+%s, 
            num_ratings = num_ratings+1 WHERE ISBN = %s""", (comment_info['score'], comment_info['ISBN']))
            return_code = 1
        self.db.commit()
        self.cursor.execute("""UPDATE book SET avg_rating = total_rating_score / num_ratings WHERE 
                            ISBN=%s""", (comment_info['ISBN'],))
        self.db.commit()
        return return_code

    def get_comments(self, isbn, n):
        """Given the ISBN of a book, get n relevant information for all comments about that book."""
        result = []
        self.cursor.execute("""SELECT * FROM comment WHERE ISBN=%s ORDER BY avg_usefulness DESC LIMIT %s""",
                            (str(isbn),n))
        for comment in self.cursor.fetchall():
            result.append(comment)
        return result

    def update_comment_score(self, loginID, commentID, attrib_name):
        """Given a comment and a score, update the total usefulness score of the comment. Assuming this function will
        never be called with a user trying to rate their own comment (since there will be other measures for
        preventing that), so just need to check if the user has already rated this comment and is trying to change
        their vote."""
        self.cursor.execute("SELECT rating FROM rates WHERE loginID = %s AND commentID = %s", (loginID, commentID))
        old_rating = self.cursor.fetchall()
        if old_rating:
            # This user already rated this comment. Change the rating.
            if old_rating[0][0] == attrib_name:
                # Remove the rating, because the user already voted for this.
                self.cursor.execute("UPDATE comment SET " + attrib_name + "=" + attrib_name + "-1 WHERE commentID=%s",
                                    (commentID,))
                self.cursor.execute("""DELETE FROM rates WHERE loginID=%s AND commentID=%s""",
                                    (loginID, commentID))
            else:
                self.cursor.execute("UPDATE comment SET " + old_rating[0][0]+ "=" + old_rating[0][0] + "-1, " + attrib_name
                                    + "=" + attrib_name + "+1 WHERE commentID=%s""", (commentID,))
                self.cursor.execute("""UPDATE rates SET rating=%s WHERE loginID=%s AND commentID=%s""",
                                    (attrib_name, loginID, commentID))
        else:
            # New rating, just need to update one value and add a new rating tuple to rates
            self.cursor.execute("UPDATE comment SET "+attrib_name+"="+attrib_name+"+1 WHERE commentID=%s",
                                (commentID,))
            self.cursor.execute("""INSERT INTO rates VALUES (%s,%s,%s)""", (loginID, commentID, attrib_name))
        self.db.commit()
        self.update_comment_avg_score(commentID)

    def update_comment_avg_score(self, commentID):
        """Given a comment ID, update the average usefulness. This will only ever be called internally, so no need
        for validity checks."""
        self.cursor.execute("""UPDATE comment SET avg_usefulness=(2*veryUseful+useful)/(veryUseful+useful+useless)
        WHERE commentID=%s""", (commentID,))
        self.db.commit()

    def search_customers(self, loginID):
        """Given a single login ID, see if that customer exists on the database. Return true if so, false if not."""
        self.cursor.execute("""SELECT COUNT(*) FROM customercredentials WHERE loginID = %s""", (loginID,))
        if self.cursor.fetchone()[0]:
            return True
        else:
            return False

    def update_trust_status(self, loginID, otherLoginID, status):
        """Update the trust status given both usernames and the status. If a relationship between the two usernames
        exists, either update the status if it is changing the status OR delete the relationship if the status is the
        same (since we are removing the trust status). Otherwise, just create a new relationship."""
        self.cursor.execute("""SELECT trustStatus FROM trusts WHERE loginID=%s AND otherLoginID=%s""",
                            (loginID, otherLoginID))
        result = self.cursor.fetchone()
        if result:
            if result[0] == status:
                self.cursor.execute("""DELETE FROM trusts WHERE loginID=%s AND otherLoginID=%s""",
                                    (loginID, otherLoginID))
            else:
                self.cursor.execute("""UPDATE trusts SET trustStatus=%s WHERE loginID=%s AND otherLoginID=%s""",
                                    (status, loginID, otherLoginID))
        else:
            self.cursor.execute("""INSERT INTO trusts VALUES (%s, %s, %s)""", (loginID, otherLoginID, status))
        self.db.commit()

    def get_basic_userinfo(self, loginID, my_id):
        """Given a single login ID, get basic info (name, number of orders made, number of books purchased,
        comments, total trust score, number trusted and untrusted, etc.). AVOID sensitive information (address,
        phone, password, specifics of orders, etc...) NOTE: No need to check if it is a valid loginID, as this
        function will only be used in the context where the login ID has already been checked and is valid."""
        info ={'loginID': '', 'firstName': '', 'lastName': '', 'orderCount': 0, 'books_purchased': 0, 'num_comments': 0,
               'comments': [], 'books_commented': [], 'trusted': 0, 'untrusted': 0, 'personalStatus': ''}
        self.cursor.execute("""SELECT DISTINCT C.loginID, firstName, lastName, COUNT(DISTINCT orderNumber),
        COUNT(DISTINCT commentID) FROM customercredentials C, comment CO, orderlog O 
        WHERE C.loginID = %s AND O.loginID = %s AND CO.loginID = %s""", (loginID, loginID, loginID))

        result = self.cursor.fetchone()
        info['loginID'] = result[0]
        info['firstName'] = result[1]
        info['lastName'] = result[2]
        info['orderCount'] = result[3]
        info['num_comments'] = result[4]

        self.cursor.execute("""SELECT SUM(quantity) FROM orderlog O, productof P WHERE O.orderNumber = P.orderNumber
        AND loginID=%s""", (loginID,))
        result = self.cursor.fetchone()
        info['books_purchased'] = result[0]

        self.cursor.execute("""SELECT * FROM comment WHERE loginID = %s ORDER BY commentDate DESC""", (loginID,))
        result = self.cursor.fetchall()
        for comment in result:
            info['comments'].append(comment)

        for comment in info['comments']:
            info['books_commented'].append(self.get_single_book_info(comment[1]))
        self.cursor.execute("""SELECT COUNT(loginID) FROM trusts WHERE otherLoginID=%s AND trustStatus='TRUSTED'""",
                            (loginID,))
        result = self.cursor.fetchone()
        info['trusted'] = result[0]

        self.cursor.execute("""SELECT COUNT(loginID) FROM trusts WHERE otherLoginID=%s AND trustStatus='UNTRUSTED'""",
                            (loginID,))
        result = self.cursor.fetchone()
        info['untrusted'] = result[0]

        self.cursor.execute("""SELECT trustStatus FROM trusts WHERE loginID=%s AND otherLoginID=%s""",
                            (my_id, loginID))
        result = self.cursor.fetchone()
        if result:
            info['personalStatus'] = result[0]
        return info

    def end_session(self):
        self.db.close()
