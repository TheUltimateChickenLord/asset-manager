"""FastAPI app for asset_manager"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from asset_manager.core.middleware import LoggingMiddleware
from asset_manager.db.base import Base
from asset_manager.db.session import engine
from asset_manager.routes import auth


Base.metadata.create_all(engine)

app = FastAPI()

app.add_middleware(LoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
