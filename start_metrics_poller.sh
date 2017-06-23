#!/bin/sh

celery -A metrics_poller worker -c 1 -B -E -l debug
