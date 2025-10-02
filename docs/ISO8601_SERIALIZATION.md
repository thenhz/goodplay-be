# ISO 8601 DateTime Serialization Guide

## Overview
All API responses now automatically serialize datetime objects to **ISO 8601 format** as specified in the OpenAPI documentation. This ensures consistent date formatting across all endpoints and compatibility with frontend frameworks.

## What Changed
Previously, Flask's default JSON encoder serialized datetime objects in HTTP date format (e.g., `Thu, 02 Oct 2025 09:36:40 GMT`). Now all dates are returned in ISO 8601 format (e.g., `2025-10-02T09:36:40.123456+00:00`).

## Implementation Details

### 1. Core Utilities (`app/core/utils/json_encoder.py`)

#### `serialize_datetime(dt)`
Converts a single datetime object to ISO 8601 string.

```python
from app.core.utils.json_encoder import serialize_datetime

dt = datetime(2025, 10, 2, 9, 36, 40, tzinfo=timezone.utc)
result = serialize_datetime(dt)
# Result: "2025-10-02T09:36:40+00:00"
```

#### `serialize_model_dates(data)`
Recursively serializes all datetime fields in dictionaries and lists.

```python
from app.core.utils.json_encoder import serialize_model_dates

data = {
    "user": {
        "created_at": datetime.now(timezone.utc),
        "profile": {
            "last_login": datetime.now(timezone.utc)
        }
    }
}

serialized = serialize_model_dates(data)
# All datetime fields are now ISO 8601 strings
```

### 2. Automatic Serialization in Responses (`app/core/utils/responses.py`)

All response helper functions now **automatically** serialize datetime fields:

```python
from app.core.utils.responses import success_response, error_response

# Example: User registration
user_data = {
    "user_id": "12345",
    "email": "test@example.com",
    "created_at": datetime.now(timezone.utc),  # Will be auto-serialized
    "updated_at": datetime.now(timezone.utc)   # Will be auto-serialized
}

return success_response("USER_REGISTRATION_SUCCESS", user_data)
```

**Response:**
```json
{
  "success": true,
  "message": "USER_REGISTRATION_SUCCESS",
  "data": {
    "user_id": "12345",
    "email": "test@example.com",
    "created_at": "2025-10-02T09:36:40.123456+00:00",
    "updated_at": "2025-10-02T09:36:40.123456+00:00"
  }
}
```

### 3. Model Serialization (`app/core/models/base_model.py`)

#### Option 1: Use BaseModel (Recommended for new models)

```python
from app.core.models.base_model import BaseModel

class MyModel(BaseModel):
    def __init__(self):
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def to_dict(self):
        data = {
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
        # Automatically serializes all datetime fields
        return self.serialize_dates(data)
```

#### Option 2: Manual serialization (For existing models)

```python
from app.core.utils.json_encoder import serialize_model_dates

class User:
    def to_dict(self):
        user_dict = {
            "email": self.email,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
        # Serialize all datetime fields
        return serialize_model_dates(user_dict)
```

## Usage Examples

### Controller Example
```python
@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        success, message, result = auth_service.register_user(
            email, password, first_name, last_name
        )

        if success:
            # Datetime fields in 'result' will be auto-serialized
            return success_response(message, result, 201)
        else:
            return error_response(message)
    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)
```

### Service Example
```python
def register_user(self, email, password, first_name, last_name):
    user = User(email=email, first_name=first_name, last_name=last_name)
    user.set_password(password)

    # Save to database
    user_id = self.repository.create(user.to_dict(include_sensitive=True))

    # Return user data (datetime fields will be serialized in controller)
    return True, "USER_REGISTRATION_SUCCESS", {
        "user_id": user_id,
        "email": user.email,
        "created_at": user.created_at,  # Still datetime object here
        "updated_at": user.updated_at   # Will be serialized in response
    }
```

### Model Example
```python
class User:
    def __init__(self):
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def to_dict(self, include_sensitive=False):
        from app.core.utils.json_encoder import serialize_model_dates

        user_dict = {
            "email": self.email,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "gaming_stats": {
                "last_activity": self.gaming_stats.get("last_activity")
            }
        }

        # Serialize all datetime fields (including nested ones)
        return serialize_model_dates(user_dict)
```

