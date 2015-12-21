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
		return 'Usage: `air <CODE> [<CODE2> ...]` e.g. `air LGA`.'

	responses = []
	for airport in args:
		airportData = getAirportData(airport)
		if airportData is None:
			responses.append('Error loading data for %s (is the FAA API down?)' % airport)
			break #If the API is broken, no need to club it to death

		try:
			delay = 'Delay (average): %s - %s' % (
				airportData['status']['avgDelay'],
				airportData['status']['reason'],
			) if airportData['delay'] == 'true' else 'No delay. :thumbsup:'

			header = '*%s*\n' % airport if len(args) > 1 else ''
			weather = airportData['weather']
			response = '%sWeather: %s - %s - Wind: %s - Visibility: %s\n%s' % (
				header,
				weather['temp'], weather['weather'], weather['wind'], weather['visibility'],
				delay
			)
			responses.append(response)
		except KeyError:
			responses.append('Unrecognized format: ```%s```' % json.dumps(airportData, indent=2))
		#TODO: handle other exceptions?

	return '\n\n'.join(responses)

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
		if channel is None:
			isPrivate = False
		else:
			isPrivate = channel.get('is_im', False)
			channelID = channel['id']

		text = eventJson['text']

		userDm = self.mentionString() + ': '
		isDm = text.startswith(userDm)

		strippedTokens = [t for t in re.split(r'\W', text) if t != '']
		if isDm:
			strippedTokens = strippedTokens[1:]

		responses = None

		#Bartender mostly respond to DM's and private chats
		if isPrivate or isDm:
			if len(strippedTokens) == 0:
				responses = [
					'Cat got your tongue?',
					'What was that?',
					'I can\'t hear you...',
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
				commandName = strippedTokens[0].lower()
				if commandName == 'quit':
					user = self.getUser(userID)
					if user['is_owner']:
						goodbyes = [
							'Goodbye.',
							'Bye.',
							'Later on.',
						]
						self.sendMessage(goodbyes, channelID)
						sys.exit(0)
					else:
						goodbyes = [
							'Haha',
							'Good one.',
							'You get out!',
						]
						self.sendMessage(goodbyes, channelID)
						return

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


					#Dummy values for help display
					'help': None,
					'quit': None,
				}
				if commandName == 'help':
					self.sendMessage('*Commands*\n%s' % ', '.join(sorted(commands.keys())), channelID)
					return

				command = commands.get(commandName)
				if command is None:
					responses = [
						'What?',
						'Huh?',
						'I don\'t understand.',
						'My responses are limited. You must ask the right questions.',
					]
				else:
					arguments = strippedTokens[1:]
					responses = command(arguments)

		elif self.userID() in event.mentions:
			responses = [
				'My ears are burning...',
			]

		if responses is not None:
			self.sendMessage(responses, channelID)

def main():
	#TODO: parse arguments

	b = Bartender('xoxb-11017522369-7VdJedQjJ5yAnnWs6jOOhXZk')
	b.handleEvents()

	return 0

if __name__ == '__main__':
	sys.exit(main())
