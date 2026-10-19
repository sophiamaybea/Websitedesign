"""Single worker with durable leasing. Run one instance per SQLite database."""
import logging
import os
import sys
import time
from . import engine, store

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("mend.worker")


def once():
    job = store.claim_job(int(os.getenv("MEND_WORKER_LEASE_SECONDS", "300")))
    if job is None:
        return False
    try:
        engine.process(job)
        log.info("Proposal ready for job %s", job["id"])
    except Exception as exc:
        store.fail_job(job["id"], type(exc).__name__ + ": " + str(exc))
        log.exception("Job failed %s", job["id"])
    return True


def main():
    store.initialise()
    if "--once" in sys.argv:
        once()
        return
    delay = max(0.5, float(os.getenv("MEND_WORKER_POLL_SECONDS", "2")))
    while True:
        if not once():
            time.sleep(delay)


if __name__ == "__main__":
    main()
