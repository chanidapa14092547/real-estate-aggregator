import requests
from bs4 import BeautifulSoup
import time
import csv
import logging

class BaseScraper:
    """Base template for a web scraper handling common scraping tasks."""
    
    def __init__(self, base_url, delay=1.0):
        self.base_url = base_url
        self.delay = delay # Rate limiting
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0'})
        
    def fetch_page(self, url, retries=3):
        """Fetches a page with retry logic and rate limiting."""
        for attempt in range(retries):
            try:
                time.sleep(self.delay)
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                logging.warning(f"Attempt {attempt+1} failed for {url}: {e}")
                time.sleep(self.delay * (attempt + 1))
        logging.error(f"Failed to fetch {url} after {retries} attempts.")
        return None

    def parse_listing(self, html):
        """To be implemented by subclasses to parse specific listing pages."""
        raise NotImplementedError

    def scrape_all(self, start_url, output_file):
        """Main scraping loop."""
        print(f"Starting scrape from {start_url}")
        # In a real scraper, loop through pages
        html = self.fetch_page(start_url)
        if html:
            data = self.parse_listing(html)
            self.save_to_csv([data], output_file)
            
    def save_to_csv(self, data, filename):
        """Saves data to a CSV file."""
        if not data: return
        keys = data[0].keys()
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            dict_writer = csv.DictWriter(f, keys)
            dict_writer.writeheader()
            dict_writer.writerows(data)

class DDPropertyScraper(BaseScraper):
    """Example implementation of a specific site scraper."""
    
    def parse_listing(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        # Dummy parsing logic for illustration
        title_elem = soup.find('h1', class_='listing-title')
        price_elem = soup.find('span', class_='price')
        return {
            'title': title_elem.text if title_elem else 'N/A',
            'price': price_elem.text if price_elem else 'N/A',
            'source': 'DDProperty'
        }
