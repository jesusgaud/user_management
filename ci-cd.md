# CI/CD Pipeline Overview

This project uses GitHub Actions to automate testing and deployment for pushes and pull requests to the `main` and `development` branches.

---

## ✅ Workflow Triggers

| Event         | Branch         | Action                              |
|---------------|----------------|-------------------------------------|
| Push          | main, development | Triggers full test + deploy        |
| Pull Request  | main, development | Triggers test only                 |

---

## 🧪 Job 1: `test`

- **Python setup**: Python 3.10.12
- **Installs dependencies** from `requirements.txt`
- **PostgreSQL service** launched via `services`
- **Runs tests** using `pytest`
- **Environment variable**:
  `DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/myappdb`

---

## 🐳 Job 2: `build-and-push-docker`

- Runs only for **push events** on `main` or `development`
- Uses `docker/setup-buildx-action@v3`
- Logs into DockerHub using GitHub Secrets:
  - `DOCKERHUB_USERNAME`
  - `DOCKERHUB_TOKEN`
- Builds image with:
  - `jesusgaud/user_management:<commit-sha>`
  - `jesusgaud/user_management:latest`
- Pushes image to DockerHub
- **Security scan** with Trivy (blocks on `HIGH` or `CRITICAL`)

---

## 🔒 Secrets Required

| Secret Name         | Description                |
|---------------------|----------------------------|
| `DOCKERHUB_USERNAME`| DockerHub username         |
| `DOCKERHUB_TOKEN`   | DockerHub access token     |

---

## 📌 Deployment Note

Per project instructions:
- Code is deployed to `main` **only** when project is ready for submission.
