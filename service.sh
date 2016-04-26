#!/bin/bash

set -u

##### Settings #####

COMMAND=SlackBot/Bartender.py

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

	echo "Starting..."
	nohup $PROCESS &
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
