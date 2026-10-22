# Event Management System

A web-based application designed to simplify event discovery, registration, and event management through a user-friendly interface.

## Features

- User registration and login
- Browse and view available events
- Register for events
- Database-backed application using SQLite
- Admin access for authorized event management
- Event registration statistics and popular event listings

## Tech Stack

- **Backend:** Python, Flask
- **Frontend:** HTML, CSS, JavaScript
- **Database:** SQLite
- **Version Control:** Git and GitHub
- **Deployment:** PythonAnywhere

## Project Structure

```text
EventManagementSystem/
├── app.py
├── requirements.txt
├── templates/
├── static/
├── .gitignore
└── README.md
```

## Local Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/snehajalihal/EventManagementSystem.git
   cd EventManagementSystem
   ```

2. Create and activate a Python virtual environment.

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Configure the required environment variables, including the Flask secret key.

5. Initialize or configure the SQLite database as required by the application.

6. Start the application using the appropriate Flask command for the project.

## Deployment

The application is deployed using PythonAnywhere.

## Learning Outcomes

This project demonstrates practical experience with Flask application development, database integration, authentication, role-based access, and web application deployment.

## Author

Sneha J

## Screenshots

### 1. Homepage
![Homepage](screenshots/homepage.png)

### 2. Event Registration
![Event Registration](screenshots/event-registration.png)

### 3. Admin Dashboard
![Admin Dashboard](screenshots/admin-dashboard.png)
