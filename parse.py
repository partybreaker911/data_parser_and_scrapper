import sqlite3
import os
import re
import requests
from bs4 import BeautifulSoup


def scrape_data(url, base_url):
    # Set headers to mimic a web browser
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/",
    }

    # Retrieve HTML content from the URL
    response = requests.get(url, headers=headers)
    html = response.content

    # Parse the HTML content with BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")

    # Find the unordered list with square bullets
    ul_list = soup.find("ul", attrs={"type": "square"})

    data = {}
    if ul_list:
        # Find each list item in the unordered list
        li_list = ul_list.find_all("li")
        for li in li_list:
            # Get the category text and strip any whitespace
            category_text = li.find("a").text.strip()

            # Find all links in the div and create subcategories
            links_div = li.find("div")
            links = re.findall(r'<a href="(.*?)">(.*?)</a>', str(links_div))
            subcategories = [(link[1], base_url + link[0]) for link in links]

            # Add the category and subcategories to the data dictionary
            data[category_text] = subcategories

    return data


def scrape_svg(url, base_url, filename):
    response = requests.get(url)
    html = response.content

    soup = BeautifulSoup(html, "html.parser")
    div_element = soup.find("div", class_="svg-graph")

    if div_element:
        object_element = div_element.find("object")
        if object_element and object_element.has_attr("data"):
            svg_url = object_element["data"]
            svg_response = requests.get(base_url + svg_url)
            svg_content = svg_response.content

            # Create the 'svg' directory if it doesn't exist
            if not os.path.exists("svg"):
                os.makedirs("svg")

            # Save the SVG file in the 'svg' directory
            svg_path = os.path.join("svg", filename)
            with open(svg_path, "wb") as file:
                file.write(svg_content)

            print(f"SVG graph saved to {svg_path}")
        else:
            print("SVG graph URL not found in object element")
    else:
        print("SVG graph div element not found")


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
        """CREATE TABLE IF NOT EXISTS Subcategories (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        subcategory TEXT NOT NULL,
                        url TEXT NOT NULL,
                        svg_filename TEXT,
                        category_id INTEGER,
                        FOREIGN KEY (category_id) REFERENCES Category (id)
                    )"""
    )
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS Products (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        product TEXT NOT NULL,
                        url TEXT NOT NULL,
                        subcategory_id INTEGER,
                        FOREIGN KEY (subcategory_id) REFERENCES Subcategories (id)
        )"""
    )
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS MarketPlace(
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL
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
                "INSERT INTO Subcategories (subcategory, url, category_id) VALUES (?, ?, ?)",
                (subcategory, url, category_id),
            )
            subcategory_id = cursor.lastrowid

            # Scrape SVG graph
            filename = f"{category}_{subcategory}_graph.svg"
            scrape_svg(url, base_url, filename)

            # Update Products table with SVG filename
            cursor.execute(
                "UPDATE Subcategories SET svg_filename = ? WHERE id = ?",
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
base_url = "https://index.minfin.com.ua/ua/"
database_name = "mydatabase.db"  # Replace with the desired database name

data = scrape_data(url, base_url)
create_database(data, database_name)
