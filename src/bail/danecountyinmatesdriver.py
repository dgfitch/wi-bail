import time
import itertools
import re
from datetime import date, timedelta

import click
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException, WebDriverException, UnexpectedAlertPresentException, ElementClickInterceptedException
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
        click.echo(f"Loading inmate details from {url}")
        self.load_url(url)

        tables = self.driver.find_elements_by_xpath('//div[contains(@class,"col-sm-12")]/table')
        if len(tables) == 0:
            return None
        detail = tables[0]
        arrest_info = tables[1:]
        cases = []
        case_urls = []
        arrests = []

        for arrest in arrest_info:
            header = arrest.find_elements_by_xpath("./tbody/tr/td")
            detail_rows = arrest.find_elements_by_xpath("./tbody//div//tr")[1:]
            detail_cells = [row.find_elements_by_xpath(".//td") for row in detail_rows]
            def find_url(e):
                links = e.find_elements_by_xpath(".//a")
                if links:
                    return links[0].get_attribute('href')
                return None

            details = [{
                'offense': d[0].text,
                'date': d[1].text,
                'disposition_date': d[2].text,
                'court_case_number': d[3].text,
                'court_case_url': find_url(d[3]),
                'entry_code': d[4].text,
                } for d in detail_cells]

            arrests.append({
                'date': header[0].text,
                'agency': header[1].text,
                'arrest_number': header[2].text,
                'agency_case_number': header[3].text,
                'details': details,
                })

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
            'arrests': arrests,
        }

    def inmates(self):
        url = f"https://danesheriff.com/Inmates"
        self.load_url(url)
        done = False
        inmate_urls = []

        # They changed it so some slow Javascript makes the select box show up
        time.sleep(5)
        select = Select(self.driver.find_element_by_xpath("//select"))
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
            # Disabling it is slower than it used to be
            time.sleep(2)
            keep_going = "disabled" not in next_button.get_attribute("class")
            if keep_going:
                try:
                    print(f"Loading next page...")
                    next_button.click()
                    time.sleep(1)
                except (WebDriverException, ElementClickInterceptedException) as e:
                    print(f"Error clicking next, assuming we are done")
                    done = True
            else:
                print(f"Loading complete!")
                done = True

        return inmate_urls

    def close(self):
        self.driver.close()
