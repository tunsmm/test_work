import itertools
import os
from datetime import datetime

import minio.error

from settings import client


def get_bucket_name():
    today = datetime.now()
    return f'{today.year}{today.month:02}{today.day}'


def create_bucket(supposed: str, client=client):
    check_bucket = client.bucket_exists(supposed)
    if not check_bucket:
        client.make_bucket(supposed)


def add_files_in_bucket(file_name: str, contents: bytes, bucket_name: str, client=client):
    with open(file_name, 'wb') as file:
        file.write(contents)

    client.fput_object(f'{bucket_name}', f"{file_name}", f"{file_name}")
    os.remove(file_name)


def delete_files_from_bucket(files_list: list, client=client):
    number_file = itertools.count(1)
    files_dict = {}
    for obj in files_list:
        file_name = obj[0]
        date_reg = obj[1]
        bucket_name = obj[2]
        number_key = f'{next(number_file)}'
        if client.bucket_exists(bucket_name):
            try:
                client.get_object(bucket_name, file_name)
                client.remove_object(bucket_name, file_name)
                files_dict[number_key] = {"file name": file_name,
                                       "date_reg": date_reg}
            except minio.error.S3Error:
                files_dict[number_key] = {"errors": f"Файл {file_name} не найден в хранилище"}
    return files_dict
3