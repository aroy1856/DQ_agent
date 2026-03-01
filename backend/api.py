"""
FastAPI application for the DQ Agent.

Multi-turn conversation support with thread management and AI rule generation.
"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from src.dq_agent.api.thread_routes import router as thread_router
from src.dq_agent.api.rules_routes import router as rules_router


load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not os.environ.get("OPENAI_API_KEY"):
        print("WARNING: OPENAI_API_KEY not set.")
    yield


app = FastAPI(
    title="DQ Agent API",
    description="Data Quality Agent with AI rule generation",
    version="2.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(thread_router, prefix="/thread", tags=["Threads"])
app.include_router(rules_router, prefix="/thread", tags=["Rules"])


@app.get("/")
async def root():
    return {"status": "healthy", "service": "DQ Agent API", "version": "2.1.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
