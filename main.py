from fastapi import FastAPI

from api import loans, ussd

app = FastAPI(title="Umoja Loans API", version="1.0.0")

# Include routers
app.include_router(ussd.router, prefix="/api/v1", tags=["USSD"])
app.include_router(loans.router, prefix="/api/v1", tags=["Loans"])


@app.get("/")
async def root():
    return {"message": "Welcome to Umoja Loans API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
