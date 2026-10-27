# 💊 MediShare - Online Medicine Donation Platform

A simple web platform built with **Django** and **Bootstrap** that connects medicine donors with verified NGOs to help medicines reach needy patients instead of going to waste.

---

## 🌟 What Does This Project Do?

Many people have unused, unexpired medicines at home after recovery. At the same time, many NGOs and charitable clinics need free medicines for poor patients. 

**MediShare solves this by:**
1. Allowing people to donate sealed, unexpired medicines.
2. Allowing verified NGOs to request medicines for patients.
3. Giving admins full control to verify safety, check expiry dates, and track delivery.

---

## 👥 User Roles & Features

### 1. 💙 Donor
- Register and login (using username or email).
- Add medicine details (Name, Quantity, Expiry Date, Storage, Photo).
- Track donation status (`Pending`, `Approved`, `Rejected`).
- Download and print official **Donation Receipts**.

### 2. 🏥 NGO (Recipient)
- Register with official NGO name and registration number.
- Browse available medicines in the marketplace.
- Request medicines with a clinical reason.
- Track delivery step-by-step from dispatch to delivery.

### 3. 👑 Admin (Safety & Verification)
- Verify new NGOs before they can request medicines.
- Review donated medicines (check photos, expiry dates, and packaging).
- Approve or reject medicine requests.
- Update shipment status: `Requested` ➔ `Approved` ➔ `Packed` ➔ `Shipped` ➔ `Out for Delivery` ➔ `Delivered`.

---

## 🔄 How It Works (In 4 Easy Steps)

1. **Donate**: Donor uploads details of unused, sealed medicine.
2. **Review**: Admin checks the expiry date and packaging condition.
3. **Request**: Approved medicines appear in the NGO marketplace for requests.
4. **Track**: NGO and Donor can track the medicine delivery live until delivered.

---

## 🛠️ Built With

- **Backend:** Python, Django
- **Frontend:** HTML5, CSS3, Bootstrap 5, Bootstrap Icons
- **Database:** SQLite (default Django database)

---

## 🚀 How to Run on Your Computer

### 1. Clone or Download the project
```bash
git clone https://github.com/your-username/medishare.git
cd med_tech-main
```

### 2. Install requirements
Make sure you have Python installed, then run:
```bash
pip install -r requirements.txt
```

### 3. Setup Database
```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Create an Admin Account
```bash
python manage.py createsuperuser
```
*(Enter a username, email, and password of your choice)*

### 5. Start the Server
```bash
python manage.py runserver
```

Open your browser and go to:
👉 **http://127.0.0.1:8000/**

---

## 📂 Project Structure

```text
med_tech-main/
├── core/                  # Main application folder
│   ├── templates/         # HTML web pages
│   ├── models.py          # Database models (User, Donations, Requests)
│   ├── views.py           # Logic for login, donations, tracking
│   └── urls.py            # Page links & routes
├── medicine_donation/     # Project settings folder
│   └── settings.py        # Django configuration
├── media/                 # Uploaded photos of medicines
├── requirements.txt       # List of required packages
└── manage.py              # Django command-line tool
```

---

## 📜 License
This project is open-source and free to use for educational and learning purposes.
