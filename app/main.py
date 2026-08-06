import os
import sys
from pathlib import Path

# Add project root directory to sys.path so app can be imported when running script directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.database import engine, Base, get_db
from app.auth import get_current_user_from_cookie
from app.pricing import get_pricing_config
from app.routers import auth, profile, orders, admin, feedback


# Create database tables if they do not exist
Base.metadata.create_all(bind=engine)

app = FastAPI(title="ReelToDigit", version="1.0.0")

# Mount Static Files
os.makedirs("app/static/css", exist_ok=True)
os.makedirs("app/static/js", exist_ok=True)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")

# Include Routers
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(orders.router)
app.include_router(admin.router)
app.include_router(feedback.router)

@app.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_from_cookie(request, db)
    pricing = get_pricing_config(db)
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "user": user,
            "pricing": pricing
        }
    )

if __name__ == "__main__":
    import uvicorn
    import sys
    from pathlib import Path
    # Ensure current working dir is in sys.path when executed directly
    sys.path.insert(0, str(Path(__file__).parent.parent))
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)

