from pony.orm import *
import geocoder
import requests
import json
from pony.orm import *

from .db import DB, Case
from .counties import Counties, FIPS

class Geocode():
    def __init__(self, db):
        self.db = db

    def process(self, x, session):
        if not x or x == "":
            return None

        if x.fips == None:
            x.fips = FIPS[x.county_number]

        if x.county_name == None:
            x.county_name = Counties[x.county_number]

        existing = Case.select(lambda c: c.address == x.address and c.latitude != None and c.longitude != None)

        if existing:
            print(f"{x}: existing!")
            x.latitude = existing[0].latitude
            x.longitude = existing[0].longitude
        else:
            g = geocoder.osm(x, session=session)
            if g.ok:
                x.latitude = g.latlng[0]
                x.longitude = g.latlng[1]
                print(f"{x.address}: {g.latlng}")
        flush()

    @db_session
    def geocode(self):
        with requests.Session() as session:
            for c in Case.select(lambda c: c.latitude == None and c.longitude == None).order_by(lambda c: c.id):
                self.process(c, session)
        self.save()

    def load(self):
        reading = open("./geocode.json", "r") 
        json.load(reading)
        # TODO

    def save(self):
        addresses = [{'address': c.address, 'longitude': c.longitude, 'latitude': c.latitude} for c in Case.select(c.latitude != None and longitude != None)]
        out_file = open("./geocode.json", "w") 
        json.dump(addresses, out_file)

