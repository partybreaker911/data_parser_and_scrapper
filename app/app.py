import sqlite3

from flask import Flask, render_template, request


app = Flask(__name__)


@app.route("/", methods=["GET"])
def index():
    # Connect to the database
    connection = sqlite3.connect("mydatabase.db")
    cursor = connection.cursor()

    # Retrieve the available categories from the Category table
    cursor.execute("SELECT category FROM Category")
    categories = cursor.fetchall()

    connection.close()

    return render_template("index.html", categories=categories)


@app.route("/products", methods=["POST"])
def display_product():
    # Retrieve the selected category, subcategory, and product from the form submission
    category = request.form["category"]
    subcategory = request.form["subcategory"]
    product = request.form["product"]

    # Connect to the database
    connection = sqlite3.connect("mydatabase.db")
    cursor = connection.cursor()

    # Retrieve the data for the selected product from the Products table
    cursor.execute("SELECT * FROM Products WHERE product = ?", (product,))
    product_data = cursor.fetchone()

    connection.close()

    return render_template("product.html", product_data=product_data)


@app.route("/subcategories", methods=["GET"])
def get_subcategories():
    # Retrieve the selected category from the query parameters
    category = request.args.get("category")

    # Connect to the database
    connection = sqlite3.connect("mydatabase.db")
    cursor = connection.cursor()

    # Retrieve the subcategories for the selected category from the Subcategories table
    cursor.execute(
        "SELECT subcategory FROM Subcategories WHERE category_id IN (SELECT id FROM Category WHERE category = ?)",
        (category,),
    )
    subcategories = cursor.fetchall()

    connection.close()

    return {"subcategories": [subcategory[0] for subcategory in subcategories]}


@app.route("/products", methods=["GET"])
def get_products():
    # Retrieve the selected category and subcategory from the query parameters
    category = request.args.get("category")
    subcategory = request.args.get("subcategory")

    # Connect to the database
    connection = sqlite3.connect("mydatabase.db")
    cursor = connection.cursor()

    # Retrieve the products for the selected category and subcategory from the Products table
    cursor.execute(
        "SELECT product FROM Products WHERE subcategory_id IN (SELECT id FROM Subcategories WHERE subcategory = ? AND category_id IN (SELECT id FROM Category WHERE category = ?))",
        (subcategory, category),
    )
    products = cursor.fetchall()

    connection.close()

    return {"products": [product[0] for product in products]}


if __name__ == "__main__":
    app.run()
