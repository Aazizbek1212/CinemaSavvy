Slack/Email message to collaborators

Subject: [Action Required] Repo history rewritten — rotate your local clones and update secrets

Hi team,

We rewrote repository history to remove committed secrets and are rotating credentials for MinIO, Postgres, and SMTP.

Required actions for all contributors:
1) Delete or move any local clones and reclone the repo:
   - `git clone <repo-url>`
2) Do NOT commit any `.env` or secret files. Use the secure channel to obtain the generated secrets if you need them locally.
3) Update CI/production secrets (Ops): update `MINIO_*`, `POSTGRES_PASSWORD`, `EMAIL_HOST_PASSWORD`, `SECRET_KEY` in the deployment provider's secret store and redeploy.
4) Verify basic app functionality after deployment: run smoke tests (file upload/download, DB connectivity, and send test email).

If you have any automation or scripts that reference plain `.env` files, please update them to use environment variables or secrets injections from your CI.

Contact: @ops (replace) or @Aazizbek1212 for questions.

Thanks — Security Team