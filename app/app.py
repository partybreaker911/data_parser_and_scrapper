from flask import Flask, render_template, request
import sqlite3
import plotly
import plotly.graph_objs as go
import matplotlib.pyplot as plt

app = Flask(__name__)
DATABASE = "scraped_data.db"


def get_categories():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Category")
    categories = cursor.fetchall()
    conn.close()
    return categories


def get_subcategories(category_id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Subcategory WHERE category_id = ?", (category_id,))
    subcategories = cursor.fetchall()
    conn.close()
    return subcategories


def get_products(subcategory_id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Product WHERE subcategory_id = ?", (subcategory_id,))
    products = cursor.fetchall()
    conn.close()
    return products


def get_short_term_prices(product_id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ShortTermPrice WHERE product_id = ?", (product_id,))
    short_term_prices = cursor.fetchall()
    conn.close()
    return short_term_prices


@app.route("/")
def index():
    categories = get_categories()
    return render_template("index.html", categories=categories)


@app.route("/subcategories")
def subcategories():
    category_id = request.args.get("category_id")
    subcategories = get_subcategories(category_id)
    return render_template("subcategories.html", subcategories=subcategories)


@app.route("/products")
def products():
    subcategory_id = request.args.get("subcategory_id")
    products = get_products(subcategory_id)
    return render_template("products.html", products=products)


@app.route("/short_term_prices")
def short_term_prices():
    product_id = request.args.get("product_id")
    short_term_prices = get_short_term_prices(product_id)

    # Extract dates and prices from the short term prices
    dates = [price[3] for price in short_term_prices]
    prices = [price[2] for price in short_term_prices]

    # Create a plot using Plotly
    plot_data = go.Scatter(x=dates, y=prices, mode="lines", name="Price")

    layout = go.Layout(
        title="Short Term Prices", xaxis=dict(title="Date"), yaxis=dict(title="Price")
    )

    figure = go.Figure(data=[plot_data], layout=layout)

    # Convert the plot figure to JSON for rendering in the template
    plot_json = plotly.io.to_json(figure)

    return render_template(
        "short_term_prices.html",
        short_term_prices=short_term_prices,
        plot_json=plot_json,
    )


if __name__ == "__main__":
    app.run()
