#!/usr/bin/env python3

import datetime
import json
import pprint
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

def searchCommand(args):
	if len(args) == 0:
		return [
			'What would you like to search for?',
			'What can I help you find?',
			'What are you looking for?',
			'Can I help you?',
		]
	else:
		search = ' '.join(args)
		searchUrl = search.replace(' ', '%20') #TODO: do this properly
		return '*Search results for "%s"*\nGoogle: http://www.google.com/search?q=%s\nLMGTFY: http://www.lmgtfy.com/?q=%s' % (
			search, searchUrl, searchUrl,
		)

def rollCommand(n):
	def command(args):
		return str(random.randint(1, n))
	return command

def targetedCommand(responses):
	def command(args):
		if len(args) == 0:
			return responses
		else:
			user = args[0]
			if user.startswith('<@') and user.endswidth('>'):
				mention = user
			else:
				mention = '<@%s>' % user
			return ['%s: %s' % (mention, response) for response in responses]

	return command

class Bartender(SlackBot.SlackBot):

	def __init__(self, token):
		SlackBot.SlackBot.__init__(self, token)

	def handleMessage(self, event):
		eventJson = event.event
		pprint.pprint(eventJson)

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

		text = eventJson.get('text')
		if text is None:
			return #TODO: handle this better

		userDm = self.mentionString() + ': '
		isDm = text.startswith(userDm)

		strippedTokens = [t for t in re.split(r'\W', text) if t != '']
		if isDm:
			strippedTokens = strippedTokens[1:]

		responses = None
		delay = (150, 450)

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
			elif strippedTokens[:2] == ['knock', 'knock']:
				responses = [
					'Who\'s there?',
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
					#Bar
					'beer': targetedCommand([':beer:', ':beers:']),
					'champagne': targetedCommand([':champgane:']),
					'cocktail': targetedCommand([':cocktail:']),
					'coffee': targetedCommand([':coffee:']),
					'sake': targetedCommand([':sake:']),
					'tea': targetedCommand([':tea:']),
					'wine': targetedCommand([':wine_glass:']),

					#One-off gambling
					'd3': rollCommand(3),
					'd4': rollCommand(4),
					'd6': rollCommand(6),
					'd10': rollCommand(10),
					'd12': rollCommand(12),
					'd20': rollCommand(20),
					'roll': rollCommand(100),
					'flip': lambda args: ['Heads.' if random.randint(0, 1) == 0 else 'Tails.'],

					#Virtual assistant
					'air': airportCommand,
					'airport': airportCommand,
					'search': searchCommand,

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
					delay = (250, 750)
				else:
					#TODO: avoid special case
					if command in ['air', 'airport']:
						delay = None

					arguments = strippedTokens[1:]
					responses = command(arguments)

		elif self.userID() in event.mentions:
			responses = [
				'My ears are burning...',
			]

		if responses is not None:
			self.sendMessage(responses, channelID, delay=delay)

def main():
	#TODO: parse arguments

	b = Bartender('xoxb-11017522369-7VdJedQjJ5yAnnWs6jOOhXZk')
	b.handleEvents()

	return 0

if __name__ == '__main__':
	sys.exit(main())
