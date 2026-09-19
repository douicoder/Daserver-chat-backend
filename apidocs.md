# Chat Backend API Documentation

Base URL: `http://localhost:5000`

All request and response bodies are JSON unless otherwise noted.

---

## Authentication

All protected endpoints require a JWT token in the `Authorization` header:

```
Authorization: Bearer <token>
```

Tokens are returned by the `/api/auth/register` and `/api/auth/login` endpoints.

---

## REST API Endpoints

---

### POST /api/auth/register

Register a new user account.

**Request Body:**

```json
{
  "username": "string (required, non-empty)",
  "password": "string (required, min 6 characters)"
}
```

**Response: 201 Created**

```json
{
  "access_token": "jwt-token-string",
  "expires_at": "2026-01-01T00:00:00+00:00",
  "user": {
    "id": "uuid",
    "username": "string",
    "is_admin": false
  }
}
```

**Errors:**

| Status | Code | When |
|--------|------|------|
| 400 | VALIDATION_ERROR | Empty username, password < 6 chars, missing fields |
| 409 | USER_ALREADY_EXISTS | Username already taken |

---

### POST /api/auth/login

Authenticate and receive a JWT token.

**Request Body:**

```json
{
  "username": "string (required)",
  "password": "string (required)"
}
```

**Response: 200 OK**

```json
{
  "access_token": "jwt-token-string",
  "expires_at": "2026-01-01T00:00:00+00:00",
  "user": {
    "id": "uuid",
    "username": "string",
    "is_admin": false
  }
}
```

**Errors:**

| Status | Code | When |
|--------|------|------|
| 401 | INVALID_CREDENTIALS | Wrong username or password |

---

### GET /api/auth/me

Get the currently authenticated user's profile.

**Headers:** `Authorization: Bearer <token>`

**Response: 200 OK**

```json
{
  "id": "uuid",
  "username": "string",
  "is_admin": false
}
```

**Errors:**

| Status | Code | When |
|--------|------|------|
| 401 | AUTHENTICATION_ERROR | Missing, invalid, or expired token |

---

### GET /api/users/me

Identical to `GET /api/auth/me`. Returns the currently authenticated user.

**Headers:** `Authorization: Bearer <token>`

**Response: 200 OK**

```json
{
  "id": "uuid",
  "username": "string",
  "is_admin": false
}
```

---

### GET /api/messages

Retrieve chat message history with pagination. Messages are returned newest-first.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| page | int | 1 | Page number (min 1) |
| limit | int | 50 | Messages per page (min 1, max 100) |

**Response: 200 OK**

```json
{
  "messages": [
    {
      "id": "uuid",
      "sender_id": "uuid",
      "sender_username": "alice",
      "content": "Hello world",
      "created_at": "2026-01-01T00:00:00+00:00",
      "attachment": {
        "id": "uuid",
        "original_filename": "photo.jpg",
        "mime_type": "image/jpeg",
        "size": 102400
      }
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 50,
    "total": 120,
    "total_pages": 3
  }
}
```

**Notes:**

- `content` is the decrypted plaintext message. It will be an empty string `""` if the message is attachment-only.
- `attachment` is `null` if the message has no attachment.

**Errors:**

| Status | Code | When |
|--------|------|------|
| 401 | AUTHENTICATION_ERROR | Missing or invalid token |

---

### POST /api/attachments

Upload a file. Returns metadata and a download URL. The file is stored on disk with a randomly generated filename.

**Headers:** `Authorization: Bearer <token>`, `Content-Type: multipart/form-data`

**Form Data:**

| Field | Type | Required |
|-------|------|----------|
| file | file | Yes |

**Response: 201 Created**

```json
{
  "id": "uuid",
  "original_filename": "holiday.jpg",
  "mime_type": "image/jpeg",
  "size": 482931,
  "created_at": "2026-01-01T00:00:00+00:00",
  "download_url": "/api/attachments/uuid"
}
```

**Validation Rules:**

