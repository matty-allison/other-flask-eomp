import hmac
import sqlite3
from datetime import timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt import JWT, jwt_required, current_identity
from flask_mail import Mail, Message

# Creating a users class
class Users(object):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password


# Function for creating the users database and creating the tables
def addAccount():
    conn = sqlite3.connect('sales.db')
    print("database opened")

    conn.execute("CREATE TABLE IF NOT EXISTS accounts(id INTEGER PRIMARY KEY AUTOINCREMENT,"
                 "name TEXT NOT NULL,"
                 "surname TEXT NOT NULL,"
                 "username TEXT NOT NULL,"
                 "email TEXT NOT NULL,"
                 "password TEXT NOT NULL)")
    print("users added created")
    conn.close()


# function for creating the products table with a foreign key from the users table
def addProduct():
    with sqlite3.connect('sales.db') as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER FORIEGN KEY,"
                     "product_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                     "product_name TEXT NOT NULL,"
                     "product_description TEXT NOT NULL,"
                     "product_price TEXT NOT NULL)")
    print("products table created")


# Calling the functions to create the table
addAccount()
addProduct()


# fetching the users from the table
def get_user():
    with sqlite3.connect('sales.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM accounts')
        accounts = cursor.fetchall()
        the_data = []
        for data in accounts:
            the_data.append(Users(data[0], data[3], data[5]))
    return the_data


the_accounts = get_user()

# authentication functions
username_table = {u.username: u for u in the_accounts}
userid_table = {u.id: u for u in the_accounts}


def authenticate(username, password):
    user = username_table.get(username, None)
    if user and hmac.compare_digest(user.password.encode('utf-8'), password.encode('utf-8')):
        return user


def identity(payload):
    user_id = payload['identity']
    return userid_table.get(user_id, None)


app = Flask(__name__)
CORS(app)
app.debug = True
app.config['SECRET_KEY'] = 'super-secret'
app.config["JWT_EXPIRATION_DELTA"] = timedelta(days=1)
jwt = JWT(app, authenticate, identity)
#email building
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'matthewatwork18@gmail.com'
app.config['MAIL_PASSWORD'] = 'Mallison17$'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

mail = Mail(app)

@app.route('/protected')
@jwt_required()
def protected():
    return '%s' % current_identity


# first route to register new users
@app.route('/register/', methods=["POST"])
def register():
    confirmation = {}
    try:

        if request.method == "POST":

            name = request.form['name']
            surname = request.form['surname']
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']

            with sqlite3.connect("sales.db") as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO accounts("
                               "name,"
                               "surname,"
                               "username,"
                               "email,"
                               "password) VALUES(?, ?, ?, ?, ?)", (name, surname, username, email, password))
                conn.commit()
                confirmation["message"] = "User registered successfully"
                confirmation["status_code"] = 200
                msg = Message('Hello', sender='matthewatwork18@gmail.com', recipients=[email])
                msg.body = "Hello and welcome new user, you have now registered to Point of sale."
                mail.send(msg)
    except ValueError:
        if request.method != "POST":
            return
    finally:
        return confirmation


# route for adding new users
@app.route('/add-product/', methods=["POST"])
@jwt_required()
def add_product():
    confirmation = {}

    if request.method == "POST":

        product_name = request.form['product_name']
        product_description = request.form['product_description']
        product_price = request.form['product_price']

        with sqlite3.connect("sales.db") as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO products("
                           "product_name,"
                           "product_description,"
                           "product_price) VALUES (?, ?, ?)", (product_name, product_description, product_price))
            conn.commit()
            confirmation["message"] = "Product add successfully"
            confirmation["status_code"] = 200
        return confirmation


# route to view users
@app.route('/view-users/', methods=["GET"])
def view_users():
    confirmation = {}
    with sqlite3.connect('sales.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM accounts')

        accounts = cursor.fetchall()

    confirmation["status_code"] = 200
    confirmation["data"] = accounts
    return confirmation


# route to display all products the database
@app.route('/show-products/', methods=["GET"])
def show_Products():
    confirmation = {}
    with sqlite3.connect('sales.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM products')

        products = cursor.fetchall()

    confirmation["status_code"] = 200
    confirmation["data"] = products
    return confirmation


# route to view one product (product id required)
@app.route('/view-product/<int:product_id>/', methods=["GET"])
@jwt_required()
def view_product(product_id):
    confirmation = {}

    with sqlite3.connect("sales.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products WHERE product_id=" + str(product_id))

        confirmation["status_code"] = 200
        confirmation["description"] = "Product retrieved successfully"
        confirmation["data"] = cursor.fetchone()

    return jsonify(confirmation)


# route to edit a product (product id required)
@app.route('/edit-product/<int:product_id>/', methods=["PUT"])
@jwt_required()
def edit_product(product_id):
    confirmation = {}

    if request.method == "PUT":
        with sqlite3.connect('sales.db') as conn:
            product_name = request.form['product_name']
            product_description = request.form['product_description']
            product_price = request.form['product_price']
            put_data = {}

            if product_name is not None:
                put_data["product_name"] = product_name
                cursor = conn.cursor()
                cursor.execute("UPDATE products SET product_name=? WHERE product_id=?", (put_data["product_name"], product_id))
                conn.commit()

                confirmation["message"] = "Product name changed successfully"
                confirmation["status_code"] = 200

            if product_description is not None:
                put_data["product_description"] = product_description
                cursor = conn.cursor()
                cursor.execute("UPDATE products SET product_description=? WHERE product_id=?", (put_data["product_description"], product_id))
                conn.commit()

                confirmation["m("")essage"] = "Product description changed successfully"
                confirmation["status_code"] = 200

            if product_price is not None:
                put_data["product_price"] = product_price
                cursor = conn.cursor()
                cursor.execute("UPDATE products SET product_price=? WHERE product_id=?", (put_data["product_price"], product_id))
                conn.commit()

                confirmation["message"] = "Product price updated successfully"
                confirmation["status_code"] = 200

    return confirmation


# route to delete a product (product id required)
@app.route('/delete-product/<int:product_id>/')
@jwt_required()
def delete_product(product_id):
    confirmation = {}

    with sqlite3.connect('sales.db') as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM products WHERE product_id=" + str(product_id))
        conn.commit()
        confirmation["message"] = "Product successfully deleted"
        confirmation["status_code"] = 200
    return confirmation

#route to view a single product
@app.route('/show-product/<int:product_id>/', methods=["GET"])
def show_product(product_id):
    confirmation = {}

    with sqlite3.connect('sales.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM products WHERE product_id=' + str(product_id))

        products = cursor.fetchall()

    confirmation["status_code"] = 200
    confirmation["data"] = products
    return confirmation

if __name__ == '__main__':
    app.run(debug=True)
