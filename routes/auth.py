from fastapi import APIRouter, Request, Depends, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.auth import hash_password, verify_password, create_access_token, COOKIE_NAME, get_current_user_from_cookie

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/register", response_class=HTMLResponse)
def get_register(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_from_cookie(request, db)
    if user:
        return RedirectResponse(url="/profile", status_code=303)
    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={"user": user, "error": None}
    )

@router.post("/register", response_class=HTMLResponse)
def post_register(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    full_name: str = Form(...),
    phone: str = Form(""),
    db: Session = Depends(get_db)
):
    email = email.strip().lower()
    if password != confirm_password:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={
                "user": None,
                "error": "Passwords do not match.",
                "email": email,
                "full_name": full_name,
                "phone": phone
            },
            status_code=400
        )

    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={
                "user": None,
                "error": "An account with this email already exists.",
                "email": email,
                "full_name": full_name,
                "phone": phone
            },
            status_code=400
        )

    new_user = User(
        email=email,
        hashed_password=hash_password(password),
        full_name=full_name,
        phone=phone,
        role="customer"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token({"sub": str(new_user.id)})
    response = RedirectResponse(url="/profile?message=Account+created!+Please+complete+your+shipping+address.", status_code=303)
    response.set_cookie(key=COOKIE_NAME, value=token, httponly=True, max_age=86400 * 7)
    return response

@router.get("/login", response_class=HTMLResponse)
def get_login(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_from_cookie(request, db)
    if user:
        return RedirectResponse(url="/orders", status_code=303)
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"user": user, "error": None}
    )

@router.post("/login", response_class=HTMLResponse)
def post_login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    next_url: str = Form("/orders"),
    db: Session = Depends(get_db)
):
    email = email.strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "user": None,
                "error": "Invalid email or password.",
                "email": email
            },
            status_code=400
        )

    token = create_access_token({"sub": str(user.id)})
    dest = next_url if next_url and next_url.startswith("/") else "/orders"
    response = RedirectResponse(url=dest, status_code=303)
    response.set_cookie(key=COOKIE_NAME, value=token, httponly=True, max_age=86400 * 7)
    return response

@router.get("/logout")
def get_logout():
    response = RedirectResponse(url="/login?message=Logged+out+successfully.", status_code=303)
    response.delete_cookie(COOKIE_NAME)
    return response
