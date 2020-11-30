import time
import itertools
import re
from datetime import date, timedelta

import click
from selenium import webdriver
from selenium.webdriver.support.ui import Select
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

    def find_td(self, thing, text):
        try:
            td = thing.find_element_by_xpath(f'//td[text()="{text}"]/following-sibling::td')
            return td.text
        except NoSuchElementException:
            return None

    def inmate_details(self, url):
        self.load_url(url)

        tables = self.driver.find_elements_by_xpath("//table")
        detail = tables[0]
        arrest_info = tables[1]
        cases = []
        case_urls = []

        # TODO: Full arrest information rows, not just cases
        # columns: Offense, Date/Time, Disposition Date, Court Case Number, Entry Code
        for link in arrest_info.find_elements_by_xpath(".//a"):
            cases.append(link.text)
            case_urls.append(link.get_attribute('href'))

        return {
            'url': url,
            'name': self.find_td(detail, "Name"),
            'status': self.find_td(detail, "Status"),
            'building': self.find_td(detail, "Building"),
            'area': self.find_td(detail, "Area"),
            'scheduled_release': self.find_td(detail, "Scheduled Release"),
            'booking_number': self.find_td(detail, "Booking Number"),
            'booking_date': self.find_td(detail, "Booking Date"),
            'name_number': self.find_td(detail, "Name Number"),
            'cases': cases,
            'cases': case_urls,
        }

    def inmates(self):
        url = f"https://danesheriff.com/Inmates"
        self.load_url(url)
        done = False
        inmate_urls = []
        select = Select(self.driver.find_element_by_xpath('//select'))
        select.select_by_value('100')
        iteration = 0

        while not done:
            iteration += 1
            rows = self.driver.find_elements_by_xpath("//table[@id='tblInmates']//tr")
            for x in rows:
                if x.text.startswith("Name"):
                    continue
                link = x.find_element_by_link_text('Detail')
                url = link.get_attribute('href')
                inmate_urls.append(url)
            next_button = self.driver.find_element_by_link_text('Next')
            # It would be too easy to use the web standards to enable or disable buttons
            # keep_going = next_button.is_enabled()
            # So we have to check class
            keep_going = "disabled" not in next_button.get_attribute("class")
            if keep_going:
                next_button.click()
                print(f"Loading next page...")
                time.sleep(1)
            else:
                print(f"Loading complete!")
                done = True

        return inmate_urls

    def close(self):
        self.driver.close()
