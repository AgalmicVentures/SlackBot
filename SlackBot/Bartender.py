#!/usr/bin/env python3

import random
import re
import slacksocket
import sys
import time

class SlackBot:
	"""
	Base class which implements a lots of useful helpers.
	"""

	def __init__(self, token, translate=True):
		self._token = token
		self._translate = translate
		self._idField = 'name' if translate else 'id'

		self._socket = slacksocket.SlackSocket(token, translate=translate)

	def userID(self):
		"""
		Returns the bot's user ID.
		"""
		return self._socket.user

	def getChannel(self, channelID):
		channels = [u for u in self._socket.loaded_channels['channels'] if u[self._idField] == channelID]
		if len(channels) == 0:
			if self._translate:
				user = self.getUser(channelID)
				if user is not None:
					channels = [u for u in self._socket.loaded_channels['ims'] if u['user'] == user['id']]
			else:
				channels = [u for u in self._socket.loaded_channels['ims'] if u[self._idField] == channelID]

		return channels[0] if len(channels) > 0 else None

	def getUser(self, userID):
		users = [u for u in self._socket.loaded_users if u[self._idField] == userID]
		return users[0] if len(users) > 0 else None

	def sendMessage(self, message, channelID):
		"""
		Sends a message to a channel as this bot.

		:param message: str or [str]
		:param channelID: str
		:return: bool indicating success
		"""
		#Take a random message from a list
		if type(message) is list:
			message = random.sample(message, 1)[0]

		self._socket.send_msg(message, channel_id=channelID)

	def handleEvents(self, delay=0.1):
		"""
		Starts an infinite event handling loop.
		"""
		for event in self._socket.events():
			self.handleEvent(event)
		#while True:
		#	#TODO: handle ConnectionResetError
		#	events = self._client.rtm_read()
		#
		#	for event in events:
		#		self.handleEvent(event)
		#	time.sleep(delay)

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

class Bartender(SlackBot):

	def __init__(self, token):
		SlackBot.__init__(self, token)

	def handleMessage(self, event):
		eventJson = event.event
		print(eventJson)

		#Ignore own messages
		userID = eventJson.get('user')
		if userID == self.userID():
			return

		channelID = eventJson['channel']
		channel = self.getChannel(channelID)
		isPrivate = channel.get('is_im', False)
		print('Channel isPrivate: %s' % isPrivate)

		text = eventJson['text']
		strippedTokens = [t for t in re.split(r'\W', text.lower()) if t != '']

		responses = None
		if isPrivate:
			if strippedTokens[0] in ['hello', 'hi', 'hey', 'greetings']:
				responses = [
					'Hello.',
					'Hello <@%s>.' % userID,
					'Greetings, <@%s>.' % userID,
				]
			elif strippedTokens[:2] == ['how', 'are', 'you']:
				responses = [
					'Good.',
					'Doing good.'
				]
		else:
			userMention = '<@%s>' % self.userID()
			userDm = userMention + ': '
			if text.startswith(userDm):
				commandName = strippedTokens[1] if len(strippedTokens) > 0 else None
				commands = {
					'd3': lambda args: [str(random.randint(1, 3))],
					'd4': lambda args: [str(random.randint(1, 4))],
					'd6': lambda args: [str(random.randint(1, 6))],
					'd10': lambda args: [str(random.randint(1, 10))],
					'd12': lambda args: [str(random.randint(1, 12))],
					'd20': lambda args: [str(random.randint(1, 20))],
					'flip': lambda args: ['Heads.' if random.randint(0, 1) == 0 else 'Tails.'],
					'roll': lambda args: [str(random.randint(1, 100))],
				}

				command = commands.get(commandName)
				if command is None:
					responses = [
						'What?',
						'Huh?',
						'My responses are limited. You must ask the right questions.',
					]
				else:
					arguments = strippedTokens[2:]
					responses = command(arguments)

			elif userMention in text:
				responses = [
					'My ears are burning...',
				]

		if responses is not None:
			self.sendMessage(responses, channel['id'])

def main():
	#TODO: parse arguments

	b = Bartender('xoxb-11017522369-7VdJedQjJ5yAnnWs6jOOhXZk')
	b.handleEvents()

	return 0

if __name__ == '__main__':
	sys.exit(main())
