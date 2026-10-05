# Barber Contract Trainer v2

- FastAPI
- Pydantic request/response models
- Automatically generated OpenAPI specification
- Swagger UI
- SQLite
- Real INSERT / SELECT / UPDATE operations
- Two-step frontend flow
- Several intentionally introduced bugs

## Setup

### Windows

```powershell
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Open:

- UI: http://127.0.0.1:8000
- Swagger: http://127.0.0.1:8000/docs
- OpenAPI: http://127.0.0.1:8000/openapi.json
- Debug DB view: http://127.0.0.1:8000/api/debug/bookings

After the first launch, the following file will be created next to `main.py`:

```text
barber.db
```

This is a standard SQLite database.

You can open it using:

- DB Browser for SQLite
- DataGrip
- IntelliJ Database
- sqlite3 CLI

## What to Practice

### 1. UI → API Contract

Complete the form and open:

DevTools → Network → Fetch/XHR

Compare the actual request with the Swagger/OpenAPI specification.

### 2. Request Contract

Check:

- required / optional fields
- data types
- enum values
- string length
- null / empty / missing fields
- nested DTOs
- extra fields
- invalid JSON
- Content-Type

### 3. Response Contract

Check:

- HTTP status
- response body schema
- data types
- business values
- error structure

### 4. Database

After creating a booking, check the `bookings` table:

```sql
SELECT *
FROM bookings
ORDER BY created_at DESC;
```

Verify the full flow:

UI → request → response → DB.

### 5. Business Logic

Pay special attention to:

- past dates
- already booked time slots
- different barbers booked for the same time
- booking updates
- cancellation
- repeated cancellation
- service price
- two concurrent users

## Interview Mode

Do not open `BUGS.md` until you finish.

First, try to find the issues yourself:

1. Happy path
2. Swagger contract
3. Network
4. Negative / boundary tests
5. DB verification
6. Direct API calls
7. Race condition / business logic cases