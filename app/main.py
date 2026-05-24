from fastapi import FastAPI
from app.routes.template_routes import router as template_router
from app.routes.notification_routes import router as notification_router
from app.routes.user_routes import router as user_router
import app.models
from app.database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(template_router, prefix="/templates")
app.include_router(notification_router, prefix="/notifications")
app.include_router(user_router, prefix="/users")