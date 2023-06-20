import os
import re
import asyncio
import aiohttp
import sqlite3
from bs4 import BeautifulSoup


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

            data = {}
            if ul_list:
                li_list = ul_list.find_all("li")
                for li in li_list:
                    category_text = li.find("a").text.strip()

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
                                        products[store] = price_decimal
                                        # print(price_decimal)
                                subcategory_data[subcategory_name] = {
                                    "products": products,
                                }

                    data[category_text] = subcategory_data

            return data


async def scrape_svg(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            html = await response.text()

            soup = BeautifulSoup(html, "html.parser")
            div_element = soup.find("div", class_="svg-graph")

            if div_element:
                object_element = div_element.find("object")
                if object_element and object_element.has_attr("data"):
                    svg_url = object_element["data"]
                    async with session.get(svg_url) as svg_response:
                        svg_content = await svg_response.text()

                        svg_soup = BeautifulSoup(svg_content, "html.parser")
                        data_divs = svg_soup.find_all("div", class_="data")

                        for data_div in data_divs:
                            onmouseover_attr = data_div.get("onmouseover")
                            if onmouseover_attr:
                                match = re.search(
                                    r"sh\((\d+),(\d+),(-?\d+),'(.+?)'", onmouseover_attr
                                )
                                if match:
                                    product_id = int(match.group(1))
                                    price = int(match.group(2))
                                    timestamp = match.group(4)

                                    await create_database(product_id, price, timestamp)
                else:
                    print("SVG graph URL not found in object element")
            else:
                print("SVG graph div element not found")


async def create_database(data, database_name, product_id, price, timestamp):
    connection = sqlite3.connect(database_name)
    cursor = connection.cursor()

    cursor.execute(
        """CREATE TABLE IF NOT EXISTS Category (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL
            )"""
    )

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
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS Prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                Product_id INTEGER NOT NULL,
                Price INTEGER NOT NULL,
                Timestamp TEXT NOT NULL
            )"""
    )

    cursor.execute(
        "INSERT INTO Prices (Product_id, Price, Timestamp) VALUES (?, ?, ?)",
        (product_id, price, timestamp),
    )
    for category, subcategories in data.items():
        cursor.execute("INSERT INTO Category (category) VALUES (?)", (category,))
        category_id = cursor.lastrowid

        tasks = []
        for subcategory, url in subcategories:
            cursor.execute(
                "INSERT INTO Subcategories (subcategory, url, category_id) VALUES (?, ?, ?)",
                (subcategory, url, category_id),
            )
            subcategory_id = cursor.lastrowid

            filename = f"{category}_{subcategory}_graph.svg"
            task = asyncio.create_task(scrape_svg(url, base_url, filename))
            tasks.append(task)

        await asyncio.gather(*tasks)

    connection.commit()
    connection.close()

    print("Database created and data inserted successfully.")


# Example usage
url = (
    "https://index.minfin.com.ua/ua/markets/wares/prods/"  # Replace with the actual URL
)
base_url = "https://index.minfin.com.ua/ua/"
database_name = "mydatabase.db"  # Replace with the desired database name


async def main():
    data = await scrape_data(url, base_url)
    print(data)
    # await create_database(data, database_name)


asyncio.run(main())
