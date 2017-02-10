import csv

class User(object):
	'''
	A user object, to make it more clear what each user variables are.
	It was getting too confusing with all the difference array addresses
	'''

	#user id, current state, city, address, week type, pickup day, reminder setting, confusion, thread, lvl
	def __init__(self, user_id):
		self.user_id = user_id
		self.current_state = -2
		self.city = 'first'
		self.address = 'first'
		self.week_type = 0
		self.pickup_day = 0
		self.reminder = False
		self.confusion = 0
		self.thread = '?'
		self.lvl = 0
		self.reminder_time = -2

	def pull(self, database_path):
		'''
		Pulls the user from database if it exists
		'''

		user_list = []
		new = True

		with open(database_path, "rb") as csvfile:
			readCSV = csv.reader(csvfile, delimiter=',')
			for row in readCSV:
				user_list.append(row)

		for temp_user in user_list:
			if temp_user[0] == self.user_id:
				self.current_state = temp_user[1]
				self.city = temp_user[2]
				self.address = temp_user[3]
				self.week_type = temp_user[4]
				self.pickup_day = temp_user[5]
				self.reminder = temp_user[6]
				self.confusion = temp_user[7]
				self.thread = temp_user[8]
				self.lvl = temp_user[9]
				self.reminder_time = temp_user[10]
				new = False

		#if user is new add to db
		if new == True:
			dummy = [self.user_id, self.current_state, self.city, self.address,
				self.week_type, self.pickup_day, self.reminder, self.confusion,
				self.thread, self.lvl, self.reminder_time]

			user_list.append(dummy)

		with open(database_path, "wb") as csvfile:
			writer = csv.writer(csvfile)
			writer.writerows(user_list)

	def push(self, database_path):
		'''
		pushes the updated user back the database
		'''

		user_list = []

		with open(database_path, "rb") as csvfile:
			readCSV = csv.reader(csvfile, delimiter=',')
			for row in readCSV:
				user_list.append(row)

		for i in range(0,len(user_list)):
			if user_list[i][0] == self.user_id:
				user_list[i][1] = self.current_state
				user_list[i][2] = self.city
				user_list[i][3] = self.address
				user_list[i][4] = self.week_type
				user_list[i][5] = self.pickup_day
				user_list[i][6] = self.reminder
				user_list[i][7] = self.confusion
				user_list[i][8] = self.thread
				user_list[i][9] = self.lvl
				user_list[i][10] = self.reminder_time

		with open(database_path, "wb") as csvfile:
			writer = csv.writer(csvfile)
			writer.writerows(user_list)

def get_users(database_path):
	'''
	Pulls a list of all the users
	'''
	user_list = []

	with open(database_path, "rb") as csvfile:
		readCSV = csv.reader(csvfile, delimiter=',')
		for row in readCSV:
			user_list.append(row)

	return user_list	