"""
Database Schemas for BookMyResort

Each Pydantic model represents a collection in MongoDB (collection name is the lowercase of the class name).
"""
from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr


class RestaurantItem(BaseModel):
    name: str
    category: str
    price: float = Field(..., ge=0)
    image: Optional[str] = None


class OrderedItem(BaseModel):
    name: str
    price: float = Field(..., ge=0)
    quantity: int = Field(..., ge=1)


class Booking(BaseModel):
    """
    Booking collection schema
    Collection: "booking"
    """
    booking_id: str
    guest_name: str
    email: EmailStr
    location: str
    check_in_date: str  # ISO date string YYYY-MM-DD
    check_out_date: str  # ISO date string YYYY-MM-DD
    check_in_time: str   # e.g. 14:00
    check_out_time: str  # e.g. 11:00
    nights: int = Field(..., ge=1)
    price_per_night: float = Field(..., ge=0)
    accommodation_total: float = Field(..., ge=0)
    restaurant_addons: List[OrderedItem] = []
    restaurant_total: float = 0
    total_amount: float = Field(..., ge=0)


class BookingCreate(BaseModel):
    guest_name: str
    email: EmailStr
    location: str
    check_in_date: str
    check_out_date: str
    check_in_time: str
    check_out_time: str
    restaurant_addons: List[OrderedItem] = []
