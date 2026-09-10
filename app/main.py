import os

from fastapi import FastAPI, Depends, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, constr
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.agent.runner import run_travel_agent
from app.agent.graph import check_db_health
from app.config import APP_API_KEY, ENVIRONMENT, LOCAL_PDF_DIR, FRONTEND_ORIGINS
from app.logging_config import logger

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="Travel Agent API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS: required for the browser frontend to be able to call this API at all.
# Restrict to your actual frontend domain(s) in production - do NOT use "*"
# once this is public, or any site on the internet can call your API from
# a visitor's browser using their rate-limit slot.
app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "x-api-key"],
)


class ChatRequest(BaseModel):
    message: constr(min_length=1, max_length=2000)
    thread_id: str | None = None


def verify_api_key(x_api_key: str | None = Header(default=None)):
    """
    Server-to-server auth. NOT used to protect the public /chat endpoint,
    since a key shipped in a browser bundle isn't actually secret (anyone
    can read it from devtools/Network tab). Use this only on endpoints you
    intend to call from your own backend, scripts, or another service -
    for the public browser widget, CORS + rate limiting below are the real
    protection.
    """
    if ENVIRONMENT != "production" and not APP_API_KEY:
        return  # allow unauthenticated calls in local dev if no key is configured
    if x_api_key != APP_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


@app.get("/health")
def health():
    db_ok = check_db_health()
    if not db_ok:
        raise HTTPException(status_code=503, detail="Database unavailable")
    return {"status": "ok"}


@app.post("/chat")
@limiter.limit("4/minute")
def chat(request: Request, body: ChatRequest):
    """
    Public endpoint for the browser frontend. Protected by CORS (only your
    configured frontend origin can call it from a browser) and per-IP rate
    limiting, not by API key - see verify_api_key's docstring for why.
    """
    try:
        result = run_travel_agent(body.message, body.thread_id)
        return result
    except Exception:
        logger.exception("chat endpoint failed")
        raise HTTPException(
            status_code=500,
            detail="Too many requests. Try again after some time.",
        )


@app.get("/download/{filename}")
def download(filename: str):
    """
    Only needed when PDF_BUCKET is not configured, i.e. pdf_path from /chat
    is a local file path rather than a presigned S3 URL. In production with
    PDF_BUCKET set, the frontend should just use the URL returned directly
    in pdf_path and this endpoint is unused.
    """
    safe_name = os.path.basename(filename)  # prevent path traversal
    path = os.path.join(LOCAL_PDF_DIR, safe_name)
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path, media_type="application/pdf", filename=safe_name)


@app.post("/admin/chat", dependencies=[Depends(verify_api_key)])
@limiter.limit("10/minute")
def admin_chat(request: Request, body: ChatRequest):
    """
    Example of a key-protected route for server-to-server use (internal
    tools, scripts, another backend) - not called by the browser frontend.
    """
    result = run_travel_agent(body.message, body.thread_id)
    return result