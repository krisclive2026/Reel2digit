import uuid
from typing import List
from fastapi import APIRouter, Request, Depends, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Order, Cassette, ShippingLabel, Payment, User, MediaAsset
from app.auth import get_current_user_from_cookie
from app.pricing import get_pricing_config, calculate_order_price
from app.payments import build_upi_link, generate_qr_base64

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/orders", response_class=HTMLResponse)
def list_orders(
    request: Request,
    message: str = None,
    error: str = None,
    db: Session = Depends(get_db)
):
    user = get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/login?next_url=/orders", status_code=303)

    orders = db.query(Order).filter(Order.user_id == user.id).order_by(Order.created_at.desc()).all()
    return templates.TemplateResponse(
        request=request,
        name="orders_list.html",
        context={
            "user": user,
            "orders": orders,
            "message": message,
            "error": error
        }
    )

@router.get("/orders/new", response_class=HTMLResponse)
def get_new_order(
    request: Request,
    error: str = None,
    db: Session = Depends(get_db)
):
    user = get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/login?next_url=/orders/new", status_code=303)

    # Check if address is populated
    has_address = bool(user.street_address and user.city and user.state and user.postal_code)
    pricing = get_pricing_config(db)

    return templates.TemplateResponse(
        request=request,
        name="order_wizard.html",
        context={
            "user": user,
            "has_address": has_address,
            "pricing": pricing,
            "error": error
        }
    )

@router.post("/orders/calculate")
def api_calculate_price(
    cassette_count: int = Form(...),
    db: Session = Depends(get_db)
):
    pricing = get_pricing_config(db)
    count = max(1, min(cassette_count, pricing.max_cassettes))
    calc = calculate_order_price(count, pricing.unit_price, pricing.shipping_flat)
    return JSONResponse(calc)

