import math

import unittest

from fastapi import FastAPI, HTTPException

class Test(unittest.TestCase):
	def test_read_file(self):
		self.assertIn("8000105;FF;de:06412:10;Frankfurt(Main)Hbf;FV;8,663789;50,107145;DB Station und Service AG;1866;", read_file("D_Bahnhof_2020_alle.CSV"))
		self.assertIn("8011160;BLS;de:11000:900003201;Berlin Hbf;FV;13,369545;52,525592;DB Station und Service AG;1071;", read_file("D_Bahnhof_2020_alle.CSV"))

	def test_read_table(self):
		self.assertEqual(
			read_table(["Verkehr;DS100;Status", "FV;Test Station;", "RV;Kein Fernverkehr;", ""]), 
			{"Test Station": {"Verkehr": "FV", "DS100": "Test Station", "Status": ""}}
			)

	def test_distance(self):
		self.assertEqual(distance(8.663789, 50.107145, 13.369545, 52.525592), 423)

	def test_main(self):
		self.assertEqual(
			main(
				"FF", "BLS", 
				{
					"FF": {"NAME": "Frankfurt(Main)Hbf", "Laenge": "8,663789", "Breite": "50,107145"}, 
					"BLS": {"NAME": "Berlin Hbf", "Laenge": "13,369545", "Breite": "52,525592"}
				}
			), 
			{"from": "Frankfurt(Main)Hbf", "to": "Berlin Hbf", "distance": 423, "unit": "km"}
			)


def read_file(filename):
	'''parse the table out of a given file to a list of lines'''
	try:
		with open(filename) as file:
			lines = file.read().split("\n")
	except:
		HTTPException(status_code = 400, detail = "Could not load data-file: {}".format(filename))

	return lines


def read_table(lines):
	'''convert a list of lines to a two dimensional dictionary'''

	table = {}

	# the elements of the first line are saved as headlines to be used as keys
	headlines = lines[0].split(";")
	count_col = len(headlines)
	
	# read the data 
	for x in lines[1:]:
		if not x:
			continue
			
		ele = {}
		line = x.split(";")
		for i in range(count_col):
			ele[headlines[i]] = line[i]
			
		# check if station is far distance station
		if ele["Verkehr"] == "FV":
			# using the short hand as key in the dictionary
			table[ele["DS100"]] = ele
		
	return table


def distance(longitude_from, latitude_from, longitude_to, latitude_to):
	'''calculate the distance between two coordinates in km'''

	radius_earth = 6371
	# calculates the length of the circle of latitude of the average latitude in km
	# to later know how long the distance between two longitude is 
	circumference_latitude = 2 * math.pi * radius_earth * math.cos(math.radians((latitude_from + latitude_to) / 2))

	# calculates the differences and converts them to km
	diff_longitude = (longitude_from - longitude_to) * (circumference_latitude / 360) # (circumference_latitude / 360) is the distance between two longitudes at a given latitude in km
	diff_latitude  = (latitude_from - latitude_to) * 111.1324 # 111.1324 is the distance between two longitudes in km

	# Pythagoras to calculate the distance between the stations rounded to km
	return int(math.sqrt(diff_longitude**2 + diff_latitude**2))


def main(ds_from, ds_to, table):
	'''take the input stations and the parsed table, 
output a dictionary with the values: from, to, distance, unit'''

	# getting all infos for the input stations from the table
	try:
		station_from = table[ds_from]
	except:
		raise HTTPException(status_code = 400, detail = "Could not find station: {}".format(ds_from))
		
	try:
		station_to   = table[ds_to]
	except:
		raise HTTPException(status_code = 400, detail = "Could not find station: {}".format(ds_to))
		
	# create the output
	dic = {}

	dic["from"]     = station_from["NAME"]
	dic["to"]       = station_to["NAME"]
	dic["distance"] = distance(
		float(station_from["Laenge"].replace(",", ".")), 
				float(station_from["Breite"].replace(",", ".")),
		float(station_to["Laenge"].replace(",", ".")),
				float(station_to["Breite"].replace(",", ".")),
		)
	dic["unit"]     = "km"

	return dic

table = read_table(read_file("D_Bahnhof_2020_alle.CSV"))

app = FastAPI()
@app.get("/api/v1/distance/{start}/{destination}")

async def read_input(start, destination):
	return main(start, destination, table)
