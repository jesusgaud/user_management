# 📌 Feature Selection: User Profile Management

## ✅ Feature Overview
**Selected Feature:** User Profile Management (Easy Tier)

## 📘 Why This Feature?
- Ensures we can realistically complete and fully implement it.
- Allows focus on testing, QA, and CI/CD integrations.
- Core functionality that aligns with real-world use cases.

## 🔍 Planned Functionality
- Allow users to:
  - View and edit their profile (name, email, etc.)
  - Update password securely
  - View role/tier (e.g., admin, tier1, tier2)

## 🧠 Next Steps
- Integrate feature endpoints into FastAPI.
- Connect functionality to PostgreSQL via SQLAlchemy.
- Write tests using pytest + async DB setup.
- Link to auth flow using JWT tokens.

## 🔗 README Integration (To-Do)
- We’ll add a reference to this `docs/feature.md` in the final `README.md` during project submission.


### ✅ Test Case 1: User Registration

**Test Objective**
Confirm that a new user can be registered through the `/register` endpoint and is persisted in the PostgreSQL database.

---

**Steps to Reproduce**
1. Start the application using Docker:
 ```sh
   docker compose up
```

2. Navigate to the FastAPI Swagger UI at:

   `http://localhost/docs`

3. Expand the  `POST /register` endpoint.

4. Enter the following payload in the request body:
 ```sh
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
5. Click `Execute` to submit the request.

6. Open pgAdmin:
- Navigate to `Servers → Postgres → myappdb → Schemas → public → Tables → users`.

- Run:
 ```sh
   SELECT * FROM public.users ORDER BY id ASC;
```
- Confirm that the newly registered user appears.

**Expected Result**
The user record should be saved in the database with all fields accurately recorded.
**Screenshot Evidence**
![User Successfully Registered](/screenshots/user-registration-success.png)
