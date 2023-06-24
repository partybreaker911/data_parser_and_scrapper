import requests
import sqlite3
import re
from bs4 import BeautifulSoup


def scrape_data(url, base_url, headers):
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


def scrape_product_data(urls, base_url, headers):
    data = []

    for url in urls:
        response = requests.get(url, headers=headers)
        html = response.content
        soup = BeautifulSoup(html, "html.parser")
        # print(soup)
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


def scrape_product_table(product_urls):
    # Список для хранения данных о продуктах
    products_data = []

    # Перебор ссылок на продукты
    for product_url in product_urls:
        # Выполнение запроса к странице продукта
        response = requests.get(product_url)
        html = response.text

        # Парсинг HTML
        soup = BeautifulSoup(html, "html.parser")

        # Поиск таблицы с данными
        table = soup.find("div", class_="prodsdataview").find("table")

        # Извлечение данных из таблицы
        rows = table.find_all("tr")
        for row in rows:
            # Извлечение данных из ячеек
            cells = row.find_all("td")
            if len(cells) == 4:
                date = cells[0].text.strip()
                price = cells[2].text.strip()

                # Сохранение данных в список словарей
                product_data = {"date": date, "price": price}
                products_data.append(product_data)

    return products_data


# Пример использования функции
url = "https://index.minfin.com.ua/ua/markets/wares/prods/"
base_url = "https://index.minfin.com.ua/ua/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/",
}

data = scrape_data(url, base_url, headers)
sub_urls = []
prod_urls = []
for category, subcategories in data.items():
    for subcategory, subcategory_url in subcategories:
        sub_urls.append(subcategory_url)
for url in sub_urls:
    product_data = scrape_product_data([url], base_url, headers)
for product_name, product_url in product_data:
    prod_urls.append(product_url)
for url in prod_urls:
    scrape_product_table([url])
