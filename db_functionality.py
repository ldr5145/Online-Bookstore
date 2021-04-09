import mysql.connector as sqlcon


class db_operations:
    def __init__(self,db_name):
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
            title VARCHAR(300) NOT NULL,
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
            firstName VARCHAR(50),
            lastName VARCHAR(50),
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

