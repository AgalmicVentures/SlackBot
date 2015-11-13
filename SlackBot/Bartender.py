#!/usr/bin/env python3

import json
import random
import re
import requests
import sys

from SlackBot import SlackBot

#TODO: stop duplicating this
def getAirportData(airport):
	try:
		request = requests.get('http://services.faa.gov/airport/status/%s?format=json' % airport)
		return request.json()
	except Exception as e:
		return None

def airportCommand(args):
	if len(args) == 0:
		return 'Usage: `airport <CODE>` e.g. `airport LGA`.'
	else:
		airport = args[0]
		airportData = getAirportData(airport)
		if airportData is None:
			return 'Error loading data for %s (is the FAA API down?)'
		else:
			return '```%s```' % json.dumps(airportData, indent=2)

def rollCommand(n):
	def roll(args):
		return str(random.randint(1, n))
	return roll

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

		#Bartender mostly respond to DM's and private chats
		userDm = self.mentionString() + ': '
		if isPrivate or text.startswith(userDm):
			if len(strippedTokens) == 0:
				responses = [
					'Cat got your tongue?',
					'What was that?',
				]
			elif strippedTokens[0] in ['hello', 'hi', 'hey', 'greetings']:
				responses = [
					'Hello.',
					'Hello <@%s>.' % userID,
					'Greetings, <@%s>.' % userID,
				]
			elif strippedTokens[:3] == ['how', 'are', 'you']:
				responses = [
					'Good.',
					'Doing good.',
					'Well, thank you.',
				]
			else:
				commandName = strippedTokens[1] if len(strippedTokens) > 0 else None
				commands = {
					'd3': rollCommand(3),
					'd4': rollCommand(4),
					'd6': rollCommand(6),
					'd10': rollCommand(10),
					'd12': rollCommand(12),
					'd20': rollCommand(20),
					'roll': rollCommand(100),

					'flip': lambda args: ['Heads.' if random.randint(0, 1) == 0 else 'Tails.'],

					'air': airportCommand,
					'airport': airportCommand,
				}

				command = commands.get(commandName)
				if command is None:
					responses = [
						'What?',
						'Huh?',
						'I don\'t understand.',
						'My responses are limited. You must ask the right questions.',
					]
				else:
					arguments = strippedTokens[2:]
					responses = command(arguments)

		elif self.userID() in event.mentions:
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
