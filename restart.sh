#!/bin/bash

set -e
set -u

./stop.sh
sleep 1
./start.sh
