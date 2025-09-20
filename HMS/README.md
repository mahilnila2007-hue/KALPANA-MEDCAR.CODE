# KALPANA MEDCARE - Healthcare Management System

A comprehensive healthcare data management system designed for small to medium-sized clinics. This Flask-based web application provides patient management, appointment scheduling, and data export capabilities with a modern, responsive interface.

## 🏥 Features

### Patient Management
- ✅ Add new patients with comprehensive details
- ✅ Edit existing patient records
- ✅ Delete patients with confirmation
- ✅ Real-time patient search functionality
- ✅ Predefined symptoms dropdown for easy selection
- ✅ Visit tracking with editable visit counts
- ✅ Data validation for all required fields

### Appointment Scheduling
- ✅ Advanced appointment booking system
- ✅ Time conflict detection and prevention
- ✅ Enhanced time slot blocking (1-hour booking blocks overlapping 30-min slots)
- ✅ Available slot visualization with color coding
- ✅ Custom time slot creation beyond default hours
- ✅ Patient search and selection for appointments
- ✅ Duration-based booking (15/30/45/60 minutes)
- ✅ Appointment status management (scheduled/completed/cancelled)
- ✅ Today's schedule view
- ✅ Weekly schedule overview
- ✅ Appointment rescheduling and cancellation

### Data Management & Export
- ✅ SQLite database for reliable data storage
- ✅ CSV export for patient data
- ✅ CSV export for appointment schedules
- ✅ Comprehensive statistics dashboard
- ✅ Data integrity with foreign key constraints

### User Interface
- ✅ Modern, responsive design with glass-morphism effects
- ✅ Animated gradient backgrounds
- ✅ Smooth transitions and micro-interactions
- ✅ Mobile-friendly responsive layout
- ✅ Intuitive navigation with section-based interface
- ✅ Real-time data updates

## 📁 Project Structure

```
Amma code/
│
├── templates/
│   └── index.html          # Main HTML template with Flask integration
├── static/
│   ├── js/
│   │   └── script.js       # Frontend JavaScript with API integration
│   └── css/
│       └── style.css       # Comprehensive styling and animations
│
├── app.py                  # Flask backend application
├── patient.db             # SQLite database for patient data (auto-created)
├── data.db                 # SQLite database for appointments (auto-created)
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## 🚀 Installation & Setup

### Prerequisites
- Python 3.7 or higher
- pip (Python package installer)

### Step 1: Clone/Download the Project
Download the project files to your local machine.

### Step 2: Create Virtual Environment (Recommended)
```bash
cd "Amma code"
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Run the Application
```bash
python app.py
```

The application will start on `http://localhost:5000`

## 🔐 Login Credentials

**Username:** `kalpana`  
**Password:** `1204`

## 💾 Database Schema

### Patients Table (patient.db)
```sql
CREATE TABLE patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    serial_number TEXT UNIQUE NOT NULL,
    patient_name TEXT NOT NULL,
    phone_number TEXT NOT NULL,
    age INTEGER NOT NULL,
    sex TEXT NOT NULL,
    marital_status TEXT NOT NULL,
    problem TEXT NOT NULL,
    times_of_visit INTEGER DEFAULT 1,
    date_added DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Appointments Table (data.db)
```sql
CREATE TABLE appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    patient_name TEXT NOT NULL,
    patient_phone TEXT NOT NULL,
    date DATE NOT NULL,
    time TIME NOT NULL,
    duration INTEGER DEFAULT 30,
    notes TEXT,
    status TEXT DEFAULT 'scheduled',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients (id)
);
```

### Predefined Symptoms Table (data.db)
```sql
CREATE TABLE predefined_symptoms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symptom_name TEXT UNIQUE NOT NULL,
    category TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🔧 API Endpoints

### Authentication
- `POST /api/login` - User authentication

### Patient Management
- `GET /api/patients` - Get all patients
- `POST /api/patients` - Create new patient
- `PUT /api/patients/<id>` - Update patient
- `DELETE /api/patients/<id>` - Delete patient

