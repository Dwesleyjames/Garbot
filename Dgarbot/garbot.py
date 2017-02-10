'''
Core Garbot Routine

Takes input from users and gets the right output back to them
For Garbot the Flask server takes care of all communication with Messenger and SMS


'''
#Python Modules
import requests
import csv
from random import randrange
import re
import datetime
import time

#Custom Modules
import guelph_garbage_api
import User

database_path = 'databases/user_state_db.csv'

def core(message, user_id):
	'''Core routine for Garbot'''
	#Pull User Info
	user = User.User(user_id)
	user.pull(database_path)

	#Hardcode for city of guelph *******************************************
	#indicates first time the program is run
	if user.city == 'first':
		reply_msg = 'Hi, my name is Garbot and I am excited to help you. Before I get started I need to know what city you live in!'
		user.city = 'second'
		user.push(database_path)
		return reply_msg

	#City selection, if it's not guelph, though shall not pass
	if user.city == 'second':
		if 'guelph' in message.lower():
			user.city = 'guelph'
			user.push(database_path)
			reply_msg = 'Great! Now what can I do for you?'
			return reply_msg

		else:
			reply_msg = 'Sorry I do not yet support ' + message.upper() + '. Please re-enter another city or I will let you know when I support your city.'
			return reply_msg

	#Natural language flow section begins ************************************

	#Check input routine for special flags, NOT YET IMPLEMENTED
	#Should have something so that if a user enters a thread and says something like actually cancel that or forget it it removes from the thread
	flags = check_flags(message, user)

	#Switch to city_selection, intent or thread
	#if no current intent then update intent and set lvl to 0, just a note but intent should include all chit chat also
	if user.thread == '?':
		user, reply_msg = get_intent(message, user)
	
	#if there is an intent and lvl is not 0 run thread
	#user should be updated with the next state
	#user, reply_msg = thread(user)

	#Threads navigated with user.thread which is the thread and user.lvl which is the lvl of depth within each thread
	if user.thread != '?':
		user, reply_msg = thread(message, user)

		
	#Check for end of thread, if its the end prompt for restart message
	#log everything!

	#push user back
	user.push(database_path)

	return reply_msg


def get_intent(message, user):
	'''Understand intent from user passes back the state the reply message and user state they are going into'''
	confidence_setting = 0.4	#Communication Confidence Setting
	#Get Intent
	confidence, user.thread = parse_intent(message)

	#Luis flagged no confidence
	if user.thread == 'None':
		confidence = 0

	#Call WIT response for specified intent
	if int(user.confusion)==2:
	 	if message == "no" or message =="nah" or message == "no thanks":
	 		reply_msg = "No problem, anything else I can do for you today?"
	 		user.thread = '?'
	 		user.confusion = 0
	 		user.intent = '?'

	 	else:
	 		notify_human(message, user)
	 		reply_msg = "Alright I let them know and they will be getting back to you. In the mean time is there anything else I can do for you?"
	 		user.thread = '?'
	 		user.intent = '?'
	 		user.confusion = 0


	elif confidence < confidence_setting and int(user.confusion)==1:
		reply_msg = "Sorry! I am unable to answer your question. Would you like my supervisor to contact you with an answer?"
		user.confusion = 2	#flag confusion
		state = '02'
		user.thread = '?'
		intent = '?'

	elif confidence < confidence_setting:
		reply_msg = "Hey I am not totally sure what you mean by this!"
		user.confusion = 1	#flag confusion
		state = '01'
		user.thread = '?'

	else:
		user.confusion = 0
		state = '0' #This should actually lookup stuff
		reply_msg = ""

	#System is setup for using ? but LUIS returns None sometimes

	return user, reply_msg



def check_flags(message, user):
	'''Checks for special flags'''
	#Too many mis-understood intents
	#No city flag = 1

	#reset = flag 2

	return 0


def parse_intent(message):
	'''Parses intent, gives back confidence and intent'''

	#Microsoft Intent Parsing
	r = requests.get('https://api.projectoxford.ai/luis/v1/application?' + \
		'id=0d4b035f-3dc6-4088-bc19-b51b880d834a&subscription-key=' + \
		'8b0f634a195147a491e95fe47270f29c&q='+message)

	confidence = r.json()['intents'][0]['score']
	intent = r.json()['intents'][0]['intent']


	print "Confidence: " + str(confidence)
	print "Intent: " + str(intent)

	return confidence, intent


