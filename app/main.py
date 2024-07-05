from fastapi import FastAPI, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import (
    get_swagger_ui_html,
    get_redoc_html,
)
from fastapi.openapi.utils import get_openapi
from starlette.middleware.cors import CORSMiddleware

# Import routers
from app.modules.auth.auth_route import router as auth_router
from app.modules.social_auth.social_auth_route import (
    router as social_auth_router,
)
from app.modules.user.user_route import router as user_router


app = FastAPI()


# Custom error handling for validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    error_messages = ""
    for error in exc.errors():
        field_name = error.get("loc")[1]  # Get the field name from the error location
        if error.get("type") == "value_error":
            error_messages += f"{field_name.capitalize()} {error.get('msg')}. "
        elif error.get("type") == "string_too_short":
            error_messages += f"{field_name.capitalize()} should have at least 8 characters. "
        else:
            error_messages += f"{field_name.capitalize()} {error.get('msg')}. "

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": error_messages.strip()},
    )


# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this as needed for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# OpenAPI metadata
def custom_openapi():
    openapi_schema = get_openapi(
        title="Fast Api Auth",
        version="1.0.0",
        description="This is a sample FastAPI project with Swagger documentation.",
        routes=app.routes,
    )
    return openapi_schema


# Serve Swagger UI
@app.get("/docs", include_in_schema=False)
async def get_documentation():
    return get_swagger_ui_html(openapi_url="/openapi.json", title="API Documentation")


@app.get("/openapi.json", include_in_schema=False)
async def get_open_api_endpoint():
    return JSONResponse(content=custom_openapi())


# Include ReDoc if needed
@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(openapi_url="/openapi.json", title="API Documentation")


# Include routers
app.include_router(user_router, prefix="/api/v1/users", tags=["users"])
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(social_auth_router, prefix="/api/v1/social-auth", tags=["social-auth"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
