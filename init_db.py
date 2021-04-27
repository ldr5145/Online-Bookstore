import mysql.connector as sqlcon
import db_functionality as db_func
import data_management as data_manage
from random import randint

db_ops = db_func.db_operations("projectdb")
db_ops.init_db()

data_list = data_manage.format_csv('books.csv')
author_dict, book_list = data_manage.extract_authors(data_list)

db_ops.populate_tables(book_list, author_dict, 'books.csv')

"""The next section is used to create some mock data that can be used for demoing. Comment out if you want to
insert data fully using the user interface."""
manager_credentials = []
manager_personal = []
customer_credentials = []
customer_personal = []
order_log = []
product_of = []
rates = []
comment = []
trusts = []
return_request = []
isbn_list = db_ops.demo_get_all_books()
# super manager
manager_credentials.append(['super_manager', 'Super', 'Manager', 'password', '8887776565'])
manager_personal.append(['8887776565', '100 Super Manager Road'])
db_ops.demo_insert_managers(manager_credentials, manager_personal)

# customers
fnames = ['John', 'James', 'Anna', 'Jennifer', 'Scott', 'Mark', 'Victoria', 'Katie', 'Joseph', 'Leo']
lnames = ['Smith', 'Cole', 'Lin', 'Williams', 'Davis', 'Brown', 'Garcia', 'Martinez', 'Anderson', 'Jackson']
for i in range(100):
    customer_credentials.append(['customer'+str(i+1), fnames[randint(0, len(fnames)-1)], lnames[randint(0, len(lnames)-1)],
                                 'password', '88877766'+str(i).zfill(2)])
    customer_personal.append([customer_credentials[i][4], str(i+1)+' Customer Lane'])
db_ops.demo_insert_customers(customer_credentials, customer_personal)

#orders
for i in range(1000):
    order_log.append([i+1, 'customer'+str(randint(1,100)),
                      str(randint(2000,2020))+'-'+str(randint(1,12)).zfill(2)+'-'+str(randint(1,28)).zfill(2)])
for i in range(1000):
    num_books = randint(1, 10)
    for book in range(num_books):
        isbn = isbn_list[randint(0, len(isbn_list)-1)]
        product_of.append([isbn, i+1, randint(1, 20)])
db_ops.demo_insert_orders(order_log, product_of)

#comments
# here only want a couple books so that I can find all the commments, so I hand-selected a few ISBN's I want
isbn_list_shortened = ['9780439064866', '9780822210894', '9780226323985']
#                     [Harry Potter, Streetcar Named Desire, Gilgamesh]
for i in range(100):
    for num_orders in range(randint(0,5)):
        comment.append([isbn_list_shortened[randint(0, 2)], 'customer'+str(i+1), randint(0,10),
                        str(randint(2000,2020))+'-'+str(randint(1,12)).zfill(2)+'-'+str(randint(1,28)).zfill(2)])
db_ops.demo_insert_comments(comment)

#trusts
options = ['TRUSTED', 'UNTRUSTED']
for i in range(100):
    for num_trusts in range(randint(0, 5)):
        otherLogin = 'customer'+str(randint(1,100))
        if (['customer'+str(i+1), otherLogin, 'TRUSTED'] not in trusts and
                ['customer'+str(i+1), otherLogin, 'UNTRUSTED'] not in trusts and 'customer'+str(i+1) != otherLogin):
            trusts.append(['customer'+str(i+1), otherLogin, options[randint(0, 1)]])
db_ops.demo_insert_trusts(trusts)

#rates
options = ['veryUseful', 'useful', 'useless']
for i in range(600):
    rates.append(['customer'+str(randint(1,100)), randint(1,100), options[randint(0,2)]])
db_ops.demo_insert_rates(rates)

#return requests
for i in range(20):
    orderNumber = randint(1,1000)
    valid_books = db_ops.get_books_in_order(orderNumber)
    [isbn, max_quantity] = valid_books[randint(0,len(valid_books)-1)]
    quantity = randint(1,max_quantity)
    return_request.append([orderNumber,
                           str(randint(2000,2020))+'-'+str(randint(1,12)).zfill(2)+'-'+str(randint(1,28)).zfill(2),
                           isbn, quantity])
db_ops.demo_insert_return_requests(return_request)
