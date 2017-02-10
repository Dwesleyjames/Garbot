'''
personalize.py
This library is designed to personalize and track the user moving through the flow

this relies on a CSV database in the format
user id, current state, city, address, week type, pickup day,reminder setting

'''

import csv
import re
import guelph_garbage_api
import datetime


#-------------- Core Message Routing Method
#Should update the current state and return a response message
def personalize(user_fb_id, user_msg):

    msg = "" #the message that will be returned to the user
    new_state = 0 #variables for the new state
    current_state = int(get_current_state(user_fb_id))
    #print current_state
    states = {"state_0":"Great, I am excited to help, first I need the city where you live. PS currently I only work for Canadian Cities!",
        "state_0_error":"Sorry I don't recognize that city, try re-entering it! :)",
        "state_1":"What is your address?",
        "state_1_error":"Sorry I can't recognize that address, please try re-entering it!",
        "state_2":"A bunch of info here!, do you want a reminder? Yes or no?",
        "state_2_error":"Sorry not a valid input, yes or no?",
        "state_3":"Main menu baby!"}

    #Modify user message to remove spaces
    user_msg_mod = user_msg.strip()

    #Check what routine the user was at previously and pass the response to that routine
    if current_state == -1:
        new_state, msg = state_new(user_fb_id, user_msg_mod, states)

    elif current_state == 0:
        new_state, msg = state_0(user_fb_id, user_msg_mod, states)

    elif current_state == 1:
        new_state, msg = state_1(user_fb_id, user_msg_mod, states)

    elif current_state == 2:
        new_state, msg = state_2(user_fb_id, user_msg_mod, states)

    elif current_state == 3:
        new_state, msg = state_3(user_fb_id, user_msg_mod, states)


    update_current_state(user_fb_id, new_state) #Updates the DB with the user's new state

    return msg




#-------------- Methods unique to each state
#Ex Def state_0(), state_1(), etc.

#State 0------------------
#needs to return a description if no variables are input
# new_state, msg = state_0(user_fb_id, user_msg)
def state_new(user_fb_id, user_msg, states):
    #print("state new executing")
    
    msg = "Hi! My name is Garbot I am excited to help. Lets get started, what CITY do you live in?"

    return 0, msg




#State 0------------------
#needs to return a description if no variables are input
# new_state, msg = state_0(user_fb_id, user_msg)
def state_0(user_fb_id, user_msg, states):
    #print("state zero executing")
    #Some city check, to determine if city is invalid, if invalid send to state_0_error
    #Check for reset command
    if user_msg == "reset" or user_msg == "Reset":
        new_state = 0
        msg = "Reset Selected - Please enter the city you live in"
        temp = [user_fb_id,0,0,0,0,0,True]
        update_user(temp)
        return new_state, msg

    #Error Check return flag
    if user_msg == "":
        return 0, "Hey I couldn't understand that city can you try re-entering it!"


    user = pull_user(user_fb_id)
    user[2] = user_msg
    update_user(user)

    #Check for invalid cities, this is hardcoded, should be expanded in the future
    if user_msg != "guelph" and user_msg != "Guelph":
        msg = "Sorry I do not support the city: " + user_msg.upper() + \
            " that you entered. Please re-enter a different city or just leave it and I will let you know when we support your city!"
        return 0, msg

    #send to new state
    new_state = 1
    msg = states["state_1"]

    return 1, msg


#Received address and re-routes as appropriate
# new_state, msg = state_0(user_fb_id, user_msg)
def state_1(user_fb_id, user_msg, states):
    #print("state one executing")

    #Check for reset command
    if user_msg == "reset" or user_msg == "Reset":
        new_state = 0
        msg = "Reset Selected - Please enter the city you live in"
        temp = [user_fb_id,0,0,0,0,0,True]
        update_user(temp)
        return new_state, msg

    #Some address check, if invalid send to state_1_error
    parsed = re.split(r'(?<=\d)(?:-\d+)?\s+', user_msg)

    #Check that address has two parts and that the first part is a string

    if len(parsed)!= 2 or type(parsed[0]) == int:
        return 1, "Sorry I don't think this is a valid address! Try re-entering it."    

    user = pull_user(user_fb_id)
    user[3] = user_msg    

    #Pull the relevant garbage day info out!
    #assuming just for guelph for now
    pickup_info = guelph_garbage_api.guelph_garbage(parsed[0],parsed[1])

    #If error flag is passed through guelph_garbage function then prompt for re-entry
    if pickup_info[0] == "error":
        msg = "Sorry I can't find the address you entered, please re-enter your address or type reset to change the city you live in."
        return 1, msg

    user[4] = pickup_info[0]
    user[5] = pickup_info[1]
    #user id, current state, city, address, week type, pickup day,reminder setting



    update_user(user)

    #Get tailored info
    garbage_date, holiday_flag = guelph_garbage_api.next_pickup_date(datetime.date.today(),user[5])
    garbage_day = garbage_date.strftime("%A")
    garbage_type = guelph_garbage_api.garbage_type(user[4],garbage_date)

    if datetime.date.today().strftime("%A").lower() == garbage_day.lower():
        msg = "Great this means that your pickup day is "+pickup_info[1]+ " and you are on the " + pickup_info[0] + \
            " schedule. So this morning you should, or should have :), put out your ORGANICS and " + garbage_type.upper() + \
            ". Do you want to setup a reminder for the evening before?"
    else:
        msg = "Great this means that your pickup day is "+pickup_info[1]+ " and you are on the " + pickup_info[0] + \
            " schedule. So this upcoming " + pickup_info[1] + " you should put out your ORGANICS and " + garbage_type.upper() + \
            ". Do you want to setup a reminder for the evening before?"
    
    #send to new state
    new_state = 2

    return new_state, msg



