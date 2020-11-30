import time
import itertools
import re
from datetime import date, timedelta

import click
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, WebDriverException, UnexpectedAlertPresentException
import geckodriver_autoinstaller


class DaneCountyInmatesDriver:
    def __init__(self):
        geckodriver_autoinstaller.install()

        self.driver = webdriver.Firefox()
        # Don't do any implicit waiting now
        self.driver.implicitly_wait(0)

    def test(self):
        self.driver.get("http://www.python.org")
        assert "Python" in self.driver.title
        return self.driver.title

    def load_url(self, url):
        loaded = False
        while not loaded:
            try:
                self.driver.get(url)
                loaded = True
            except (WebDriverException, UnexpectedAlertPresentException) as e:
                click.echo(f"Error {e} loading url {url}, retrying after 2 seconds...")
                time.sleep(2)

    def inmate_details(self, inmate_url):
        self.load_url(url)

        # TODO: what to grab
        return {
            'url': url,
            'location': 'Unknown',
            'cases': list(self.get_cases()),
        }

    def inmates(self):
        url = f"https://danesheriff.com/Inmates"
        self.load_url(url)
        done = False

        while not done:
            rows = self.driver.find_elements_by_xpath("//table[@id='tblInmates']//tr")
            inmate_urls = []
            for x in rows:
                if x.text.startswith("Name"):
                    continue
                link = x.find_element_by_link_text('Detail')
                url = link.get_attribute('href')
                inmate_urls.append(url)
            next_button = self.driver.find_element_by_link_text('Next')
            return [self.inmate_details(x) for x in inmate_urls]
            if not next_button.get_attribute('enabled'):
                done = True
            else:
                next_button.click()
                time.sleep(1)

        print(inmate_urls)
        return
        return [self.inmate_details(x) for x in inmate_urls]

    def close(self):
        self.driver.close()
