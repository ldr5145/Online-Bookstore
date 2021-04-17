import mysql.connector as sqlcon
import datetime
import re

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
            pass VARCHAR(50) NOT NULL,
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
            pass VARCHAR(50) NOT NULL,
            phone  CHAR(10) NOT NULL,
            PRIMARY KEY (loginID),
            FOREIGN KEY (phone) REFERENCES ManagerPersonal(phone)
            ON UPDATE CASCADE ON DELETE RESTRICT)""")

        # Comment
        self.cursor.execute(
            """CREATE TABLE Comment (
            commentID INT,
            ISBN VARCHAR(13) NOT NULL,
            loginID VARCHAR(30) NOT NULL,
            score TINYINT NOT NULL,
            message TEXT,
            usefulness FLOAT,
            commentDate DATE,
            PRIMARY KEY (commentID),
            FOREIGN KEY (ISBN) REFERENCES Book(ISBN)
            ON UPDATE RESTRICT ON DELETE CASCADE,
            FOREIGN KEY (loginID) REFERENCES CustomerCredentials(loginID)
            ON UPDATE CASCADE ON DELETE CASCADE)""")

        # OrderLog
        self.cursor.execute(
            """CREATE TABLE OrderLog (
            orderNumber INT,
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
                count = count+1
                failed_books.append(t[1])
        if failed_books:
            print("\nSome books were not added to the database because they had an invalid format:")
            print(failed_books, sep='\n')
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

        result = {'success': True, 'message':[], 'errorCodes':[], 'duplicatePhone':False}

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

        return result

    def add_customer(self, info, dup):
        """Take in a (valid) set of new user information and insert properly into the database."""
        if not dup:
            self.cursor.execute("INSERT INTO customerpersonal VALUES (%s,%s)", (int(info['phone']), info['address']))

        self.cursor.execute("INSERT INTO customercredentials VALUES (%s,%s,%s,%s,%s)", (info['loginID'], info['firstName'],
                                                                                        info['lastName'], info['password'],
                                                                                        int(info['phone'])))
        self.db.commit()

    def confirm_login(self, info):
        """Given a username and a password, confirm whether it is a valid account and check if it is a customer or
        a manager. NOTE: managers and customers are intentionally separated, so a manager's account won't be found
        in customer, and vice versa. Therefore, we can return a definitive result on the first hit but need to check
        both tables if we miss the first search."""
        self.cursor.execute("SELECT * FROM customercredentials WHERE loginID=%s AND pass=%s",
                            (info['loginID'], info['password']))
        if len(self.cursor.fetchall()):
            return False, True

        self.cursor.execute("SELECT * FROM managercredentials WHERE loginID=%s AND pass=%s",
                            (info['loginID'], info['password']))
        if len(self.cursor.fetchall()):
            return True, True

        return False, False

    def valid_book(self, info):
        """Given an ISBN, find the book in the database and return the price, a boolean indicating whether or not
        it exists, and the stock. NOTE: we need to return the stock because if the stock is 0 but we found the book
        we want to output a different message"""
        self.cursor.execute("SELECT ISBN, title, price, stock FROM book WHERE ISBN=%s", (info['ISBN'],))
        for book in self.cursor.fetchall():
            return True, float(book[2]), book[1], book[3]
        return False, 0, 0

    def find_books(self, query, filters, dates, order):
        """Given a query entered by the user, return all books that match the search. Results must
        satisfy the provided filters. I will be making the result a dict so that duplicates are avoided.
        Also, because I may need to sort all of the books by a certain value, each filter check will
        add a subsection of the query and only one query will be executed at the end so that all of the results
        can be ordered together."""

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
        if 'title_filt' in filters:
            query_sections += "SELECT * FROM book WHERE title LIKE %s"
            args.append('%'+query+'%')

        if 'author_filt' in filters:
            if query_sections:
                query_sections += ' UNION '
            query_sections += """SELECT B.ISBN, title, publisher, B.lang, publicationDate, pageCount, 
            stock, B.price, B.subject FROM book B, author A, wrote W WHERE W.ISBN = B.ISBN 
            AND W.authorID = A.ID AND A.name LIKE %s"""
            args.append('%' + query + '%')

        if 'lang_filt' in filters:
            if query_sections:
                query_sections += ' UNION '
            query_sections += "SELECT * FROM book WHERE lang LIKE %s"
            args.append('%' + query + '%')

        if 'publisher_filt' in filters:
            if query_sections:
                query_sections += ' UNION '
            query_sections += "SELECT * FROM book WHERE publisher LIKE %s"
            args.append('%' + query + '%')

        # determine ordering method
        if order == '0':
            query_sections += " ORDER BY publicationDate"
        elif order == '1':
            query_sections += "ORDER BY "

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

    def end_session(self):
        self.db.close()