#Display garbage day info and prompt for reminder
def state_2(user_fb_id, user_msg, states):
    #print("state two executing")
    
    #Check for reset command
    if user_msg == "reset" or user_msg == "Reset":
        new_state = 0
        msg = "Reset Selected - Please enter the city you live in"
        temp = [user_fb_id,0,0,0,0,0,True]
        update_user(temp)
        return new_state, msg
    
    #Reminder Check, if invalid send to State_2_error
    reminder = True #Dummy
    lower_msg = user_msg.lower()

    #Check input if invalid 
    if lower_msg == "yes" or lower_msg == "sure" or lower_msg == "yeah" or lower_msg == "okay" or lower_msg == "yes please":
        reminder = True

    elif lower_msg == "no" or lower_msg =="nah" or lower_msg == "no thanks":
        reminder = False

    else:
        return 2, "Sorry I didn't understand that, can you re-enter if you want a reminder"


    user = pull_user(user_fb_id)
    #update their address
    user[6] = reminder
    update_user(user)
    #write back to db

    #send to new state
    new_state = 3
    msg = "Alright you are all configured! Type reset to change any settings or type anything else to get information on your upcoming garbage day."

    return new_state, msg

#Display main menu after receiving input
def state_3(user_fb_id, user_msg, states):
    #print("state three executing")
 
    #Check for reset command
    if user_msg == "reset" or user_msg == "Reset":
        new_state = 0
        msg = "Reset Selected - Please enter the city you live in"
        temp = [user_fb_id,0,0,0,0,0,False]
        update_user(temp)
        return new_state, msg   

    #This should be main menu!
    #for now just output what they are
    #user id, current state, city, address, week type, pickup day,reminder setting
    user = pull_user(user_fb_id)

    #Check for tricky stuff
    #if holiday is not true
    garbage_date, holiday_flag = guelph_garbage_api.next_pickup_date(datetime.date.today(),user[5])
    garbage_day = garbage_date.strftime("%A")
    garbage_type = guelph_garbage_api.garbage_type(user[4],garbage_date)

    #if holiday = true some message, not working yet
    #if today modify garbage_day
    if datetime.date.today().strftime("%A").lower() == garbage_day.lower():
        msg = "Your Garbage day is TODAY, you should, or should have :), put out your ORGANICS and " + \
            garbage_type.upper() + " this morning."
    else:
        msg = "Your upcoming garbage day is " + garbage_day.upper() + " and you should put out ORGANICS and " + \
            garbage_type.upper() + "."
    
    new_state = 3

    return new_state, msg

# ------------------------------------------------------------------- Helper Functions
#This has functions to just speed up writing new states


#--------------- update_current_state
#updates the current state into the db
def update_current_state(user_fb_id, new_state):
    #user id, current state, city, address, week type, pickup day, reminder setting
    user = pull_user(user_fb_id)
    #print user
    user[1] = new_state
    #print user
    update_user (user)


#-------------- get_current_state()
#This is only for testing right now, not a production db
def get_current_state(user_fb_id):

    current_state = -1 #dummy variable
    user_state_list = []
    temp = []
    with open("user_state_db.csv") as csvfile:
        readCSV = csv.reader(csvfile, delimiter=',')

        for row in readCSV:
            user_state_list.append(row)

    #Find the status of the user
    for user in user_state_list:
        if user[0] == user_fb_id:
            current_state = user[1]


    #if the user hasn't been found add it to the list at state -1 and write to db
    if current_state == -1:

        #user id, current state, city, address, week type, pickup day, reminder setting
        temp = [user_fb_id,-1,0,0,0,0,True]

        user_state_list.append(temp)
        with open("user_state_db.csv", "wb") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(user_state_list)

    return current_state


#Create a function to pull a specific user's information
def pull_user(user_fb_id):
    user_state_list = []
    with open("user_state_db.csv") as csvfile:
        readCSV = csv.reader(csvfile, delimiter=',')

        for row in readCSV:
            user_state_list.append(row)

    '''
    #Find the location of the user
    for i in range(0,len(user_state_list)):
        if int(user_state_list[i][0]) == int(user_fb_id):
                user_location = i
    '''
    #Updated user search function
    for user in user_state_list:
        if user[0] == user_fb_id:
            return_user = user

    #return user_state_list[i]
    return return_user

#Function to push an updated user to the database
def update_user(entry):
    user_state_list = []

    #Main part
    with open("user_state_db.csv") as csvfile:
        readCSV = csv.reader(csvfile, delimiter=',')

        for row in readCSV:
            user_state_list.append(row)

    #Find the correct user and update the entry
    for i in range(0,len(user_state_list)):
        if user_state_list[i][0] == entry[0]:
            user_state_list[i] = entry    

    #write back to db
    with open("user_state_db.csv", "wb") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(user_state_list)    
