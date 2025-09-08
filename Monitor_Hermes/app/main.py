# App starting point
from fastapi import FastAPI, Depends
from app.ws.routes import router as ws_router
from contextlib import asynccontextmanager
from app.persistence.mongo import (
    connect_to_mongo,
    close_mongo_connection,
    get_db,
    save_message,
)
from app.persistence.models import MessageIn
from app.mqtt.client import start_mqtt
import loguru
import asyncio


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    loop = asyncio.get_event_loop()
    db = await get_db()
    start_mqtt(db, loop)
    yield
    await close_mongo_connection()


app = FastAPI(lifespan=lifespan)

app.include_router(ws_router)


@app.post("/messages")
async def create_message(message: MessageIn, db=Depends(get_db)):
    insert_id = await save_message(db, message)
    return {"insert_id": insert_id}