@router.post("/orders/new")
def post_new_order(
    request: Request,
    cassette_count: int = Form(...),
    format: str = Form("MP3"),
    accept_terms: str = Form(None),
    db: Session = Depends(get_db)
):
    user = get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    if accept_terms != "on":
        return RedirectResponse(url="/orders/new?error=You+must+accept+the+Terms+%26+Conditions+to+place+an+order.", status_code=303)

    if not user.street_address or not user.city or not user.state or not user.postal_code:
        return RedirectResponse(url="/profile?error=Please+complete+your+shipping+address+before+placing+an+order.", status_code=303)

    pricing = get_pricing_config(db)
    count = max(1, min(cassette_count, pricing.max_cassettes))

    calc = calculate_order_price(count, pricing.unit_price, pricing.shipping_flat)

    new_order = Order(
        user_id=user.id,
        status="draft",
        cassette_count=count,
        format=format.upper() if format.upper() in ["MP3", "MP4"] else "MP3",
        unit_price=calc["unit_price"],
        shipping_fee=calc["shipping"],
        total_price=calc["total"]
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    return RedirectResponse(url=f"/orders/{new_order.id}/configure", status_code=303)

@router.get("/orders/{order_id}/configure", response_class=HTMLResponse)
def get_configure_cassettes(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    user = get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    order = db.query(Order).filter(Order.id == order_id, Order.user_id == user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    pricing = get_pricing_config(db)
    existing_tags = [c.tag_name for c in order.cassettes]

    return templates.TemplateResponse(
        request=request,
        name="order_configure.html",
        context={
            "user": user,
            "order": order,
            "existing_tags": existing_tags,
            "pricing": pricing,
            "error": None
        }
    )

@router.post("/orders/{order_id}/configure")
async def post_configure_cassettes(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    user = get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    order = db.query(Order).filter(Order.id == order_id, Order.user_id == user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    form_data = await request.form()
    
    # Remove old cassettes if re-configuring
    db.query(Cassette).filter(Cassette.order_id == order.id).delete()

    cassettes_added = 0
    for i in range(1, order.cassette_count + 1):
        tag_val = form_data.get(f"tag_{i}", f"Cassette {i}").strip()
        if not tag_val:
            tag_val = f"Cassette {i}"
        cassette = Cassette(
            order_id=order.id,
            tag_name=tag_val,
            sequence=i
        )
        db.add(cassette)
        cassettes_added += 1

    db.commit()
    db.refresh(order)

    return RedirectResponse(url=f"/orders/{order.id}", status_code=303)

@router.get("/orders/{order_id}", response_class=HTMLResponse)
def get_order_detail(
    order_id: int,
    request: Request,
    message: str = None,
    error: str = None,
    db: Session = Depends(get_db)
):
    user = get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url=f"/login?next_url=/orders/{order_id}", status_code=303)

    # Allow customer to view own order, or admin to view any order
    order_query = db.query(Order).filter(Order.id == order_id)
    if user.role != "admin":
        order_query = order_query.filter(Order.user_id == user.id)

    order = order_query.first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Order Status timeline list
    statuses = [
        ("draft", "Draft Created"),
        ("paid", "Payment Recieved"),
        ("label_ready", "Shipping Label Ready"),
        ("in_transit", "In Transit to Lab"),
        ("received", "Received at Lab"),
        ("processing", "Digitization in Progress"),
        ("completed", "Completed & MP3 Ready")
    ]

    status_order = ["draft", "paid", "label_ready", "in_transit", "received", "processing", "completed"]
    current_idx = status_order.index(order.status) if order.status in status_order else -1

    # Generate a UPI QR (GPay/PhonePe/Paytm-compatible) for unpaid orders.
    upi_qr_base64 = None
    upi_link = None
    if order.status == "draft":
        upi_link = build_upi_link(order.total_price, f"ReelToDigit Order {order.order_number}")
        upi_qr_base64 = generate_qr_base64(upi_link)

    return templates.TemplateResponse(
        request=request,
        name="order_detail.html",
        context={
            "user": user,
            "order": order,
            "statuses": statuses,
            "status_order": status_order,
            "current_idx": current_idx,
            "message": message,
            "error": error,
            "upi_qr_base64": upi_qr_base64,
            "upi_link": upi_link
        }
    )

@router.post("/orders/{order_id}/pay")
def post_pay_order(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    user = get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    order = db.query(Order).filter(Order.id == order_id, Order.user_id == user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status not in ["draft"]:
        return RedirectResponse(url=f"/orders/{order.id}?error=Order+is+already+paid+or+cancelled.", status_code=303)

    # Record Payment
    payment = Payment(
        order_id=order.id,
        amount=order.total_price,
        provider="demo_stripe",
        status="captured"
    )
    db.add(payment)

    # Generate stub shipping label
    tracking_num = f"RTD-TRACK-{uuid.uuid4().hex[:8].upper()}"
    label = ShippingLabel(
        order_id=order.id,
        tracking_number=tracking_num,
        carrier="India Post",
        label_url=f"/orders/{order.id}/label"
    )
    db.add(label)

    # Update order status to paid & label_ready
    order.status = "label_ready"
    db.commit()

    return RedirectResponse(url=f"/orders/{order.id}?message=Payment+successful!+Your+shipping+label+is+now+ready.", status_code=303)

@router.get("/orders/{order_id}/label", response_class=HTMLResponse)
def get_shipping_label(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    user = get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if user.role != "admin" and order.user_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    if not order.shipping_label:
        raise HTTPException(status_code=400, detail="Shipping label not generated yet.")

    return templates.TemplateResponse(
        request=request,
        name="shipping_label.html",
        context={
            "order": order,
            "label": order.shipping_label,
            "customer": order.user
        }
    )

@router.get("/media/{media_id}/download")
def download_media_asset(
    media_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    from app.storage import get_download_url

    user = get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url=f"/login", status_code=303)

    media = db.query(MediaAsset).filter(MediaAsset.id == media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media asset not found")

    order = db.query(Order).filter(Order.id == media.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Associated order not found")

    if user.role != "admin" and order.user_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    # Determine provider and generate presigned or local URL
    provider = "s3" if media.file_url.startswith("orders/") else "local"
    download_url = get_download_url(provider, media.file_url)

    return RedirectResponse(url=download_url, status_code=303)

@router.post("/orders/{order_id}/cancel")
def post_cancel_order(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    user = get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    order = db.query(Order).filter(Order.id == order_id, Order.user_id == user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Free cancel pre-transit rule: status must be draft, paid, or label_ready
    if order.status not in ["draft", "paid", "label_ready"]:
        return RedirectResponse(
            url=f"/orders/{order.id}?error=Cannot+cancel+order+once+it+is+in+transit+or+received+at+lab.+Please+contact+support.",
            status_code=303
        )

    order.status = "cancelled"
    db.commit()

    return RedirectResponse(url=f"/orders/{order.id}?message=Order+cancelled+successfully.", status_code=303)
