# App starting point
from fastapi import FastAPI
from app.ws.routes import router as ws_router

app = FastAPI()

app.include_router(ws_router)