### Appointment Management
- `GET /api/appointments` - Get all appointments
- `POST /api/appointments` - Create new appointment
- `PUT /api/appointments/<id>` - Update appointment
- `DELETE /api/appointments/<id>` - Delete appointment

### Data Export
- `GET /api/export/patients` - Export patients as CSV
- `GET /api/export/appointments` - Export appointments as CSV

### Symptoms
- `GET /api/symptoms` - Get predefined symptoms

## 🎨 Key Features Implemented

### Enhanced Time Slot Management
The system now properly handles time slot blocking:
- When a 1-hour appointment is booked, all overlapping 30-minute slots are automatically blocked
- Visual indication of available vs. booked slots with color coding
- Real-time conflict detection prevents double-booking

### Predefined Symptoms
Added a comprehensive dropdown with 24 common symptoms categorized by:
- General (Fever, Fatigue, Loss of Appetite)
- Respiratory (Cough, Cold, Shortness of Breath)
- Gastrointestinal (Stomach Ache, Nausea, Vomiting)
- Neurological (Headache, Dizziness, Insomnia)
- Musculoskeletal (Body Pain, Joint Pain, Back Pain)
- Cardiovascular (Chest Pain, High Blood Pressure)
- And more...

### Modern UI/UX
- Glass-morphism design with backdrop filters
- Animated gradient backgrounds
- Smooth transitions and hover effects
- Responsive grid layouts
- Mobile-optimized interface

## 🔍 Usage Guide

### Adding a New Patient
1. Navigate to "Add New Patient" section
2. Fill in all required fields
3. Use the predefined symptoms dropdown for quick selection
4. Submit the form to save patient data

### Booking an Appointment
1. Go to "Doctor's Visit Schedule" section
2. Select date and time
3. Choose patient from dropdown or search
4. Set appointment duration
5. Add optional notes
6. Click "Book Appointment"

### Managing Time Slots
- View available slots in the time slots overview
- Add custom time slots beyond default 9 AM - 6 PM
- Visual indicators show available (green) vs booked (red) slots
- Click on any available slot to select it for booking

### Exporting Data
- Use export buttons to download patient or appointment data as CSV
- Files include comprehensive information for record-keeping

## 🛠 Customization

### Adding New Symptoms
Symptoms can be added directly to the database or through the predefined_symptoms table:
```sql
INSERT INTO predefined_symptoms (symptom_name, category) 
VALUES ('New Symptom', 'Category');
```

### Modifying Time Slots
Default time slots are 9 AM - 6 PM in 30-minute intervals. This can be modified in the `generateTimeSlots()` function in script.js.

### Styling Changes
All styles are contained in `static/css/style.css` with well-organized sections for easy customization.

## 🔧 Technical Details

### Backend (Flask)
- RESTful API design
- SQLite database with proper relationships
- Input validation and error handling
- CSV export functionality
- Session management

### Frontend (JavaScript)
- Async/await for API calls
- Real-time data updates
- Enhanced time conflict detection
- Dynamic form validation
- Responsive design principles

### Database
- Two separate SQLite databases for organization
- Foreign key constraints for data integrity
- Automatic timestamp tracking
- Indexing for performance

## 🐛 Troubleshooting

### Common Issues
1. **Database not found**: Databases are auto-created on first run
2. **Port already in use**: Change port in app.py or kill existing process
3. **Permission errors**: Ensure write permissions in project directory

### Debug Mode
The application runs in debug mode by default. For production, set `debug=False` in app.py.

## 📝 Future Enhancements

- [ ] User authentication with multiple user accounts
- [ ] Patient medical history tracking
- [ ] Prescription management
- [ ] Email/SMS notifications for appointments
- [ ] Payment tracking
- [ ] Advanced reporting and analytics
- [ ] Integration with external systems

## 🤝 Contributing

This project is designed for Kalpana Medcare. For modifications or enhancements, please ensure proper testing of all features.

## 📄 License

This project is proprietary to Kalpana Medcare.

## 📞 Support

For technical support or questions about the system, please contact the development team.

---

**Developed for Kalpana Medcare - September 2025**
