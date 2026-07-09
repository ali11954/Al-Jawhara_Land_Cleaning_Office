import os
import psycopg2
import psycopg2.extras
from contextlib import contextmanager

DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_url():
    if DATABASE_URL:
        url = DATABASE_URL
        if url.startswith('postgres://'):
            url = url.replace('postgres://', 'postgresql://', 1)
        return url
    return None

@contextmanager
def get_db():
    db_url = get_db_url()
    if db_url:
        conn = psycopg2.connect(db_url)
        conn.autocommit = False
        try:
            yield conn
        finally:
            conn.close()
    else:
        import sqlite3
        _db_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        db_path = os.path.join(_db_dir, 'instance', 'aljwahrh_land.db')
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

def fetch_all(conn, query, params=None):
    db_url = get_db_url()
    if db_url:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(query, params or ())
        rows = cur.fetchall()
        cur.close()
        return [dict(r) for r in rows]
    else:
        cur = conn.cursor()
        cur.execute(query, params or ())
        rows = cur.fetchall()
        cur.close()
        return [dict(r) for r in rows]

def fetch_one(conn, query, params=None):
    db_url = get_db_url()
    if db_url:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(query, params or ())
        row = cur.fetchone()
        cur.close()
        return dict(row) if row else None
    else:
        cur = conn.cursor()
        cur.execute(query, params or ())
        row = cur.fetchone()
        cur.close()
        return dict(row) if row else None

def execute(conn, query, params=None):
    db_url = get_db_url()
    cur = conn.cursor()
    cur.execute(query, params or ())
    conn.commit()
    last_id = None
    try:
        last_id = cur.fetchone()[0] if cur.description else cur.lastrowid
    except:
        last_id = cur.lastrowid if hasattr(cur, 'lastrowid') else None
    cur.close()
    return last_id
