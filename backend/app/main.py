from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import Annotated

app = FastAPI()

class AuthParam(BaseModel):
    code: str
    state: str
    status: str

@app.get("/")
async def root():
    return {"message": "hello world" }

@app.get("/auth/redirect")
async def aurinko_redirect(auth_param: Annotated[AuthParam, Query()]):
    print("redirect visited")
    print(auth_param)
    return {"message": "redirect visited"}


