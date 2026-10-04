# HotelMS Aura — Advanced Level

A premium Flask + SQLite Hotel Management System designed as a final-year showcase project.

## Stack
- Python / Flask
- Flask-SQLAlchemy
- Flask-Login
- SQLite
- ReportLab PDF invoices
- HTML / CSS / JavaScript

## Major modules
- Secure role-based login
- Smart room availability + overlap prevention
- Booking / cancellation / payment status
- Admin Control Center
- Hotel Intelligence dashboard
- Housekeeping workflow
- Dining / service orders
- Reviews + complaints
- Guest Hub with preferences
- Notification inbox
- Aura Concierge (rule-based digital assistant)
- Digital check-in arrival token
- Demo payment transaction history
- PDF invoices
- Existing Quiz + Attendance modules preserved

## Demo accounts
- Admin: `admin@hotel.com` / `admin123`
- Teacher: `teacher@hotel.com` / `teacher123`
- Student: `student1@hotel.com` / `student123`
- Guest: `guest@hotel.com` / `guest123`

## Run on Windows
```powershell
cd hotel-management-system
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python seed.py
python app.py
```

Open `http://127.0.0.1:5000`

## Important
For a clean first run, the `instance/hotel.db` file is intentionally not included. `python seed.py` creates the database automatically.

This project includes a **demo payment** flow for academic/testing purposes. It is not a real payment gateway.
