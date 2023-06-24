import requests
import sqlite3
import re
from bs4 import BeautifulSoup


# Function to create the database and tables
def create_database():
    conn = sqlite3.connect("scraped_data.db")
    c = conn.cursor()

    # Create Category table
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS Category (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT
        )
    """
    )

    # Create Subcategory table
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS Subcategory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER,
            name TEXT,
            url TEXT,
            FOREIGN KEY (category_id) REFERENCES Category(id)
        )
    """
    )

    # Create Product table
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS Product (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            url TEXT,
            subcategory_id INTEGER,
            FOREIGN KEY (subcategory_id) REFERENCES Subcategory(id)
        )
    """
    )

    # Create ShortTermPrice table
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS ShortTermPrice (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            price TEXT,
            date TEXT,
            FOREIGN KEY (product_id) REFERENCES Product(id)
        )
    """
    )

    conn.commit()
    conn.close()


def scrape_data(url, base_url, headers):
    # Retrieve HTML content from the URL
    response = requests.get(url, headers=headers)
    html = response.content

    # Parse the HTML content with BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")

    # Find the unordered list with square bullets
    ul_list = soup.find("ul", attrs={"type": "square"})

    data = []
    if ul_list:
        # Find each list item in the unordered list
        li_list = ul_list.find_all("li")
        for li in li_list:
            # Get the category text and strip any whitespace
            category_text = li.find("a").text.strip()

            # Find all links in the div and create subcategories
            links_div = li.find("div")
            links = re.findall(r'<a href="(.*?)">(.*?)</a>', str(links_div))
            subcategories = [
                (category_text, link[1], base_url + link[0]) for link in links
            ]

            # Add the subcategories to the data list
            data.extend(subcategories)

    return data


def scrape_product_data(url, base_url, headers):
    # Retrieve HTML content from the URL
    response = requests.get(url, headers=headers)
    html = response.content

    # Parse the HTML content with BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")

    data = []
    # Find all tables with the class "prodsview"
    rows = soup.find_all("tr")
    for row in rows:
        th_elements = row.find_all("th", class_="wp-head")
        if len(th_elements) == 2:
            product_name = (
                th_elements[0].text.replace("\xa0", " ")
                + " "
                + th_elements[1].text.replace("\xa0", " ")
            )
            product_url = base_url + th_elements[0].find("a")["href"]
            data.append((product_name, product_url))

    return data


def scrape_product_table(product_data):
    # Dictionary to store product data
    products_data = {}

    for product_name, product_url in product_data:
        response = requests.get(product_url)
        html = response.text
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("div", class_="prodsdataview").find("table")
        rows = table.find_all("tr")
        product_prices = []

        for row in rows:
            cells = row.find_all("td")
            if len(cells) == 4:
                date = cells[0].text.strip()
                price = cells[2].text.strip()
                product_price = {"price": price, "date": date}
                product_prices.append(product_price)

        products_data[product_name] = product_prices

    return products_data


def insert_category(category_name):
    conn = sqlite3.connect("scraped_data.db")
    c = conn.cursor()

    # Check if the category already exists
    c.execute("SELECT id FROM Category WHERE name = ?", (category_name,))
    category_id = c.fetchone()

    # If the category doesn't exist, insert a new record
    if not category_id:
        c.execute("INSERT INTO Category (name) VALUES (?)", (category_name,))
        category_id = c.lastrowid
    else:
        category_id = category_id[0]

    conn.commit()
    conn.close()

    return category_id


def insert_subcategory(category_id, subcategory_name, subcategory_url):
    conn = sqlite3.connect("scraped_data.db")
    c = conn.cursor()

    # Check if the subcategory already exists
    c.execute(
        "SELECT id FROM Subcategory WHERE category_id = ? AND name = ?",
        (category_id, subcategory_name),
    )
    subcategory_id = c.fetchone()

    # If the subcategory doesn't exist, insert a new record
    if not subcategory_id:
        c.execute(
            "INSERT INTO Subcategory (category_id, name, url) VALUES (?, ?, ?)",
            (category_id, subcategory_name, subcategory_url),
        )
        subcategory_id = c.lastrowid
    else:
        subcategory_id = subcategory_id[0]

    conn.commit()
    conn.close()

    return subcategory_id


def insert_product(subcategory_id, product_name, product_url):
    conn = sqlite3.connect("scraped_data.db")
    c = conn.cursor()

    # Check if the product already exists
    c.execute(
        "SELECT id FROM Product WHERE subcategory_id = ? AND name = ?",
        (subcategory_id, product_name),
    )
    product_id = c.fetchone()

    # If the product doesn't exist, insert a new record
    if not product_id:
        c.execute(
            "INSERT INTO Product (subcategory_id, name, url) VALUES (?, ?, ?)",
            (subcategory_id, product_name, product_url),
        )
        product_id = c.lastrowid
    else:
        product_id = product_id[0]

    conn.commit()
    conn.close()

    return product_id


def insert_short_term_price(product_id, price, date):
    conn = sqlite3.connect("scraped_data.db")
    c = conn.cursor()

    # Check if the short term price already exists
    c.execute(
        "SELECT id FROM ShortTermPrice WHERE product_id = ? AND price = ? AND date = ?",
        (product_id, price, date),
    )
    short_term_price_id = c.fetchone()

    # If the short term price doesn't exist, insert a new record
    if not short_term_price_id:
        c.execute(
            "INSERT INTO ShortTermPrice (product_id, price, date) VALUES (?, ?, ?)",
            (product_id, price, date),
        )

    conn.commit()
    conn.close()


# Create the database and tables
create_database()

# Example usage
url = "https://index.minfin.com.ua/ua/markets/wares/prods/"
base_url = "https://index.minfin.com.ua/ua/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/",
}

data = scrape_data(url, base_url, headers)

for category_name, subcategory_name, subcategory_url in data:
    # Insert category and get the category_id
    category_id = insert_category(category_name)

    # Insert subcategory and get the subcategory_id
    subcategory_id = insert_subcategory(category_id, subcategory_name, subcategory_url)

    # Scrape product data for the subcategory URL
    product_data = scrape_product_data(subcategory_url, base_url, headers)

    for product_name, product_url in product_data:
        # Insert product and get the product_id
        product_id = insert_product(subcategory_id, product_name, product_url)

        # Scrape and insert short term prices for the product URL
        product_prices = scrape_product_table([(product_name, product_url)])
        for price_data in product_prices.get(product_name, []):
            insert_short_term_price(product_id, price_data["price"], price_data["date"])
