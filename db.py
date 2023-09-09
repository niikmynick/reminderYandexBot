import sqlite3
import logging

conn = sqlite3.connect('identifier.sqlite')
cur = conn.cursor()
connected = False


def connect():
    global conn, cur, connected
    try:
        conn = sqlite3.connect('identifier.sqlite')
        cur = conn.cursor()
        connected = True

    except sqlite3.Error as e:
        logging.error(e)
        raise SystemExit


def get_users():
    try:
        cur.execute(f"select id, username from User")
        return cur.fetchall()

    except sqlite3.Error as e:
        logging.error(e)
        return []


def insert_user(user_id, login, username):
    try:
        cur.execute(
            f"insert into User (id, login, username) values ({user_id}, '{login}', '{username}')")
        conn.commit()

    except sqlite3.Error as e:
        logging.error(e)
