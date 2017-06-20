import threading
import metrics_poller


def schedule_tasks():
    metrics_poller.metrics_definitions.delay()
    threading.Timer(5.0, schedule_tasks).start()


schedule_tasks()
