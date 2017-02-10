
import json
import personalize
import requests
import twilio.twiml
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
                    try:
                        message_text = messaging_event["message"]["text"]  # the message's text
                    except:
                        print messaging_event
                        return "ok", 200
                    timestamp = messaging_event["timestamp"]

                    fb_user_id = "fb_" + sender_id  #modify user id to include fb_ so that it can be properly identified in the database
                    msg = personalize.personalize(fb_user_id,message_text)

                    send_message(sender_id, msg)

                if messaging_event.get("delivery"):  # delivery confirmation
                    pass

                if messaging_event.get("optin"):  # optin confirmation
                    pass

                if messaging_event.get("postback"):  # user clicked/tapped "postback" button in earlier message, configured right now for the initial USER_DEFINED_PAYLOAD
                    if messaging_event["message"]["postback"]["payload"] == "USER_DEFINED_PAYLOAD":
                        sender_id = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message
                        send_message(sender_id,"Hi! My name is Garbot and I am here to to help you remember to take out your garbage. To get started please enter the city where you live!")

                print messaging_event
    return "ok", 200

@app.route('/bot/')
def bot():
    return render_template('cover.html')

@app.route('/tos_privacy/')
def tos_privacy():
    return render_template('tos_privacy.html')


@app.route('/sms/', methods=['POST'],strict_slashes=False)
#This is a webhook for sms
def sms():
    #message = client.messages.create(to="+12316851234", from_="+15555555555",body="Hello there!")
    #Respond in same fashion as FB code
    message_text = request.values.get('Body', None)
    print message_text
    sm_user_id = "sm_" + sender_id  #modify user id to include fb_ so that it can be properly identified in the database
    msg = personalize.personalize(sm_user_id,message_text)  
    resp = twilio.twiml.Response()
    resp.message(msg)
    print str(resp)
    return str(resp)
    

@app.route('/sms/', methods=['GET'],strict_slashes=False)
def sms_verify():
    return "Hello world", 200

def send_message(recipient_id, message_text):

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



if __name__ == "__main__":
    context = ('key.crt', 'key.key')
    app.run(host='0.0.0.0', port=4000, ssl_context=context, threaded=True)
