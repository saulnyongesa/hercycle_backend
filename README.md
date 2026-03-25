# 🩸 HemaCycle Backend & Web Portals

HemaCycle is a dedicated health platform designed to empower women in their reproductive age through menstrual health tracking and machine learning-driven anemia risk assessments. The system bridges the gap between individual tracking and community healthcare by allowing Community Health Volunteers (CHVs) to monitor, advise, and support users.

This repository contains the Django backend, API endpoints, and the web-based dashboards for Admins, CHVs, and Women/Adolescents.

## 👥 User Roles Explained

The system is built around three distinct user roles, each with specific permissions and interfaces:

1. 👑 Admin (Superuser)
   * Role: System administrator and overseer.
   * Capabilities: Approves new CHV registrations, views global platform statistics, and manages database records via the Django Admin panel and Custom Admin Dashboard.

2. 🩺 Community Health Volunteer (CHV)
   * Role: Local healthcare provider/monitor.
   * Capabilities: Registers on the platform (requires Admin approval). Once approved, they can onboard new women/adolescents, view AI-generated health & anemia risk reports for their assigned users, and send direct Medical Advice notes.

3. 🌸 Woman / Adolescent
   * Role: The primary end-user.
   * Capabilities: Uses the personal health web app to log menstrual cycles (start/end dates, flow intensity), log daily symptoms (cramps, fatigue, pale skin), read educational health articles, and receive targeted advice from their assigned CHV.

---

## 🚀 Local Setup & Installation

Follow these steps to get the project running on your local machine.

### 1. Prerequisites
Ensure you have the following installed on your system:
* Python (Latest Version - 3.10+ recommended)
* Git

### 2. Clone the Repository
Open your terminal or command prompt and run:
git clone https://github.com/saulnyongesa/hercycle_backend.git
cd hercycle_backend

### 3. Create and Activate a Virtual Environment
It is best practice to isolate your project dependencies. Create a virtual environment (.venv):

For Windows:
python -m venv .venv
.venv\Scripts\activate

For macOS/Linux:
python3 -m venv .venv
source .venv/bin/activate

### 4. Install Dependencies
With your virtual environment active, install the required Python packages:
pip install --upgrade pip
pip install -r requirements.txt

### 5. Apply Database Migrations
Initialize your local SQLite database with the required tables:
python manage.py makemigrations
python manage.py migrate

---

## 🧪 Testing Guide: Step-by-Step Walkthrough

To fully test the system, you will need to create and interact with all three user roles. Follow this specific sequence to mimic a real-world deployment.

### Step 1: Create the Admin Account & Start Server
First, create the Superuser (Admin) account.
python manage.py createsuperuser
# Follow the prompts to set a username (e.g., 'admin'), email, and password.

Now, start the development server:
python manage.py runserver
*The server will be live at http://127.0.0.1:8000/*

### Step 2: Register a Demo CHV
1. Open your browser and go to http://127.0.0.1:8000/. You will see the HemaCycle landing page.
2. Click "CHV & Admin Portal".
3. Go to the Register tab.
4. Fill in the details (e.g., Username: NurseJane, Org: Red Cross, Password: testpassword123).
5. Click Submit Application. The system will notify you that the account is pending Admin approval.

### Step 3: Admin Approves the CHV
CHVs cannot log in until an Admin verifies them.
1. Navigate to the Django Admin panel: http://127.0.0.1:8000/admin/
2. Log in using the Superuser credentials you created in Step 1.
3. Under the core app models, locate CHV Profiles.
4. Click on NurseJane's profile, check the 'Is approved' checkbox, and save.
5. (Optional) Visit http://127.0.0.1:8000/admin-dashboard/ to view the custom Admin stats dashboard.

### Step 4: CHV Onboards a Woman
1. Go back to the main landing page http://127.0.0.1:8000/.
2. Click "CHV & Admin Portal" and log in as the CHV (NurseJane).
3. You are now in the CHV Dashboard. Click "Add New Girl/Woman".
4. Fill in the details (e.g., Username: Sarah99, Password: sarahpassword).
5. Important: The system will generate a profile for her. Note her username and password. 

### Step 5: The Woman Logs In to Her App
1. Open an Incognito Window (or log out of the CHV account) and go to http://127.0.0.1:8000/.
2. Click the pink "🌸 For Women (My Health App)" button. 
3. This redirects you to the user application view (/user-app/).
4. Log in using Sarah99 and her password. 
5. Note: Behind the scenes, the system authenticates her using JWT tokens and stores them in localStorage for a seamless SPA (Single Page Application) experience.

### Step 6: Log Health Data (The Woman's Perspective)
1. On Sarah's dashboard, click "💧 Start Period". Select a flow intensity (e.g., Heavy) and click Start.
2. Click "🤕 Log Symptom". Log "Pale Skin" with a severity of 4, and "Fatigue" with a severity of 5.
3. Navigate to the "📚 Library" tab to read educational articles (if any have been added by the admin).

### Step 7: CHV Reviews Data & Sends Advice
1. Switch back to your CHV browser window (logged in as NurseJane) and refresh the dashboard.
2. Click on Sarah99's profile to view her details.
3. Observe the ML Report: Because Sarah logged Heavy flow, Pale Skin, and Fatigue, the Machine Learning service will flag her as "High Risk" for anemia and display suggestions.
4. Click "Add Note/Advice" and type: "Hi Sarah, I noticed your fatigue and heavy flow. Please make sure to eat iron-rich foods like spinach this week. Let's talk on Tuesday."
5. Submit the advice.

### Step 8: The Notification Loop Completes
1. Switch back to Sarah's browser window (the User App) and refresh the page.
2. Observe the Dashboard:
   * A cyan 🩺 Advice Card will now appear at the top of her dashboard displaying the personalized note from NurseJane.
   * A yellow notification dot will appear on the 🔔 Bell icon in the top right.
3. Click the Bell icon to view the unread notification regarding her new advice message. Click "Mark all as read".

🎉 Congratulations! You have successfully tested the entire HemaCycle backend and web ecosystem.