def parse_reminder(message):
	'''Parses to check if there is a reminder'''
	'''********** This should be fused with the parse_intent function somehow *****************'''
	#Sweet Microsoft LUIS upgrade

	try:
		r = requests.get('https://api.projectoxford.ai/luis/v1/application?' + \
		'id=0d4b035f-3dc6-4088-bc19-b51b880d834a&subscription-key=' + \
		'8b0f634a195147a491e95fe47270f29c&q='+message)

		if r.json()['entities'][0]['type'] == "builtin.datetime.time":
			reminder_time = r.json()['entities'][0]['resolution']['time']
			confidence = 1
		else:
			confidence = 0
			reminder_time = "NA"

	except:
		confidence = 0
		reminder_time = "NA"


	print "Confidence: " + str(confidence)
	print "Reminder time: " + str(reminder_time)

	if reminder_time != "NA":
		reminder_hour = reminder_time[1:3]
	else:
		reminder_hour = "NA"

	return confidence, reminder_hour

def thread(message, user):
	'''manages conversations currently in a thread mode'''
	reply_msg = 'you should not see this :('

	if user.thread == 'parents':
		print 'parents routine activated'
		reply_msg = 'My mom was an AI and my father was a Garbage Truck.'
		user.thread = '?'

	elif user.thread == 'pickup_day':
		print 'pickup_day routine activated'
		reply_msg, user = pickup_day(message, user)
	
	#in progress
	elif user.thread == 'stop_reminder':
		print 'stop_reminder routine activated'
		reply_msg = 'I will no longer remind you about your garbage day, is there anything else I can do for you?'
		user.reminder = False
		user.thread = '?'

	#Dual access points as they really mean the same thing
	elif user.thread == 'start_reminder' or user.thread == 'change_reminder_time':
		print 'start_reminder and/or change routine activated'
		#Check that an address is on file, if not re-route to the pickup_day routine
		if user.address == 'first':
			user.thread = 'pickup_day'
			user.confusion = 0
			user.lvl = 0
			reply_msg, user = pickup_day(message, user)
		
		elif user.reminder == 'True' and int(user.reminder_time) != -2:

			if int(user.reminder_time) > 12:
				temp = str(int(user.reminder_time)-12)
				reply_msg = 'You already have a reminder that is set for ' + temp + 'PM. Is there anything else I can do for you?'
			elif int(user.reminder_time) < 12:
				reply_msg = 'You already have a reminder that is set for ' + user.reminder_time + 'AM. Is there anything else I can do for you?'
			else:
				reply_msg = 'You already have a reminder that is set for noon. Is there anything else I can do for you?'

		else:
			reply_msg, user = change_reminder(message, user)


	elif user.thread == 'greeting':
		print 'greeting routine activated'
		greeting_array = ['Hey', 'Hi'] 

		#randomly select one goodbye
		random_index = randrange(0,len(greeting_array))
		reply_msg = greeting_array[random_index] + ', what can I do for you today?'
		user.thread = '?'

	elif user.thread == 'goodbye':
		print 'goodbye routine activated'
		goodbye_array = ['Later!', 'Bye!', 'Catch you soon!', 'Bye Bye!', 'Goodbye', 'Have a good day', 'Have an awesome day'] 

		#randomly select one goodbye
		random_index = randrange(0,len(goodbye_array))
		reply_msg = goodbye_array[random_index]
		user.thread = '?'

	elif user.thread == 'thanks':
		print 'thanks routine activating'
		welcome_array = ['No problem', 'Anytime', 'My pleasure', 'Happy to help', 'Don\'t mention it', 'Always a pleasure']
		#randomly generate a your welcome routine
		random_index = randrange(0,len(welcome_array))
		reply_msg = welcome_array[random_index] + '. Don\'t hesitate to ask anything else.'
		user.thread = '?'

	elif user.thread == 'name':
		print 'name routine activating'
		reply_msg = 'My name is Garbot the Friendly Garbage Bot but you can call my Garbot for short!'
		user.thread = '?'
	
	elif user.thread == 'what_version':
		print 'version routine activatings'
		reply_msg = 'I am Garbot version 2!'
		user.thread = '?'

	elif user.thread == 'garbot_age':
		print 'garbot_age routine activating'
		reply_msg = 'A bot never tells ;)'
		user.thread = '?'

	elif user.thread == 'garbot_live' or user.thread == 'garbot_where':
		print 'garbot_live routine activating'
		reply_msg = 'I live in the cloud. I have a great view!'
		user.thread = '?'

	elif user.thread == 'garbot_single':
		print 'garbot_single routine activating'
		reply_msg = 'Maaaaybe'
		user.thread = '?'

	elif user.thread == 'what_can' or user.thread == 'what_else':
		print 'what_can routine activating'
		reply_msg = 'I can answer questions about when and what garbage should be put out, I can remind you and I ' + \
			'can pass off questions to my human colleagues if I am unable to answer your questions!'
		user.thread = '?'

	elif user.thread == 'negative':
		print 'negative routine activating'
		reply_msg = 'It has been my pleasure helping you, feel free to contact me anytime!'
		user.thread = '?'

	elif user.thread == 'positive':
		print 'positive routine activating'
		reply_msg = 'At your service, what can I do for you?'
		user.thread = '?'

	elif user.thread == 'where_does_x_go':
		print 'where_does_x_go routine activating'
		reply_msg = 'Check here: http://guelphapps.elasticbeanstalk.com/ for ' + \
			'Guelph\'s waste sorting tool. Anything else I can do for you?'
		user.thread = '?'

	elif user.thread == 'forget_me':
		print 'forget_me routine activating'
		reply_msg, user = forget_me(message, user)


	return user, reply_msg

