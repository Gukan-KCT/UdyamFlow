import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.application_routes import application_router
from app.api.audit_routes import audit_router
from app.api.auth_routes import auth_router
from app.api.checklist_routes import checklist_router
from app.api.compliance_routes import certificate_router, compliance_router, schemes_router
from app.api.delay_analytics_routes import delay_analytics_router
from app.api.document_routes import document_router
from app.api.grievance_routes import grievance_router
from app.api.inspection_routes import inspection_router
from app.api.profile_routes import profile_router
from app.api.routes import router
from app.db import get_connection, init_db
from app.seed.seed_data import seed_all_udyamflow_data

IS_VERCEL = bool(os.getenv("VERCEL"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup hook – lightweight on Vercel, full pipeline locally."""
    try:
        if IS_VERCEL:
            # Serverless: only init schema + seed demo data (fast, no LLM)
            with get_connection() as conn:
                init_db(conn)
                from app.db import ingest_csv_data
                ingest_csv_data(conn)
                seed_all_udyamflow_data(conn)
        else:
            # Local dev: run the full detection & insight pipeline
            from app.core.orchestrator import run_full_pipeline
            with get_connection() as conn:
                await run_full_pipeline(conn, top_k_ai_insights=0)
    except Exception as e:
        print(f"Warning: Startup pipeline encountered error: {e}")
    yield


app = FastAPI(
    title="FilePulse & Single-Window API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Configuration – permissive on Vercel, strict locally
if IS_VERCEL:
    allow_origins = ["*"]
    allow_credentials = False
    origin_regex = r"https://.*\.vercel\.app"
else:
    raw_cors = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    origins = [origin.strip() for origin in raw_cors.split(",") if origin.strip()]
    if not origins or "*" in origins:
        allow_origins = ["*"]
        allow_credentials = False
    else:
        allow_origins = origins
        allow_credentials = True
    origin_regex = None

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_origin_regex=origin_regex,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(auth_router)
app.include_router(audit_router)
app.include_router(profile_router)
app.include_router(checklist_router)
app.include_router(application_router)
app.include_router(document_router)
app.include_router(inspection_router)
app.include_router(grievance_router)
app.include_router(delay_analytics_router)
app.include_router(compliance_router)
app.include_router(certificate_router)
app.include_router(schemes_router)


# Standardized Error Handling
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "status_code": exc.status_code,
            "detail": exc.detail,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": True,
            "status_code": 422,
            "detail": exc.errors(),
            "message": "Input validation failed",
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "status_code": 500,
            "detail": "An internal server error occurred.",
        },
    )


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "project": "FilePulse",
        "environment": "vercel" if IS_VERCEL else "local",
    }
