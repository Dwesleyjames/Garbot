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

#Custom Modules
import guelph_garbage_api
import User

database_path = 'user_state_db.csv'

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

	#Check input routine for special flags
	flags = check_flags(message, user)

	#Switch to city_selection, intent or thread
	#if no current intent then update intent and set lvl to 0, just a note but intent should include all chit chat also
	if user.thread == '?':
		user, reply_msg, intent = get_intent(message, user)
	
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


def city_selection():
	'''Works to initially screen for the correct city, this is hardcoded'''
	pass



def get_intent(message, user):
	'''Understand intent from user using WIT passes back the state the reply message and user state they are going into'''
	confidence_setting = 0.75	#Communication Confidence Setting
	#Get Intent
	confidence, intent = parse_intent(message)

	#Call WIT response for specified intent
	if confidence < confidence_setting and int(user.confusion)>=1:
		reply_msg = "Sorry! I am unable to answer your question, I let my supervisor know and they will contact you about this :)"
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
		user.thread = intent
		reply_msg = ""



	return user, reply_msg, intent



def check_flags(message, user):
	'''Checks for special flags'''
	#Too many mis-understood intents
	#No city flag = 1

	#reset = flag 2

	return 0


def check_for_end():
	'''Checks for WIT's end response and modifies message and variables appropriately'''
	pass


def pull_user(user_id):
	'''Pulls user info and creates a new db entry if it doesn't exist'''

	current_state = -1 #dummy variable
	user_state_list = []
	user = []
	with open("user_state_db.csv") as csvfile:
		readCSV = csv.reader(csvfile, delimiter=',')

		for row in readCSV:
			user_state_list.append(row)

	#Find the status of the user
	for temp_user in user_state_list:
		if temp_user.user_id == user_id:
			user = temp_user
			current_state = user[1]


	#if the user hasn't been found add it to the list at state -1 and write to db
	if current_state == -1:

		#user id, current state, city, address, week type, pickup day, reminder setting, confusion, thread, lvl
		user = [user_id,-2,"first","first",0,0,True,0,"?",0]

		user_state_list.append(user)
		with open("user_state_db.csv", "wb") as csvfile:
			writer = csv.writer(csvfile)
			writer.writerows(user_state_list)

	return user


def push_user(user):
	'''updates user'''
	user_state_list = []
	new_db_list = []
	with open("user_state_db.csv") as csvfile:
		readCSV = csv.reader(csvfile, delimiter=',')
		for row in readCSV:
			user_state_list.append(row)

	for temp_user in user_state_list:

		if temp_user.user_id == user.user_id:
			new_db_list.append(user)
		else:
			new_db_list.append(temp_user)



	with open("user_state_db.csv", "wb") as csvfile:
		writer = csv.writer(csvfile)
		writer.writerows(new_db_list)


def parse_intent(message):
	'''Parses intent, gives back confidence and intent, this recognition is trained in the WIT.ai Engine'''

	headers = {"Authorization": "Bearer SZRCYZJAVJYHCNARNTBH32G24VMYPQ7L"}
	r = requests.get("https://api.wit.ai/message?v=20160526&q="+message, headers=headers)

	try:
		confidence = r.json()['entities']['intent'][0]['confidence']
		intent = r.json()['entities']['intent'][0]['value']
	except:
		return 0, "?"

	print "Confidence: " + str(r.json()['entities']['intent'][0]['confidence'])
	print "Intent: " + str(r.json()['entities']['intent'][0]['value'])

	return confidence, intent


def thread(message, user):
	'''manages conversations currently in a thread mode'''
	if user.thread == 'parents':
		print 'parents routine activated'
		reply_msg = 'My mom was an AI and my father was a Garbage Truck.'
		user.thread = '?'

	elif user.thread == 'pickup_day':
		print 'pickup_day routine activated'
		reply_msg, user = pickup_day(message, user)

	elif user.thread == 'reminder':
		print 'reminder routine activated'
		reply_msg = 'reminder stuff'
		user.thread = '?'

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
		reply_msg = 'Please enter your address'
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
				user.confusion = 0
				user.thread = '?'
				user.lvl = 0
			else:
				#This mean the information received back from the garbage day lookup is good so it can be stored
				user.week_type = pickup_info[0]
				user.pickup_day = pickup_info[1]

				user.address = message
				reply_msg = 'Great that means your garbage day is ' + user.pickup_day.upper() + '. Would you like to set a reminder?'
					

				#Get tailored info ******************************************************************
				garbage_date, holiday_flag = guelph_garbage_api.next_pickup_date(datetime.date.today(),user.pickup_day)
				garbage_day = garbage_date.strftime("%A")
				garbage_type = guelph_garbage_api.garbage_type(user.week_type,garbage_date)

				if datetime.date.today().strftime("%A").lower() == garbage_day.lower():
					reply_msg = "Great this means that your pickup day is "+pickup_info[1]+ " and you are on the " + pickup_info[0] + \
						" schedule. So this morning you should, or should have :), put out your ORGANICS and " + garbage_type.upper() + \
						". Do you want to setup a reminder for the evening before?"
				else:
					reply_msg = "Great this means that your pickup day is "+pickup_info[1]+ " and you are on the " + pickup_info[0] + \
						" schedule. So this upcoming " + pickup_info[1] + " you should put out your ORGANICS and " + garbage_type.upper() + \
						". Do you want to setup a reminder for the evening before?"

				#*****************************************************************************************
				user.lvl = 2 #Move to next step

	elif int(user.lvl) == 2:
		
		#this should be converted to natural language processing
		lower_msg = message.lower()

		if lower_msg == "yes" or lower_msg == "sure" or lower_msg == "yeah" or lower_msg == "okay" or lower_msg == "yes please":
			reminder = True
			reply_msg = "Great a reminder has been set for you, anything else I can do for you?"
			user.reminder = reminder
			user.thread = '?'
			user.lvl = 0
			user.confusion = 0


		elif lower_msg == "no" or lower_msg =="nah" or lower_msg == "no thanks":
			reminder = False
			reply_msg = "Understood, anything else I can do for you?"
			user.reminder = reminder
			user.thread = '?'
			user.lvl = 0
			user.confusion = 0

		else:
			#Check for confusion
			if int(user.confusion) == 1:
				reply_msg = 'Sorry I still don\' understand if you want a reminder or not, no problem I sent our conversation to my supervisor for clarification. ' + \
					'They will get back to you on this, in the mean time please let me know if there is anything else I can help you with!'
				user.thread = '?'
				user.lvl = 0
				user.confusion = 0

			else:
				reply_msg = 'Sorry I didn\'t understand that, can you try re-entering'
				user.confusion = '1'



	return reply_msg, user







