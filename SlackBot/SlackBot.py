
import datetime
import random
import slacksocket
import time

class SlackBot:
	"""
	Base class which implements a lots of useful helpers.
	"""

	def __init__(self, token, translate=True):
		self._token = token
		self._translate = translate
		self._idField = 'name' if translate else 'id'

		self.reconnect()

		#List of (time, message) pairs
		self._queuedMessages = []

	def token(self):
		"""
		Returns the token.

		:return: str
		"""
		return self._token

	def userID(self):
		"""
		Returns the bot's user ID.

		:return: str
		"""
		return self._socket.user

	def user(self):
		"""
		Returns the JSON of the current user.

		:return: dict
		"""
		return self.getUser(self.userID())

	def mentionString(self):
		"""
		Returns the mention string of the user (@ID).

		:return: str
		"""
		return '<@%s>' % self.user()['id']

	def reconnect(self):
		"""
		Reconnects to Slack.
		"""
		self._socket = slacksocket.SlackSocket(self._token, translate=self._translate)

	def getChannel(self, channelID):
		"""
		Gets a channel from an ID.

		:param channelID: str
		:return dict (channel JSON)
		"""
		channels = [u for u in self._socket.loaded_channels['channels'] if u[self._idField] == channelID]
		if len(channels) == 0:
			channels = [u for u in self._socket.loaded_channels['groups'] if u[self._idField] == channelID]

		if len(channels) == 0:
			if self._translate:
				user = self.getUser(channelID)
				if user is not None:
					channels = [u for u in self._socket.loaded_channels['ims'] if u['user'] == user['id']]
			else:
				channels = [u for u in self._socket.loaded_channels['ims'] if u[self._idField] == channelID]

		return channels[0] if len(channels) > 0 else None

	def getUser(self, userID):
		"""
		Gets a user from an ID.

		:param userID: str
		:return dict (user JSON)
		"""
		users = [u for u in self._socket.loaded_users if u[self._idField] == userID]
		return users[0] if len(users) > 0 else None

	def sendMessage(self, message, channelID, delay=None):
		"""
		Sends a message to a channel as this bot.

		:param message: str or [str]
		:param channelID: str
		:return: bool indicating success
		"""
		if delay is not None:
			delayType = type(delay)
			if delayType is datetime.timedelta:
				t = datetime.datetime.now() + delay
			elif delayType is int:
				t = datetime.datetime.now() + datetime.timedelta(milliseconds=delay)
			elif delayType is tuple:
				minDelay, maxDelay = delay
				t = datetime.datetime.now() + datetime.timedelta(milliseconds=random.randint(minDelay, maxDelay))
			else:
				raise ValueError('Invalid delay type: %s' % delayType)

			self._queuedMessages.append( (t, message, channelID) )
			return

		#Take a random message from a list
		if type(message) is list:
			message = random.sample(message, 1)[0]

		self._socket.send_msg(message, channel_id=channelID)

	#TODO: add this API to slacksocket and do a pull request
	def _getEventAsync(self):
		try:
			return self._socket._eventq.pop(0)
		except IndexError:
			return None

	def handleEvents(self):
		"""
		Starts an infinite event handling loop.
		"""
		while True:
			#Process all events
			while True:
				event = self._getEventAsync()
				if event is None:
					break

				self.handleEvent(event)

			#Send any queued messages
			now = datetime.datetime.now()
			newQueuedMessages = []
			for queuedMessage in self._queuedMessages:
				t, message, channelID = queuedMessage
				if t <= now:
					self.sendMessage(message, channelID)
				else:
					newQueuedMessages.append(queuedMessage)
			self._queuedMessages = newQueuedMessages

			#Sleep for a bit
			time.sleep(0.1)

	def handleEvent(self, event):
		"""
		Handle a single event from the event stream.
		"""
		eventType = event.type
		if eventType == 'hello':
			self.handleHello(event)
		elif eventType == 'message':
			self.handleMessage(event)
		#TODO: other event types

	def handleHello(self, event):
		"""
		Handles a hello event (overriden by implementations).
		"""

	def handleMessage(self, event):
		"""
		Handles a hello event (overriden by implementations).
		"""
