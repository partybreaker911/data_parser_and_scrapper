import re
import requests
import sqlite3
from bs4 import BeautifulSoup


def scrape_data(url):
    # Retrieve data from the URL
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/",
    }
    response = requests.get(url, headers)
    html = response.content

    soup = BeautifulSoup(html, "html.parser")
    ul_element = soup.find("ul", attrs={"type": "square"})

    data = {}
    if ul_element:
        li_elements = ul_element.find_all("li")
        for li in li_elements:
            a_element = li.find("a")
            category = a_element.text.strip()
            links_div = li.find("div")
            links = re.findall(r'<a href="(.*?)">(.*?)</a>', str(links_div))
            subcategories = [(link[1], url + link[0]) for link in links]

            data[category] = subcategories

    return data


def scrape_svg(url, filename):
    response = requests.get(url)
    html = response.content

    soup = BeautifulSoup(html, "html.parser")
    div_element = soup.find("div", class_="svg-graph")

    if div_element:
        svg_code = div_element.prettify()

        with open(filename, "w") as file:
            file.write(svg_code)

        print(f"SVG graph saved to {filename}")
    else:
        print("SVG graph not found")


def create_database(data, database_name):
    # Create SQLite database and tables
    connection = sqlite3.connect(database_name)
    cursor = connection.cursor()

    # Create Category table
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS Category (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        category TEXT NOT NULL
                    )"""
    )

    # Create Products table
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS Products (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        subcategory TEXT NOT NULL,
                        url TEXT NOT NULL,
                        svg_filename TEXT,
                        category_id INTEGER,
                        FOREIGN KEY (category_id) REFERENCES Category (id)
                    )"""
    )

    # Insert data into Category and Products tables
    for category, subcategories in data.items():
        # Insert category into Category table
        cursor.execute("INSERT INTO Category (category) VALUES (?)", (category,))
        category_id = cursor.lastrowid

        # Insert subcategories into Products table
        for subcategory, url in subcategories:
            cursor.execute(
                "INSERT INTO Products (subcategory, url, category_id) VALUES (?, ?, ?)",
                (subcategory, url, category_id),
            )
            subcategory_id = cursor.lastrowid

            # Scrape SVG graph
            filename = f"{category}_{subcategory}_graph.svg"
            scrape_svg(url, filename)

            # Update Products table with SVG filename
            cursor.execute(
                "UPDATE Products SET svg_filename = ? WHERE id = ?",
                (filename, subcategory_id),
            )

    # Commit changes and close connection
    connection.commit()
    connection.close()

    print("Database created and data inserted successfully.")


# Example usage
url = (
    "https://index.minfin.com.ua/ua/markets/wares/prods/"  # Replace with the actual URL
)
database_name = "mydatabase.db"  # Replace with the desired database name

data = scrape_data(url)
create_database(data, database_name)
