from celery import Celery
from celery.utils.log import get_task_logger
import redis
from contextlib import contextmanager
from hawkular.metrics import HawkularMetricsClient, MetricType
from config import config

LOCK_EXPIRE = 10 * 60

app = Celery('tasks', broker='redis://localhost:6379/0')
logger = get_task_logger(__name__)
token = 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJteXByb2plY3QiLCJrdWJlcm5ldGVzLmlvL3NlcnZpY2VhY2NvdW50L3NlY3JldC5uYW1lIjoiaGF3a3VsYXItYmlsbGluZy1yZWFkZXItdG9rZW4tYzFmZmYiLCJrdWJlcm5ldGVzLmlvL3NlcnZpY2VhY2NvdW50L3NlcnZpY2UtYWNjb3VudC5uYW1lIjoiaGF3a3VsYXItYmlsbGluZy1yZWFkZXIiLCJrdWJlcm5ldGVzLmlvL3NlcnZpY2VhY2NvdW50L3NlcnZpY2UtYWNjb3VudC51aWQiOiJlYjZmYWRjZC01NTJmLTExZTctYjBhZS01NDA0YTYxMDFhYzkiLCJzdWIiOiJzeXN0ZW06c2VydmljZWFjY291bnQ6bXlwcm9qZWN0Omhhd2t1bGFyLWJpbGxpbmctcmVhZGVyIn0.jrlkCuypQ3ebVp7yOjX_5144JXANt0KK6--eK3BYDQ75L4pGCzjaTLPnC8_tdImvZDzWngDQKG6HT5qfVJWVO5E1ohqRxxBwDn-7sdnfce3EynK58LgFgLKXwQHa1VWyMeywAWndYtYNsMLh1OR4z6dWgbp0vgMfEzyeBHWAfRP16nA-5ENbMBjf-GNUr2rfvF1HhbhhiU7t1ljR1ponU8HVusHgWWvBlbSknzuM3DDCFU36ZCeIku2HQfl_t_XQbwEANpkRi0aEl-ImtoRlbHvc7B9gi4ctAurXLKOukV8YYrQFZwy_1f85_y2lxLc6pfnNQc6FZTgc-tHcj7aQmw'


@contextmanager
def redis_lock(lock_id):
    r = redis.StrictRedis(host='localhost', port=6379, db=1)

    status = True

    try:
        status = r.get(lock_id)
    except RedisError as e:
        logger.error(str(e))

    if not status:
        try:
            r.setex(lock_id, LOCK_EXPIRE, True)
        except RedisError as e:
            logger.error(str(e))

    yield status

    try:
        r.delete(lock_id)
    except RedisError as e:
        logger.error(str(e))


@app.task
def metrics_definitions():
    lock_id = 'metrics_definitions_lock'
    logger.info('Polling metrics definitions')

    with redis_lock(lock_id) as locked:
        if not locked:
            logger.info('polling 4real')
            client = HawkularMetricsClient(
                tenant_id='myproject',
                scheme='https',
                host='metrics-openshift-infra.192.168.100.5.xip.io',
                port=443,
                path='hawkular/metrics',
                token=token
            )
            print(client.query_metric_definitions())
