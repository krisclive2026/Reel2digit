from typing import Optional
from fastapi import APIRouter, Request, Depends, Form, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
import uuid
from app.models import Order, PricingConfig, User, MediaAsset, Cassette, Payment, ShippingLabel
from app.auth import get_current_admin, get_current_user_from_cookie
from app.storage import upload_media_asset

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/admin", response_class=HTMLResponse)
def get_admin_dashboard(
    request: Request,
    status_filter: Optional[str] = None,
    message: str = None,
    error: str = None,
    db: Session = Depends(get_db)
):
    admin = get_current_admin(request, db)

    query = db.query(Order)
    if status_filter:
        query = query.filter(Order.status == status_filter)
    orders = query.order_by(Order.created_at.desc()).all()

    pricing = db.query(PricingConfig).first()
    if not pricing:
        pricing = PricingConfig(unit_price=15.00, shipping_flat=8.99, max_cassettes=50)
        db.add(pricing)
        db.commit()
        db.refresh(pricing)

    users = db.query(User).order_by(User.created_at.desc()).all()

    all_statuses = ["draft", "paid", "label_ready", "in_transit", "received", "processing", "completed", "cancelled"]

    return templates.TemplateResponse(
        request=request,
        name="admin_dashboard.html",
        context={
            "user": admin,
            "orders": orders,
            "pricing": pricing,
            "users": users,
            "status_filter": status_filter,
            "all_statuses": all_statuses,
            "message": message,
            "error": error
        }
    )

@router.post("/admin/orders/{order_id}/status")
def update_order_status(
    order_id: int,
    request: Request,
    new_status: str = Form(...),
    db: Session = Depends(get_db)
):
    admin = get_current_admin(request, db)
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order.status = new_status
    db.commit()

    return RedirectResponse(
        url=f"/admin?message=Order+{order.order_number}+status+updated+to+{new_status}.",
        status_code=303
    )

@router.post("/admin/orders/{order_id}/confirm-payment")
def confirm_upi_payment(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Manually confirms a UPI payment the admin has verified in their bank/UPI
    app, since there's no payment gateway generating an automatic webhook."""
    admin = get_current_admin(request, db)
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != "draft":
        return RedirectResponse(
            url=f"/admin?error=Order+{order.order_number}+is+not+awaiting+payment.",
            status_code=303
        )

    payment = Payment(
        order_id=order.id,
        amount=order.total_price,
        provider="upi_manual",
        status="captured"
    )
    db.add(payment)

    tracking_num = f"RTD-TRACK-{uuid.uuid4().hex[:8].upper()}"
    label = ShippingLabel(
        order_id=order.id,
        tracking_number=tracking_num,
        carrier="India Post",
        label_url=f"/orders/{order.id}/label"
    )
    db.add(label)

    order.status = "label_ready"
    db.commit()

    return RedirectResponse(
        url=f"/admin?message=Payment+confirmed+for+{order.order_number}.+Shipping+label+is+ready.",
        status_code=303
    )

@router.post("/admin/orders/{order_id}/media")
async def add_order_media(
    order_id: int,
    request: Request,
    file_name: Optional[str] = Form(None),
    file_url: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    cassette_id: Optional[int] = Form(None),
    db: Session = Depends(get_db)
):
    admin = get_current_admin(request, db)
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    final_name = file_name.strip() if file_name else None
    final_url = file_url.strip() if file_url else None

    # Handle file upload if provided
    if file and file.filename:
        provider, identifier = upload_media_asset(file.file, file.filename)
        final_url = identifier
        if not final_name:
            import os
            _, ext = os.path.splitext(file.filename)
            final_name = f"Digitized_Tape{ext or '.mp3'}"

    if not final_url:
        return RedirectResponse(
            url=f"/admin?error=Please+select+a+file+to+upload+or+provide+a+file+URL.",
            status_code=303
        )

    media = MediaAsset(
        order_id=order.id,
        cassette_id=cassette_id if cassette_id else None,
        file_name=final_name or "Digitized_Tape.mp3",
        file_url=final_url
    )
    db.add(media)
    
    # Auto transition to completed if media added
    if order.status != "completed":
        order.status = "completed"

    db.commit()

    return RedirectResponse(
        url=f"/admin?message=Uploaded+media+asset+for+Order+{order.order_number}.",
        status_code=303
    )

@router.post("/admin/pricing")
def update_pricing(
    request: Request,
    unit_price: float = Form(...),
    shipping_flat: float = Form(...),
    max_cassettes: int = Form(...),
    db: Session = Depends(get_db)
):
    admin = get_current_admin(request, db)
    pricing = db.query(PricingConfig).first()
    if not pricing:
        pricing = PricingConfig()
        db.add(pricing)

    pricing.unit_price = max(0.01, round(unit_price, 2))
    pricing.shipping_flat = max(0.00, round(shipping_flat, 2))
    pricing.max_cassettes = max(1, max_cassettes)

    db.commit()

    return RedirectResponse(
        url="/admin?message=Pricing+config+updated+successfully.",
        status_code=303
    )

@router.post("/admin/users/{user_id}/promote")
def promote_user_role(
    user_id: int,
    request: Request,
    role: str = Form("admin"),
    db: Session = Depends(get_db)
):
    admin = get_current_admin(request, db)
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    target_user.role = role
    db.commit()

    return RedirectResponse(
        url=f"/admin?message=User+{target_user.email}+role+updated+to+{role}.",
        status_code=303
    )
