from fastapi import FastAPI
from jinja2 import Environment, Template, FileSystemLoader
import os
from pathlib import Path
from app.routes.template_routes import router as template_router
import app.models
from app.database import Base, engine

Base.metadata.create_all(bind=engine)

env = Environment(loader=FileSystemLoader("templates"))

app = FastAPI()
app.include_router(template_router, prefix="/templates")