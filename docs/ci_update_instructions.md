Updating CI / Production Secrets

GitHub Actions

1) Open your repository on GitHub → Settings → Secrets and variables → Actions → New repository secret.
2) Add the following secrets (use values from `secrets/.env.generated` or the generated `.env.*` files):
   - `MINIO_ACCESS_KEY`
   - `MINIO_SECRET_KEY`
   - `MINIO_ENDPOINT`
   - `POSTGRES_PASSWORD`
   - `EMAIL_HOST_PASSWORD`
   - `SECRET_KEY`
3) If your workflows reference `.env` or use `env:` in workflow files, update them to use `secrets.VARIABLE_NAME`.
4) After updating secrets, re-run your deployment workflow or redeploy the environment.

Example GitHub Actions snippet (use in workflow):

```yaml
env:
  MINIO_ACCESS_KEY: ${{ secrets.MINIO_ACCESS_KEY }}
  MINIO_SECRET_KEY: ${{ secrets.MINIO_SECRET_KEY }}
  MINIO_ENDPOINT: ${{ secrets.MINIO_ENDPOINT }}
  POSTGRES_PASSWORD: ${{ secrets.POSTGRES_PASSWORD }}
  EMAIL_HOST_PASSWORD: ${{ secrets.EMAIL_HOST_PASSWORD }}
  SECRET_KEY: ${{ secrets.SECRET_KEY }}
```

GitLab CI

1) Go to your project → Settings → CI/CD → Variables → Add variable.
2) Add variables with the same names as above and mark them as "Protected" and "Masked" where appropriate.
3) Ensure your `.gitlab-ci.yml` uses the variables (they are injected into job environments automatically).

Common providers (Render / Heroku / DigitalOcean App Platform)

- Each provider has a dashboard section for environment variables; paste the same keys there.
- After updating, trigger a deploy or restart the service.

Notes & Safety

- Never commit environment files to the repository.
- Rotate secrets in the provider panel and delete old/unused keys.
- Update any third-party integrations that relied on old MinIO access keys.
- If using Kubernetes, update the secret objects and restart pods.

If you want, I can prepare provider-specific step-by-step screenshots or a GitHub Actions PR template to automate reading secrets from `secrets/.env.generated` securely during ops handoff.