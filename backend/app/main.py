from fastapi import FastAPI, Query
from api.main import api_router
from typing import Annotated

app = FastAPI()

app.include_router(api_router)



