import mysql.connector as sqlcon


class db_operations:
    def __init__(self,db_name):
        self.db = sqlcon.connect(
            host="localhost",
            user="root",
            passwd="password",
            auth_plugin="mysql_native_password",
            database=db_name
        )
        self.cursor = self.db.cursor()

    def init_db(self):
        """Initialize the database for use.
         Usage: db_operations.init_db()
         This should be a single-use function as any calls to it after the first one on the same database
         will throw errors, since it is creating the database tables that will be manipulated in the other
         functions.
        """
        self.cursor.execute("USE %s", self.db.database)

        self.cursor.execute("CREATE TABLE Author")
