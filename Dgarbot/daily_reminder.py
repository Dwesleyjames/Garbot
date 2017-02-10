'''

daily_reminder.py

Software that sends a message specific for the day

Hunts through the list, checks the day and sends a message if they requested a reminder
Also double checks if the input is valid

Date format:
user id, current state, city, address, week type, pickup day, reminder setting

'''
import requests
import datetime
import csv
import guelph_garbage_api
import json

def send_daily_reminder():
	to_send = get_daily_reminder_list()
	current_day = datetime.date.today()
	tomorrow = current_day + datetime.timedelta(days=1)
	week_a_type = guelph_garbage_api.garbage_type("Week A",tomorrow)
	week_b_type = guelph_garbage_api.garbage_type("Week B",tomorrow)

	for user in to_send:
		msg = ""
		if user[4] == "Week A":
			msg = msg + "Garbot here reminding you that you should put out your ORGANICS and " + week_a_type.upper() + " tonight or tomorrow morning!"

		else:
			msg = msg + "Garbot here reminding you that you should put out your ORGANICS and " + week_b_type.upper() + " tonight or tomorrow morning!"

		print user[0] + " " + msg

		if user[0][0:3] == "fb_":
			send_message(user[0],msg)
		elif user[0][0:3] == "sm_":
			print "Cellphone"


def get_daily_reminder_list():
	user_state_list = []
	to_send = []

	with open("databases/user_state_db.csv") as csvfile:
		readCSV = csv.reader(csvfile, delimiter=',')

		for row in readCSV:
			user_state_list.append(row)

	#print user_state_list
	current_day = datetime.date.today()
	tomorrow = current_day + datetime.timedelta(days=1)
	tomorrow_string = tomorrow.strftime("%A").upper()

	for user in user_state_list:
		if user[5] == tomorrow_string and user[6] == "True":
			to_send.append(user)
			#print user[5]
	
	return to_send

#Send routine from online
def send_message(recipient_id, message_text):

	recipient_id_mod = recipient_id[3:]
	params = {
		"access_token": "EAAJbyoMPh9MBAAZCzAfP2gHIESG8DPo8hlMoez9hmgtr5iYAiZAGNo2C23QQVFg6yYCnPvP6pgmSfYyZARSXt4xrPfaY4rEyBC2vPFiie6LZAYTdI1ZANcmsrTpaQfpHdqMZBByJmfZBB8kZCydVDFr5BDse8HhGZAnyJEMgunCGeNgZDZD"
	}
	headers = {
		"Content-Type": "application/json"
	}
	data = json.dumps({
		"recipient": {
			"id": recipient_id_mod
		},
		"message": {
			"text": message_text
		}
	})
	#print data
	#print message_text
	r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)

def send_all():
	to_send = get_all()
	current_day = datetime.date.today()
	tomorrow = current_day + datetime.timedelta(days=1)
	week_a_type = guelph_garbage_api.garbage_type("Week A",tomorrow)
	week_b_type = guelph_garbage_api.garbage_type("Week B",tomorrow)

	for user in to_send:
		msg = ""
		if user[4] == "Week A":
			msg = msg + "Garbot here reminding you that you should put out your ORGANIC and " + week_a_type.upper() + " tonight or tomorrow morning!"

		else:
			msg = msg + "Garbot here reminding you that you should put out your ORGANIC and " + week_b_type.upper() + " tonight or tomorrow morning!"

		print msg

		if user[0][0:3] == "fb_":
			send_message(user[0],msg)
		elif user[0][0:3] == "sm_":
			print "Cellphone"


def get_all():
	user_state_list = []
	to_send = []

	with open("databases/user_state_db.csv") as csvfile:
		readCSV = csv.reader(csvfile, delimiter=',')

		for row in readCSV:
			user_state_list.append(row)
		
	return user_state_list


