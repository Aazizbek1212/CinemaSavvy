# Google OAuth and HTTPS setup

## Google OAuth

Create a Google OAuth 2.0 Web application and register these callback URLs:

- Local: `http://localhost:8000/social/complete/google-oauth2/`
- Production: `https://YOUR_DOMAIN/social/complete/google-oauth2/`

Set the generated values in `.env`:

```text
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY=...
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET=...
```

The application uses the email address returned by Google and marks a social account as verified.

## HTTPS

Set these production values:

```text
DEBUG=False
ALLOWED_HOSTS=YOUR_DOMAIN,www.YOUR_DOMAIN
CSRF_TRUSTED_ORIGINS=https://YOUR_DOMAIN,https://www.YOUR_DOMAIN
FRONTEND_URL=https://YOUR_DOMAIN
```

Terminate TLS at Nginx and proxy requests to the Django container. Nginx must send
`X-Forwarded-Proto` so Django can enforce HTTPS and secure cookies correctly.

The repository Nginx file currently provides the HTTP proxy and forwarded headers. Add
the certificate paths and a `listen 443 ssl` server block on the deployment host before
enabling `SECURE_SSL_REDIRECT` in production.