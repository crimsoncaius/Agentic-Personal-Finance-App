# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .database import Base, engine
from .init_db import seed_categories
from .routers import categories, transactions, reports, agent, auth
from .migrations import migrate_database

# 1. Run database migrations
migrate_database()

# 2. Create tables
Base.metadata.create_all(bind=engine)

# 3. Seed categories
seed_categories()

# 4. Create FastAPI app
app = FastAPI(
    title="Personal Finance App",
    description="Track expenses, incomes, and generate basic reports.",
    version="1.0.0",
    # Disable automatic redirects for trailing slashes
    redirect_slashes=False,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React dev server default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 5. Include Routers
app.include_router(auth.router)  # Add auth router first
app.include_router(categories.router)
app.include_router(transactions.router)
app.include_router(reports.router)
app.include_router(agent.router)

if __name__ == "__main__":
    # Run the app
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
