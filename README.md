# EduConnect 🎓
### Hyperlocal Digitalized Tuitions & Collaborative Learning Platform

A clean, minimalist 3-Step Flask web platform engineered for 1-click deployment on **Render** and version control on **GitHub**.

---

## 🎯 The 3 Core Steps

1. **Step 1: Take Data**: Students & Tutors register with subject preferences and live GPS coordinates captured via the HTML5 Geolocation API.
2. **Step 2: Haversine Algorithm**: Calculates great-circle physical distance in kilometers ($R = 6,371\text{ km}$) across Earth's spherical surface, filtering candidates by radius (5–50 km) and sorting closest-first.
3. **Step 3: Cohorts & Chat**: Micro-tuition batches with live asynchronous 3-second AJAX polling chat.

---

## 🚀 How to Upload to GitHub (Git)

Run these commands inside this **`educonnect`** folder:

```bash
cd "c:\src\educonnect"

# 1. Initialize Git repository
git init

# 2. Add all files
git add .

# 3. Create initial commit
git commit -m "Initial commit: EduConnect 3-step platform ready for Render"

# 4. Set branch to main
git branch -M main

# 5. Link to your GitHub repository (replace with your repo URL)
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/educonnect.git

# 6. Push code to GitHub
git push -u origin main
```

---

## 🌐 How to Deploy on Render (Free & Fast)

1. Go to [render.com](https://render.com) and log in.
2. Click **New +** $\rightarrow$ **Web Service**.
3. Select **Build and deploy from a Git repository** and connect your `educonnect` repository.
4. Fill in the settings:
   - **Name**: `educonnect`
   - **Language**: `Python`
   - **Branch**: `main`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Plan**: `Free`
5. Click **Create Web Service**!

> 💡 **Database on Render**:
> `app.py` has built-in automatic fallback: if an external MySQL database isn't configured, it automatically initializes and runs on embedded SQLite with pre-seeded demo accounts, guaranteeing your Render app **never crashes**!

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
