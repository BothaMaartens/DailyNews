# DailyNews Application

Welcome to the DailyNews web application! This Django project is configured to run on a MariaDB backend and features a custom user authentication system.

This guide provides step-by-step instructions for setting up the environment, installing dependencies, configuring the database, and running the application.

## Prerequisites

Before starting, ensure you have the following installed on your system:

1. **Python 3.x** (We developed using Python 3.10+)

2. **MariaDB / MySQL Server:** The application requires **MariaDB 10.5 or newer** (or MySQL equivalent). If you are using XAMPP, ensure your MySQL version meets this requirement, or use Django 4.2.

3. **Git** (Optional, for cloning the repository)

4. Use the requirements.txt to validate the requirements.

## 1. Project Setup - Locally, using a virtual environment. 

Follow these steps to prepare your environment:

### 1.1 Create Virtual Environment

Navigate to the project's root directory (`project_NewsApp`):

Create a virtual environment (named 'venv' or similar)
python -m venv venv


### 1.2 Activate Environment

Activate the virtual environment based on your operating system:

**Windows (PowerShell):**

-- `.\venv\Scripts\Activate`


**macOS/Linux (Bash):**

-- `source venv/bin/activate`


You should see the virtual environment name in your terminal prompt (e.g., `(venv)`).

### 1.3 Install Dependencies

Install all necessary Python packages using the provided `requirements.txt` file.

-- `pip install -r requirements.txt`


## 2. Database Configuration (MariaDB)

This application uses MariaDB/MySQL. You must create the database and ensure the connection details in `settings.py` are correct.

### 2.1 Start MariaDB Server

Ensure your MariaDB/MySQL server (e.g., via XAMPP Control Panel) is running.

### 2.2 Create the Database

Log in to your MariaDB console (as root or a user with creation privileges) and create the required database.

Log in to MariaDB console
mysql -u root -p

Create the database
CREATE DATABASE dailynews_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

Exit
EXIT;


### 2.3 Apply Schema Migrations

Activate MySQL/MariaDB in your Django env. 

-- `pip install mysqlclient`

With the database created, run Django's migrations to build all the necessary tables.

-- `python manage.py migrate`


## 3. Data Loading (Initial Users and Content)

The existing application data (users, articles) has already been migrated. But to get a feel for the application, populate the database with the initial users as manual loaded using the UI. 

### 3.1 Prepare Fixture File

* The file `DailyNews_BaseUsers.txt` is available as reference for current/test users.

### 3.2 Load Fixture Data

Use the `loaddata` command to populate the database with test data:

-- `python manage.py loaddata initial_data_dump.json`


## 4. Final Project Setup

Once the initial data is laoded, make the required migrations:

-- `python manage.py makemigrations DailyNews_App`

Migrate the database to ensure all data is loaded to the created mysql database; dailynews_db:

-- `python manage.py migrate`

For testing the Django Super User can be created to act as and access the Django Admin interface. Run the following command in your virtual environment shell: 

-- `python manage.py createsuperuser`

Follow the Shell prompts to complete setup. -You will be requested to add a password that will not show, but it is stored. 

## 5. Project Setup - Using Docker.

Access the link below to the public remote repository:

`http://hub.docker.com/repository/docker/bothamaartens/dailynews/general`

On the docker hub repository page, the following pull request can be found: 

`docker pull bothamaartens/dailynews:latest`

Depending on preference of use, this pull request can either be run in "Play With Docker" web of in the Docker Desktop built in terminal. 

After pulling the docker image, it can be run with the following command: 

`docker run -d -p 80:80 bothamaartens/dailynews:latest`

To view the web page after running the Docker image, you can

1. Open http://localhost ~ Open in your browser if using Docker Desktop.
2. Click on the ``80`` symbol when using PWD.

With the Docker image running the app can be operated as stated below. 

## 6. Running the Application

Once all steps above are complete, you can start the development server.

-- `python manage.py runserver`


The application will be available at:

[http://127.0.0.1:8000/](http://127.0.0.1:8000/)

### Testing Access

* You can access the Django Admin site at `http://127.0.0.1:8000/admin/`.

* Use any credentials present in the loaded test data to log in. Or create custom users to test. 

### Registering an Editor or Journalist.

When an Editor or journalist is registered, an access password must be supplied to join the publisher. These passwords are hardcoded and is just used to ensure that readers/parties without permission can't join the publishers. The passwords are as follow: 

Publisher       | `Password`

ActualToday     | `ActualToday`

SportToday      |`SportToday`

**Very Important. Only editors affiliated with the Publisher can publish articles that a Journalist have written for said publication.
