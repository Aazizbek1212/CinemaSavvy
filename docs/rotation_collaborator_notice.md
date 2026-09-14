MinIO & Credentials Rotation Notice

Summary
- We performed a sensitive-history purge and are rotating credentials for MinIO, Postgres, and SMTP.
- Repository history has been rewritten; all contributors must reclone the repository to avoid conflicts.

Actions You Must Take
1) Recloning after history rewrite
   - Delete local clones or move them aside.
   - Fresh clone: `git clone <repo-url>`

2) Update your local environment
   - Do NOT commit secrets.
   - If you need local .env values, ask the ops owner for secure access to `secrets/.env.generated`.

3) Update CI / Production secrets
   - Update CI environment variables for:
     - `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, `MINIO_ENDPOINT`
     - `POSTGRES_PASSWORD`
     - `EMAIL_HOST_PASSWORD` (and other email vars)
   - After updating secrets, restart services or redeploy pipelines.

4) Verify services
   - MinIO: check console and run an upload/download smoke test.
   - DB: run migrations and check connections.
   - Email: send a test email.

5) Revoke old credentials
   - Remove old MinIO users/keys and rotate any external keys.
   - Revoke old DB passwords and rotate DB users if applicable.

Who to contact
- Ops owner: @ops (replace with actual handle)
- Repo owner: @Aazizbek1212

If you want, I can:
- Draft a short email/Slack message for collaborators.
- Automate CI secret update instructions for common providers (GitHub Actions, GitLab CI, Render, etc.).
