#!/bin/sh

: ${worker_count:=4}
: ${log_level:=error}
: ${monitor=-E}

rm -f ./celerybeat-schedule.db
celery -A metrics_poller worker -B -c $worker_count -l $log_level $monitor $@
