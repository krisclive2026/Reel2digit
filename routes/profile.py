from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user_from_cookie, get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/profile", response_class=HTMLResponse)
def get_profile(
    request: Request,
    message: str = None,
    db: Session = Depends(get_db)
):
    user = get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/login?next_url=/profile", status_code=303)
    return templates.TemplateResponse(
        request=request,
        name="profile.html",
        context={
            "user": user,
            "message": message,
            "error": None
        }
    )

@router.post("/profile", response_class=HTMLResponse)
def post_profile(
    request: Request,
    full_name: str = Form(...),
    phone: str = Form(""),
    street_address: str = Form(""),
    city: str = Form(""),
    state: str = Form(""),
    postal_code: str = Form(""),
    country: str = Form("USA"),
    db: Session = Depends(get_db)
):
    user = get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    user.full_name = full_name.strip()
    user.phone = phone.strip()
    user.street_address = street_address.strip()
    user.city = city.strip()
    user.state = state.strip()
    user.postal_code = postal_code.strip()
    user.country = country.strip()

    db.commit()
    db.refresh(user)

    return templates.TemplateResponse(
        request=request,
        name="profile.html",
        context={
            "user": user,
            "message": "Profile and shipping address updated successfully!",
            "error": None
        }
    )
