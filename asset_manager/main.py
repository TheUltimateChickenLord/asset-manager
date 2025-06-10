"""FastAPI app for asset_manager"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from asset_manager.core.middleware import LoggingMiddleware
from asset_manager.db.base import Base
from asset_manager.db.session import engine
from asset_manager.routes import (
    user,
    role,
    auth,
    assets,
    requests,
    assignments,
    labels,
    maintenance,
)


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
app.include_router(user.router, prefix="/api/users")
app.include_router(role.router, prefix="/api/roles")
app.include_router(assets.router, prefix="/api/assets")
app.include_router(requests.router, prefix="/api/requests")
app.include_router(assignments.router, prefix="/api/assignments")
app.include_router(labels.router, prefix="/api/labels")
app.include_router(maintenance.router, prefix="/api/maintenance")
