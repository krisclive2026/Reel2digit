# Deploying ReelToDigit on AWS Lightsail

This stack (FastAPI + Postgres + MinIO + Nginx via Docker Compose) runs on
Lightsail with no code changes — a Lightsail instance is a standard Ubuntu
VM. Only the host-level setup differs from EC2.

## 1. Create the instance

- Platform: Linux/Unix
- Blueprint: OS Only → **Ubuntu 22.04 LTS**
- Plan: **$12/mo** (2 GB RAM, 2 vCPU, 60 GB SSD) minimum — Postgres + MinIO +
  the app together need more than the $5 plan's 512 MB.
- Instance name: e.g. `reeltodigit-prod`

## 2. Attach a static IP

Lightsail console → Networking → Create static IP → attach to the instance.
Free while attached to a running instance. Use this IP for DNS and for the
Jenkins `DEPLOY_HOST` credential.

## 3. Open firewall ports

Instance → Networking tab → IPv4 Firewall → add rules:

| Application | Protocol | Port  |
|---|---|---|
| SSH         | TCP | 22  (usually open by default) |
| HTTP        | TCP | 80  |
| HTTPS       | TCP | 443 (once certs are added) |

Do **not** open port 9001 (MinIO console) publicly. Reach it via SSH tunnel
when needed:
```
ssh -L 9001:localhost:9001 ubuntu@<lightsail-static-ip>
```
then browse `http://localhost:9001` on your own machine.

## 4. Install Docker on the instance

```bash
ssh ubuntu@<lightsail-static-ip>
sudo apt update && sudo apt install -y docker.io docker-compose-plugin git
sudo usermod -aG docker ubuntu
# log out and back in for the group change to apply
```

## 5. Clone the repo and configure `.env`

```bash
sudo mkdir -p /opt/reeltodigit && sudo chown ubuntu:ubuntu /opt/reeltodigit
git clone <your-repo-url> /opt/reeltodigit
cd /opt/reeltodigit
cp .env.example .env
nano .env   # set SECRET_KEY, POSTGRES_PASSWORD, MINIO_ROOT_PASSWORD to real values
```

## 6. First-time bring-up

```bash
docker compose build
docker compose up -d
docker compose ps   # confirm app, db, minio, nginx are all healthy/running
curl -f http://localhost/
```

## 7. GitHub Actions secrets to configure

In your GitHub repo → Settings → Secrets and variables → Actions → New
repository secret, add:

- `LIGHTSAIL_HOST` → the instance's static IP (just the IP, no `ubuntu@`
  prefix — the workflow sets the username separately)
- `LIGHTSAIL_SSH_KEY` → the full contents of your private key file
  (`~/.ssh/reeltodigit.pem` from WSL, or whichever key you SSH in with).
  Paste the entire file including the `-----BEGIN ... KEY-----` and
  `-----END ... KEY-----` lines.

The workflow at `.github/workflows/deploy.yml` already references these
secret names — no further changes needed. It runs on every push to `main`,
and can also be triggered manually from the repo's Actions tab.

## 8. Known open item before this is production-ready

`test_e2e.py` currently fails due to a SQLite schema drift (the `orders`
table is missing a `format` column relative to `schema_postgres.sql`), so
the Jenkinsfile test stage has `|| true` to avoid blocking deploys. Fix with
an Alembic migration and remove the `|| true` so failing tests actually gate
deploys.

## Notes

- All storage, DB, and env-var wiring is already S3-compatible via MinIO —
  swapping to real AWS S3 later only requires changing `.env` values
  (`AWS_ENDPOINT_URL`, access keys), no code changes.
- Lightsail instances don't support IAM instance roles like EC2 — if you do
  switch to real S3, you'll authenticate with an IAM user's access key/secret
  instead of an attached role.
