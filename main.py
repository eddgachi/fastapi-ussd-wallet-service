from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from fastapi.middleware.gzip import GZipMiddleware

from core.limiter import limiter

from api import loans, mpesa, ussd, admin

app = FastAPI(title="Umoja Loans API", version="1.0.0")

# Initialize Limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add Gzip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Include routers
app.include_router(ussd.router, prefix="/api/v1", tags=["USSD"])
app.include_router(loans.router, prefix="/api/v1", tags=["Loans"])
app.include_router(mpesa.router, prefix="/api/v1", tags=["M-Pesa"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])


@app.get("/")
async def root():
    return {"message": "Welcome to Umoja Loans API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
