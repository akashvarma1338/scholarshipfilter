# 🎓 Scholarship Eligibility Filter

A web-based application that shortlists scholarship candidates by applying academic and socioeconomic rules. The system takes student details as input, evaluates them against predefined eligibility criteria, and clearly displays eligibility results.

## ✨ Features

### Core Features
- **Student Application Form**: Collect student details including name, course, marks, income, category, etc.
- **Multiple Scholarship Support**: Check eligibility for multiple scholarships with different rule sets
- **Eligibility Checking**: Apply rules and display eligibility status
- **Rejection Reasons**: Clear explanation of why a student is not eligible

### Mandatory Innovations (Implemented)
1. **Multiple Scholarship Support** - System checks eligibility for multiple scholarships with different rules
2. **Reason for Rejection** - Specific reasons displayed when student is not eligible
3. **Dynamic Rule Update (Admin Feature)** - Admin can modify rules without changing code
4. **Priority Scoring System** - Students ranked based on marks and income
5. **Dashboard View** - Statistics showing total applicants, eligible count, and top priority students

## 🛠️ Technology Stack

- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Backend**: Python (Flask)
- **Database**: SQLite
- **Styling**: Custom CSS with modern design

## 📁 Project Structure

```
eduhack/
├── app.py                 # Main Flask application
├── config.py              # Configuration settings
├── models.py              # Database models (Student, Scholarship, Rule)
├── rules_engine.py        # Rules-based eligibility checking logic
├── requirements.txt       # Python dependencies
├── scholarship.db         # SQLite database (auto-created)
├── templates/             # HTML templates
│   ├── index.html         # Student application form
│   ├── results.html       # Eligibility results page
│   ├── dashboard.html     # Statistics dashboard
│   ├── admin.html         # Admin panel
│   ├── admin_login.html   # Admin login page
│   ├── 404.html           # Error page
│   └── 500.html           # Error page
└── static/                # Static files
    ├── css/
    │   └── style.css      # Main stylesheet
    └── js/
        ├── main.js        # Main JavaScript
        └── admin.js       # Admin panel JavaScript
```

## 🚀 Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Steps

1. **Navigate to project directory**
   ```bash
   cd eduhack
   ```

2. **Create virtual environment (optional but recommended)**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Open in browser**
   - Main Application: http://localhost:5000
   - Dashboard: http://localhost:5000/dashboard
   - Admin Panel: http://localhost:5000/admin

## 🔐 Admin Authentication (Google OAuth)

The admin panel uses **Google OAuth 2.0** for authentication. Here's how it works:

### Setting Up Google OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Navigate to **APIs & Services** > **Credentials**
4. Click **Create Credentials** > **OAuth Client ID**
5. Select **Web Application**
6. Add authorized redirect URI: `http://localhost:5000/admin/google/callback`
7. Copy the **Client ID** and **Client Secret**

### Configure the Application

Set environment variables or update `config.py`:
```python
GOOGLE_CLIENT_ID = 'your-client-id.apps.googleusercontent.com'
GOOGLE_CLIENT_SECRET = 'your-client-secret'
```

### Demo Mode

By default, `DEMO_MODE = True` in config.py, which:
- Auto-approves all new admin registrations
- First registered admin becomes Super Admin

Set `DEMO_MODE = False` for production to require Super Admin approval for new registrations.

### Admin Roles

- **Super Admin**: First registered admin, can approve/revoke other admins
- **Admin**: Regular admin, can manage scholarships and rules

## 📋 Default Scholarship Rules

The system comes with 4 pre-configured scholarships:

### 1. Merit Excellence Scholarship (₹50,000)
- Marks ≥ 85%
- No backlogs
- Full-time student

### 2. Financial Assistance Scholarship (₹75,000)
- Marks ≥ 75%
- Family income ≤ ₹2,50,000
- No backlogs
- Full-time student

### 3. SC/ST Welfare Scholarship (₹60,000)
- Marks ≥ 60%
- Category: SC or ST
- Family income ≤ ₹3,00,000
- Full-time student

### 4. General Academic Scholarship (₹25,000)
- Marks ≥ 75%
- Family income ≤ ₹2,50,000
- No backlogs
- Full-time student

## 🎯 Priority Scoring System

Students are ranked based on:
- **Marks Score (0-50 points)**: Higher marks = Higher score
- **Income Score (0-50 points)**: Lower income = Higher score
- **Category Bonus**: SC/ST +5, EWS +4, OBC +3

## 📖 API Endpoints

### Students
- `GET /api/students` - Get all students
- `GET /api/students/<id>` - Get specific student
- `POST /api/students` - Create new student
- `DELETE /api/students/<id>` - Delete student

### Scholarships
- `GET /api/scholarships` - Get all scholarships
- `GET /api/scholarships/<id>` - Get specific scholarship
- `POST /api/scholarships` - Create scholarship (Admin)
- `PUT /api/scholarships/<id>` - Update scholarship (Admin)
- `DELETE /api/scholarships/<id>` - Delete scholarship (Admin)

### Rules
- `POST /api/rules` - Create rule (Admin)
- `PUT /api/rules/<id>` - Update rule (Admin)
- `DELETE /api/rules/<id>` - Delete rule (Admin)

### Eligibility
- `GET /api/check-eligibility/<student_id>` - Check eligibility for all scholarships
- `GET /api/rankings/<scholarship_id>` - Get ranked eligible students

### Dashboard
- `GET /api/dashboard/stats` - Get dashboard statistics

## 🎨 Screenshots

### Student Application Form
Clean, intuitive form for students to enter their details.

### Eligibility Results
Clear display of eligible and not-eligible scholarships with reasons.

### Dashboard
Overview showing total applicants, eligibility statistics, and top priority students.

### Admin Panel
Manage scholarships and rules dynamically without code changes.

## 📝 Code Comments

The codebase is well-documented with clear comments explaining each step:
- Python files include docstrings and inline comments
- JavaScript functions are documented with JSDoc-style comments
- CSS is organized with section headers

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 License

This project is for educational purposes.

---

**Built with ❤️ for Education**
