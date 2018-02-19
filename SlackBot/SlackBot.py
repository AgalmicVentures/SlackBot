
# Copyright (c) 2015-2018 Agalmic Ventures LLC (www.agalmicventures.com)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import datetime
import queue
import random
import slacksocket
import time

class SlackBot(object):
	"""
	Base bot class with helpers to simplify business logic in an actual bot.
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

	def userId(self):
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
		return self.getUser(self.userId())

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

	def getChannel(self, channelId):
		"""
		Gets a channel from an ID.

		:param channelId: str
		:return dict (channel JSON)
		"""
		channels = [u for u in self._socket.loaded_channels['channels'] if u[self._idField] == channelId]
		if len(channels) == 0:
			channels = [u for u in self._socket.loaded_channels['groups'] if u[self._idField] == channelId]

		if len(channels) == 0:
			if self._translate:
				user = self.getUser(channelId)
				if user is not None:
					channels = [u for u in self._socket.loaded_channels['ims'] if u['user'] == user['id']]
			else:
				channels = [u for u in self._socket.loaded_channels['ims'] if u[self._idField] == channelId]

		return channels[0] if len(channels) > 0 else None

	def getUser(self, userId):
		"""
		Gets a user from an ID.

		:param userId: str
		:return dict (user JSON)
		"""
		users = [u for u in self._socket.loaded_users if u[self._idField] == userId]
		return users[0] if len(users) > 0 else None

	def sendMessage(self, message, channelId, delay=None):
		"""
		Sends a message to a channel as this bot.

		:param message: str or [str]
		:param channelId: str
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

			self._queuedMessages.append( (t, message, channelId) )
			return

		#Take a random message from a list
		if type(message) is list:
			message = random.sample(message, 1)[0]

		self._socket.send_msg(message, channel_id=channelId)

	def handleEvents(self):
		"""
		Starts an infinite event handling loop.
		"""
		while True:
			#Process all events
			while True:
				try:
					event = self._socket.get_event(timeout=0)
				except queue.Empty:
						break

				self.handleEvent(event)

			#Send any queued messages
			now = datetime.datetime.now()
			newQueuedMessages = []
			for queuedMessage in self._queuedMessages:
				t, message, channelId = queuedMessage
				if t <= now:
					self.sendMessage(message, channelId)
				else:
					newQueuedMessages.append(queuedMessage)
			self._queuedMessages = newQueuedMessages

			#Sleep for a bit
			time.sleep(0.1)

	def handleEvent(self, event):
		"""
		Handle a single event from the event stream.
		"""
		try:
			eventType = event.type
		except AttributeError:
			print('Event type is missing for event: %s' % event)

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
