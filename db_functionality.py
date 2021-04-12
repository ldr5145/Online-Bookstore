import mysql.connector as sqlcon
import datetime


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
            passwd VARCHAR(50) NOT NULL,
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
            print(*failed_books, sep='\n')
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

    def end_session(self):
        self.db.close()
