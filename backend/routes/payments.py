import stripe as stripe_lib
from fastapi import APIRouter, HTTPException, Request, Depends
from models.database import db, get_current_user, logger
from utils.runtime_config import get_stripe_api_key, get_stripe_webhook_secret
from datetime import datetime, timezone
import uuid

router = APIRouter()

@router.post("/checkout")
async def create_checkout(request: Request):
    body = await request.json()
    service_id = body.get("service_id", "")
    origin_url = body.get("origin_url", "")
    if not service_id or not origin_url:
        raise HTTPException(status_code=400, detail="service_id and origin_url required")
    service = await db.services.find_one({"id": service_id}, {"_id": 0})
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    price = float(service.get("price", 0))
    if price <= 0:
        raise HTTPException(status_code=400, detail="Invalid price")
    api_key = await get_stripe_api_key()
    if not api_key:
        raise HTTPException(status_code=503, detail="Stripe is not configured. Set the API key in CMS → Settings → Stripe.")
    success_url = f"{origin_url}/checkout/success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{origin_url}/"
    metadata = {"service_id": service_id, "service_name": service.get("title", "")}
    try:
        user = await get_current_user(request)
        metadata["user_id"] = user.get("user_id", "")
        metadata["user_email"] = user.get("email", "")
    except Exception:
        pass
    client = stripe_lib.StripeClient(api_key)
    session = await client.checkout.sessions.create_async({
        "payment_method_types": ["card"],
        "line_items": [{
            "price_data": {
                "currency": service.get("currency", "usd"),
                "product_data": {"name": service.get("title", "Service")},
                "unit_amount": int(price * 100),
            },
            "quantity": 1,
        }],
        "mode": "payment",
        "success_url": success_url,
        "cancel_url": cancel_url,
        "metadata": metadata,
    })
    tx = {"id": str(uuid.uuid4()), "session_id": session.id, "service_id": service_id,
          "service_name": service.get("title", ""), "amount": price, "currency": service.get("currency", "usd"),
          "status": "initiated", "payment_status": "pending", "metadata": metadata,
          "created_at": datetime.now(timezone.utc).isoformat()}
    await db.payment_transactions.insert_one(tx)
    return {"url": session.url, "session_id": session.id}

@router.get("/checkout/status/{session_id}")
async def checkout_status(session_id: str, request: Request):
    api_key = await get_stripe_api_key()
    if not api_key:
        raise HTTPException(status_code=503, detail="Stripe is not configured.")
    client = stripe_lib.StripeClient(api_key)
    session = await client.checkout.sessions.retrieve_async(session_id)
    update_data = {"status": session.status, "payment_status": session.payment_status}
    if session.payment_status == "paid":
        update_data["paid_at"] = datetime.now(timezone.utc).isoformat()
    await db.payment_transactions.update_one({"session_id": session_id}, {"$set": update_data})
    return {"status": session.status, "payment_status": session.payment_status,
            "amount_total": session.amount_total, "currency": session.currency}

@router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    body = await request.body()
    sig_header = request.headers.get("Stripe-Signature", "")
    webhook_secret = await get_stripe_webhook_secret()
    if not webhook_secret:
        logger.warning("Stripe webhook received but STRIPE_WEBHOOK_SECRET is not configured")
        return {"status": "error", "detail": "Webhook secret not configured"}
    try:
        event = stripe_lib.Webhook.construct_event(body, sig_header, webhook_secret)
    except stripe_lib.error.SignatureVerificationError as e:
        logger.error(f"Webhook signature verification failed: {e}")
        return {"status": "error", "detail": "Invalid signature"}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "error"}
    if event["type"] == "checkout.session.completed":
        session_obj = event["data"]["object"]
        if session_obj.get("payment_status") == "paid":
            await db.payment_transactions.update_one(
                {"session_id": session_obj["id"]},
                {"$set": {"status": "complete", "payment_status": "paid",
                          "paid_at": datetime.now(timezone.utc).isoformat()}})
    return {"status": "ok"}
