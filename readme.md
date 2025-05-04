# User Management Microservice

This project is a containerized FastAPI-based user management system with PostgreSQL, pgAdmin, and Nginx reverse proxy integration. It supports robust user registration, authentication, and administration features.

---

## ✅ Phase 1: Completed Setup & Manual QA Testing

### 🔧 Environment Setup Summary

- **Containers**:
  - `fastapi`: Python 3.12 with automatic table creation on startup
  - `postgres`: PostgreSQL 16.2
  - `pgadmin`: Accessible at `localhost:5050` with default admin credentials
  - `nginx`: Reverse proxy routing traffic to FastAPI (port `8000`)

- **Volumes**:
  - PostgreSQL and pgAdmin data persist across restarts.

- **Docker Compose**: Launches all services via `docker compose up`

---

### ⚙️ Key File Structure & Configuration

| File                         | Purpose                                      |
|-----------------------------|----------------------------------------------|
| `Dockerfile`                | Multi-stage FastAPI image with glibc patch   |
| `docker-compose.yml`       | Defines and connects services                |
| `nginx/nginx.conf`         | Nginx reverse proxy for FastAPI              |
| `app/models/user_model.py` | SQLAlchemy ORM model for `users` table       |
| `app/database.py`          | Async engine and session management          |
| `main.py`                  | App entry point with router and DB init      |

> ✅ Tables are auto-created on startup based on the models.

---

## 🧪 Manual QA Test: User Registration

### ✔️ Steps to Reproduce

1. Navigate to [http://localhost/docs](http://localhost/docs)
2. Execute POST `/register` with the following payload:

```json
{
  "email": "jesusgaud@gmail.com",
  "nickname": "clever_fox_821",
  "first_name": "Jesus",
  "last_name": "Gaud",
  "bio": "Experienced software developer specializing in web applications.",
  "profile_picture_url": "https://example.com/profiles/john.jpg",
  "linkedin_profile_url": "https://linkedin.com/in/johndoe",
  "github_profile_url": "https://github.com/johndoe",
  "role": "ANONYMOUS",
  "password": "Secure*1234"
}
```

### ✅ Expected vs Actual Result

| Action         | Expected Outcome                                      | Actual Result         |
|----------------|--------------------------------------------------------|------------------------|
| Submit request | `200 OK` with JSON response of new user info          | ✅ As expected          |
| pgAdmin check  | User inserted into `myappdb.public.users` table       | ✅ Verified in DB       |

### 🖼️ Screenshot Evidence

![Registration Success - DB Verification](docs/screenshots/user-registration-success.png)

---

## 📁 QA & DevOps Documentation

| File                  | Purpose                          |
|-----------------------|----------------------------------|
| `ci-cd.md`            | CI/CD pipeline setup and logic   |
| `qa-test-plan.md`     | Manual QA test planning and logs |
| `README.md` (this)    | Project overview and testing log |

---

## 🔜 Next Step

We will resume with **Email Verification** testing and automation.

