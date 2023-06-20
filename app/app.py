from flask import Flask, render_template, request
import sqlite3

app = Flask(__name__)

DATABASE = "your_database.db"  # Укажите имя вашей базы данных SQLite


def get_database_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def index():
    conn = get_database_connection()
    cursor = conn.cursor()

    # Получаем список категорий товаров
    cursor.execute("SELECT id, name FROM Category")
    categories = cursor.fetchall()

    selected_category_id = request.args.get("category_id")
    selected_place_id = request.args.get("place_id")

    if selected_category_id:
        # Получаем данные о продуктах и ценах для выбранной категории и сети продуктов
        query = """
            SELECT pr.name AS product_name, c.name AS category_name, pp.price, pp.date
            FROM ProductPrice pp
            JOIN Product pr ON pp.product_id = pr.id
            JOIN Category c ON pr.category_id = c.id
        """
        params = []

        if selected_category_id != "":
            query += "WHERE pr.category_id = ? "
            params.append(selected_category_id)

        if selected_place_id != "":
            if selected_category_id != "":
                query += "AND pp.place_id = ? "
            else:
                query += "WHERE pp.place_id = ? "
            params.append(selected_place_id)

        query += "ORDER BY pp.price ASC"

        cursor.execute(query, params)
        rows = cursor.fetchall()
    else:
        rows = []

    # Получаем список сетей продуктов
    cursor.execute("SELECT id, name FROM Place")
    places = cursor.fetchall()

    conn.close()

    return render_template(
        "index.html",
        categories=categories,
        rows=rows,
        places=places,
        selected_category_id=selected_category_id,
        selected_place_id=selected_place_id,
    )


if __name__ == "__main__":
    app.run()
