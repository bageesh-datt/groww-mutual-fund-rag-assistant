"""
FastAPI Main Application Entry Point
Exposes REST API endpoints for RAG chat queries, system health monitoring, and admin ingestion triggers.
Includes standard library fallback HTTP server for zero-dependency local execution.
"""

import json
import os
import re
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.config import settings
from app.ingestion.scheduler import start_scheduler, stop_scheduler, run_ingestion_job, get_scheduler_status
from app.rag.intent import classify_query_intent
from app.rag.refusal import generate_refusal_response
from app.rag.retriever import retrieve_context
from app.rag.generator import synthesize_grounded_answer
from app.rag.vector_store import vector_store_manager
from app.utils.logger import get_logger

logger = get_logger("app.main")

def handle_chat_query(query: str) -> dict:
    """
    Core RAG Chat query processing pipeline.
    """
    query = query.strip()
    if not query:
        return {"status": "error", "message": "Query cannot be empty"}

    logger.info(f"Processing chat query: '{query}'")

    # 1. Intent Classification
    intent_info = classify_query_intent(query)
    intent_type = intent_info["intent"]

    # 2. Refusal Handling for Non-Factual Intents
    if intent_type in ["ADVISORY", "PERFORMANCE", "UNSUPPORTED"]:
        refusal_res = generate_refusal_response(intent_info)
        return {
            "status": refusal_res["status"],
            "intent": intent_type,
            "answer": refusal_res["answer"],
            "source_url": refusal_res["source_url"],
            "last_updated": refusal_res["last_updated"],
            "disclaimer": settings.DISCLAIMER_TEXT
        }

    # 3. Factual Query RAG Pipeline
    scheme_slug = intent_info.get("scheme_slug")
    fact_type = intent_info.get("fact_type")

    retrieval_res = retrieve_context(
        query=query,
        scheme_slug=scheme_slug,
        fact_type=fact_type,
        top_k=3,
        confidence_threshold=settings.CONFIDENCE_THRESHOLD
    )

    if not retrieval_res["has_context"]:
        logger.warning(f"No context retrieved for query: '{query}'")
        return {
            "status": "fallback",
            "intent": intent_type,
            "answer": settings.FALLBACK_RESPONSE_TEXT,
            "source_url": None,
            "last_updated": None,
            "disclaimer": settings.DISCLAIMER_TEXT
        }

    generation_res = synthesize_grounded_answer(query, retrieval_res["retrieved_chunks"])

    return {
        "status": generation_res["status"],
        "intent": intent_type,
        "answer": generation_res["answer"],
        "source_url": generation_res["source_url"],
        "last_updated": generation_res["last_updated"],
        "disclaimer": settings.DISCLAIMER_TEXT
    }

# Try FastAPI Setup
try:
    from pydantic import BaseModel, Field
    from fastapi import FastAPI, HTTPException, status
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import FileResponse

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logger.info("==================================================")
        logger.info("STARTING GROWW FAQ ASSISTANT FASTAPI BACKEND")
        logger.info("==================================================")
        try:
            start_scheduler()
        except Exception as e:
            logger.error(f"Scheduler startup error: {e}")
        yield
        try:
            stop_scheduler()
        except Exception as e:
            logger.error(f"Scheduler shutdown error: {e}")

    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description="Facts-Only RAG Mutual Fund FAQ Assistant grounded exclusively in 5 Groww scheme URLs.",
        lifespan=lifespan
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    class ChatRequest(BaseModel):
        query: str = Field(..., example="What is the exit load of HDFC Mid-Cap Opportunities Fund Direct Growth?")
        session_id: str | None = Field(default=None, example="usr_sess_123")

    @app.get("/api/v1/health")
    async def health_check():
        stats = vector_store_manager.get_stats()
        scheduler_info = get_scheduler_status()
        return {
            "status": "healthy",
            "project": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
            "scheduler": scheduler_info,
            "vector_store": stats
        }

    @app.post("/api/v1/chat")
    async def chat_query_endpoint(request: ChatRequest):
        res = handle_chat_query(request.query)
        if res.get("status") == "error":
            raise HTTPException(status_code=400, detail=res["message"])
        return res

    @app.post("/api/v1/ingest")
    async def trigger_ingestion_endpoint():
        res = run_ingestion_job()
        return res

    @app.get("/")
    async def root():
        index_file = backend_dir.parent / "frontend" / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return {
            "message": f"Welcome to {settings.PROJECT_NAME} API v{settings.VERSION}",
            "docs": "/docs",
            "chat_endpoint": "/api/v1/chat",
            "health_endpoint": "/api/v1/health"
        }

except ImportError:
    logger.warning("FastAPI/Pydantic not installed. Using standard library HTTP server fallback.")
    app = None

# Standard Library HTTP Server Fallback for Standalone Execution
if __name__ == "__main__":
    if app:
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)
    else:
        from http.server import HTTPServer, BaseHTTPRequestHandler

        class SimpleHTTPHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == "/" or self.path == "/index.html":
                    index_file = backend_dir.parent / "frontend" / "index.html"
                    if index_file.exists():
                        self.send_response(200)
                        self.send_header("Content-Type", "text/html; charset=utf-8")
                        self.end_headers()
                        with open(index_file, "rb") as f:
                            self.wfile.write(f.read())
                        return

                if self.path == "/api/v1/health":
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    res = {
                        "status": "healthy",
                        "project": settings.PROJECT_NAME,
                        "version": settings.VERSION,
                        "scheduler": get_scheduler_status(),
                        "vector_store": vector_store_manager.get_stats()
                    }
                    self.wfile.write(json.dumps(res).encode())
                    return

                self.send_response(404)
                self.end_headers()

            def do_POST(self):
                if self.path == "/api/v1/chat":
                    length = int(self.headers.get("Content-Length", 0))
                    body = self.rfile.read(length).decode("utf-8")
                    data = json.loads(body) if body else {}
                    query = data.get("query", "")
                    
                    res = handle_chat_query(query)

                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(json.dumps(res).encode())
                    return

                if self.path == "/api/v1/ingest":
                    res = run_ingestion_job()
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(json.dumps(res).encode())
                    return

                self.send_response(404)
                self.end_headers()

            def do_OPTIONS(self):
                self.send_response(200)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
                self.send_header("Access-Control-Allow-Headers", "Content-Type")
                self.end_headers()

        logger.info("Starting Groww FAQ Assistant HTTP Server on http://localhost:8000 ...")
        httpd = HTTPServer(("0.0.0.0", 8000), SimpleHTTPHandler)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            logger.info("Server stopped.")
