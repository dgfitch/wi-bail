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
            if details:
                count_number = details[0].text
                statute = details[1].text
                description = details[2].text
                severity = details[3].text
                disposition = details[4].text
                yield {
                    'count_number': count_number,
                    'statute': statute,
                    'description': description,
                    'severity': severity,
                    'disposition': disposition
                }

    def get_dd(self, dt):
        """Given the definition title, find the following value"""
        # TODO: error trapping in here if we don't find this element?
        # Right now the outer loop captures
        click.echo("Looking for " + dt)
        dd = self.driver.find_element_by_xpath(f'//dt[text()="{dt}"]/following-sibling::dd')
        return dd.text

    def get_race(self):
        """Look up race, which is different than above because the dt has a info icon in a span in it"""
        click.echo("Looking for Race")
        dd = self.driver.find_element_by_xpath(f'//dt/span/following::dd')
        return dd.text

    def get_matching_text(self, string):
        return self.driver.find_elements_by_xpath(f"//*[contains(text(), '{string}')]")

    def get_bail(self, string):
        """Look up bail"""
        click.echo(f"Looking for bail info using '{string}'")
        elements = self.get_matching_text(string)
        return len(elements) > 0

    def case_details(self, case_number, county_number):
        url = f"https://wcca.wicourts.gov/caseDetail.html?caseNo={case_number}&countyNo={county_number}&mode=details"
        self.driver.get(url)

        trying = True
        click.echo(f"Case loaded, trying to fetch...")
        while trying:
            try:
                defendant_dob = self.get_dd("Defendant date of birth")
                address = self.get_dd("Address")
                da_number = self.get_dd("DA case number")
                case_type = self.get_dd("Case type")
                filing_date = self.get_dd("Filing date")
                sex = self.get_dd("Sex")
                race = self.get_race()
                charges = list(self.get_charges())
                signature_bond = self.get_bail("Signature bond set")
                cash_bond = self.get_bail("Cash bond set")
                # TODO: Cash value

                # TODO: Most "recent" bail value?
                # https://wcca.wicourts.gov/caseDetail.html?caseNo=2020CF001514&countyNo=13&mode=details
                # "DE requesting $100 total cash bond. State requesting $400 total cash bond." But the final thing is what the Ct. set

                # TODO: For traffic, pull out "Bond amount" dd if it exists
                # ex: https://wcca.wicourts.gov/caseDetail.html?caseNo=2020TR004755&countyNo=13&mode=details

                trying = False

            except NoSuchElementException:
                find_captcha = self.driver.find_elements_by_id("rc-imageselect")
                if len(find_captcha) > 0:
                    click.confirm('Suspected captcha, continue?')
                else:
                    click.echo(f"Element not found, waiting...")
                    time.sleep(5)
            except:
                raise

        return {
            'defendant_dob': defendant_dob,
            'address': address,
            'da_number': da_number,
            'case_type': case_type,
            'filing_date': filing_date,
            'sex': sex,
            'signature_bond': signature_bond,
            'cash_bond': cash_bond,
            'charges': charges,
        }

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

    def cases_for_dates(self, county_number, dates):
        cases = [self.calendar_cases(county_number, d) for d in dates]
        # Flatten it out and limit to unique
        return set(itertools.chain.from_iterable(cases))

    def cases_for_month(self, county_number):
        four_weeks = itertools.islice(self.weeks_past_year(), 4)
        return self.cases_for_dates(county_number, four_weeks)

    def cases_for_week(self, county_number):
        week = [next(self.weeks_past_year())]
        return self.cases_for_dates(county_number, week)

    def cases_for_year(self, county_number):
        past_year = self.weeks_past_year()
        return self.cases_for_dates(county_number, past_year)

    def close(self):
        self.driver.close()
