"""
FastAPI Application for Authentication and User Management.

This application provides endpoints for user authentication, social authentication,
and user management operations.

Dependencies:
    - Python 3.7+
    - FastAPI
    - uvicorn
    - dotenv

Environment Variables:
    - HOST: Hostname for the FastAPI server.
    - PORT: Port number for the FastAPI server.

Middleware:
    - CORS: Cross-Origin Resource Sharing middleware to handle CORS headers.

Routers:
    - /api/v1/auth: Authentication routes.
    - /api/v1/social-auth: Social authentication routes.
    - /api/v1/user: User management routes.

Exceptions Handled:
    - RequestValidationError: Custom handler to manage validation errors and provide structured JSON responses.

"""

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi

# Import routers
from modules.auth.auth_route import router as auth_router
from modules.social_auth.social_auth_route import router as social_auth_router
from modules.user.user_route import router as user_router

# Import middleware
from middlewares.validation_exception_handler import validation_exception_handler
from starlette.middleware.cors import CORSMiddleware

# Other imports
import os
from dotenv import load_dotenv
import uvicorn

# Initialize FastAPI application
app = FastAPI(docs_url="/documentation", redoc_url=None)

# Load environment variables
load_dotenv()

# Read HOST and PORT from environment variables
host = os.getenv("HOST")
port = int(os.getenv("PORT"))

# Custom error handling for validation errors
app.add_exception_handler(RequestValidationError, validation_exception_handler)


# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this as needed for security
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# OpenAPI metadata
def custom_openapi():
    openapi_schema = get_openapi(
        title="Fast Api Auth", version="1.0.0", description="This is a sample FastAPI project with Swagger documentation.", routes=app.routes, openapi_version="3.1.0"
    )
    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    for path, methods in openapi_schema["paths"].items():
        for method, details in methods.items():
            if path.startswith("/api/v1/user"):
                details["security"] = [{"bearerAuth": [{"users": True}]}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


# Serve Swagger UI
@app.get("/api/v1/documentation", include_in_schema=False)
async def get_documentation():
    return get_swagger_ui_html(openapi_url="/api/v1/openapi.json", title="API Documentation")


@app.get("/docs", include_in_schema=False)
async def redirect_to_docs():
    return RedirectResponse(url="/api/v1/documentation")


@app.get("/api/v1/openapi.json", include_in_schema=False)
async def get_open_api_endpoint():
    return JSONResponse(content=custom_openapi())


# Include routers
app.include_router(user_router, prefix="/api/v1/user", tags=["users"])
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(social_auth_router, prefix="/api/v1/social-auth", tags=["social-auth"])


if __name__ == "__main__":
    uvicorn.run("main:app", host=host, port=port, reload=True)
