# EduConnect 🎓
### Hyperlocal Digitalized Tuitions & Collaborative Learning Platform

A clean, minimalist 3-Step Flask web platform engineered for connecting near by mentors and students.
---

## 🎯 The 3 Core Steps

1. **Step 1: Take Data**: Students & Tutors register with subject preferences and live GPS coordinates captured via the HTML5 Geolocation API.
2. **Step 2: Haversine Algorithm**: Calculates great-circle physical distance in kilometers ($R = 6,371\text{ km}$) across Earth's spherical surface, filtering candidates by radius (5–50 km) and sorting closest-first.
3. **Step 3: Cohorts & Chat**: Micro-tuition batches with live asynchronous 3-second AJAX polling chat.

---
## 📂 Project Structure

```
educonnect/
│
├── app.py              <-- Minimalist 3-Step backend (supports MySQL & SQLite)
├── requirements.txt    <-- Python dependencies for Render (Flask, Gunicorn, etc.)
├── Procfile            <-- Render / Cloud deployment startup command
├── render.yaml         <-- Render Blueprint configuration
├── runtime.txt         <-- Python version (3.11.9)
├── .gitignore          <-- Git ignore rules
├── schema.sql          <-- MySQL schema
├── start.bat           <-- 1-click local launcher
├── README.md           <-- Documentation & deploy guide
│
├── static/
│   └── js/location.js  <-- HTML5 GPS location script
│
└── templates/          <-- Clean HTML templates (No extra menus or bloat)
    ├── index.html
    ├── login.html
    ├── student_registration_form.html
    ├── teacher_registration_form.html
    ├── dashboard.html
    ├── nearby.html
    ├── cohorts.html
    └── cohort_detail.html
```

---

## 💻 Local Testing

Run `start.bat` or:
```bash
python app.py
```
Visit **http://127.0.0.1:5000** in your browser.
