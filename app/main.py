from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .database import init_db
from .routers import projects, requirements, persons, commits, tests, tickets
import os

app = FastAPI(title="TrackTix – Requirement Traceability System", version="1.0.0")

@app.on_event("startup")
def startup():
    init_db()

# API routes
app.include_router(projects.router,     prefix="/api")
app.include_router(requirements.router, prefix="/api")
app.include_router(persons.router,      prefix="/api")
app.include_router(commits.router,      prefix="/api")
app.include_router(tests.router,        prefix="/api")
app.include_router(tickets.router,      prefix="/api")

# Static files
_base = os.path.dirname(os.path.dirname(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(_base, "static")), name="static")

@app.get("/", include_in_schema=False)
def index():
    return FileResponse(os.path.join(_base, "static", "index.html"))

@app.get("/{path:path}", include_in_schema=False)
def spa(path: str):
    return FileResponse(os.path.join(_base, "static", "index.html"))
