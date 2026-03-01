# job-application-tracker
Full-stack web application designed to help users manage and  track their job applications in a structured, secure, and user-friendly environment.




Structure for the project:


jobtracker/
│
├── jobtracker/        # project config
│   ├── settings.py
│   ├── urls.py
│   └── ...
│
├── accounts/            # authentication app
│   ├── templates/
│   │   └── accounts/
│   │       ├── register.html
│   │       └── login.html
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── ...
│
├── tracker/            # main business logic
│   ├── templates/
│   │   └── tracker/
│   │       └── dashboard.html
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── ...
│
├── templates/
│   └── base.html
├── static/
├── manage.py



ERDs:

A User can create multiple Companies
A User can create multiple Applications
A Company can have multiple Applications
An Application can have multiple Interviews


User

| Key | Name        | Type         |
| --- | ----------- | ------------ |
| PK  | id          | Integer      |
|     | username    | Varchar(150) |
|     | email       | Varchar(254) |
|     | password    | Varchar(128) |
|     | is_active   | Boolean      |
|     | date_joined | DateTime     |


Company

| Key | Name       | Type           |
| --- | ---------- | -------------- |
| PK  | id         | Integer        |
| FK  | user_id    | Integer (User) |
|     | name       | Varchar(255)   |
|     | website    | Varchar(200)   |
|     | location   | Varchar(255)   |
|     | created_at | DateTime       |


Application

| Key | Name         | Type              |
| --- | ------------ | ----------------- |
| PK  | id           | Integer           |
| FK  | user_id      | Integer (User)    |
| FK  | company_id   | Integer (Company) |
|     | job_title    | Varchar(255)      |
|     | salary_range | Varchar(100)      |
|     | status       | Varchar(20)       |
|     | date_applied | Date              |
|     | notes        | Text              |
|     | created_at   | DateTime          |



Interview

| Key | Name           | Type                  |
| --- | -------------- | --------------------- |
| PK  | id             | Integer               |
| FK  | application_id | Integer (Application) |
|     | interview_type | Varchar(50)           |
|     | date           | DateTime              |
|     | notes          | Text                  |
|     | result         | Varchar(100)          |
|     | created_at     | DateTime              |



App flow (for now):

/ → Home

/accounts/register/ → Register

/accounts/login/ → Login

/dashboard/ → Protected dashboard
