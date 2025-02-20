from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import orders
from app.core.database import pg_engine
from app.core.logging_config import setup_logging
from app.models.models import Base
import logging

# Set up logging
logger = setup_logging()
logger = logging.getLogger('app.main')

app = FastAPI(
    title="Orders API",
    description="API for managing orders with PostgreSQL and MySQL sync",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables
Base.metadata.create_all(bind=pg_engine)
logger.info("Database tables created successfully")

# Include routers
app.include_router(orders.router)
logger.info("API routes initialized successfully")

@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "Welcome to Orders API!"}
