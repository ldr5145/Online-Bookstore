import mysql.connector as sqlcon
import db_functionality as db_func
import data_management as data_manage

dbops = db_func.db_operations("projectdb")
dbops.init_db()

data_list = data_manage.format_csv('books.csv')
author_dict, book_list = data_manage.extract_authors(data_list)

dbops.populate_tables(book_list, author_dict)
dbops.end_session()