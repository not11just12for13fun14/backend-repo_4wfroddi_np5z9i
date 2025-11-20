import os
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from typing import List, Optional

from database import db, create_document, get_documents
from schemas import Booking, BookingCreate, OrderedItem

app = FastAPI(title="BookMyResort API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "BookMyResort Backend Running"}


@app.get("/test")
def test_database():
    """Verify database connectivity and list collections"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set",
        "database_name": "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set",
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["connection_status"] = "Connected"
            try:
                response["collections"] = db.list_collection_names()[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response


# Static data for locations with price and facilities
class Location(BaseModel):
    name: str
    image: str
    price_per_night: float
    available: bool
    facilities: List[str]


LOCATIONS: List[Location] = [
    Location(name="Chennai", image="https://images.unsplash.com/photo-1501117716987-c8e1ecb2101f?q=80&w=1400&auto=format&fit=crop", price_per_night=149.0, available=True, facilities=["pool", "spa", "gym"]),
    Location(name="Salem", image="https://images.unsplash.com/photo-1500375592092-40eb2168fd21?q=80&w=1400&auto=format&fit=crop", price_per_night=119.0, available=True, facilities=["pool", "gym"]),
    Location(name="Kerala", image="https://images.unsplash.com/photo-1604177091072-df5bb03e9b7b?q=80&w=1400&auto=format&fit=crop", price_per_night=199.0, available=True, facilities=["pool", "spa", "yoga"]),
    Location(name="Madurai", image="https://images.unsplash.com/photo-1547586696-ea22b4e52f95?q=80&w=1400&auto=format&fit=crop", price_per_night=129.0, available=False, facilities=["gym"]),
    Location(name="Coimbatore", image="https://images.unsplash.com/photo-1502920514313-52581002a659?q=80&w=1400&auto=format&fit=crop", price_per_night=139.0, available=True, facilities=["pool", "spa"]),
    Location(name="Bangalore", image="https://images.unsplash.com/photo-1496412705862-e0088f16f791?q=80&w=1400&auto=format&fit=crop", price_per_night=179.0, available=True, facilities=["pool", "gym", "spa"]),
]


@app.get("/api/locations")
async def get_locations():
    return [loc.model_dump() for loc in LOCATIONS]


class BookingResponse(BaseModel):
    booking_id: str


@app.post("/api/book", response_model=BookingResponse)
async def create_booking(payload: BookingCreate):
    # Validate location exists and fetch price
    location = next((l for l in LOCATIONS if l.name == payload.location), None)
    if not location:
        raise HTTPException(status_code=400, detail="Invalid location")

    # Compute nights and totals
    from datetime import datetime
    d1 = datetime.fromisoformat(payload.check_in_date)
    d2 = datetime.fromisoformat(payload.check_out_date)
    nights = (d2 - d1).days
    if nights < 1:
        raise HTTPException(status_code=400, detail="Checkout must be after checkin")

    restaurant_total = sum(item.price * item.quantity for item in payload.restaurant_addons)
    accommodation_total = nights * location.price_per_night
    total = accommodation_total + restaurant_total

    booking_id = str(uuid.uuid4())[:8].upper()

    booking_doc = Booking(
        booking_id=booking_id,
        guest_name=payload.guest_name,
        email=payload.email,
        location=payload.location,
        check_in_date=payload.check_in_date,
        check_out_date=payload.check_out_date,
        check_in_time=payload.check_in_time,
        check_out_time=payload.check_out_time,
        nights=nights,
        price_per_night=location.price_per_night,
        accommodation_total=accommodation_total,
        restaurant_addons=payload.restaurant_addons,
        restaurant_total=restaurant_total,
        total_amount=total,
    )

    try:
        create_document("booking", booking_doc)
    except Exception as e:
        # If DB not configured, still allow booking without persistence
        print("DB Error:", e)

    # Email sending would be handled on another endpoint; frontend will call after booking
    return BookingResponse(booking_id=booking_id)


class SendEmailPayload(BaseModel):
    booking_id: str
    guest_name: str
    email: EmailStr
    location: str
    check_in_date: str
    check_out_date: str
    check_in_time: str
    check_out_time: str
    restaurant_addons: List[OrderedItem] = []
    total_amount: float


@app.post("/api/send-confirmation")
async def send_confirmation(payload: SendEmailPayload):
    # Placeholder implementation that simulates sending success
    # In a real setup, integrate with SendGrid/Mailgun/SES or SMTP
    return {"status": "sent", "booking_id": payload.booking_id}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
