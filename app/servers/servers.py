import itertools
import uuid

from fastapi import HTTPException

import bucket
from app.db import db


async def create_upload_files(files):
    check_files(files)

    bucket_name = bucket.get_bucket_name()
    bucket.create_bucket(bucket_name)
    db.db_requests(bucket_name)

    number_request = db.get_db_requests()
    result = {"request_number": number_request}
    number_file = itertools.count(1)

    for file in files:
        file_name = f'{uuid.uuid4()}.jpg'
        contents = await file.read()
        bucket.add_files_in_bucket(file_name, contents, bucket_name)
        db.write_to_db(file_name)
        result[f'{next(number_file)}'] = file_name
    return result


def check_files(files):
    if len(files) > 15:
        raise HTTPException(400, detail="Превышено число файлов")


def read_files(item_id):
    number_file = itertools.count(1)
    files_list = db.get_file_from_db(item_id)
    result = {"request_number": item_id}
    for file in files_list:
        result[f'{next(number_file)}'] = {
            "file_name": file[0],
            "registration_date": file[1]}
    return result


def delete_files(item_id: int):
    files_list = db.get_file_from_db(item_id)  # получаем из таблицы inbox файлы по номеру запроса
    result = {"delete_request_number": item_id}
    del_files = bucket.delete_files_from_bucket(files_list)
    result['delete_files'] = del_files
    if len(files_list) == 0:
        return HTTPException(404, detail="Not found in DB")  # при отсутствии записей в базе данных
    else:
        db.delete_req_from_db(item_id)  # удаляем файлы из базы данных
        result['delete_status'] = f'{HTTPException(200)}'
        result['detail'] = "OK"
    return result
