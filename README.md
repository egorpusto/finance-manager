# Finance Manager

## 📝 Description
A Django-based personal finance management application that helps users track income and expenses. The app features transaction categorization, financial statistics, and user-friendly dashboards.

## ✨ Features

- **Transaction Management**: Record financial transactions with amount, date and category
- **Categories System**: Customizable categories for better expense tracking
- **User Authentication**: Secure registration and login system
- **Dashboard**: Overview of financial activities
- **Admin Panel**: Full control over transactions and categories
- **PostgreSQL Support**: Ready for production deployments

## 🛠 Technologies

- Python 3.x
- Django 5.x
- PostgreSQL (production)
- SQLite (development)
- Bootstrap 5 (UI)
- HTML/CSS

## 🚀 Getting Started

### 1. Clone the project

git clone https://github.com/egorpusto/finance-manager.git
cd finance-manager

### 2. Create and activate a virtual environment

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

### 3. Install dependencies

pip install -r requirements.txt

### 4. Run migrations

python manage.py migrate

### 5. Create a superuser (for admin panel)

python manage.py createsuperuser

### 6. Start the development server

python manage.py runserver

Visit:

- http://127.0.0.1:8000/ - Main interface
- http://127.0.0.1:8000/admin/ - Admin panel

## 🗂 Project Structure

- `finance/`
  - `transactions/` — Main app
    - `migrations/` — Database migrations
    - `templates/` — HTML templates
    - `forms.py` — Transaction forms
    - `models.py` — Data models
    - `urls.py` — App URLs
    - `views.py` — View logic
  - `finance/` — Project config
    - `settings.py` — Django settings
    - `urls.py` — Project URLs
    - `wsgi.py` — WSGI config
  - `manage.py` — Management script
  - `requirements.txt` — Dependencies

---

Made with ❤️ by egorpusto