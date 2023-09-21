#!/bin/bash

# Validate argument count
if [ "$#" -ne 1 ]; then
	echo "Usage: $0 <sleep_time_in_hours>"
	exit 1
fi

# Sleep time is given in seconds and converted to hours
sleep_time=$(( $1 * 60 * 60 ))

# Start the loop
while true;do
	echo "--------------------------------------"
	echo "Starting program..."
	echo "Sleep time is set to: $sleep_time seconds ($1 hours)"

	source "rss-feeds/bin/activate"

	echo "Venv activated."
	echo "Starting program..."

	python3 main.py

	echo ""
	echo "--------------------------------------"
	echo "DONE."

	curr_time=$(date "+%c")

	echo "Ended at: $curr_time"
	echo "Sleeping for $sleep_time seconds ($1 hours)"

	deactivate
	sleep $sleep_time
done