## Best Practices

### ✅ DO:
1. **Use response helpers**: Always use `success_response()` and `error_response()` - they handle serialization automatically
2. **Call `serialize_model_dates()` in `to_dict()`**: Ensure all model classes serialize dates in their `to_dict()` method
3. **Use timezone-aware datetimes**: Always create datetime objects with `timezone.utc`
4. **Test date formats**: Verify that API responses return ISO 8601 format

### ❌ DON'T:
1. **Manual string conversion**: Don't manually convert datetime to string - let the utilities handle it
2. **Use naive datetimes**: Always include timezone information
3. **Skip serialization**: Don't forget to call `serialize_model_dates()` in model `to_dict()` methods
4. **Custom date formats**: Don't create custom date formatters - use ISO 8601 standard

## ISO 8601 Format Specification

### Format: `YYYY-MM-DDTHH:MM:SS.ffffff+TZ`

Example: `2025-10-02T09:36:40.123456+00:00`

- **YYYY**: 4-digit year
- **MM**: 2-digit month (01-12)
- **DD**: 2-digit day (01-31)
- **T**: Separator between date and time
- **HH**: 2-digit hour (00-23)
- **MM**: 2-digit minute (00-59)
- **SS**: 2-digit second (00-59)
- **ffffff**: Microseconds (optional, up to 6 digits)
- **+TZ**: Timezone offset (e.g., `+00:00` for UTC, `+01:00` for CET)

### Special Cases
- **UTC timezone**: `+00:00` or `Z` (both are valid)
- **Date only**: `2025-10-02` (for `date` objects)
- **No microseconds**: `2025-10-02T09:36:40+00:00` (if not needed)

## Frontend Integration

### JavaScript
```javascript
// Parse ISO 8601 date from API response
const response = await fetch('/api/auth/register', { method: 'POST', body: data });
const json = await response.json();

// Convert ISO 8601 string to Date object
const createdAt = new Date(json.data.created_at);
console.log(createdAt); // Date object
```

### TypeScript
```typescript
interface User {
  user_id: string;
  email: string;
  created_at: string; // ISO 8601 string
  updated_at: string; // ISO 8601 string
}

// Parse and use
const user: User = response.data;
const createdDate = new Date(user.created_at);
```

## Testing

Run the ISO 8601 serialization test suite:

```bash
# Run all serialization tests
python -m pytest tests/test_iso8601_serialization.py -v

# Test specific functionality
python -m pytest tests/test_iso8601_serialization.py::TestISO8601Serialization::test_user_model_serialization -v
```

## Migration Checklist for Existing Models

For each model class:

1. ✅ Import `serialize_model_dates` in `to_dict()` method
2. ✅ Call `serialize_model_dates(data)` before returning from `to_dict()`
3. ✅ Verify all datetime fields are serialized correctly
4. ✅ Update tests to expect ISO 8601 format
5. ✅ Update OpenAPI documentation examples if needed

Example migration:

```python
# BEFORE
def to_dict(self):
    return {
        "created_at": self.created_at,  # Returns datetime object
        "updated_at": self.updated_at
    }

# AFTER
def to_dict(self):
    from app.core.utils.json_encoder import serialize_model_dates

    data = {
        "created_at": self.created_at,
        "updated_at": self.updated_at
    }
    return serialize_model_dates(data)  # Returns ISO 8601 strings
```

## Troubleshooting

### Issue: Dates still in HTTP format
**Solution**: Ensure model's `to_dict()` method calls `serialize_model_dates()`

### Issue: Timezone information missing
**Solution**: Use `datetime.now(timezone.utc)` instead of `datetime.now()`

### Issue: Nested dates not serialized
**Solution**: `serialize_model_dates()` handles nested structures automatically - ensure you're calling it on the top-level dict

### Issue: Date parsing fails in frontend
**Solution**: Verify the date string is valid ISO 8601 - all modern browsers support `new Date(isoString)`

## References

- [ISO 8601 Standard](https://en.wikipedia.org/wiki/ISO_8601)
- [Python datetime.isoformat()](https://docs.python.org/3/library/datetime.html#datetime.datetime.isoformat)
- [OpenAPI DateTime Format](https://swagger.io/docs/specification/data-models/data-types/#string)
