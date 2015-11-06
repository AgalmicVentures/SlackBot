#!/usr/bin/env python3

import random
import re
import sys

from SlackBot import SlackBot

class Bartender(SlackBot.SlackBot):

	def __init__(self, token):
		SlackBot.SlackBot.__init__(self, token)

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
			elif strippedTokens[:3] == ['how', 'are', 'you']:
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
