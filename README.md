#  alx\_travel\_app\_0x00

A simplified travel booking API built with Django. This app allows users to view listings, make bookings, and leave reviews.

##  Project Overview

This project is a clone of `alx_travel_app` with a focus on:

* Defining Django models for **Listing**, **Booking**, and **Review**
* Creating serializers to expose model data via APIs
* Implementing a custom management command to **seed** the database with sample data

---

##  Project Structure

```
alx_travel_app_0x00/
├── listings/
│   ├── models.py         # Defines User, Listing, Booking, Review models
│   ├── serializers.py    # Serializers for Listing and Booking
│   └── management/
│       └── commands/
│           └── seed.py   # Seeds database with sample listings
├── manage.py
└── ...
```

---

##  Models

### `User`

Custom user model extending Django's `AbstractUser`, with a UUID primary key and `phone_number`.

### `Listing`

* Linked to `User`
* Fields: title, price, description, location, created\_at

### `Booking`

* Linked to `Listing` and `User` (host)
* Fields: status, start\_date, end\_date

### `Review`

* Linked to `Booking`, `Listing`, and `User`
* Fields: rating, comment

---

##  Serializers

Located in `listings/serializers.py`:

* `ListingSerializer`
* `BookingSerializer`

Used to convert model instances into JSON for API responses.

---

##  Seeding the Database

A custom Django management command that populates the database with sample data.

### Command File

`listings/management/commands/seed.py`

### Run Seeder

Make sure you've made migrations and migrated:

```bash
python manage.py makemigrations
python manage.py migrate
```

Then run the seed command:

```bash
python manage.py seed
```

 Creates:

* A default user (`dkd`)
* 10 sample listings linked to the user

---

##  Getting Started

### 1. Clone the Repo

```bash
git clone https://github.com/realdkd001/alx_travel_app_0x00.git
cd alx_travel_app_0x00
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Server

```bash
python manage.py runserver
```

---

## 🧪 API Testing

Use tools like [Postman](https://www.postman.com/) or `curl` to test the API endpoints (e.g., `/api/listings/`, `/api/bookings/`).

---

## 🧠 Author

**Daniel (DKD)**
ALX Software Engineering Program
