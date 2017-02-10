'''
Guelph_Garbage.py

Guelph Garbage Lookup Module
This Module is designed to pull from Guelph Garbage Schedule ZOHO Form

Call this function to get it working
weekly_schedule, pickup_day = guelph_garbage(number,street)

type = type_check(Week_Type, next_day)

next_day = next_pickup_day (date, pickup_day)


'''

#Imports
import csv
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
#import urllib2
from BeautifulSoup import BeautifulSoup
import requests
import datetime

#Load Streets
def get_streets():
	with open('guelph_streets.csv', 'rb') as f:
		reader = csv.reader(f)
		streets = list(reader)


	#Compare input to list and return value if >some number


	return(streets)

#Find Match
def match(street):
	streets = get_streets()
	output = process.extractOne(street, streets)
	print output
	return(output[0][0])


#using validated address pull data from Guelph Garbage ZOHO form 
def pull_data(number,street):

	url = 'https://creator.zohopublic.com/webservices/cartlookupforfall2013/view-perma/searchResults/gaT6gejP7DWsrGKPWtTg1MKhkMnpNXxObq4druv9BQZ61VvyTMmZ7fyhkJUPeW7pP7evEaMPQGVSqTq3MZENSP6esQ20CqZtREG3?number=' + number + '&name=' + street
	page = requests.get(url)
	data = BeautifulSoup(page.text)
	return(data)

#input directly from user 
def guelph_garbage(number,street):

	data = pull_data(number,match(street))
	if not data:
		pickup_day = "error"
		weekly_schedule = "error"
	else:
		a = data.findAll("td")
		b = a[0].findAll("td")
		c = b[0].findAll("span")

		pickup_day = c[2].string
		weekly_schedule = c[1].string
		

	return weekly_schedule, pickup_day

#Get the day lookup functions working
#garbage_type = garbage_type_check(Week_Type, next_day)

def garbage_type(week_type,next_day):
	
	iso_date = next_day.isocalendar()
	msg = ""
	#easy check for guelph in 2016
	#for Week A type iso == even then garbage+organic
	#for Week A type iso == odd then recyclable+organic

	if week_type == "Week A":
		if iso_date[1] % 2 == 0:
			msg = "garbage"
		else:
			msg = "recyclables"

	if week_type == "Week B":
		if iso_date[1] % 2 == 0:
			msg = "recyclables"
		else:
			msg = "garbage"

	return msg


#Next pickup day function
#next_date = next_pickup_date (date, pickup_day)
#takes a date and a pickup day and returns the upcoming pickup date, takes into account weekly irregularities
#date should be of type datetime


def next_pickup_date (date, pickup_day):

	iso_day = 0 #temp value
	iso_date = date.isocalendar()

	#tupule to array
	upcoming_iso_date = []
	upcoming_iso_date.extend(iso_date)


	#Transfrom string day to real day
	lower_pickup_day = pickup_day.lower()

	if lower_pickup_day == "monday":
		iso_day = 1
	elif lower_pickup_day == "tuesday":
		iso_day = 2
	elif lower_pickup_day == "wednesday":
		iso_day = 3		
	elif lower_pickup_day == "thursday":
		iso_day = 4
	elif lower_pickup_day == "friday":
		iso_day = 5
	elif lower_pickup_day == "saturday":
		iso_day = 6
	elif lower_pickup_day == "sunday":
		iso_day = 7

	upcoming_iso_date[2] = iso_day #set the day to the person's actual garbage day

	#Check if day has already been passed if so increase the day by a week
	if iso_date[2] > iso_day:
		upcoming_iso_date[1] = upcoming_iso_date[1] + 1

	#check for holiday these are hardcoded and should have a better way figured out
	#Holiday's only occur on mondays or fridays
	#if upcoming holiday monday push all days one to the right
	#if upcoming holiday is a friday it is only relevant for the friday day, not programmed as there are no more for the year

	holiday_mondays = [7,21,31,36,41,52]

	holiday_flag = False
	for holiday in holiday_mondays:
		if upcoming_iso_date[1] == holiday:
			holiday_flag = True

	#change date type back to datetime.date format and return holiday_flag so they know if its a special day
	next_date = iso_to_gregorian(*upcoming_iso_date)
	return next_date, holiday_flag

#taken from stack overflow to concert from iso date time to normal date time usage is *iso
def iso_year_start(iso_year):
	"The gregorian calendar date of the first day of the given ISO year"
	fourth_jan = datetime.date(iso_year, 1, 4)
	delta = datetime.timedelta(fourth_jan.isoweekday()-1)
	return fourth_jan - delta 

def iso_to_gregorian(iso_year, iso_week, iso_day):
	"Gregorian calendar date for the given ISO year, week and day"
	year_start = iso_year_start(iso_year)
	return year_start + datetime.timedelta(days=iso_day-1, weeks=iso_week-1)



