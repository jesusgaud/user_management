from builtins import Exception
from fastapi import FastAPI
from starlette.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

from app.database import Database
from app.dependencies import get_settings
from app.routers import user_routes
from app.utils.api_description import getDescription

from fastapi.staticfiles import StaticFiles
import os

app = FastAPI(
    title="User Management",
    description=getDescription(),
    version="0.0.1",
    contact={
        "name": "API Support",
        "url": "http://www.example.com/support",
        "email": "support@example.com",
    },
    license_info={"name": "MIT", "url": "https://opensource.org/licenses/MIT"},
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    settings = get_settings()
    Database.initialize(settings.database_url, settings.debug)

    # ✅ Ensure models are loaded before creating tables
    from app.models import user_model  # Import model to register with Base
    await Database.create_tables()

    # Create directory for profile pictures if not exists
    os.makedirs("profile_pictures", exist_ok=True)

@app.exception_handler(Exception)
async def exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"message": "An unexpected error occurred."}
    )

# Register all API routes
app.include_router(user_routes.router)

# Mount static files for profile pictures
app.mount("/profile_pictures", StaticFiles(directory="profile_pictures"), name="profile_pics")
