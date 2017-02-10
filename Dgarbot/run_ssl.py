
import json
import garbot
import requests
import twilio.twiml
import csv
import time
import User
#from twilio.rest import TwilioRestClient
from flask import Flask, request, render_template

app = Flask(__name__)

#Twilio Configuration Information
'''
account_sid = "SK33facec7b6a730dc6a7199e11a708e74"
auth_token = "MHJjpyu6SbfzNh1RatY1boDTGwZonnmM" #Don't lose this
client = TwilioRestClient(account_sid, auth_token)
'''

@app.route('/webhook/', methods=['GET'],strict_slashes=False)
def verify():
	# when the endpoint is registered as a webhook, it must
	# return the 'hub.challenge' value in the query arguments
	if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
		if not request.args.get("hub.verify_token") == "dude_its_me":
			return "Verification token mismatch", 403
		return request.args["hub.challenge"], 200

	return "Hello world", 200


@app.route('/webhook/', methods=['POST'],strict_slashes=False)
def webook():

	# endpoint for processing incoming messaging events

	data = request.get_json()

	if data["object"] == "page":

		for entry in data["entry"]:
			for messaging_event in entry["messaging"]:

				#Check for types of messages and deal with accordingly 

				if messaging_event.get("message"):  # someone sent us a message

					sender_id = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message
					recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID
					
					#Not all message types are supported, ex. images, this try catches these other exceptions, they should be coded for eventually
					try:
						message_text = messaging_event["message"]["text"]  # the message's text
					except:
						print messaging_event
						return "ok", 200
					timestamp = messaging_event["timestamp"]

					fb_user_id = "fb_" + sender_id  #modify user id to include fb_ so that it can be properly identified in the database
					msg = garbot.core(message_text,fb_user_id)
					log("receive",fb_user_id, message_text)

					send_message(sender_id, msg)

				if messaging_event.get("delivery"):  # delivery confirmation
					pass

				if messaging_event.get("optin"):  # optin confirmation
					pass

				if messaging_event.get("postback"):  # user clicked/tapped "postback" button in earlier message, configured right now for the initial USER_DEFINED_PAYLOAD
					pass

					'''
					#This code snipett does not work
					if messaging_event["message"]["postback"]["payload"] == "USER_DEFINED_PAYLOAD":
						sender_id = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message
						send_message(sender_id,"Hi! My name is Garbot and I am here to to help you remember to take out your garbage. To get started please enter the city where you live!")
					'''

				#print messaging_event
	return "ok", 200


@app.route('/garbot/')
def bot():
	return render_template('garbot.html')

@app.route('/')
def index():
	return render_template('index.html')

@app.route('/tos_privacy/')
def tos_privacy():
	return render_template('tos_privacy.html')


@app.route('/sms/', methods=['POST'],strict_slashes=False)
def sms():
	#Respond in same fashion as FB code
	message_text = request.values.get('Body', None)
	sender_id = request.values.get('From', None)
	#print message_text

	sm_sender_id = "sm_" + sender_id  #modify user id to include fb_ so that it can be properly identified in the database

	log("receive",sm_sender_id, message_text) #add message to log

	msg = garbot.core(message_text,sm_sender_id)  #receive response from core garbot routine
	resp = twilio.twiml.Response()
	resp.message(msg)   #this sends the actual message

	log("send",sm_sender_id,msg) #add response to log

	print str(resp) #print message to the terminal window for easier monitoring
	return str(resp)
	

@app.route('/sms/', methods=['GET'],strict_slashes=False)
def sms_verify():
	return "Hello world", 200


def send_message(recipient_id, message_text):
	
	fb_user_id="fb_" + recipient_id #modify for easier searching

	log("send",fb_user_id, message_text)    #add to log

	params = {
		"access_token": "EAAJbyoMPh9MBAAZCzAfP2gHIESG8DPo8hlMoez9hmgtr5iYAiZAGNo2C23QQVFg6yYCnPvP6pgmSfYyZARSXt4xrPfaY4rEyBC2vPFiie6LZAYTdI1ZANcmsrTpaQfpHdqMZBByJmfZBB8kZCydVDFr5BDse8HhGZAnyJEMgunCGeNgZDZD"
	}
	headers = {
		"Content-Type": "application/json"
	}
	data = json.dumps({
		"recipient": {
			"id": recipient_id
		},
		"message": {
			"text": message_text
		}
	})
	r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)


@app.route('/backend/', methods=['GET'], strict_slashes=False)
def backend():
	'''Backend for website, currently just output user states'''
	user_state_list = []
	log = []

	#if password is no good throw an access denied
	try:
		password = request.args.get('password', '')
	except:
		password = 'null'

	if password != 'double_bro':
		return "Access Denied"

	user_state_list = User.get_users('databases/user_state_db.csv')


	with open("databases/log.csv") as csvfile:
		readCSV = csv.reader(csvfile, delimiter=',')

		for row in readCSV:
			log.append(row)

	return render_template("backend.html",users=user_state_list,log=log)


def log(status,user_id, message):

	with open("databases/log.csv", "a") as f:    
		writer = csv.writer(f)
		writer.writerow([status,time.time(),user_id,message])

	print status, user_id, message


if __name__ == "__main__":
	context = ('/etc/nginx/ssl/bundle.crt', '/etc/nginx/ssl/thinkingzoo.key')
	app.run(host='0.0.0.0', port=4000, ssl_context=context, threaded=True)
