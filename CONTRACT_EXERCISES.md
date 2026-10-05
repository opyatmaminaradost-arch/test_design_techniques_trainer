# CONTRACT EXERCISES

These are exercises, not answers.

## Exercise 1 — Happy Path

Create a booking:

```json
{
  "serviceId": "haircut",
  "barberId": "max",
  "date": "2030-10-10",
  "time": "10:00",
  "customer": {
    "name": "Sergei"
    "phone": "+79991234567",
    "email": "test@example.com"
  },
  "comment": "",
  "consent": true
}
```

Check:

- `201 Created`
- `bookingId`
- `status`
- `price`
- the corresponding record in SQLite

## Exercise 2 — Missing Required Field

Remove `customer.phone`.

Questions:

- What HTTP status do you expect?
- What does the response look like?
- Does the actual behavior match the API contract?

## Exercise 3 — Type Mismatch

Send:

```json
"consent": "true"
```

Compare Pydantic's actual behavior with the expected API contract.

## Exercise 4 — Price Tampering

Add:

```json
"price": 1
```

Questions:

- What does the API return?
- What value is stored in the database?

## Exercise 5 — Booking Conflict

Create two bookings:

- Max / 10:00
- Anna / 10:00

Should these bookings conflict with each other?

## Exercise 6 — Stale Availability

1. Request the available time slots.
2. Create a booking.
3. Request availability again.

What happens to the already booked time slot?

## Exercise 7 — PATCH

Create two bookings.

Try to update one booking using `PATCH` so that it gets the same time