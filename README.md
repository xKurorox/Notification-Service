# Notification Service
A multi-channel notification API that sends emails, SMS, and webhooks using a Redis priority queue, with automatic retries and delivery tracking.

## Features
- **Multi-channel delivery** — send notifications via email (SendGrid), SMS (Twilio), or webhook
- **Template engine** — Jinja2-powered templates with variable substitution and subject/body support
- **Priority queue** — notifications are scored by priority (critical → high → normal → low) and processed in order via Redis
- **Channel fallback** — if a user's requested channel is disabled, automatically falls back to their preferred channel
- **Delivery tracking** — every send attempt is logged with status, response code, and error message
- **Retry worker** — failed notifications are retried with exponential backoff, up to 5 attempts before moving to dead letter
- **Analytics** — aggregate counts by status, channel, and priority
- **User management** — per-user channel preferences and enable/disable flags

## Tech Stack
| | |
|---|---|
| Python | Language |
| FastAPI | Web framework |
| SQLAlchemy | ORM |
| PostgreSQL | Database |
| Pydantic | Request/response validation |
| Redis | Priority queue |
| SendGrid | Email delivery |
| Twilio | SMS delivery |
| httpx | Webhook delivery |
| Jinja2 | Template rendering |
| Uvicorn | ASGI server |
| Pytest | Testing |

## Architecture Overview
The API is split into three routers: users, templates, and notifications. Notifications are not sent synchronously — when `POST /notifications/send` is called, the notification is saved to the database and pushed onto a Redis sorted set (`notifications`) with a priority score. The route returns immediately with status `queued`.

A separate `priority_worker.py` process runs in a loop, popping the highest-priority notification off the queue and dispatching it to the appropriate channel handler (email, SMS, or webhook). Each handler returns a result dict with `success`, `status_code`, and optionally `error`, which is used to update the notification status and create a `DeliveryAttempt` record.

A second background process, `retry_worker.py`, scans for notifications with status `failed` and retries them using exponential backoff (`2^attempt` seconds between retries). After 5 failed attempts the notification is marked `dead_letter` and no longer retried.

Channel selection follows this logic: use the requested channel if it's enabled for the user, otherwise fall back to the user's `preferred_channel`. If that is also disabled, the request is rejected with a 400.

## API Documentation

### Users
| Method | URL | Description |
|--------|-----|-------------|
| POST | /users | Create a new user |
| GET | /users | List all users |
| GET | /users/{user_id} | Get a single user |
| PUT | /users/{user_id} | Update a user's info |
| DELETE | /users/{user_id} | Deactivate a user (soft delete) |

### Templates
| Method | URL | Description |
|--------|-----|-------------|
| POST | /templates | Create a template |
| GET | /templates | List all templates |
| GET | /templates/{template_id} | Get a single template |
| POST | /templates/{template_id}/render | Render a template with variables |

### Notifications
| Method | URL | Description |
|--------|-----|-------------|
| POST | /notifications/send | Queue a notification for delivery |
| GET | /notifications | List notifications (filterable) |
| GET | /notifications/analytics | Aggregate counts by status, channel, priority |
| GET | /notifications/{notification_id} | Get a notification with all delivery attempts |
| GET | /notifications/{notification_id}/attempts | Get all delivery attempts for a notification |

Query parameters for `GET /notifications`:
- `user_id` — filter by user
- `status` — filter by status (`queued`, `sent`, `failed`, `dead_letter`)
- `channel` — filter by channel (`email`, `sms`, `webhook`)
- `priority` — filter by priority (`low`, `normal`, `high`, `critical`)

## Setup Instructions

### 1. Clone the repository
```
git clone <your-repo-url>
cd notification-service
```

### 2. Create and activate a virtual environment
```
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
```

### 3. Install dependencies
```
pip install -r requirements.txt
```

### 4. Configure environment variables
Create a `.env` file in the project root:
```
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=notification_service

REDIS_HOST=localhost
REDIS_PORT=6379

SENDGRID_API_KEY=your_sendgrid_api_key
SENDER_EMAIL=your_verified_sender@example.com

TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_SENDER=your_twilio_phone_number
```

### 5. Start Redis
```
redis-server --port 6379
```

### 6. Run the API server
```
uvicorn app.main:app --reload
```

### 7. Run the priority worker (separate terminal)
```
python -m app.priority_worker
```

### 8. Run the retry worker (separate terminal)
```
python -m app.retry_worker
```

The API will be available at `http://localhost:8000`. Interactive docs are at `http://localhost:8000/docs`.

## Running Tests
```
python -m pytest test/ -v
```
