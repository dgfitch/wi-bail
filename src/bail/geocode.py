from pony.orm import *
import geocoder
import requests
import json

from .db import DB, Case, GeocodedAddress

class Geocode():
    def process(self, x, session):
        if not x or x == "":
            return None
        existing = GeocodedAddress.select(lambda a: x == a.address)
        if existing:
            print(f"{x}: existing!")
        else:
            g = geocoder.osm(x, session=session)
            if g.ok:
                GeocodedAddress(
                    address=x,
                    latitude=g.latlng[0],
                    longitude=g.latlng[1],
                )
                flush()
                print(f"{x}: {g.latlng}")

    def geocode(self):
        with requests.Session() as session:
            for c in Case.select():
                self.process(c.address, session)
        self.save()

    def load(self):
        reading = open("./geocode.json", "r") 
        json.load(reading)

    def save(self):
        addresses = [{'address': a.address, 'longitude': a.longitude, 'latitude': a.latitude} for a in GeocodedAddress.select()]
        out_file = open("./geocode.json", "w") 
        json.dump(addresses, out_file)