- File size must not exceed `MAX_FILE_SIZE_MB` (default 25 MB).
- File extension must be in the allowed list: `jpg`, `jpeg`, `png`, `gif`, `webp`, `pdf`, `txt`, `zip`.
- MIME type is detected from file content signatures, not just the client-provided type.
- Original filename is sanitized with `secure_filename()`.
- Server-side filename is a random hex string (e.g., `9f31b8c4e2a74f...`).

**Errors:**

| Status | Code | When |
|--------|------|------|
| 400 | VALIDATION_ERROR | No file provided, empty filename |
| 401 | AUTHENTICATION_ERROR | Missing or invalid token |
| 413 | FILE_TOO_LARGE | File exceeds max size |
| 415 | UNSUPPORTED_FILE_TYPE | File extension not in allowed list |

---

### GET /api/attachments/{attachment_id}

Download a previously uploaded file. The file is streamed as a binary download.

**Headers:** `Authorization: Bearer <token>`

**Response: 200 OK**

- `Content-Type`: The detected MIME type of the file.
- `Content-Disposition`: `attachment; filename="<original_filename>"`
- Body: Raw file bytes.

**Notes:**

- Any authenticated user can download any attachment.
- The physical storage path is never exposed to the client.

**Errors:**

| Status | Code | When |
|--------|------|------|
| 401 | AUTHENTICATION_ERROR | Missing or invalid token |
| 404 | ATTACHMENT_ERROR | Attachment ID does not exist |

---

### GET /api/admin/users

List all registered users. Admin only.

**Headers:** `Authorization: Bearer <admin-token>`

**Response: 200 OK**

```json
[
  {
    "id": "uuid",
    "username": "alice",
    "is_admin": false,
    "created_at": "2026-01-01T00:00:00+00:00"
  },
  {
    "id": "uuid",
    "username": "admin",
    "is_admin": true,
    "created_at": "2026-01-01T00:00:00+00:00"
  }
]
```

**Errors:**

| Status | Code | When |
|--------|------|------|
| 401 | AUTHENTICATION_ERROR | Missing or invalid token |
| 403 | AUTHORIZATION_ERROR | Token is valid but user is not an admin |

---

### POST /api/admin/users/{user_id}/password

Change another user's password. Admin only. The admin cannot see the existing password.

**Headers:** `Authorization: Bearer <admin-token>`

**Request Body:**

```json
{
  "new_password": "string (required, min 6 characters)"
}
```

**Response: 200 OK**

```json
{
  "message": "Password updated successfully"
}
```

**Errors:**

| Status | Code | When |
|--------|------|------|
| 400 | VALIDATION_ERROR | Password < 6 characters |
| 401 | AUTHENTICATION_ERROR | Missing or invalid token |
| 403 | AUTHORIZATION_ERROR | Token is valid but user is not an admin |
| 404 | USER_NOT_FOUND | User ID does not exist |

---

## Socket.IO Events

Connect to the Socket.IO server at `http://localhost:5000`.

---

### Connection

The client must provide the JWT token as a query parameter during the Socket.IO handshake:

```javascript
const socket = io("http://localhost:5000", {
  query: { token: "your-jwt-token" }
});
```

**Behavior:**

- If the token is missing or invalid, the connection is rejected.
- If the token is valid, the user is tracked as an authenticated connection.
- The server logs the connection and disconnection of each user.

---

### Client Event: send_message

Sent by the client to broadcast a message to all connected users.

**Payload:**

```json
{
  "content": "Hello world",
  "attachment_id": null
}
```

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| content | string or null | No* | Text content of the message. Stripped of leading/trailing whitespace. Max length: `MAX_MESSAGE_LENGTH` (default 5000). |
| attachment_id | string or null | No* | UUID of a previously uploaded attachment. Must belong to the sender and not already be attached to another message. |

\* At least one of `content` or `attachment_id` must be provided.

**Validation Rules:**

- The message must contain at least `content` (non-empty after stripping) or `attachment_id`.
- If `attachment_id` is provided, it must exist, belong to the sender, and not already be attached to another message.
- Content is encrypted with AES-256-GCM before storage.
- The sender is always derived from the authenticated connection, never from the payload.

