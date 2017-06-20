from celery import Celery
from celery.utils.log import get_task_logger
import redis

from hawkular.metrics import HawkularMetricsClient, MetricType

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from model.namespace import Namespace

from contextlib import contextmanager
from config import config

LOCK_EXPIRE = 10 * 60

app = Celery('tasks', broker='redis://localhost:6379/0')
logger = get_task_logger(__name__)

sa_connect = '{0}://{1}:{2}@{3}/{4}'.format(
    config['database']['driver'],
    config['database']['user'],
    config['database']['password'],
    config['database']['host'],
    config['database']['db']
)

engine = create_engine(
    sa_connect, convert_unicode=True,
    pool_recycle=3600, pool_size=10)
db_session = scoped_session(sessionmaker(
    autocommit=False, autoflush=False, bind=engine))

Base = declarative_base()
Base.metadata.create_all(engine)

ns = Namespace(name='asdf')
print(ns)
db_session.add(ns)
db_session.commit()

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
            print(client.query_tenants())
        else:
            logger.info('Polling metrics definitions task already running')
