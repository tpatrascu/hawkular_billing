#!/bin/sh

celery -A metrics_poller worker -c 4 -B -E -l debug
