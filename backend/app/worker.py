"""Redis delivery is retryable; the database job is the source of truth (outbox)."""
import os
import time
import dramatiq
from dramatiq.brokers.redis import RedisBroker
from sqlalchemy import select
from .config import Settings
from .db import make_database
from .models import Job
from .processing import process_job
from .security import now

broker=RedisBroker(url=os.getenv("REDIS_URL","redis://localhost:6379/0"))
dramatiq.set_broker(broker)
settings=Settings()
_,factory=make_database(settings)
@dramatiq.actor(max_retries=3,time_limit=120000)
def process_document(job_id: str):
    process_job(factory,settings,job_id)

def dispatch():
    while True:
        with factory() as db:
            ids=list(db.scalars(select(Job.id).where(Job.state=="pending",Job.next_at<=now()).limit(100)))
        for job_id in ids: process_document.send(job_id)
        # Redelivery is intentional: a crash between commit and enqueue cannot lose a job.
        time.sleep(15)
if __name__=="__main__": dispatch()
