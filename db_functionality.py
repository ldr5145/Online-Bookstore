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
        self.cursor.execute("DROP DATABASE %s" % self.db.database)
        self.__init__(self.db_name)
        self.cursor.execute("USE %s" % self.db.database)

        # Book
        self.cursor.execute(
            """CREATE TABLE Book (
            ISBN VARCHAR(13),
            title VARCHAR(300),
            publisher VARCHAR(100),
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
            ID INT,
            name VARCHAR(200),
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
            word VARCHAR(50),
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

    def populate_tables(self, data_book, data_author, initial_stock=20):
        """Populate relevant tables with formatted data stored in dictionary structures.
        The data will already be properly formatted in dictionary form (retrieved from a
        .csv file), so this function takes the pre-formatted data and stores it in Book and
        Author tables, since those should be populated upon initialization."""
        count = 0
        self.cursor.execute(
            """ALTER TABLE book MODIFY COLUMN title VARCHAR(300)
            CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL""")
        self.cursor.execute(
            """ALTER TABLE book MODIFY COLUMN publisher VARCHAR(300)
            CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL""")
        print("The following books were not added to the database because they had an invalid format:")
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
                print(t[1])
        print("\nTotal books not included in database: ", count)
        self.cursor.execute(
            """SELECT COUNT(*)
            FROM book""")
        num_successful = self.cursor.fetchall()
        print(num_successful[0][0], "books successfully inserted into table \"Book\".")
        self.db.commit()

    def end_session(self):
        self.db.close()