---

### Server Event: receive_message

Broadcast to all connected clients (including the sender) when a message is sent successfully.

**Payload:**

```json
{
  "id": "uuid",
  "sender_id": "uuid",
  "sender_username": "alice",
  "content": "Hello world",
  "created_at": "2026-01-01T00:00:00+00:00",
  "attachment": {
    "id": "uuid",
    "original_filename": "photo.jpg",
    "mime_type": "image/jpeg",
    "size": 102400
  }
}
```

**Notes:**

- `content` is the decrypted plaintext. Empty string if attachment-only.
- `attachment` is `null` if the message has no attachment.

---

### Server Event: error

Sent to the client that triggered the error. Not broadcast.

**Payload:**

```json
{
  "code": "VALIDATION_ERROR",
  "message": "A message must contain content, an attachment, or both"
}
```

**Possible error codes:**

| Code | When |
|------|------|
| AUTHENTICATION_ERROR | Socket connection is not authenticated |
| VALIDATION_ERROR | Invalid payload format, empty message, content too long |
| ATTACHMENT_ERROR | Attachment not found, not owned by sender, or already used |
| MESSAGE_ERROR | General message processing failure |

---

### Disconnect

When a client disconnects, the server removes them from the authenticated connections map and logs the event. No payload is sent.

---

## Error Response Format

All REST API errors follow a consistent JSON format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable description"
  }
}
```

### Error Code Reference

| Code | HTTP Status | Description |
|------|-------------|-------------|
| VALIDATION_ERROR | 400 | Invalid request body or parameters |
| AUTHENTICATION_ERROR | 401 | Missing, invalid, or expired JWT token |
| INVALID_CREDENTIALS | 401 | Wrong username or password |
| AUTHORIZATION_ERROR | 403 | Authenticated but not authorized (e.g., non-admin accessing admin endpoint) |
| USER_NOT_FOUND | 404 | User does not exist |
| ATTACHMENT_ERROR | 404 | Attachment does not exist |
| USER_ALREADY_EXISTS | 409 | Username already taken |
| FILE_TOO_LARGE | 413 | Uploaded file exceeds max size |
| UNSUPPORTED_FILE_TYPE | 415 | File extension not in allowed list |
| MESSAGE_ERROR | 400 | General message processing failure |

---

## JWT Token Structure

The JWT token contains the following claims:

```json
{
  "sub": "user-uuid",
  "username": "alice",
  "is_admin": false,
  "iat": 1700000000,
  "exp": 1700003600
}
```

| Claim | Description |
|-------|-------------|
| sub | User ID (UUID) |
| username | The user's username |
| is_admin | Whether the user has admin privileges |
| iat | Issued-at timestamp |
| exp | Expiration timestamp (configurable via `JWT_EXPIRATION_MINUTES`) |

---

## Configuration

All configuration is loaded from environment variables (`.env` file).

| Variable | Default | Description |
|----------|---------|-------------|
| FLASK_ENV | development | Flask environment |
| DATABASE_URL | sqlite:///chat.db | SQLAlchemy database URL |
| JWT_SECRET_KEY | (required) | Secret key for signing JWT tokens |
| JWT_EXPIRATION_MINUTES | 60 | Token expiration time in minutes |
| MESSAGE_ENCRYPTION_KEY | (required) | 64-char hex string (32 bytes) for AES-256-GCM |
| FILE_STORAGE_PATH | ./storage/attachments | Directory for storing uploaded files |
| MAX_FILE_SIZE_MB | 25 | Maximum upload file size in MB |
| MAX_MESSAGE_LENGTH | 5000 | Maximum message text length in characters |
| CORS_ALLOWED_ORIGINS | http://localhost:3000 | Comma-separated list of allowed CORS origins |

---

## CLI Commands

### Create Admin User

```bash
python run.py create-admin
```

Securely prompts for username and password. Creates an admin user in the database.

### Run Server

```bash
python run.py
```

Starts the server on `http://0.0.0.0:5000`.

### Run Tests

```bash
pytest tests/ -v
```
