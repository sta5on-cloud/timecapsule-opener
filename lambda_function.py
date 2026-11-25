"""TimeCapsule opener: opens every capsule whose time has come.

Runs once a minute from EventBridge Scheduler (asynchronous invocation). The function does
not talk to SNS: it returns the opened capsule ids, and the Lambda service sends the
invocation record to the timecapsule-dev-events topic (on-success destination).
"""
import os
import ssl
from datetime import datetime, timezone

import pg8000.native

CA_FILE = os.path.join(os.path.dirname(__file__), "rds-ca.pem")

_conn = None


def db():
    global _conn
    if _conn is None:
        _conn = pg8000.native.Connection(
            host=os.environ["DB_HOST"],
            port=int(os.environ.get("DB_PORT", "5432")),
            database=os.environ["DB_NAME"],
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
            ssl_context=ssl.create_default_context(cafile=CA_FILE),
            # The database is stopped every evening: fail fast instead of hanging until the function timeout.
            timeout=5,
        )
    return _conn


def lambda_handler(event, context):
    global _conn
    try:
        # opened_at IS NULL makes the UPDATE return only rows it changed, so overlapping
        # runs never report the same capsule twice.
        rows = db().run(
            """UPDATE capsules
                  SET opened_at = (NOW() AT TIME ZONE 'UTC')
                WHERE opened_at IS NULL AND open_at <= (NOW() AT TIME ZONE 'UTC')
            RETURNING id"""
        )
    except Exception:
        _conn = None
        raise

    capsule_ids = [row[0] for row in rows]
    if capsule_ids:
        print(f"opened capsules: {capsule_ids}")
    return {
        "type": "capsules.opened",
        "count": len(capsule_ids),
        "capsule_ids": capsule_ids,
        "opened_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
