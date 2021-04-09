import mysql.connector as sqlcon
import db_functionality as db_func

dbops = db_func.db_operations("projectdb")
dbops.init_db()