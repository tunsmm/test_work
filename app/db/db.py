import sqlite3
from datetime import datetime

data_base = sqlite3.connect('main.sqlite')
cursor_db = data_base.cursor()


def db_requests(bucket_name: str, cursor=cursor_db, db=data_base):
    cursor.execute("INSERT INTO requests (bucket) VALUES (?)", (bucket_name,))
    db.commit()


def get_db_requests(cursor=cursor_db, db=data_base) -> int:
    request_number = (cursor.execute("SELECT max(id) FROM requests").fetchone()[0])
    db.commit()
    return request_number


def write_to_db(file_name: str, cursor=cursor_db, db=data_base):
    today = datetime.now()
    num = cursor.execute("SELECT max(id) FROM requests").fetchone()[0]
    cursor.execute("INSERT INTO inbox(req, filename, date_reg) VALUES (?,?,?)",
              (num, f'{file_name}', f'{today.strftime("%d-%m-%Y %H:%M")}'))
    db.commit()


def get_file_from_db(req_number: int, cursor=cursor_db, db=data_base) -> list:
    cursor.execute("""
                SELECT filename, date_reg, bucket 
                FROM inbox join requests
                on inbox.req=requests.id
                WHERE req LIKE (?)""", (req_number,))
    items = cursor.fetchall()
    db.commit()
    return items


def delete_req_from_db(request_number: int, cursor=cursor_db, db=data_base):
    cursor.execute("""PRAGMA foreign_keys = ON""")
    cursor.execute("""
                DELETE FROM requests
                 WHERE id = (?)""", (request_number,))
    db.commit()
