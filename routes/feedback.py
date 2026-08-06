from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Order, Feedback
from app.auth import get_current_user_from_cookie

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/orders/{order_id}/feedback", response_class=HTMLResponse)
def get_feedback_form(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    user = get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url=f"/login?next_url=/orders/{order_id}/feedback", status_code=303)

    order = db.query(Order).filter(Order.id == order_id, Order.user_id == user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != "completed":
        return RedirectResponse(
            url=f"/orders/{order.id}?error=Feedback+can+only+be+submitted+after+the+order+is+completed.",
            status_code=303
        )

    return templates.TemplateResponse(
        request=request,
        name="feedback.html",
        context={
            "user": user,
            "order": order,
            "error": None
        }
    )

@router.post("/orders/{order_id}/feedback")
def post_feedback(
    order_id: int,
    request: Request,
    rating: int = Form(...),
    comment: str = Form(""),
    db: Session = Depends(get_db)
):
    user = get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    order = db.query(Order).filter(Order.id == order_id, Order.user_id == user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.feedback:
        return RedirectResponse(
            url=f"/orders/{order.id}?message=Feedback+already+submitted+for+this+order.+Thank+you!",
            status_code=303
        )

    rating_val = max(1, min(5, rating))
    fb = Feedback(
        order_id=order.id,
        user_id=user.id,
        rating=rating_val,
        comment=comment.strip() if comment else None
    )
    db.add(fb)
    db.commit()

    return RedirectResponse(
        url=f"/orders/{order.id}?message=Thank+you+for+your+feedback!+We+value+your+input.",
        status_code=303
    )
