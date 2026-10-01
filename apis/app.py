"""
General Ledger Anomaly Monitor — FastAPI Web Application Server
"""
from __future__ import annotations
import os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from apis.routes import router

app = FastAPI(
    title="SAP Vendor Intelligence & AP Risk Agent (VIRA)",
    version="3.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


def get_dashboard_html() -> str:
    possible_paths = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "dashboard.html"),
        os.path.join(os.getcwd(), "frontend", "dashboard.html"),
        os.path.join(os.getcwd(), "dashboard.html"),
    ]
    for path in possible_paths:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
    return "<h1>Error: frontend/dashboard.html not found</h1>"


@app.get("/", response_class=HTMLResponse)
def dashboard():
    return HTMLResponse(get_dashboard_html())
