#!/usr/bin/env python3

# Copyright (c) 2015-2017 Agalmic Ventures LLC (www.agalmicventures.com)
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

import argparse
import json
import pprint
import random
import re
import requests
import socket
import sys

import SlackBot

#TODO: stop duplicating this
def getAirportData(airport):
	try:
		request = requests.get('http://services.faa.gov/airport/status/%s?format=json' % airport)
		return request.json()
	except Exception as e:
		print('Error grabbing airport data: %s' % e)
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
			delay = 'Delay reason: %s - Min: %s - Max: %s - Average: %s' % (
				airportData['status']['reason'],
				airportData['status']['minDelay'],
				airportData['status']['maxDelay'],
				airportData['status']['avgDelay'],
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

def dnsCommand(args):
	if len(args) == 0:
		return [
			'What domains would you like to look up?',
			'Please enter a list of domains to look up.',
		]
	else:
		responses = []
		for arg in args:
			parsedUrl = arg[arg.find('|') + 1:-1]
			try:
				response = socket.gethostbyname(parsedUrl)
			except Exception as e:
				response = str(e)

			if len(args) == 1:
				responses.append(response)
			else:
				responses.append('%s: %s' % (parsedUrl, response))
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

def rollCommand(args):
	if len(args) == 0:
		n = 100
	else:
		try:
			n = int(args[0])
		except ValueError:
			return 'You must enter a valid number for the maximum value.'

	value = random.randint(1, n)
	return 'Rolling 1 - %d: %d' % (n, value)

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

		strippedTokens = [t for t in re.split(r' ', text) if t != '']
		if isDm:
			strippedTokens = strippedTokens[1:]

		lowerStrippedTokens = [t.lower() for t in strippedTokens]

		responses = None
		delay = (150, 450)

		#Bartender mostly respond to DM's and private chats
		if isPrivate or isDm:
			#TODO: separate conversation engine from command engine
			if len(strippedTokens) == 0:
				responses = [
					'Cat got your tongue?',
					'What was that?',
					'I can\'t hear you...',
				]
			elif lowerStrippedTokens[0] in ['hello', 'hi', 'hey', 'greetings', 'howdy']:
				responses = [
					'Hello.',
					'Hello <@%s>.' % userID,
					'Greetings, <@%s>.' % userID,
					'Hi there.',
				]
			elif lowerStrippedTokens[0] in ['goodbye', 'bye']:
				responses = [
					'Later on!',
					'Goodbye.',
					'Bye.',
					'Goodbye <@%s>.' % userID,
					'See you later.',
				]
			elif lowerStrippedTokens[0] == 'thanks' or lowerStrippedTokens[0:1] == ['thank', 'you']:
				responses = [
					'You\'re welcome.',
					'You\'re welcome <@%s>.' % userID,
					'No problem.',
				]
			elif lowerStrippedTokens[:3] == ['how', 'are', 'you']:
				responses = [
					'Good. You?',
					'Doing good.',
					'Well, thank you.',
					'Very well. You?'
				]
			elif lowerStrippedTokens[:2] == ['knock', 'knock']:
				responses = [
					'Who\'s there?',
				]
				#TODO: handle the rest of a knock-knock joke by keeping per-user state
			else:
				commandName = lowerStrippedTokens[0]
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

				#TODO: move this out to the top level
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
					'roll': rollCommand,
					'flip': lambda args: ['Heads.' if random.randint(0, 1) == 0 else 'Tails.'],

					#Virtual assistant
					'air': airportCommand,
					'airport': airportCommand,
					'search': searchCommand,

					#IT
					'dns': dnsCommand,

					#Dummy values for help diwsplay
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
						'Sorry, I don\'t understand.'
						'My responses are limited. You must ask the right questions.',
					]
					delay = (250, 750)
				else:
					#TODO: avoid special case
					if command in ['air', 'airport', 'dns']:
						delay = None

					arguments = strippedTokens[1:]
					responses = command(arguments)

		elif self.userID() in event.mentions:
			responses = [
				'My ears are burning...',
				'Hmmm?',
			]

		if responses is not None:
			self.sendMessage(responses, channelID, delay=delay)

def main():
	#Parse arguments
	parser = argparse.ArgumentParser(description='Bartender (Slack Bot)')

	parser.add_argument('token', action='store', help='Slack API token.')

	arguments = parser.parse_args(sys.argv[1:])

	b = Bartender(arguments.token)
	b.handleEvents()

	return 0

if __name__ == '__main__':
	sys.exit(main())
