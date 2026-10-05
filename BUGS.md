# BUGS / ANSWER KEY

Do not open this file before completing the exercise on your own.

## BUG 1

`POST /api/availability/check` accepts dates in the past.

The contract states that the date must be today or in the future.

## BUG 2

The availability endpoint always returns the full list of time slots.

After creating a booking, the occupied slot is still returned as available.

## BUG 3

The phone number documentation states:

`+` followed by 10–15 digits.

However, the backend currently validates mainly the string length through Pydantic.

For example, a string with the correct length but an invalid format may still pass validation.

## BUG 4

The duplicate booking check ignores `barberId`.

For example, creating:

Max / 10:00

will incorrectly block:

Anna / 10:00

even though these are different barbers.

## BUG 5 — Security / Business Logic

The frontend sends the `price` field.

The backend trusts the value provided by the client:

```json
"price": 1
```

and stores it in the database.

According to the business rule,