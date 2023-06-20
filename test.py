import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re
import sqlite3
from datetime import datetime


async def scrape_data(url, base_url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/",
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            html = await response.text()

            soup = BeautifulSoup(html, "html.parser")
            ul_list = soup.find("ul", attrs={"type": "square"})

            conn = sqlite3.connect(
                "your_database.db"
            )  # Replace with your desired database name
            cursor = conn.cursor()

            create_tables(cursor)

            data = {}
            if ul_list:
                li_list = ul_list.find_all("li")
                for li in li_list:
                    category_text = li.find("a").text.strip()
                    category_id = get_or_insert_category(cursor, category_text)

                    links_div = li.find("div")
                    links = re.findall(r'<a href="(.*?)">(.*?)</a>', str(links_div))
                    subcategories = [(link[1], base_url + link[0]) for link in links]

                    subcategory_data = {}
                    for subcategory in subcategories:
                        subcategory_name, subcategory_url = subcategory
                        subcategory_html = await session.get(
                            subcategory_url, headers=headers
                        )
                        subcategory_soup = BeautifulSoup(
                            await subcategory_html.text(), "html.parser"
                        )
                        table = subcategory_soup.find("div", class_="prodsview")
                        if table:
                            rows = table.find_all("tr")
                            if len(rows) > 1:
                                products = {}
                                for row in rows[1:-1]:
                                    columns = row.find_all("td")
                                    if len(columns) > 1:
                                        store = columns[0].text.strip()
                                        price = columns[1].find("big").text.strip()
                                        price_decimal = float(
                                            re.sub(r"[^0-9.,]+", "", price).replace(
                                                ",", "."
                                            )
                                        )
                                        place_id = get_or_insert_place(cursor, store)
                                        product_id = get_or_insert_product(
                                            cursor, subcategory_name, category_id
                                        )
                                        cursor.execute(
                                            """
                                            INSERT INTO ProductPrice (product_id, place_id, price, date) VALUES (?, ?, ?, ?)
                                        """,
                                            (
                                                product_id,
                                                place_id,
                                                price_decimal,
                                                datetime.now(),
                                            ),
                                        )
                                        products[store] = price_decimal
                                subcategory_data[subcategory_name] = {
                                    "products": products,
                                }

                    data[category_text] = subcategory_data

            conn.commit()
            conn.close()

            return data


def create_tables(cursor):
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS Category (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS Product (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE,
            category_id INTEGER,
            FOREIGN KEY (category_id) REFERENCES Category (id)
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS Place (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS ProductPrice (
            id INTEGER PRIMARY KEY,
            product_id INTEGER,
            place_id INTEGER,
            price REAL,
            date DATETIME,
            FOREIGN KEY (product_id) REFERENCES Product (id),
            FOREIGN KEY (place_id) REFERENCES Place (id)
        )
    """
    )


def get_or_insert_category(cursor, name):
    cursor.execute(
        """
        SELECT id FROM Category WHERE name = ?
    """,
        (name,),
    )
    category_id = cursor.fetchone()
    if category_id is None:
        cursor.execute(
            """
            INSERT INTO Category (name) VALUES (?)
        """,
            (name,),
        )
        category_id = cursor.lastrowid
    else:
        category_id = category_id[0]
    return category_id


def get_or_insert_product(cursor, name, category_id):
    cursor.execute(
        """
        SELECT id FROM Product WHERE name = ?
    """,
        (name,),
    )
    product_id = cursor.fetchone()
    if product_id is None:
        cursor.execute(
            """
            INSERT INTO Product (name, category_id) VALUES (?, ?)
        """,
            (name, category_id),
        )
        product_id = cursor.lastrowid
    else:
        product_id = product_id[0]
    return product_id


def get_or_insert_place(cursor, name):
    cursor.execute(
        """
        SELECT id FROM Place WHERE name = ?
    """,
        (name,),
    )
    place_id = cursor.fetchone()
    if place_id is None:
        cursor.execute(
            """
            INSERT INTO Place (name) VALUES (?)
        """,
            (name,),
        )
        place_id = cursor.lastrowid
    else:
        place_id = place_id[0]
    return place_id


async def main():
    url = "https://index.minfin.com.ua/ua/markets/wares/prods/"  # Replace with the actual URL
    base_url = "https://index.minfin.com.ua/ua/"  # Replace with the base URL
    data = await scrape_data(url, base_url)
    print(data)  # You can do further processing or printing of the scraped data here


if __name__ == "__main__":
    asyncio.run(main())
