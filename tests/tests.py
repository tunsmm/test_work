import unittest
from datetime import datetime

import minio
import sqlite3
from fastapi import HTTPException

from settings import client
from fastapi import UploadFile

from app.servers import servers
from app.db import db


db = sqlite3.connect('tests/test_db.sqlite')
c = db.cursor()
test_bucket_name = 'testbucket'
count_files = 3


class TestCaseCreateNewDB(unittest.TestCase):
    def test_create(self):
        try:
            client.remove_bucket(test_bucket_name)
        except minio.error.S3Error:
            print('Корзины нет')
        c.execute("""DROP TABLE IF EXISTS inbox""")
        db.commit()
        c.execute("""DROP TABLE IF EXISTS requests""")
        db.commit()
        c.execute("""CREATE TABLE requests
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      bucket TEXT)""")
        db.commit()
        c.execute("""CREATE TABLE inbox
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     req INTEGER, filename TEXT, date_reg TEXT,
                     FOREIGN KEY(req) REFERENCES requests(id) ON DELETE CASCADE)""")
        db.commit()


class TestCaseMethods(unittest.TestCase):
    def test_1_date_for_bucket_name(self):
        today = datetime.now()
        today_str = f'{today.year}{today.month:02}{today.day}'
        check_def = servers.get_bucket_name()
        self.assertEqual(check_def, today_str)

    def test_2_create_bucket(self):
        servers.create_bucket(test_bucket_name)
        self.assertTrue(client.bucket_exists(test_bucket_name))

    def test_3_check_file_no_image(self):
        files = []
        file = UploadFile('test.docx')
        file.content_type = 'application/docs'
        files.append(file)
        with self.assertRaises(HTTPException) as context:
            servers.check_files(files)
        self.assertEqual(400, context.exception.status_code)

    def test_4_check_file_image(self):
        files = []
        file = UploadFile('test.jpg')
        file.content_type = 'image/jpeg'
        files.append(file)
        self.assertEqual(None, servers.check_files(files))

    def test_5_number_of_file(self):
        files = []
        for i in range(16):
            file = UploadFile(f'{i}.jpg')
            file.content_type = 'image/jpeg'
            files.append(file)
        with self.assertRaises(HTTPException) as context:
            servers.check_files(files)
        self.assertEqual(400, context.exception.status_code)

    def test_6_write_to_db_req(self):
        db.db_requests(test_bucket_name, c, db)
        number_request = db.get_db_requests(c, db)
        self.assertEqual(1, number_request)

    def test_7_add_files(self):
        files = []
        list_name_files = []
        for i in range(count_files):
            file = UploadFile(f'test_file_{i}.jpg')
            file.content_type = 'image/jpeg'
            files.append(file)
        for file in files:
            file_name = file.filename
            list_name_files.append(file_name)
            servers.add_files(file_name, file.file.read(), test_bucket_name)
            db.write_to_db(file_name, c, db)
        list_objects = client.list_objects(test_bucket_name)
        list_from_minio = [obj.object_name for obj in list_objects]
        self.assertEqual(list_from_minio, list_name_files)

    def test_8_get_files_from_db(self):
        list_file_from_inbox = db.get_file_from_db(1, c, db)
        self.assertEqual(count_files, len(list_file_from_inbox))

    def test_9_delete_file_bucket(self):
        files_list = db.get_file_from_db(1, c, db)
        servers.delete_files_from_bucket(files_list, client)
        list_objects = client.list_objects(test_bucket_name)
        list_from_minio = [obj.object_name for obj in list_objects]
        self.assertEqual(0, len(list_from_minio))

    def test_10_delete_req_from_db(self):
        db.delete_req_from_db(1, c, db)
        c.execute("""SELECT * FROM inbox join requests
                     on inbox.req=requests.id
                     WHERE req LIKE (?)""", (1,))
        items = c.fetchall()
        self.assertEqual(0, len(items))

    def test_after_all(self):
        list_objects = client.list_objects(test_bucket_name)
        list_from_minio = [obj.object_name for obj in list_objects]
        for file in list_from_minio:
            client.remove_object(test_bucket_name, file)
        client.remove_bucket(test_bucket_name)