def pickup_day(message, user):
	'''pickup day routine, this controls flow through the pickup day routine'''
	#user id, current state, city, address, week type, pickup day, reminder setting, confusion, thread, lvl

	if user.address != 'first' and int(user.lvl) != 2:
		#reply_msg = 'Your address is set to: ' + user.address + ' which means your garbage day is ' + user.pickup_day.upper() + ' and you are on the ' + user.week_type.upper() + ' schedule.'
		#*****************************************************
		garbage_date, holiday_flag = guelph_garbage_api.next_pickup_date(datetime.date.today(),user.pickup_day)
		garbage_day = garbage_date.strftime("%A")
		garbage_type = guelph_garbage_api.garbage_type(user.week_type,garbage_date)

		#if holiday = true some message, not working yet
		#if today modify garbage_day
		if datetime.date.today().strftime("%A").lower() == garbage_day.lower():
			reply_msg = "Your Garbage day is TODAY, you should, or should have :), put out your ORGANICS and " + \
				garbage_type.upper() + " this morning."
		else:
			reply_msg = "Your upcoming garbage day is " + garbage_day.upper() + " and you should put out ORGANICS and " + \
				garbage_type.upper() + "."
	
		#*****************************************************
		user.thread = '?'
		user.lvl = '0'

	elif int(user.lvl) == 0:
		reply_msg = 'To help you I need your STREET ADDRESS, please enter it now.'
		user.lvl = 1
	
	elif int(user.lvl) == 1:

		#test for valid address
		parsed = re.split(r'(?<=\d)(?:-\d+)?\s+', message)

		#Check that address has two parts and that the first part is a string
		if len(parsed) != 2 or type(parsed[0]) == int:
			
			#Check for previous confusion and exit if they are confused again
			if int(user.confusion) == 1:
				reply_msg = 'Alright there seems to be some confusion, I let my supervisor know and ' + \
					'they will be getting back to you. In the mean time is there anything else I can do for you?'
				notify_human(message, user)
				user.confusion = 0
				user.thread = '?'
				user.lvl = 0
			else:
				reply_msg = 'Sorry I don\'t think this is a valid address! Try re-entering it.'
				user.confusion = 1

		else:
			#Check address in Guelph Database
			pickup_info = guelph_garbage_api.guelph_garbage(parsed[0],parsed[1])

			#If error flag is passed through guelph_garbage function then prompt for re-entry
			if pickup_info[0] == "error":
				reply_msg = "Sorry I can't find your address in my database, I let my supervisor know and they will be getting back to you."
				notify_human(message, user)
				user.confusion = 0
				user.thread = '?'
				user.lvl = 0
			else:
				#This mean the information received back from the garbage day lookup is good so it can be stored
				user.week_type = pickup_info[0]
				user.pickup_day = pickup_info[1]

				user.address = message
				#reply_msg = 'Great that means your garbage day is ' + user.pickup_day.upper() + '. Would you like to set a reminder?'
					

				#Get tailored info ******************************************************************
				garbage_date, holiday_flag = guelph_garbage_api.next_pickup_date(datetime.date.today(),user.pickup_day)
				garbage_day = garbage_date.strftime("%A")
				garbage_type = guelph_garbage_api.garbage_type(user.week_type,garbage_date)

				if datetime.date.today().strftime("%A").lower() == garbage_day.lower():
					reply_msg = "Great this means that your pickup day is "+pickup_info[1]+ " and you are on the " + pickup_info[0] + \
						" schedule. So this morning you should, or should have :), put out your ORGANICS and " + garbage_type.upper() + \
						". Do you want to setup a REMINDER?"
				else:
					reply_msg = "Great this means that your pickup day is "+pickup_info[1]+ " and you are on the " + pickup_info[0] + \
						" schedule. So this upcoming " + pickup_info[1] + " you should put out your ORGANICS and " + garbage_type.upper() + \
						". Do you want to setup a REMINDER?"

				#*****************************************************************************************
				user.lvl = 2 #Move to next step

	elif int(user.lvl) == 2:
		
		#this should be converted to natural language processing
		lower_msg = message.lower()

		if lower_msg == "yes" or lower_msg == "sure" or lower_msg == "yeah" or lower_msg == "okay" or lower_msg == "yes please" or lower_msg == "thanks" or lower_msg == "thank you" or lower_msg == "thanks!":
			#If reminder requested pass directly to change_reminder routine
			#this should work if the user requests a reminder with or without a time
			user.thread = 'start_reminder'
			user.lvl = 0
			user.confusion = 0
			reply_msg, user = change_reminder(message, user)

		#this should be replaced with language processing
		elif lower_msg == "no" or lower_msg =="nah" or lower_msg == "no thanks" or lower_msg == "nope":
			reminder = False
			reply_msg = "Understood, anything else I can do for you?"
			user.reminder = reminder
			user.thread = '?'
			user.lvl = 0
			user.confusion = 0

		else:
			#Check for confusion
			if int(user.confusion) == 1:
				reply_msg = 'Sorry I still don\'t understand if you want a reminder or not, no problem I sent our conversation to my supervisor for clarification. ' + \
					'They will get back to you on this, in the mean time please let me know if there is anything else I can help you with!'
				user.thread = '?'
				user.lvl = 0
				user.confusion = 0

			else:
				reply_msg = 'Sorry I didn\'t understand that, can you try re-entering'
				user.confusion = '1'



	return reply_msg, user

