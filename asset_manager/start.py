"""Entrypoint for the application"""

import uvicorn


def start():
    """Use uvicorn to start the FastAPI app"""
    uvicorn.run("asset_manager.main:app", host="0.0.0.0", port=8000, reload=True)
