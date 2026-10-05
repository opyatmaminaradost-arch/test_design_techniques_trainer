from __future__ import annotations

from datetime import date as Date, datetime
from typing import Literal, Optional
from uuid import uuid4
import sqlite3

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, EmailStr, ConfigDict

DB_PATH = "barber.db"

app = FastAPI(
    title="Barber Interview Trainer API",
    version="2.0.0",
    description="""
Training API for a two-step barber booking flow.

Use:
- `/docs` for Swagger UI
- `/openapi.json` for the raw OpenAPI contract
- the browser UI on `/`
- SQLite database file `barber.db`

The service intentionally contains several defects and contract violations for interview practice.
""",
)

SERVICES = {
    "haircut": {"id": "haircut", "name": "Мужская стрижка", "durationMin": 45, "price": 2200},
    "beard": {"id": "beard", "name": "Оформление бороды", "durationMin": 30, "price": 1400},
    "combo": {"id": "combo", "name": "Стрижка + борода", "durationMin": 75, "price": 3200},
}

BARBERS = {
    "max": {"id": "max", "name": "Максим"},
    "anna": {"id": "anna", "name": "Анна"},
    "leo": {"id": "leo", "name": "Леонид"},
}

ALL_SLOTS = ["10:00", "11:00", "12:30", "14:00", "15:30", "17:00", "18:30"]


def conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB_PATH, check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c


