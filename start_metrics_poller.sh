#!/bin/sh

celery -A metrics_poller worker -B -E -l debug
