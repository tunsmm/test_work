from fastapi import FastAPI, UploadFile
from app.servers import servers

app = FastAPI()


@app.post("/frames/")
def create_upload_files(files: list[UploadFile]):
    return servers.create_upload_files(files)


@app.get("/frames/{item_id}")
def read_files(item_id: int):
    return servers.read_files(item_id)


@app.delete("/frames/{item_id}")
def delete_files(item_id: int):
    return servers.delete_files(item_id)
