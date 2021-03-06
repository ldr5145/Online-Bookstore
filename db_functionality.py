import mysql.connector as sqlcon
import datetime
import re
import os
import hashlib
import operator


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
            ON UPDATE CASCADE ON DELETE CASCADE)""")

        # Return Request
        self.cursor.execute(
            """CREATE TABLE ReturnRequest (
            requestID INT AUTO_INCREMENT,
            orderNumber INT NOT NULL,
            requestDate DATE,
            ISBN VARCHAR(13) NOT NULL,
            quantity SMALLINT,
            status VARCHAR(25) DEFAULT 'PENDING',
            PRIMARY KEY (requestID),
            FOREIGN KEY (orderNumber) REFERENCES OrderLog(orderNumber)
            ON UPDATE RESTRICT ON DELETE CASCADE)""")

        # # HasKeyword
        # self.cursor.execute(
        #     """CREATE TABLE HasKeyword (
        #     ISBN VARCHAR(13),
        #     word VARCHAR(50) COLLATE utf8_general_ci,
        #     PRIMARY KEY (ISBN, word),
        #     FOREIGN KEY (ISBN) REFERENCES Book(ISBN)
        #     ON UPDATE RESTRICT ON DELETE CASCADE)""")

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
        # # Finally, populate HasKeyword table. For now just add words in title and author names
        # print("\nGenerating keywords for \"HasKeyword\" table...", end='')
        # for book in list_books:
        #     self.cursor.execute("SELECT title from book WHERE ISBN = %s", (book,))
        #     keywords = [i[0].split(' ') for i in self.cursor.fetchall()]
        #     self.cursor.execute("SELECT name FROM author A, wrote W WHERE A.ID = W.authorID AND W.ISBN = %s", (book,))
        #     authors = [i[0].split(' ') for i in self.cursor.fetchall()]
        #
        #     keywords.extend(authors)
        #     for word_subset in keywords:
        #         for word in word_subset:
        #             if not word.isspace() and word:
        #                 self.cursor.execute("INSERT IGNORE INTO HasKeyword VALUES(%s,%s)", (book, word))
        #                 self.db.commit()
        # print("done")

    def insert_book(self, book, authors):
        """Given all of the needed information for a book, add it to the database. NOTE: not all validity checks are in
        place, so should do a try-catch here to ensure erroneous data is not inserted into the database."""
        try:
            self.cursor.execute(
                """INSERT INTO book (ISBN, title, publisher, lang, publicationDate, pageCount, stock, price, subject) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (book['ISBN'], book['title'], book['publisher'], book['lang'],
                 datetime.datetime.strptime(book['publicationDate'], '%Y-%m-%d').date(),
                 int(book['pageCount']), int(book['stock']), float(book['price']), book['subject']))
            for auth in authors:
                self.cursor.execute("""SELECT COUNT(*) FROM author WHERE name=%s""", (auth,))
                if not self.cursor.fetchone()[0]:
                    self.cursor.execute("""INSERT INTO author (name) VALUES (%s)""", (auth,))
            self.db.commit()
            for auth in authors:
                self.cursor.execute("""SELECT ID from author WHERE name=%s""", (auth,))
                id = self.cursor.fetchone()[0]
                self.cursor.execute("""INSERT INTO wrote VALUES (%s, %s)""", (id, book['ISBN']))
                self.db.commit()
            return True
        except Exception as e:
            return False

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
        if result_query[0]:
            # unique customer username check
            self.cursor.execute("""SELECT COUNT(*) FROM customercredentials C, managercredentials M
                                WHERE C.loginID = %s OR M.loginID=%s""", (info['loginID'], info['loginID']))
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
            self.cursor.execute("""SELECT COUNT(*) FROM customerCredentials WHERE phone=%s""", (int(info['phone']),))
            phone_count = self.cursor.fetchone()
            if not phone_count[0]:
                self.cursor.execute("""DELETE FROM customerPersonal WHERE phone=%s""", (int(info['phone']),))
                self.db.commit()
            self.update_book_scores()
            self.update_comment_usefulness()

    def promote_to_manager(self, loginID):
        """Given a valid login ID, promote the user to a manager by removing their credentials from the customer
        tables and adding it to the manager tables."""
        self.cursor.execute("""SELECT * FROM customercredentials WHERE loginID=%s""", (loginID,))
        creds = self.cursor.fetchone()
        self.cursor.execute("""SELECT * FROM  customerpersonal WHERE phone=%s""", (int(creds[5]),))
        personal = self.cursor.fetchone()

        info = {'phone': creds[5], 'address': personal[1], 'loginID': creds[0], 'firstName': creds[1],
                'lastName': creds[2],
                'salt': creds[3], 'key': creds[4]}
        self.add_manager(info)

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

    def is_super_manager(self, loginID):
        """Utility function to return a boolean value whether or not the login ID entered is the ID of the
        system super manager."""
        self.cursor.execute("""SELECT managerID FROM managercredentials WHERE loginID=%s""", (loginID,))
        user_key = self.cursor.fetchone()[0]
        self.cursor.execute("""SELECT MIN(managerID) FROM managercredentials""")
        if user_key == self.cursor.fetchone()[0]:
            return True
        return False

    def valid_book(self, info):
        """Given an ISBN, find the book in the database and return the price, a boolean indicating whether or not
        it exists, and the stock. NOTE: we need to return the stock because if the stock is 0 but we found the book
        we want to output a different message"""
        self.cursor.execute("SELECT ISBN, title, price, stock FROM book WHERE ISBN=%s", (info['ISBN'],))
        for book in self.cursor.fetchall():
            return True, float(book[2]), book[1], book[3]
        return False, 0, 0, 0

    def find_books(self, query, filters, dates, order, descending, semantics, loginID):
        """Given a query entered by the user, return all books that match the search. Results must
        satisfy the provided filters. I will be making the result a dict so that duplicates are avoided.
        Also, because I may need to sort all of the books by a certain value, each filter check will
        add a subsection of the query and only one query will be executed at the end so that all of the results
        can be ordered together."""
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
            # if descending is true, add descending specification
            if int(descending):
                query_sections += " DESC"
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
        # filter results so only trusted comments are included in average rating without changing database
        if order == '2':
            actual_ratings = []
            for book in books:
                if not any(str(book[0]) in sub for sub in actual_ratings):
                    self.cursor.execute("""SELECT score FROM trusts T, comment C WHERE T.loginID = %s AND
                    T.otherLoginID = C.loginID AND T.trustStatus = 'TRUSTED' AND 
                    C.ISBN = %s""", (loginID, str(book[0])))
                    current_sum = 0
                    current_num_users = 0
                    for score in self.cursor.fetchall():
                        current_num_users = current_num_users+1
                        current_sum = current_sum+score[0]
                    final_score = None
                    if current_num_users:
                        final_score = current_sum/current_num_users
                    else:
                        final_score = None
                    actual_ratings.append([str(book[0]), final_score])
            if int(descending):
                is_reverse = True
            else:
                is_reverse = False

            actual_ratings = sorted(actual_ratings, key=lambda l:-1*float('inf') if l[1] is None else l[1],
                                    reverse=is_reverse)
            sorted_results = {}
            for [book, score] in actual_ratings:
                unfiltered_data = results[book]
                t = unfiltered_data[0]
                new_data = [(t[0],t[1],t[2],t[3],t[4],t[5],t[6],t[7],t[8],round(score,2) if score is not None else score,
                             t[9],t[10]), unfiltered_data[1]]
                sorted_results[book] = new_data
            results = sorted_results
        return results

    def find_books_by_author_separation(self, name, degree):
        """Given an author name and a degree of separation, return a list of books that are written by authors who share
        that degree separated from the specified author."""
        self.cursor.execute("""SELECT ID FROM author WHERE name=%s""", (name,))
        original_author_id = int(self.cursor.fetchone()[0])
        self.cursor.execute("""SELECT ISBN FROM wrote WHERE authorID=%s""", (original_author_id,))
        first_degree_authors = []
        for original_author_books in self.cursor.fetchall():
            self.cursor.execute("""SELECT authorID FROM wrote WHERE ISBN=%s AND authorID <> %s""",
                                (original_author_books[0], original_author_id))
            for author_id in self.cursor.fetchall():
                first_degree_authors.append(author_id[0])
        first_degree_results = {}
        for author in first_degree_authors:
            self.cursor.execute("""SELECT ISBN FROM wrote WHERE authorID=%s""",(author,))
            for ISBN in self.cursor.fetchall():
                book, author_list = self.get_single_book_info(ISBN[0])
                first_degree_results[ISBN[0]] = [book, author_list]
        if int(degree) == 1:
            return first_degree_results

        second_degree_results = {}
        authors_to_check = []
        all_authors = []
        self.cursor.execute("""SELECT authorID FROM wrote""")
        for author in self.cursor.fetchall():
            all_authors.append(int(author[0]))
        for author1 in first_degree_authors:
            for author2 in all_authors:
                if (self.is_one_degree_separated(author1, author2) and author1 != author2
                        and author2 != original_author_id):
                    authors_to_check.append(author2)
        second_degree_authors = [a for a in authors_to_check if a not in first_degree_authors]
        for author in second_degree_authors:
            self.cursor.execute("""SELECT ISBN FROM wrote WHERE authorID=%s""", (author,))
            for ISBN in self.cursor.fetchall():
                book, author_list = self.get_single_book_info(ISBN[0])
                second_degree_results[ISBN[0]] = [book, author_list]
        return second_degree_results

    def is_one_degree_separated(self,author1, author2):
        """Utility function that determines if two authors are 1-degree separated."""
        self.cursor.execute("""SELECT COUNT(*) FROM wrote W WHERE W.authorID = %s AND EXISTS
        (SELECT * FROM wrote W2 WHERE W2.authorID = %s AND W.ISBN = W2.ISBN)""", (author1, author2))
        if int(self.cursor.fetchone()[0]):
            return True
        return False

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
        return order_id

    def get_recommended_books(self, orderNumber, loginID):
        """Given an order number, return a list of several (we'll say 10 max) suggestions of books for the user to
        purchase. Need to get all the books from this order, then search all other orders and recommend books those
        customers ordered. Also need to find all of the books this user has ordered in the past as well, since we
        do not want to recommend books they already purchased."""
        invalid_isbn_list = []
        books_in_order = []
        possible_isbn_list = []
        self.cursor.execute("""SELECT orderNumber FROM orderlog WHERE loginID=%s""", (loginID,))
        for order in self.cursor.fetchall():
            self.cursor.execute("""SELECT ISBN FROM productof WHERE orderNumber=%s""", (order[0],))
            for ISBN in self.cursor.fetchall():
                invalid_isbn_list.append(ISBN[0])
        self.cursor.execute("""SELECT ISBN FROM productof WHERE orderNumber=%s""", (orderNumber,))
        for ISBN in self.cursor.fetchall():
            books_in_order.append(ISBN[0])
            self.cursor.execute("""SELECT P.ISBN FROM productof P WHERE EXISTS 
            (SELECT orderNumber FROM productof P2 WHERE ISBN = %s AND P2.orderNumber = P.orderNumber)""", (ISBN[0],))
            for valid_isbn in self.cursor.fetchall():
                possible_isbn_list.append(valid_isbn[0])
        valid_isbn_list = [i for i in possible_isbn_list if i not in invalid_isbn_list]
        return_list = []
        for book in valid_isbn_list:
            book, author = self.get_single_book_info(book)
            return_list.append([book, author])
        return return_list

    def restock_book(self, isbn, quantity):
        """Given an isbn of a book and a quantity, add that many books to inventory. If successful, return true.
        Otherwise, return false (this means the user entered an ISBN that is not present in the database)"""
        self.cursor.execute("""SELECT COUNT(*) FROM book WHERE ISBN=%s""", (isbn,))
        if self.cursor.fetchone()[0]:
            self.cursor.execute("""UPDATE book set stock=stock+%s WHERE ISBN=%s""", (quantity, isbn))
            self.db.commit()
            return True
        return False

    def get_user_orders(self, loginID):
        """Given a unique login ID, find the details about all of the orders associated with that user and return in a
        single data structure. Note: only need the order number, title/quantity of books, and date.
        Also will include the ISBN of each book to use in the return requests module. Order results by
        date from newest to oldest."""
        order_details = {}
        self.cursor.execute("""SELECT orderNumber, orderDate FROM orderlog WHERE loginID=%s 
        ORDER BY orderDate DESC, orderNumber DESC""", (loginID,))
        for order in self.cursor.fetchall():
            order_details[str(order[0])] = {'title': [], 'quantity': [], 'ISBN': []}
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
                    order_details[str(order[0])]['ISBN'].append(book[0])
        return order_details

    def get_books_in_order(self, orderNumber):
        """Utility function to send a list of all ISBN's and their quantities in an order given an order number"""
        self.cursor.execute("""SELECT ISBN, quantity FROM orderlog O, productof P WHERE O.orderNumber = P.orderNumber
        AND O.orderNumber=%s""",(orderNumber,))
        result = []
        for i in self.cursor.fetchall():
            result.append([i[0],i[1]])
        return result

    def is_empty_order(self, orderNumber):
        """Utility function to check if an order specified by orderNumber has no books associated with it. This is
        only ever called internally, so no need for validity checks."""
        self.cursor.execute("""SELECT COUNT(*) FROM productof WHERE orderNumber=%s""", (orderNumber,))
        if self.cursor.fetchone()[0]:
            return False
        return True

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
        self.update_average_book_rating(comment_info['ISBN'])
        return return_code

    def update_average_book_rating(self, isbn):
        """Maintenance function for updating the average rating of the book with the given ISBN. This should be
        called any time the number of ratings/the total rating score are updated."""
        self.cursor.execute("""UPDATE book SET avg_rating = total_rating_score / num_ratings WHERE 
                                    ISBN=%s""", (isbn,))
        self.db.commit()

    def get_comments(self, isbn, n):
        """Given the ISBN of a book, get n relevant information for all comments about that book."""
        result = []
        self.cursor.execute("""SELECT * FROM comment WHERE ISBN=%s ORDER BY avg_usefulness DESC LIMIT %s""",
                            (str(isbn), n))
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
                self.cursor.execute(
                    "UPDATE comment SET " + old_rating[0][0] + "=" + old_rating[0][0] + "-1, " + attrib_name
                    + "=" + attrib_name + "+1 WHERE commentID=%s""", (commentID,))
                self.cursor.execute("""UPDATE rates SET rating=%s WHERE loginID=%s AND commentID=%s""",
                                    (attrib_name, loginID, commentID))
        else:
            # New rating, just need to update one value and add a new rating tuple to rates
            self.cursor.execute("UPDATE comment SET " + attrib_name + "=" + attrib_name + "+1 WHERE commentID=%s",
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

    def update_comment_usefulness(self):
        """Maintenance function for updating all comment usefulness values. This should only be called in the case of
        a customer account being deleted."""
        self.cursor.execute("""UPDATE comment SET veryUseful=0, useful=0, useless=0, avg_usefulness=NULL""")
        self.db.commit()
        self.cursor.execute("""SELECT * FROM rates""")
        for rating in self.cursor.fetchall():
            self.update_comment_score(rating[0], rating[1], rating[2])

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
        info = {'loginID': '', 'firstName': '', 'lastName': '', 'orderCount': 0, 'books_purchased': 0,
                'num_comments': 0,
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

    def update_book_scores(self):
        """This is a general maintenance function that should be called any time a customer's account is deleted.
        This is because that customer may have rated a book, and although the comment itself will be removed from
        the database due to cascading foreign key rules, the book stats will not be updated since it is only
        calculated when a comment is added or updated."""
        self.cursor.execute("""UPDATE book SET avg_rating=NULL, total_rating_score=0, num_ratings=0""")
        self.db.commit()
        self.cursor.execute("""SELECT * FROM comment""")
        for comment in self.cursor.fetchall():
            self.cursor.execute("""UPDATE book SET total_rating_score=total_rating_score+%s,
            num_ratings=num_ratings+1 WHERE ISBN=%s""", (comment[3], comment[1]))
            self.db.commit()
            self.update_average_book_rating(comment[1])

    def get_book_statistics(self, n, startDate, endDate):
        """Function that takes in a result limit n and a range of valid publication dates (all specified by the user)
        and returns three lists. The lists returned are listed below in order:
            1. Best-selling books in terms of copies sold in the time zone
            2. Best-selling authors in terms of copies sold in the time zone
            3. Best-selling publishers in terms of copies sold in the time zone"""
        book_results = []
        author_results = []
        publisher_results = []

        self.cursor.execute("""SELECT title, B.ISBN, SUM(quantity) as total FROM productof P, book B WHERE 
        B.ISBN = P.ISBN AND orderNumber IN 
        (SELECT orderNumber FROM orderlog WHERE orderDate >= %s AND orderDate <= %s) GROUP BY ISBN 
        ORDER BY total DESC LIMIT %s""", (startDate, endDate, n))
        for book in self.cursor.fetchall():
            book_results.append(book)

        self.cursor.execute("""SELECT name, SUM(quantity) as total FROM productof P, author A, wrote W
         WHERE ID=authorID AND W.ISBN = P.ISBN AND orderNumber IN 
        (SELECT orderNumber FROM orderlog WHERE orderDate >= %s AND orderDate <= %s) GROUP BY name 
        ORDER BY total DESC LIMIT %s""", (startDate, endDate, n))
        for author in self.cursor.fetchall():
            author_results.append(author)

        self.cursor.execute("""SELECT publisher, SUM(quantity) as total FROM productof P, book B
                 WHERE B.ISBN = P.ISBN AND orderNumber IN 
                (SELECT orderNumber FROM orderlog WHERE orderDate >= %s AND orderDate <= %s) GROUP BY publisher 
                ORDER BY total DESC LIMIT %s""", (startDate, endDate, n))
        for publisher in self.cursor.fetchall():
            publisher_results.append(publisher)

        return book_results, author_results, publisher_results

    def get_customer_statistics(self, n):
        """Function that takes in a result limit n and returns two lists of the top ranked customers. The lists returned
        are listed below in order:
            1. Most trusted users, ranked by the difference of users who trust them and users who distrust them
            2. Most useful users, ranked by the average usefulness score of all of their comments combined"""
        trusted = []
        useful = []

        trust_dict = {}
        self.cursor.execute("""select otherLoginID, COUNT(loginID) as score_trusted
        FROM trusts GROUP BY otherLoginID, trustStatus HAVING trustStatus='TRUSTED'""")
        for cust in self.cursor.fetchall():
            trust_dict[cust[0]] = cust[1]
        self.cursor.execute("""SELECT otherLoginID, COUNT(loginID) as score_trusted FROM trusts
        GROUP BY otherLoginID, trustStatus HAVING trustStatus='UNTRUSTED'""")
        for cust in self.cursor.fetchall():
            if cust[0] in trust_dict:
                trust_dict[cust[0]] = trust_dict[cust[0]] - cust[1]
            else:
                trust_dict[cust[0]] = -cust[1]
        m = 0
        n_temp = n
        while n_temp > m and len(trust_dict):
            loginID = max(trust_dict.items(), key=operator.itemgetter(1))[0]
            self.cursor.execute("""SELECT firstName, lastName FROM customercredentials WHERE loginID=%s""", (loginID,))
            name = self.cursor.fetchone()
            trusted.append([loginID, name[0], name[1], trust_dict[loginID]])
            del trust_dict[loginID]
            n_temp = n_temp - 1

        self.cursor.execute("""SELECT C.loginID, firstName, lastName, AVG(avg_usefulness) as total_avg
        FROM comment C, customercredentials CR WHERE C.loginID = CR.loginID GROUP BY C.loginID
        ORDER BY total_avg DESC LIMIT %s""", (n,))
        for cust in self.cursor.fetchall():
            useful.append(cust)
        return trusted, useful

    def remove_customer(self, loginID):
        """Given the login ID of a customer, remove the customer from the database. Note that the ID passed in to
        this function is unchecked and so proper validity checks need to be in place."""
        try:
            self.cursor.execute("""SELECT COUNT(*) FROM customercredentials WHERE loginID=%s""", (loginID,))
            if not self.cursor.fetchone()[0]:
                return False
            self.cursor.execute("""DELETE FROM customercredentials WHERE loginID=%s""", (loginID,))
            self.db.commit()
            self.cursor.execute("""DELETE FROM customerpersonal WHERE phone NOT IN 
            (SELECT phone FROM customercredentials)""")
            self.db.commit()
            self.update_book_scores()
            self.update_comment_usefulness()
            return True
        except Exception as e:
            return False

    def remove_manager(self, loginID):
        """Given a login ID of a manager, remove the manager from the database. Note that the ID passed in to this
        function is unchecked and so proper validity checks need to be in place. However, this function will only be
        called after an authority validation has taken place, so we do not need to ensure that the caller is a
        super-manager."""
        try:
            self.cursor.execute("""SELECT COUNT(*) FROM managercredentials WHERE loginID=%s""", (loginID,))
            if not self.cursor.fetchone()[0]:
                return False
            self.cursor.execute("""DELETE FROM managercredentials WHERE loginID=%s""", (loginID,))
            self.db.commit()
            self.cursor.execute("""DELETE FROM managerpersonal WHERE phone NOT IN 
            (SELECT phone FROM managercredentials)""")
            self.db.commit()
            return True
        except Exception as e:
            return False

    def request_return(self, orderNumber, ISBN, quantity):
        """Given details needed to locate a book from a certain order and a quantity, create a return request for
        quantity amount of that book."""

        date = datetime.date.today()

        self.cursor.execute("""INSERT INTO returnrequest (orderNumber, requestDate, ISBN, quantity)
        VALUES (%s,%s,%s,%s)""", (orderNumber, date, ISBN, quantity))
        self.db.commit()

    def get_return_requests(self, loginID):
        """Given a login ID, return a dict containing all of the return requests associated with the user."""
        result = {'requestID': [], 'orderNumber': [], 'requestDate': [], 'ISBN': [], 'quantity': [], 'orderDate': [],
                  'status': [], 'title': []}
        self.cursor.execute("""SELECT requestID, R.orderNumber, requestDate, B.ISBN, quantity, orderDate, status, B.title 
        FROM returnrequest R, orderlog O, Book B WHERE O.loginID = %s AND O.orderNumber = R.orderNumber AND
        B.ISBN = R.ISBN ORDER BY requestDate DESC""", (loginID,))
        for request in self.cursor.fetchall():
            result['requestID'].append(request[0])
            result['orderNumber'].append(request[1])
            result['requestDate'].append(request[2])
            result['ISBN'].append(request[3])
            result['quantity'].append(request[4])
            result['orderDate'].append(request[5])
            result['status'].append(request[6])
            result['title'].append(request[7])
        return result

    def get_pending_requests(self):
        """Function to find all of the return requests with a status of "PENDING". This is for the manager view for when
        he/she wishes to accept or deny requests."""
        result = {'requestID': [], 'orderNumber': [], 'requestDate': [], 'ISBN': [], 'quantity': [], 'orderDate': [],
                  'title': []}
        self.cursor.execute("""SELECT requestID, R.orderNumber, requestDate, B.ISBN, quantity, orderDate, B.title 
                FROM returnrequest R, orderlog O, Book B WHERE status='PENDING' AND O.orderNumber = R.orderNumber AND
                B.ISBN = R.ISBN ORDER BY requestDate ASC""")
        for request in self.cursor.fetchall():
            result['requestID'].append(request[0])
            result['orderNumber'].append(request[1])
            result['requestDate'].append(request[2])
            result['ISBN'].append(request[3])
            result['quantity'].append(request[4])
            result['orderDate'].append(request[5])
            result['title'].append(request[6])
        return result

    def update_request_status(self, requestID, ISBN, quantity, approved):
        """Update the database once the manager makes a decision on a return request. The boolean parameter "approved"
        is passed to indicate whether the manager accepted or rejected the request. Upon approval, update the status of
        the return request, then update the order by removing the amount of books specified by quantity and ISBN, then
        finally update the stock count of the book that was returned. Upon rejection, just update the status of the
        request."""
        if approved:
            self.cursor.execute("""SELECT orderNumber FROM returnrequest WHERE requestID=%s""", (requestID,))
            orderNumber = self.cursor.fetchone()[0]
            self.cursor.execute("""UPDATE returnrequest SET status='APPROVED' WHERE requestID=%s""", (requestID,))
            self.cursor.execute("""SELECT quantity FROM productof WHERE orderNumber=%s AND ISBN=%s""",
                                (orderNumber, ISBN))
            remaining_books_ordered = self.cursor.fetchone()[0] - int(quantity)
            if not int(remaining_books_ordered):
                self.cursor.execute("""DELETE FROM productof WHERE orderNumber=%s AND ISBN=%s""", (orderNumber, ISBN))
            else:
                self.cursor.execute("""UPDATE productof SET quantity=quantity-%s WHERE orderNumber=%s AND ISBN=%s""",
                                    (quantity, orderNumber, ISBN))
            self.cursor.execute("""UPDATE book SET stock=stock+%s WHERE ISBN=%s""", (quantity, ISBN))
            self.db.commit()
            if self.is_empty_order(orderNumber):
                self.cursor.execute("""DELETE FROM orderlog WHERE orderNumber=%s""", (orderNumber,))
        else:
            self.cursor.execute("""UPDATE returnrequest SET status='DENIED' WHERE requestID=%s""", (requestID,))
            self.db.commit()

    def end_session(self):
        self.db.close()

    """All of the functions below this line are used to populate the database with mock data and are for demo
    purposes only."""
    def demo_insert_managers(self, creds, personal):
        for i in range(len(creds)):
            self.cursor.execute("""INSERT INTO managerpersonal VALUES (%s, %s)""", (personal[i][0], personal[i][1]))
            self.db.commit()
            salt, key = self.hash_password(creds[i][3])
            self.cursor.execute("""INSERT INTO managercredentials (loginID, firstName, lastName, salt, pass_key, phone)
            VALUES (%s,%s,%s,%s,%s,%s)""", (creds[i][0], creds[i][1], creds[i][2], salt, key, creds[i][4]))
            self.db.commit()

    def demo_insert_customers(self, creds, personal):
        for i in range(len(creds)):
            self.cursor.execute("""INSERT INTO customerpersonal VALUES (%s, %s)""", (personal[i][0], personal[i][1]))
            self.db.commit()
            salt, key = self.hash_password(creds[i][3])
            self.cursor.execute("""INSERT INTO customercredentials (loginID, firstName, lastName, salt, pass_key, phone)
            VALUES (%s,%s,%s,%s,%s,%s)""", (creds[i][0], creds[i][1], creds[i][2], salt, key, creds[i][4]))
            self.db.commit()

    def demo_get_all_books(self):
        """Return a list of all ISBN's in the database. This is used to randomly select books for orders in the mock
        data"""
        results = []
        self.cursor.execute("""SELECT ISBN FROM book""")
        for book in self.cursor.fetchall():
            results.append(book[0])
        return results

    def demo_insert_orders(self, log, product_of):
        for order in log:
            self.cursor.execute("""INSERT INTO orderlog VALUES (%s,%s,%s)""", (order[0],order[1],order[2]))
            self.db.commit()
        for book in product_of:
            self.cursor.execute("""SELECT COUNT(*) FROM productof WHERE ISBN=%s AND orderNumber=%s""",(book[0],book[1]))
            if not int(self.cursor.fetchone()[0]):
                self.cursor.execute("""INSERT INTO productof VALUES (%s,%s,%s)""", (book[0], book[1], book[2]))
        self.db.commit()

    def demo_insert_comments(self, comments):
        for comment in comments:
            # self.cursor.execute("""INSERT INTO comment (ISBN, loginID, score, commentDate) VALUES (%s,%s,%s,%s)""",
            #                     (comment[0], comment[1], comment[2], comment[3]))
            comment_info = {'score': comment[2], 'ISBN': comment[0], 'loginID': comment[1], 'message':''}
            self.cursor.execute("""SELECT COUNT(*) FROM comment WHERE ISBN=%s AND loginID=%s""",(comment[0],comment[1]))
            if not int(self.cursor.fetchone()[0]):
                self.cursor.execute("""INSERT INTO comment (ISBN, loginID, score, message, commentDate)
                     VALUES (%s,%s,%s,%s,%s)""", (comment_info['ISBN'], comment_info['loginID'], comment_info['score'],
                                                  comment_info['message'], comment[3]))
                self.cursor.execute("""UPDATE book SET total_rating_score = total_rating_score+%s, 
                    num_ratings = num_ratings+1 WHERE ISBN = %s""", (comment_info['score'], comment_info['ISBN']))
                self.db.commit()
                self.update_average_book_rating(comment_info['ISBN'])

    def demo_insert_trusts(self, trusts):
        for trust in trusts:
            self.cursor.execute("""INSERT INTO trusts VALUES (%s,%s,%s)""", (trust[0], trust[1], trust[2]))
            self.db.commit()

    def demo_insert_rates(self, rates):
        for rate in rates:
            self.cursor.execute("""SELECT COUNT(*) FROM rates R, comment C WHERE R.loginID = %s AND R.commentID=%s
            OR (C.commentID = %s AND C.loginID=%s)""", (rate[0], rate[1], rate[0], rate[1]))
            out = int(self.cursor.fetchone()[0])
            if not out:
                self.cursor.execute("""INSERT INTO rates VALUES (%s,%s,%s)""", (rate[0],rate[1],rate[2]))
                self.db.commit()
                # New rating, just need to update one value and add a new rating tuple to rates
                self.cursor.execute("UPDATE comment SET " + rate[2] + "=" + rate[2] + "+1 WHERE commentID=%s",
                                    (rate[1],))
                self.db.commit()
                self.update_comment_avg_score(rate[1])

    def demo_insert_return_requests(self, requests):
        for request in requests:
            self.cursor.execute("""INSERT INTO returnrequest (orderNumber, requestDate, ISBN, quantity) 
            VALUES (%s,%s,%s,%s)""", (request[0],request[1],request[2],request[3]))
            self.db.commit()