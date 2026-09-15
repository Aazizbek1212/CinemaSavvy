## Update CI / Production Secrets

Use this PR template when you rotate credentials and need to update CI/production secrets.

Checklist for PR author
- [ ] Confirm you DO NOT commit any secret values into the repo.
- [ ] Add a short description of which secrets changed and why.
- [ ] Ask ops to update repository secrets (GitHub Settings → Secrets and variables → Actions) with the keys listed below.
- [ ] Include a smoke test step in the PR to verify the change after deployment.

Required secret names (set these in GitHub repository secrets):
- `MINIO_ACCESS_KEY`
- `MINIO_SECRET_KEY`
- `MINIO_ENDPOINT`
- `POSTGRES_PASSWORD`
- `EMAIL_HOST_PASSWORD`
- `SECRET_KEY`

Optional secrets (if used):
- `MINIO_BUCKET_NAME`
- `REDIS_URL`

Example instructions for ops (paste into the repo or ticket):
1. Open: Settings → Secrets and variables → Actions → New repository secret.
2. Create each secret with the exact name above and paste the value from the secure generator.
3. Re-run the deployment workflow or merge this PR to trigger a deploy.

Do not attach `.env` files to this PR or include secret values in comments.
