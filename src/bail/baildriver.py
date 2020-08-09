import time
import itertools
from datetime import date, timedelta

import click
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
import geckodriver_autoinstaller

class BailDriver:
    def __init__(self):
        geckodriver_autoinstaller.install()

        self.driver = webdriver.Firefox()
        self.driver.implicitly_wait(10)

    def test(self):
        self.driver.get("http://www.python.org")
        assert "Python" in self.driver.title
        return self.driver.title

    def get_charges(self):
        header = self.driver.find_element_by_xpath(f'//h4[text()="Charges"]')
        table = header.parent.find_element_by_tag_name("table")
        charges = table.find_elements_by_tag_name("tr")

        # First row is the header
        charges.pop()

        for charge in charges:
            details = charge.find_elements_by_tag_name("td")
            count_number = details[0].text
            statute = details[1].text
            description = details[2].text
            severity = details[3].text
            disposition = details[4].text
            yield (count_number, statute, description, severity, disposition)

    def get_dd(self, dt):
        """Given the definition title, find the following value"""
        # TODO: error trapping in here if we don't find this element?
        # Right now the outer loop captures
        click.echo("Looking for " + dt)
        dd = self.driver.find_element_by_xpath(f'//dt[text()="{dt}"]/following-sibling::dd')
        return dd.text

    def case_details(self, case_number, county_number):
        url = f"https://wcca.wicourts.gov/caseDetail.html?caseNo={case_number}&countyNo={county_number}&mode=details"
        self.driver.get(url)

        trying = True
        while trying:
            try:
                click.echo(f"Case loaded, trying to fetch...")
                defendant_dob = self.get_dd("Defendant date of birth")
                address = self.get_dd("Address")
                da_number = self.get_dd("DA case number")
                case_type = self.get_dd("Case type")
                filing_date = self.get_dd("Case type")
                sex = self.get_dd("Sex")
                # TODO: Since this dd has a Span with a dumb icon at the end, how to find with xpath?
                # Probably special case and cheese it?
                # race = self.get_dd("Race")

                trying = False

            except NoSuchElementException:
                click.echo(f"Suspected captcha, waiting...")
                # TODO: Force the geckodriver window to take focus somehow?
                time.sleep(5)
            except:
                raise

        return defendant_dob

    def date_format(self, date):
        return date.strftime("%m-%d-%Y")

    def calendar_cases(self, county_number, date):
        date1 = self.date_format(date - timedelta(days = 6))
        date2 = self.date_format(date)
        url = f"https://wcca.wicourts.gov/courtOfficialCalendarReport.html?countyNo={county_number}&dateRange.start={date1}&dateRange.end={date2}&isCourtCal=true"
        self.driver.get(url)

        cases = self.driver.find_elements_by_class_name("case-link")
        return [c.text for c in cases]

    def weeks_past_year(self):
	start = date.today()
	d = start
	while (start - d).days < 365:
	    yield d
	    d -= timedelta(days = 7)

    def cases_for_dates(self, dates):
        cases = [calendar_cases(d) for d in dates]
        # Flatten it out and limit to unique
        return set(itertools.chain.from_iterable(cases))

    def cases_for_month(self, county_number):
        four_weeks = itertools.islice(self.weeks_past_year(), 4)
        return cases_for_dates(four_weeks)

    def cases_for_year(self, county_number):
        past_year = self.weeks_past_year()
        return cases_for_dates(past_year)

    def close(self):
        self.driver.close()
