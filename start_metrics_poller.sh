#!/bin/sh

: ${worker_count:=-c 4}
: ${log_level:=-l error}
: ${monitor=-E}

celery -A metrics_poller worker -B $worker_count $log_level $monitor $@
