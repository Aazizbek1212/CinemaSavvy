## Summary

Describe what changed and why this PR is needed.

## Checklist

- [ ] I confirmed that no secrets or credentials were committed.
- [ ] I updated any required environment variables or deployment configuration.
- [ ] I verified the relevant app checks still pass.
- [ ] I added or updated smoke-test coverage for the changed behavior.

## Deployment / Secrets Notes

If this PR changes production credentials or deployment settings, ensure the following are updated in the deployment provider or GitHub repository secrets:

- `MINIO_ACCESS_KEY`
- `MINIO_SECRET_KEY`
- `MINIO_ENDPOINT`
- `POSTGRES_PASSWORD`
- `EMAIL_HOST_PASSWORD`
- `SECRET_KEY`

## Verification

Include the commands or checks you ran to confirm the change works.
