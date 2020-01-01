#!/bin/bash

# Copyright (c) 2015-2020 Agalmic Ventures LLC (www.agalmicventures.com)
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

#XXX: Disabled so the virtual environment will work (yes, this is ridiculous)
#set -u

##### Settings #####

COMMAND=SlackBot/Bartender.py
ARGUMENTS=$(cat bartender.arguments)

##### Helpers #####

CWD=`pwd`
PROCESS=$CWD/$COMMAND

function get_processes {
	ps xa | grep $PROCESS | grep -v grep
}

function start {
	PROCESSES=$(get_processes)
	if [[ $? -eq 0 ]]; then
		echo "Already running"
		return 0
	fi

	#Automatically source a virtual environment if available
	if [ -e env/ ]; then
		source env/bin/activate
	fi

	echo "Starting..."
	nohup $PROCESS $ARGUMENTS &
	sleep 1

	PROCESSES=$(get_processes)
	if [[ $? -eq 0 ]]; then
		echo "Started."
		return 0
	else
		echo "Startup failed:"
		echo
		tail -n20 nohup.out
		return 1
	fi
}

function stop {
	PROCESSES=$(get_processes)
	if [[ $? -eq 1 ]]; then
	echo "Not running"
	exit
	fi

	PID=`echo $PROCESSES | awk '{print $1}'`
	kill $@ $PID
}
