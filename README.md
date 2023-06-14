# Web Scraping and Database Creation

This script demonstrates web scraping of data from a URL and creating a SQLite database based on the scraped data. It uses the BeautifulSoup library to parse HTML and extract information.

## Installation

1. Clone the repository or download the script files.
2. Install the required dependencies by running the following command:
## Usage

1. Update the `url` variable in the script with the desired URL to scrape data from.
2. Modify the `database_name` variable to set the desired name for the SQLite database.
3. Run the script using the following command:
4. The script will scrape the data from the provided URL, create a SQLite database, and insert the scraped data into the database.
5. SVG graphs will be saved in the current directory with filenames in the format: `{category}_{subcategory}_graph.svg`.

## Dependencies

- requests: For making HTTP requests to retrieve web page content.
- beautifulsoup4: For parsing HTML and extracting information from the web page.

## License

This script is licensed under the [MIT License](LICENSE).