def change_reminder(message, user):
	'''This is when a user request to change their reminder time or want to start a reminder'''
	confidence_setting = 0.75

	#Check if the request included a time
	confidence, reminder_hour = parse_reminder(message)

	if confidence > confidence_setting:
		user.reminder_time = reminder_hour
		user.thread = '?'
		user.lvl = 0

		#check for AM or PM
		if int(user.reminder_time) > 12:
			temp = str(int(user.reminder_time)-12)
			reply_msg = 'A reminder has been set for ' + temp + 'PM. Is there anything else I can do for you?'
		elif int(user.reminder_time) < 12:
			reply_msg = 'A reminder has been set for ' + user.reminder_time + 'AM. Is there anything else I can do for you?'
		else:
			reply_msg = 'A reminder has been set for noon. Is there anything else I can do for you?'

	else:
		if int(user.confusion) == 0:
			reply_msg = 'What time would you like a reminder?'
			user.confusion = 1

		else:
			reply_msg = 'Sorry I didn\'t understand that, I let my supervisor know to look into this, in the mean time is there anything else I can do for you?'
			notify_human(message, user)
			user.confusion = 0
			user.thread = '?'
			user.lvl = 0

	user.reminder = True
	return reply_msg, user

def forget_me(message, user):
	if int(user.lvl) == 0:
		reply_msg = 'Are you totally sure you want me to forget you?'
		user.lvl = 1
	else:
		confidence, intent = parse_intent(message)

		if intent == 'positive':
			reply_msg = 'I have forgotten you.'
			user.current_state = -2
			user.city = 'first'
			user.address = 'first'
			user.week_type = 0
			user.pickup_day = 0
			user.reminder = False
			user.confusion = 0
			user.thread = '?'
			user.lvl = 0
			user.reminder_time = -2

		else:
			reply_msg = 'What a relief!'
			user.thead = '?'
			user.lvl = 0

	return reply_msg, user




def notify_human(message, user):
	'''This is what happens when Garbot lets a human know what has been going on!'''
	'''Currently nothing actually happens, but one day who knows'''
	print 'Listed for human to follow up on'

	human_followup_list = []

	with open('databases/human_followup.csv','rb') as f:
		readCSV = csv.reader(f, delimiter=',')
		for row in readCSV:
			human_followup_list.append(row)

	dummy = [time.time(),message,user.user_id, user.current_state, user.city, user.address,
		user.week_type, user.pickup_day, user.reminder, user.confusion,
		user.thread, user.lvl, user.reminder_time]

	human_followup_list.append(dummy)

	with open('databases/human_followup.csv','wb') as f:
		writeCSV = csv.writer(f)
		writeCSV.writerows(human_followup_list)


