# 🌿 GoodLife Foundation – Visitor & Donation Tracker

**GoodLife Foundation Admin Portal** is a lightweight **Flask + SQLite3 web app** for small NGOs and orphanages to  
securely **record visitor details and track donations** in one place.

---

## ✨ Features

### 🧑‍🤝‍🧑 Visitor Management
- Capture **Name, Aadhaar number, Age, Address**
- Store **Purpose of Visit**, optional **Remarks**, and automatic **visit date**
- Data saved in the `visitors` table inside `goodlife_schema.db`

### 💝 Donation Tracking
- Record **Donor Name**, **Amount (₹)**, and **Items Donated**
- Choose **Payment Mode** (Cash / UPI / Bank Transfer)
- Optional **Payment Detail** (UPI ID or Bank Ref) shown dynamically
- Auto-records **donation_date** in the `donations` table

### 🖥️ Admin Portal
- Simple navigation header with **Visitor Entry** and **Donation Entry**
- Unified success page confirming submissions
- Works out of the box with no external database server

---

## 🛠 Tech Stack
- **Backend**: Flask 2.x  
- **Database**: SQLite3 (`goodlife_schema.db`)  
- **Frontend**: HTML5, CSS3, Jinja2 templates  
- **Language**: Python 3.x  

---

## 🚀 Getting Started

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/ShreyaVijaykumar/goodlife-foundation.git
cd goodlife-foundation
```

### 2️⃣ Install Dependencies
```bash
pip install flask
```

### 3️⃣ Run the App
```bash
python app.py
```
- Visit **http://127.0.0.1:5000/ or corresponding port**
- The SQLite database goodlife_schema.db is created automatically.

---

