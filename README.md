# SMTP Checker API

Lightweight HTTP API to validate SMTP connectivity, optional STARTTLS/SSL, authentication, and optionally send a test email.

The API aims to provide clear, structured diagnostics so you can quickly understand whether an SMTP server is reachable, supports TLS, accepts credentials, and can deliver a simple test message.

## Features

- Connectivity checks with timeouts
- STARTTLS (port 587) and implicit SSL (port 465)
- Optional authentication (LOGIN only if credentials provided)
- Optional test email sending (`send_email=true|false`)
- Detailed JSON response with step results
- Health endpoint (`GET /healthz`)

## Quick Start

### Run Locally (Python)

Requirements:
- Python 3.11+

Install and run:

```
pip install -r requirements.txt
python smtp_checker.py
```

The API listens on `http://0.0.0.0:5000` by default.

Environment variables:
- `APP_HOST` (default `0.0.0.0`)
- `APP_PORT` (default `5000`)
- `APP_DEBUG` (`true|false`, default `false`)

### Run with Docker (local)

Build and run the local image:

```
docker compose -f docker-local-compose.yml up --build
```

The service is exposed on `http://localhost:5000`.

### Run with Docker (prebuilt image)

This repo also includes a compose file referencing a prebuilt image:

```
docker compose up -d
```

Note: Adjust the image in `docker-compose.yml` if you prefer your own registry.

## API

### POST `/check-smtp`

Validates the SMTP server. Optionally authenticates and sends a test email.

Request body:

```
{
  "smtp_server": "smtp.example.com",           // required
  "smtp_port": 587,                              // default: 587
  "username": "user@example.com",              // optional (if provided, password required)
  "password": "secret",                        // optional (required when username provided)
  "from_email": "user@example.com",            // required when send_email=true
  "to_email": "recipient@example.com",         // required when send_email=true
  "send_email": true,                            // default: true
  "use_ssl": false,                              // default: true if port==465 else false
  "starttls": true,                              // default: !use_ssl
  "timeout": 10,                                 // seconds (float), default: 10
  "subject": "SMTP Test",                       // optional
  "message": "This is a test email."            // optional
}
```

Notes:
- If `use_ssl=true`, the connection uses implicit TLS (e.g., port 465).
- If `use_ssl=false` and `starttls=true`, the API attempts STARTTLS on a plain connection and fails if the server does not support it.
- If `send_email=false`, the API performs a connection/auth/NOOP check without sending a message.

Example (send a message over STARTTLS):

```
curl -sS -X POST http://localhost:5000/check-smtp \
  -H "Content-Type: application/json" \
  -d '{
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "username": "youremail@gmail.com",
    "password": "yourpassword",
    "from_email": "youremail@gmail.com",
    "to_email": "test@example.com",
    "send_email": true
  }'
```

Example (dry run: no email sent, just connect/auth):

```
curl -sS -X POST http://localhost:5000/check-smtp \
  -H "Content-Type: application/json" \
  -d '{
    "smtp_server": "smtp.example.com",
    "smtp_port": 465,
    "use_ssl": true,
    "username": "user@example.com",
    "password": "secret",
    "send_email": false
  }'
```

Success response (200):

```
{
  "status": "pass",
  "message": "SMTP check succeeded",
  "details": {
    "server": "smtp.example.com",
    "port": 587,
    "used_ssl": false,
    "used_starttls": true,
    "authenticated": true,
    "sent": true
  }
}
```

Failure response includes HTTP status code and context, e.g.:

- 400: input validation error
- 401: authentication failed
- 422: sender or recipient refused
- 502: connection/TLS/data error with upstream server
- 500: unexpected internal error

### GET `/healthz`

Simple health probe returning `{ "status": "ok" }`.

## Security Considerations

- Treat `username` and `password` as secrets. Do not log or persist them.
- Using this API to send emails may trigger provider rate limits or anti-abuse checks. Use `send_email=false` for non-delivery checks.
- Ensure you have permission to send to the specified recipient; consider using a controlled test address.
- When exposing publicly, place the API behind authentication and rate limiting.

## Development

Format/lint: this project intentionally has minimal dependencies. Keep changes small and focused.

## License

MIT or as per your organization’s policy.