def init_db() -> None:
    with conn() as c:
        c.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            booking_id TEXT PRIMARY KEY,
            service_id TEXT NOT NULL,
            barber_id TEXT NOT NULL,
            booking_date TEXT NOT NULL,
            booking_time TEXT NOT NULL,
            customer_name TEXT NOT NULL,
            customer_phone TEXT NOT NULL,
            customer_email TEXT,
            comment TEXT,
            consent INTEGER NOT NULL,
            price INTEGER NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """)
        c.commit()


@app.on_event("startup")
def startup() -> None:
    init_db()


class AvailabilityRequest(BaseModel):
    serviceId: Literal["haircut", "beard", "combo"]
    barberId: Literal["max", "anna", "leo"]
    date: Date = Field(description="Today or future date")


class AvailabilityResponse(BaseModel):
    available: bool
    slots: list[str]


class Customer(BaseModel):
    name: str = Field(min_length=2, max_length=60)
    phone: str = Field(
        min_length=11,
        max_length=16,
        description="Must match + followed by 10..15 digits",
        examples=["+79991234567"],
    )
    email: Optional[EmailStr] = None


class BookingCreate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    serviceId: Literal["haircut", "beard", "combo"]
    barberId: Literal["max", "anna", "leo"]
    date: Date
    time: str
    customer: Customer
    comment: str = Field(default="", max_length=500)
    consent: bool

    # IMPORTANT CONTRACT:
    # the server is supposed to ignore client-supplied price.
    # It is intentionally present here so testers can try tampering.
    price: Optional[int] = Field(default=None, description="Client price must be ignored by backend")


class BookingResponse(BaseModel):
    bookingId: str
    status: Literal["CONFIRMED", "CANCELLED"]
    price: int


class BookingDetails(BaseModel):
    bookingId: str
    serviceId: str
    barberId: str
    date: str
    time: str
    customer: Customer
    comment: str
    consent: bool
    price: int
    status: str
    createdAt: str


class BookingUpdate(BaseModel):
    barberId: Optional[Literal["max", "anna", "leo"]] = None
    time: Optional[str] = None
    comment: Optional[str] = Field(default=None, max_length=500)


@app.get("/", include_in_schema=False)
def index():
    return FileResponse("static/index.html")


@app.get("/api/services")
def get_services():
    return list(SERVICES.values())


@app.get("/api/barbers")
def get_barbers():
    return list(BARBERS.values())


@app.post("/api/availability/check", response_model=AvailabilityResponse)
def check_availability(req: AvailabilityRequest):
    # BUG 1: past dates are not rejected despite OpenAPI description.
    # BUG 2: booked slots are not removed from the response.
    return AvailabilityResponse(available=True, slots=ALL_SLOTS)


@app.post("/api/bookings", response_model=BookingResponse, status_code=201)
def create_booking(req: BookingCreate):
    if req.date < Date.today():
        raise HTTPException(status_code=400, detail={"code": "PAST_DATE", "message": "Past date is not allowed"})

    if req.time not in ALL_SLOTS:
        raise HTTPException(status_code=400, detail={"code": "INVALID_SLOT", "message": "Unknown time slot"})

    # BUG 3: actual phone validation is weaker than the documented contract.
    # Pydantic only checks length here, not '+' and digits format.

    if req.consent is not True:
        raise HTTPException(status_code=400, detail={"code": "CONSENT_REQUIRED", "message": "Consent must be true"})

    with conn() as c:
        # BUG 4: duplicate check ignores barber_id.
        existing = c.execute(
            """
            SELECT booking_id
            FROM bookings
            WHERE booking_date = ? AND booking_time = ? AND status = 'CONFIRMED'
            LIMIT 1
            """,
            (req.date.isoformat(), req.time),
        ).fetchone()

        if existing:
            raise HTTPException(
                status_code=409,
                detail={"code": "SLOT_ALREADY_BOOKED", "message": "Slot already booked"},
            )

        server_price = SERVICES[req.serviceId]["price"]

        # BUG 5 / security issue: backend trusts client price when present.
        final_price = req.price if req.price is not None else server_price

        booking_id = str(uuid4())
        created_at = datetime.utcnow().isoformat(timespec="seconds") + "Z"

        c.execute(
            """
            INSERT INTO bookings (
                booking_id, service_id, barber_id, booking_date, booking_time,
                customer_name, customer_phone, customer_email, comment,
                consent, price, status, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'CONFIRMED', ?)
            """,
            (
                booking_id,
                req.serviceId,
                req.barberId,
                req.date.isoformat(),
                req.time,
                req.customer.name.strip(),
                req.customer.phone,
                str(req.customer.email) if req.customer.email else None,
                req.comment,
                1 if req.consent else 0,
                final_price,
                created_at,
            ),
        )
        c.commit()

    return BookingResponse(bookingId=booking_id, status="CONFIRMED", price=final_price)


@app.get("/api/bookings/{booking_id}", response_model=BookingDetails)
def get_booking(booking_id: str):
    with conn() as c:
        row = c.execute(
            "SELECT * FROM bookings WHERE booking_id = ?",
            (booking_id,),
        ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail={"code": "BOOKING_NOT_FOUND"})

    return BookingDetails(
        bookingId=row["booking_id"],
        serviceId=row["service_id"],
        barberId=row["barber_id"],
        date=row["booking_date"],
        time=row["booking_time"],
        customer=Customer(
            name=row["customer_name"],
            phone=row["customer_phone"],
            email=row["customer_email"],
        ),
        comment=row["comment"] or "",
        consent=bool(row["consent"]),
        price=row["price"],
        status=row["status"],
        createdAt=row["created_at"],
    )


@app.patch("/api/bookings/{booking_id}", response_model=BookingDetails)
def update_booking(booking_id: str, req: BookingUpdate):
    with conn() as c:
        row = c.execute(
            "SELECT * FROM bookings WHERE booking_id = ?",
            (booking_id,),
        ).fetchone()

        if not row:
            raise HTTPException(status_code=404, detail={"code": "BOOKING_NOT_FOUND"})

        new_barber = req.barberId or row["barber_id"]
        new_time = req.time or row["booking_time"]
        new_comment = row["comment"] if req.comment is None else req.comment

        if new_time not in ALL_SLOTS:
            raise HTTPException(status_code=400, detail={"code": "INVALID_SLOT"})

        # BUG 6: PATCH can move booking into an occupied slot without conflict validation.
        c.execute(
            """
            UPDATE bookings
            SET barber_id = ?, booking_time = ?, comment = ?
            WHERE booking_id = ?
            """,
            (new_barber, new_time, new_comment, booking_id),
        )
        c.commit()

    return get_booking(booking_id)


@app.delete("/api/bookings/{booking_id}", response_model=BookingResponse)
def cancel_booking(booking_id: str):
    with conn() as c:
        row = c.execute(
            "SELECT * FROM bookings WHERE booking_id = ?",
            (booking_id,),
        ).fetchone()

        if not row:
            raise HTTPException(status_code=404, detail={"code": "BOOKING_NOT_FOUND"})

        # BUG 7: repeated cancellation is accepted as successful.
        c.execute(
            "UPDATE bookings SET status = 'CANCELLED' WHERE booking_id = ?",
            (booking_id,),
        )
        c.commit()

    return BookingResponse(
        bookingId=booking_id,
        status="CANCELLED",
        price=row["price"],
    )


@app.get("/api/debug/bookings")
def debug_bookings():
    """
    Interview-only endpoint to inspect what is actually stored in SQLite.
    """
    with conn() as c:
        rows = c.execute("SELECT * FROM bookings ORDER BY created_at DESC").fetchall()
    return [dict(r) for r in rows]
