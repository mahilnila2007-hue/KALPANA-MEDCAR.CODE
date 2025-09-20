// Global variables
let patients = [];
let appointments = [];
let customTimeSlots = [];
let currentSection = 'loginSection';
let editingPatientIndex = -1;

// API Base URL
const API_BASE = '';

// Initialize the application
window.addEventListener('load', () => {
    // Check if user is already logged in
    const currentUser = sessionStorage.getItem('currentUser');
    
    if (currentUser) {
        // User is logged in, restore the session
        try {
            const user = JSON.parse(currentUser);
            console.log('Restoring session for:', user.name);
            
            // Update welcome message
            const welcomeElement = document.getElementById('welcomeMessage');
            if (welcomeElement && user.name) {
                welcomeElement.textContent = `Welcome back, ${user.name}`;
            }
            
            // Show main menu and hide login section
            showSection('mainMenu');
            document.getElementById('loginSection').style.display = 'none';
            
            // Initialize application data
            loadData();
            updateAppointmentPatientOptions();
            generateTimeSlots();
            updateStats();
            
        } catch (error) {
            console.error('Error restoring session:', error);
            // If there's an error, clear the session and show login
            sessionStorage.removeItem('currentUser');
            showLoginPage();
        }
    } else {
        // No session, show login page
        showLoginPage();
    }
    
    // Set up event listeners for appointment form (only once)
    if (document.getElementById('appointmentDate')) {
        document.getElementById('appointmentDate').addEventListener('change', generateTimeSlots);
    }
    if (document.getElementById('appointmentTime')) {
        document.getElementById('appointmentTime').addEventListener('change', generateTimeSlots);
    }
});

// Helper function to show login page
function showLoginPage() {
    setDefaultDate();
    toggleAuthMode('login');
    sessionStorage.removeItem('registrationData');
    showSection('loginSection');
    document.getElementById('loginSection').style.display = 'block';
}

// Utility Functions
function formatTime(time) {
    const [hours, minutes] = time.split(':');
    const date = new Date();
    date.setHours(parseInt(hours), parseInt(minutes));
    return date.toLocaleTimeString('en-US', { 
        hour: 'numeric', 
        minute: '2-digit',
        hour12: true 
    });
}

function formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-GB', {
        day: '2-digit',
        month: '2-digit', 
        year: 'numeric'
    });
}

// API Functions
async function apiRequest(endpoint, method = 'GET', data = null) {
    try {
        const config = {
            method,
            headers: {
                'Content-Type': 'application/json',
            }
        };
        
        if (data) {
            config.body = JSON.stringify(data);
        }
        
        const response = await fetch(API_BASE + endpoint, config);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API request failed:', error);
        alert('Error: ' + error.message);
        throw error;
    }
}

// Authentication - handled by login() function called from HTML form onsubmit

// Navigation functions
function showSection(sectionId) {
    // Hide all sections
    document.querySelectorAll('.section').forEach(section => {
        section.classList.remove('active');
        section.style.display = 'none';
    });
    
    // Show selected section
    const targetSection = document.getElementById(sectionId);
    targetSection.style.display = 'block';
    setTimeout(() => {
        targetSection.classList.add('active');
    }, 10);
    
    // Show/hide top header based on section
    const topHeaderSpace = document.getElementById('topHeaderSpace');
    const body = document.body;
    
    if (sectionId === 'mainMenu') {
        // Show top header for main menu
        topHeaderSpace.style.display = 'block';
        body.classList.add('top-header-visible');
        
        // Update welcome message in top header
        const currentUser = sessionStorage.getItem('currentUser');
        if (currentUser) {
            const user = JSON.parse(currentUser);
            document.getElementById('topWelcomeMessage').textContent = `Welcome back, ${user.name}`;
        }
    } else {
        // Hide top header for other sections
        topHeaderSpace.style.display = 'none';
        body.classList.remove('top-header-visible');
    }
    
    currentSection = sectionId;

    // Update navigation buttons
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    // Refresh data when switching sections
    if (sectionId === 'patientSection') {
        clearPatientForm();
        editingPatientIndex = -1;
        document.getElementById('patientFormTitle').textContent = '➕ Add New Patient';
        document.getElementById('submitPatientBtn').textContent = 'Add Patient';
        document.getElementById('cancelEditBtn').classList.add('hidden');
    } else if (sectionId === 'medicalRecordsSection') {
        refreshMedicalRecordsTable();
        updateStats();
    } else if (sectionId === 'scheduleSection') {
        updateAppointmentPatientOptions();
        showTodaySchedule();
        generateTimeSlots();
    }
}

function logout() {
    // Clear user session
    sessionStorage.removeItem('currentUser');
    sessionStorage.removeItem('registrationData');
    
    // Reset welcome message
    const welcomeElement = document.getElementById('welcomeMessage');
    if (welcomeElement) {
        welcomeElement.textContent = 'Welcome to KALPANA MEDCARE';
    }
    
    // Show login section and clear form
    showSection('loginSection');
    document.getElementById('loginSection').style.display = 'block';
    document.getElementById('username').value = '';
    document.getElementById('password').value = '';
    
    // Reset form to login mode
    toggleAuthMode('login');
}

// Patient search functionality
function searchPatients() {
    const searchTerm = document.getElementById('patientSearch').value.toLowerCase().trim();
    const searchResults = document.getElementById('searchResults');
    
    if (searchTerm.length === 0) {
        searchResults.style.display = 'none';
        return;
    }

    const filteredPatients = patients.filter(patient => 
        patient.patient_name.toLowerCase().includes(searchTerm) ||
        patient.phone_number.includes(searchTerm) ||
        patient.serial_number.toLowerCase().includes(searchTerm)
    );

    if (filteredPatients.length === 0) {
        searchResults.innerHTML = '<div class="search-result-item">No patients found</div>';
        searchResults.style.display = 'block';
        return;
    }

    searchResults.innerHTML = filteredPatients.map(patient => 
        `<div class="search-result-item" onclick="selectPatient('${patient.id}', '${patient.patient_name}', '${patient.serial_number}')">
            <strong>${patient.patient_name}</strong> (${patient.serial_number})<br>
            <small>📞 ${patient.phone_number}</small>
        </div>`
    ).join('');
    searchResults.style.display = 'block';
}

function selectPatient(patientId, patientName, serialNumber) {
    document.getElementById('appointmentPatient').value = patientId;
    document.getElementById('patientSearch').value = `${patientName} (${serialNumber})`;
    document.getElementById('searchResults').style.display = 'none';
}

// Hide search results when clicking outside
document.addEventListener('click', function(e) {
    if (!e.target.closest('.search-container')) {
        document.getElementById('searchResults').style.display = 'none';
    }
});

// Patient Management Functions
function handleSexChange(selected) {
    const male = document.getElementById('male');
    const female = document.getElementById('female');
    
    if (selected === 'male') {
        female.checked = false;
    } else {
        male.checked = false;
    }
}

function handleMaritalChange(selected) {
    const married = document.getElementById('married');
    const unmarried = document.getElementById('unmarried');
    
    if (selected === 'married') {
        unmarried.checked = false;
    } else {
        married.checked = false;
    }
}

// Predefined symptoms functionality
function addPredefinedSymptom() {
    const select = document.getElementById('predefinedSymptoms');
    const textarea = document.getElementById('problem');
    const selectedSymptom = select.value;
    
    if (selectedSymptom) {
        const currentText = textarea.value.trim();
        if (currentText) {
            // Check if symptom already exists in the text
            if (!currentText.toLowerCase().includes(selectedSymptom.toLowerCase())) {
                textarea.value = currentText + ', ' + selectedSymptom;
            }
        } else {
            textarea.value = selectedSymptom;
        }
        select.value = ''; // Reset selection
    }
}

function clearSymptoms() {
    document.getElementById('problem').value = '';
    document.getElementById('predefinedSymptoms').value = '';
}

// Patient form submission
document.getElementById('patientForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const formData = {
        serial_number: document.getElementById('serialNumber').value,
        patient_name: document.getElementById('patientName').value,
        phone_number: document.getElementById('phoneNumber').value,
        age: parseInt(document.getElementById('age').value),
        times_of_visit: parseInt(document.getElementById('timesOfVisit').value),
        problem: document.getElementById('problem').value,
        sex: document.getElementById('male').checked ? 'Male' : 
             document.getElementById('female').checked ? 'Female' : '',
        marital_status: document.getElementById('married').checked ? 'Married' : 
                       document.getElementById('unmarried').checked ? 'Unmarried' : ''
    };
    
    if (!formData.sex) {
        alert('Please select sex');
        return;
    }
    
    if (!formData.marital_status) {
        alert('Please select marital status');
        return;
    }
    
    try {
        if (editingPatientIndex >= 0) {
            // Update existing patient
            const patientId = patients[editingPatientIndex].id;
            await apiRequest(`/api/patients/${patientId}`, 'PUT', formData);
            alert('Patient updated successfully!');
        } else {
            // Add new patient
            await apiRequest('/api/patients', 'POST', formData);
            alert('Patient added successfully!');
        }
        
        clearPatientForm();
        editingPatientIndex = -1;
        document.getElementById('patientFormTitle').textContent = '➕ Add New Patient';
        document.getElementById('submitPatientBtn').textContent = 'Add Patient';
        document.getElementById('cancelEditBtn').classList.add('hidden');
        
        await loadData();
        updateStats();
        updateAppointmentPatientOptions();
        
    } catch (error) {
        console.error('Failed to save patient:', error);
    }
});

function clearPatientForm() {
    document.getElementById('patientForm').reset();
    document.getElementById('timesOfVisit').value = '1';
    document.getElementById('editPatientId').value = '';
    document.getElementById('predefinedSymptoms').value = '';
}

function cancelEdit() {
    editingPatientIndex = -1;
    clearPatientForm();
    document.getElementById('patientFormTitle').textContent = '➕ Add New Patient';
    document.getElementById('submitPatientBtn').textContent = 'Add Patient';
    document.getElementById('cancelEditBtn').classList.add('hidden');
}

async function refreshMedicalRecordsTable() {
    const tbody = document.getElementById('medicalRecordsTableBody');
    tbody.innerHTML = '';
    
    patients.forEach((patient, index) => {
        const row = tbody.insertRow();
        row.innerHTML = `
            <td>${patient.serial_number}</td>
            <td>${patient.patient_name}</td>
            <td>${patient.phone_number}</td>
            <td>${patient.age}</td>
            <td>${patient.sex}</td>
            <td>${patient.marital_status}</td>
            <td style="max-width: 200px; word-wrap: break-word;">${patient.problem}</td>
            <td>
                <input type="number" class="visits-input" value="${patient.times_of_visit}" 
                       onchange="updateVisits(${index}, this.value)" min="1" 
                       style="width: 60px; padding: 5px; text-align: center; border: 1px solid #ddd; border-radius: 5px;">
            </td>
            <td>${patient.date_added || 'N/A'}</td>
            <td>
                <div class="action-buttons">
                    <button onclick="editPatientRecord(${index})" class="btn btn-small">Edit</button>
                    <button onclick="deletePatient(${index})" class="btn btn-small btn-danger">Delete</button>
                </div>
            </td>
        `;
    });
}

function editPatientRecord(index) {
    const patient = patients[index];
    editingPatientIndex = index;
    
    // Fill the form with patient data
    document.getElementById('serialNumber').value = patient.serial_number;
    document.getElementById('patientName').value = patient.patient_name;
    document.getElementById('phoneNumber').value = patient.phone_number;
    document.getElementById('age').value = patient.age;
    document.getElementById('timesOfVisit').value = patient.times_of_visit;
    document.getElementById('problem').value = patient.problem;
    
    document.getElementById('male').checked = patient.sex === 'Male';
    document.getElementById('female').checked = patient.sex === 'Female';
    document.getElementById('married').checked = patient.marital_status === 'Married';
    document.getElementById('unmarried').checked = patient.marital_status === 'Unmarried';
    
    // Update form UI for editing
    document.getElementById('patientFormTitle').textContent = '✏️ Edit Patient';
    document.getElementById('submitPatientBtn').textContent = 'Update Patient';
    document.getElementById('cancelEditBtn').classList.remove('hidden');
    
    // Switch to patient section
    showSection('patientSection');
}

async function updateVisits(index, newCount) {
    if (newCount >= 1) {
        try {
            const patientId = patients[index].id;
            await apiRequest(`/api/patients/${patientId}`, 'PUT', { times_of_visit: parseInt(newCount) });
            patients[index].times_of_visit = parseInt(newCount);
            updateStats();
        } catch (error) {
            console.error('Failed to update visits:', error);
        }
    }
}

async function deletePatient(index) {
    if (!confirm('Are you sure you want to delete this patient?')) {
        return;
    }
    
    try {
        const patientId = patients[index].id;
        await apiRequest(`/api/patients/${patientId}`, 'DELETE');
        
        await loadData();
        refreshMedicalRecordsTable();
        updateStats();
        updateAppointmentPatientOptions();
        
        alert('Patient deleted successfully!');
    } catch (error) {
        console.error('Failed to delete patient:', error);
    }
}

function updateStats() {
    const totalPatients = patients.length;
    const totalVisits = patients.reduce((sum, patient) => sum + patient.times_of_visit, 0);
    const avgVisits = totalPatients > 0 ? (totalVisits / totalPatients).toFixed(1) : 0;
    
    document.getElementById('totalPatients').textContent = totalPatients;
    document.getElementById('totalVisits').textContent = totalVisits;
    document.getElementById('avgVisits').textContent = avgVisits;
}

// Schedule Management Functions
function setDefaultDate() {
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('appointmentDate').value = today;
    document.getElementById('timeSlotsDatePicker').value = today;
}

function updateAppointmentPatientOptions() {
    const select = document.getElementById('appointmentPatient');
    select.innerHTML = '<option value="">Select a patient</option>';
    
    patients.forEach(patient => {
        const option = document.createElement('option');
        option.value = patient.id;
        option.textContent = `${patient.patient_name} (${patient.serial_number})`;
        select.appendChild(option);
    });
}

// Enhanced time conflict checking with proper slot blocking
function checkTimeConflict(date, time, duration) {
    const appointmentStart = new Date(`${date}T${time}`);
    const appointmentEnd = new Date(appointmentStart.getTime() + (duration * 60000));
    
    return appointments.some(app => {
        if (app.date !== date) return false;
        
        const existingStart = new Date(`${app.date}T${app.time}`);
        const existingEnd = new Date(existingStart.getTime() + (app.duration * 60000));
        
        return (appointmentStart < existingEnd && appointmentEnd > existingStart);
    });
}

// Enhanced slot blocking - if 1 hour is booked, block overlapping 30-min slots
function getBlockedSlots(date) {
    const blockedSlots = new Set();
    
    appointments.forEach(app => {
        if (app.date !== date) return;
        
        const startTime = new Date(`${app.date}T${app.time}`);
        const endTime = new Date(startTime.getTime() + (app.duration * 60000));
        
        // Block all 30-minute intervals that overlap with this appointment
        const current = new Date(startTime);
        while (current < endTime) {
            const timeStr = current.toTimeString().slice(0, 5);
            blockedSlots.add(timeStr);
            current.setMinutes(current.getMinutes() + 30);
        }
    });
    
    return blockedSlots;
}

// Appointment form submission
document.getElementById('appointmentForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const appointmentData = {
        date: document.getElementById('appointmentDate').value,
        time: document.getElementById('appointmentTime').value,
        patient_id: parseInt(document.getElementById('appointmentPatient').value),
        duration: parseInt(document.getElementById('appointmentDuration').value),
        notes: document.getElementById('appointmentNotes').value
    };
    
    if (!appointmentData.patient_id) {
        alert('Please select a patient');
        return;
    }
    
    // Check for conflicts
    if (checkTimeConflict(appointmentData.date, appointmentData.time, appointmentData.duration)) {
        alert('Time slot is not available. Please choose a different time.');
        return;
    }
    
    try {
        await apiRequest('/api/appointments', 'POST', appointmentData);
        alert('Appointment booked successfully!');
        
        clearAppointmentForm();
        await loadData();
        showTodaySchedule();
        generateTimeSlots();
    } catch (error) {
        console.error('Failed to book appointment:', error);
    }
});

function clearAppointmentForm() {
    document.getElementById('appointmentForm').reset();
    document.getElementById('patientSearch').value = '';
    setDefaultDate();
}

function checkAvailability() {
    const date = document.getElementById('appointmentDate').value;
    const time = document.getElementById('appointmentTime').value;
    const duration = parseInt(document.getElementById('appointmentDuration').value) || 30;
    
    if (!date || !time) {
        alert('Please select both date and time');
        return;
    }
    
    if (checkTimeConflict(date, time, duration)) {
        alert('❌ Time slot is not available. Please choose a different time.');
    } else {
        alert('✅ Time slot is available!');
    }
}

function showTodaySchedule() {
    const today = new Date().toISOString().split('T')[0];
    displayScheduleForDate(today, "Today's Schedule");
}

function showWeeklySchedule() {
    const today = new Date();
    const startOfWeek = new Date(today.setDate(today.getDate() - today.getDay()));
    
    let weeklyHtml = '<h3>This Week\'s Appointments</h3>';
    
    for (let i = 0; i < 7; i++) {
        const date = new Date(startOfWeek);
        date.setDate(startOfWeek.getDate() + i);
        const dateStr = date.toISOString().split('T')[0];
        const dayName = date.toLocaleDateString('en-US', { weekday: 'long' });
        
        const dayAppointments = appointments
            .filter(app => app.date === dateStr)
            .sort((a, b) => a.time.localeCompare(b.time));
        
        weeklyHtml += `
            <div style="margin-bottom: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 10px;">
                <h4>${dayName} - ${date.toLocaleDateString()}</h4>
                ${dayAppointments.length > 0 ? 
                    dayAppointments.map(app => `
                        <div class="appointment-card" style="margin: 10px 0; padding: 10px;">
                            <strong>${formatTime(app.time)}</strong> - ${app.patient_name} (${app.duration} min)
                            ${app.notes ? `<br><small>Notes: ${app.notes}</small>` : ''}
                        </div>
                    `).join('') 
                    : '<p style="color: #6c757d; font-style: italic;">No appointments scheduled</p>'
                }
            </div>
        `;
    }
    
    document.getElementById('scheduleTitle').textContent = '📊 Weekly Schedule';
    document.getElementById('appointmentsList').innerHTML = weeklyHtml;
}

function displayScheduleForDate(date, title) {
    const dayAppointments = appointments
        .filter(app => app.date === date)
        .sort((a, b) => a.time.localeCompare(b.time));
    
    document.getElementById('scheduleTitle').textContent = `📊 ${title}`;
    
    if (dayAppointments.length === 0) {
        document.getElementById('appointmentsList').innerHTML = 
            '<p style="text-align: center; color: #6c757d; font-size: 16px; padding: 40px;">No appointments scheduled for this day</p>';
        return;
    }
    
    const appointmentsHtml = dayAppointments.map(app => `
        <div class="appointment-card">
            <div class="appointment-time">${formatTime(app.time)} (${app.duration} min)</div>
            <div class="appointment-patient">${app.patient_name}</div>
            <div class="appointment-details">
                📞 ${app.patient_phone}
                ${app.notes ? `<br>📝 ${app.notes}` : ''}
            </div>
            <div style="margin-top: 10px;">
                <button onclick="completeAppointment('${app.id}')" class="btn btn-small btn-success">✅ Complete</button>
                <button onclick="cancelAppointment('${app.id}')" class="btn btn-small btn-danger">❌ Cancel</button>
                <button onclick="rescheduleAppointment('${app.id}')" class="btn btn-small">🔄 Reschedule</button>
            </div>
        </div>
    `).join('');
    
    document.getElementById('appointmentsList').innerHTML = appointmentsHtml;
}

function generateTimeSlots() {
    const container = document.getElementById('timeSlotsContainer');
    const selectedDate = document.getElementById('timeSlotsDatePicker').value || new Date().toISOString().split('T')[0];
    
    // Update date display
    const dateObj = new Date(selectedDate);
    const dateDisplay = dateObj.toLocaleDateString('en-GB', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    });
    document.getElementById('timeSlotsDate').textContent = dateDisplay;
    
    let slotsHtml = '';
    
    // Generate default slots from 9 AM to 6 PM
    const defaultSlots = [];
    for (let hour = 9; hour < 18; hour++) {
        for (let minute = 0; minute < 60; minute += 30) {
            defaultSlots.push(`${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`);
        }
    }
    
    // Combine default slots and custom slots
    const allSlots = [...defaultSlots, ...customTimeSlots].sort();
    const blockedSlots = getBlockedSlots(selectedDate);
    
    allSlots.forEach((timeStr, index) => {
        const isBooked = blockedSlots.has(timeStr);
        const isSelectedInForm = document.getElementById('appointmentTime').value === timeStr && 
                               document.getElementById('appointmentDate').value === selectedDate;
        
        const slotClass = isBooked ? 'booked' : (isSelectedInForm ? 'selected-time' : 'available');
        
        slotsHtml += `
            <div class="time-slot ${slotClass}" onclick="selectTimeSlot('${timeStr}')">
                <strong>${formatTime(timeStr)}</strong>
                <div style="font-size: 12px; margin-top: 5px;">
                    ${isBooked ? '❌ Booked' : '✅ Available'}
                </div>
                ${customTimeSlots.includes(timeStr) ? `
                    <button class="time-slot-delete" onclick="removeCustomTimeSlot('${timeStr}')" title="Remove custom slot">×</button>
                ` : ''}
                ${!isBooked ? `
                    <input type="text" class="time-slot-input" placeholder="Add note..." 
                           onchange="updateTimeSlotNote('${timeStr}', this.value)" 
                           onclick="event.stopPropagation();">
                ` : ''}
            </div>
        `;
    });
    
    container.innerHTML = slotsHtml;
}

function selectTimeSlot(time) {
    document.getElementById('appointmentTime').value = time;
    const selectedDate = document.getElementById('timeSlotsDatePicker').value;
    document.getElementById('appointmentDate').value = selectedDate;
    generateTimeSlots(); // Refresh to show selected time
}

function addCustomTimeSlot() {
    const customTime = prompt('Enter custom time (HH:MM format, 24-hour):', '19:00');
    if (customTime && /^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$/.test(customTime)) {
        if (!customTimeSlots.includes(customTime)) {
            customTimeSlots.push(customTime);
            customTimeSlots.sort();
            generateTimeSlots();
        } else {
            alert('This time slot already exists!');
        }
    } else if (customTime) {
        alert('Please enter time in HH:MM format (e.g., 19:00)');
    }
}

function removeCustomTimeSlot(timeStr) {
    if (confirm(`Remove custom time slot ${formatTime(timeStr)}?`)) {
        customTimeSlots = customTimeSlots.filter(slot => slot !== timeStr);
        generateTimeSlots();
    }
}

function updateTimeSlotNote(timeStr, note) {
    // This could be expanded to save notes for time slots
    console.log(`Note for ${timeStr}: ${note}`);
}

function showAvailableSlots() {
    const selectedDate = document.getElementById('timeSlotsDatePicker').value || new Date().toISOString().split('T')[0];
    const availableSlots = [];
    
    const defaultSlots = [];
    for (let hour = 9; hour < 18; hour++) {
        for (let minute = 0; minute < 60; minute += 30) {
            defaultSlots.push(`${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`);
        }
    }
    
    const allSlots = [...defaultSlots, ...customTimeSlots].sort();
    const blockedSlots = getBlockedSlots(selectedDate);
    
    allSlots.forEach(timeStr => {
        if (!blockedSlots.has(timeStr)) {
            availableSlots.push(formatTime(timeStr));
        }
    });
    
    if (availableSlots.length === 0) {
        alert(`No available slots for ${formatDate(selectedDate)}. All time slots are booked.`);
    } else {
        alert(`Available slots for ${formatDate(selectedDate)}:\n\n${availableSlots.join('\n')}`);
    }
}

async function completeAppointment(appointmentId) {
    try {
        await apiRequest(`/api/appointments/${appointmentId}`, 'PUT', { status: 'completed' });
        await loadData();
        showTodaySchedule();
        generateTimeSlots();
        alert('Appointment completed successfully!');
    } catch (error) {
        console.error('Failed to complete appointment:', error);
    }
}

async function cancelAppointment(appointmentId) {
    if (!confirm('Are you sure you want to cancel this appointment?')) {
        return;
    }
    
    try {
        await apiRequest(`/api/appointments/${appointmentId}`, 'DELETE');
        await loadData();
        showTodaySchedule();
        generateTimeSlots();
        alert('Appointment cancelled successfully!');
    } catch (error) {
        console.error('Failed to cancel appointment:', error);
    }
}

async function rescheduleAppointment(appointmentId) {
    const appointment = appointments.find(app => app.id == appointmentId);
    if (!appointment) return;
    
    const newDate = prompt('Enter new date (YYYY-MM-DD):', appointment.date);
    const newTime = prompt('Enter new time (HH:MM):', appointment.time);
    
    if (newDate && newTime) {
        if (checkTimeConflict(newDate, newTime, appointment.duration)) {
            alert('New time slot is not available. Please choose a different time.');
            return;
        }
        
        try {
            await apiRequest(`/api/appointments/${appointmentId}`, 'PUT', { 
                date: newDate, 
                time: newTime 
            });
            await loadData();
            showTodaySchedule();
            generateTimeSlots();
            alert('Appointment rescheduled successfully!');
        } catch (error) {
            console.error('Failed to reschedule appointment:', error);
        }
    }
}

// Export Functions
async function exportPatientData() {
    try {
        const response = await fetch('/api/export/patients');
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `patients_data_${new Date().toISOString().split('T')[0]}.csv`;
        a.click();
        window.URL.revokeObjectURL(url);
        alert('Patient data exported successfully!');
    } catch (error) {
        console.error('Failed to export patient data:', error);
        alert('Failed to export patient data');
    }
}

async function exportScheduleData() {
    try {
        const response = await fetch('/api/export/appointments');
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `schedule_data_${new Date().toISOString().split('T')[0]}.csv`;
        a.click();
        window.URL.revokeObjectURL(url);
        alert('Schedule data exported successfully!');
    } catch (error) {
        console.error('Failed to export schedule data:', error);
        alert('Failed to export schedule data');
    }
}

function exportAllData() {
    exportPatientData();
    exportScheduleData();
}

// Data persistence
async function loadData() {
    try {
        const [patientsData, appointmentsData] = await Promise.all([
            apiRequest('/api/patients'),
            apiRequest('/api/appointments')
        ]);
        
        patients = patientsData.patients || [];
        appointments = appointmentsData.appointments || [];
        
        console.log('Data loaded from server');
    } catch (error) {
        console.error('Failed to load data:', error);
        patients = [];
        appointments = [];
    }
}

// ===============================
// Authentication System Functions
// ===============================

let currentStep = 1;
let otpTimer = null;
let otpCountdown = 600; // 10 minutes in seconds

// Toggle between login and registration forms
function toggleAuthMode(mode) {
    const loginBtn = document.getElementById('loginToggle');
    const registerBtn = document.getElementById('registerToggle');
    const loginForm = document.getElementById('loginFormContainer');
    const registerForm = document.getElementById('registerFormContainer');

    if (mode === 'login') {
        loginBtn.classList.add('active');
        registerBtn.classList.remove('active');
        loginForm.classList.remove('hidden');
        registerForm.classList.add('hidden');
    } else {
        registerBtn.classList.add('active');
        loginBtn.classList.remove('active');
        registerForm.classList.remove('hidden');
        loginForm.classList.add('hidden');
        showRegistrationStep(1);
    }
}

// Show specific registration step
function showRegistrationStep(step) {
    // Hide all steps
    for (let i = 1; i <= 4; i++) {
        const stepElement = document.getElementById(`step${i}`);
        if (stepElement) {
            stepElement.classList.add('hidden');
        }
    }

    // Show current step
    const currentStepElement = document.getElementById(`step${step}`);
    if (currentStepElement) {
        currentStepElement.classList.remove('hidden');
    }

    currentStep = step;
}

// Handle registration form submission
async function handleRegistration() {
    const name = document.getElementById('regName').value.trim();
    const email = document.getElementById('regEmail').value.trim();
    const phone = document.getElementById('regPhone').value.trim();
    const designation = document.getElementById('regDesignation').value.trim();

    if (!name || !email || !phone || !designation) {
        alert('Please fill in all required fields.');
        return;
    }

    if (!validateEmail(email)) {
        alert('Please enter a valid email address.');
        return;
    }

    if (!validatePhone(phone)) {
        alert('Please enter a valid phone number.');
        return;
    }

    try {
        const response = await apiRequest('/api/register', 'POST', {
            name: name,
            email: email,
            phone: phone,
            designation: designation
        });

        if (response.success) {
            // Store user data temporarily
            sessionStorage.setItem('registrationData', JSON.stringify({
                name, email, phone, designation
            }));

            // Show OTP step
            document.getElementById('otpEmail').textContent = email;
            showRegistrationStep(2);
            startOtpTimer();
        } else {
            alert(response.message || 'Registration failed. Please try again.');
        }
    } catch (error) {
        console.error('Registration error:', error);
        alert('An error occurred during registration. Please try again.');
    }
}

// Start OTP countdown timer
function startOtpTimer() {
    otpCountdown = 600; // Reset to 10 minutes
    const timerElement = document.getElementById('otpTimer');
    const resendBtn = document.getElementById('resendOtp');

    resendBtn.disabled = true;
    resendBtn.style.opacity = '0.6';

    otpTimer = setInterval(() => {
        const minutes = Math.floor(otpCountdown / 60);
        const seconds = otpCountdown % 60;
        timerElement.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;

        if (otpCountdown <= 0) {
            clearInterval(otpTimer);
            timerElement.textContent = 'OTP expired';
            resendBtn.disabled = false;
            resendBtn.style.opacity = '1';
        }

        otpCountdown--;
    }, 1000);
}

// Verify OTP
async function verifyOtp() {
    const otp = document.getElementById('otpCode').value.trim();

    if (!otp || otp.length !== 6) {
        alert('Please enter a valid 6-digit OTP.');
        return;
    }

    try {
        const registrationData = JSON.parse(sessionStorage.getItem('registrationData'));
        
        const response = await apiRequest('/api/verify-otp', 'POST', {
            email: registrationData.email,
            otp: otp
        });

        if (response.success) {
            clearInterval(otpTimer);
            showRegistrationStep(3);
        } else {
            alert(response.message || 'Invalid OTP. Please try again.');
        }
    } catch (error) {
        console.error('OTP verification error:', error);
        alert('An error occurred during OTP verification. Please try again.');
    }
}

// Resend OTP
async function resendOtp() {
    try {
        const registrationData = JSON.parse(sessionStorage.getItem('registrationData'));
        
        const response = await apiRequest('/api/send-otp', 'POST', {
            email: registrationData.email
        });

        if (response.success) {
            alert('New OTP sent to your email.');
            startOtpTimer();
        } else {
            alert(response.message || 'Failed to send OTP. Please try again.');
        }
    } catch (error) {
        console.error('Resend OTP error:', error);
        alert('An error occurred while sending OTP. Please try again.');
    }
}

// Complete registration with password
async function completeRegistration() {
    const password = document.getElementById('regPassword').value;
    const confirmPassword = document.getElementById('regConfirmPassword').value;

    if (!password || !confirmPassword) {
        alert('Please fill in both password fields.');
        return;
    }

    if (password !== confirmPassword) {
        alert('Passwords do not match.');
        return;
    }

    if (password.length < 8) {
        alert('Password must be at least 8 characters long.');
        return;
    }

    try {
        const registrationData = JSON.parse(sessionStorage.getItem('registrationData'));
        
        const response = await apiRequest('/api/complete-registration', 'POST', {
            ...registrationData,
            password: password
        });

        if (response.success) {
            // Clear session data
            sessionStorage.removeItem('registrationData');
            
            // Show success step
            showRegistrationStep(4);
            
            // Auto-redirect to login after 3 seconds
            setTimeout(() => {
                toggleAuthMode('login');
            }, 3000);
        } else {
            alert(response.message || 'Registration completion failed. Please try again.');
        }
    } catch (error) {
        console.error('Registration completion error:', error);
        alert('An error occurred while completing registration. Please try again.');
    }
}

// Go back to login from success step
function goToLogin() {
    toggleAuthMode('login');
}

// Validation functions
function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function validatePhone(phone) {
    const phoneRegex = /^[0-9]{10}$/;
    return phoneRegex.test(phone.replace(/\D/g, ''));
}

// Enhanced login function to work with registered users
async function login() {
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value.trim();

    if (!username || !password) {
        alert('Please enter your email/phone/name and password.');
        return;
    }

    try {
        const response = await apiRequest('/api/login', 'POST', {
            username: username,
            password: password
        });

        if (response.success) {
            // Store user session
            sessionStorage.setItem('currentUser', JSON.stringify(response.user));
            
            // Show welcome message if provided
            if (response.message) {
                // Create a temporary success message
                const loginForm = document.getElementById('loginFormContainer');
                const successMsg = document.createElement('div');
                successMsg.className = 'login-success';
                successMsg.innerHTML = `<p style="color: #28a745; font-weight: 600; margin: 10px 0;">${response.message}</p>`;
                loginForm.appendChild(successMsg);
                
                // Remove the message after 2 seconds
                setTimeout(() => {
                    if (successMsg.parentNode) {
                        successMsg.parentNode.removeChild(successMsg);
                    }
                }, 2000);
            }
            
            // Hide login section and show main content after a brief delay
            setTimeout(() => {
                // Update welcome message with user's name
                const welcomeElement = document.getElementById('welcomeMessage');
                if (welcomeElement && response.user && response.user.name) {
                    welcomeElement.textContent = `Welcome back, ${response.user.name}`;
                }
                
                showSection('mainMenu');
                document.getElementById('loginSection').style.display = 'none';
                
                // Initialize application data after successful login
                loadData();
                updateAppointmentPatientOptions();
                generateTimeSlots();
                updateStats();
            }, 1500);
            
        } else {
            alert(response.message || 'Invalid credentials. Please check your email/phone/name and password.');
        }
    } catch (error) {
        console.error('Login error:', error);
        // Fallback to original login for backward compatibility
        if (username === 'admin' && password === 'password') {
            // Update welcome message for admin
            const welcomeElement = document.getElementById('welcomeMessage');
            if (welcomeElement) {
                welcomeElement.textContent = 'Welcome back, Administrator';
            }
            
            showSection('mainMenu');
            document.getElementById('loginSection').style.display = 'none';
            loadData();
            updateAppointmentPatientOptions();
            generateTimeSlots();
            updateStats();
        } else {
            alert('Login failed. Please check your connection and try again.');
        }
    }
}

// Forgot Password Functions
let resetOtpTimer;
let resetOtpExpiry;
let resetEmail = '';
let resetOtpValue = '';

function showForgotPassword() {
    showSection('forgotPasswordSection');
    showForgotStep(1);
    document.getElementById('resetEmail').value = '';
}

function showLoginForm() {
    showSection('loginSection');
    toggleAuthMode('login');
}

function showForgotStep(step) {
    // Hide all steps
    document.querySelectorAll('.forgot-step').forEach(step => {
        step.classList.add('hidden');
    });
    
    // Show target step
    document.getElementById(`forgotStep${step}`).classList.remove('hidden');
    
    // Clear any timers
    if (resetOtpTimer) {
        clearInterval(resetOtpTimer);
    }
}

async function sendResetOTP() {
    const email = document.getElementById('resetEmail').value.trim();
    
    if (!email) {
        alert('Please enter your email address');
        return;
    }
    
    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        alert('Please enter a valid email address');
        return;
    }
    
    try {
        const response = await fetch('/send_reset_otp', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email: email })
        });
        
        const data = await response.json();
        
        if (data.success) {
            resetEmail = email;
            showForgotStep(2);
            startResetOtpTimer(600); // 10 minutes
            document.getElementById('resetOtp').value = '';
            alert('Reset code sent to your email! Please check your inbox.');
        } else {
            alert(data.message || 'Failed to send reset code. Please check if the email is registered.');
        }
    } catch (error) {
        console.error('Error sending reset OTP:', error);
        alert('Failed to send reset code. Please check your connection and try again.');
    }
}

async function verifyResetOTP() {
    const otp = document.getElementById('resetOtp').value.trim();
    
    if (!otp || otp.length !== 6) {
        alert('Please enter the 6-digit verification code');
        return;
    }
    
    try {
        const response = await fetch('/verify_reset_otp', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                email: resetEmail,
                otp: otp 
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            resetOtpValue = otp;
            showForgotStep(3);
            clearInterval(resetOtpTimer);
            document.getElementById('newPassword').value = '';
            document.getElementById('confirmNewPassword').value = '';
        } else {
            alert(data.message || 'Invalid verification code. Please try again.');
        }
    } catch (error) {
        console.error('Error verifying reset OTP:', error);
        alert('Verification failed. Please check your connection and try again.');
    }
}

async function resendResetOTP() {
    await sendResetOTP();
    document.getElementById('resendResetBtn').disabled = true;
    setTimeout(() => {
        document.getElementById('resendResetBtn').disabled = false;
    }, 30000); // 30 seconds cooldown
}

async function resetPassword() {
    const newPassword = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmNewPassword').value;
    
    if (!newPassword || newPassword.length < 6) {
        alert('Password must be at least 6 characters long');
        return;
    }
    
    if (newPassword !== confirmPassword) {
        alert('Passwords do not match');
        return;
    }
    
    try {
        const response = await fetch('/reset_password', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                email: resetEmail,
                otp: resetOtpValue,
                new_password: newPassword 
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showForgotStep(4);
        } else {
            alert(data.message || 'Failed to reset password. Please try again.');
        }
    } catch (error) {
        console.error('Error resetting password:', error);
        alert('Password reset failed. Please check your connection and try again.');
    }
}

function startResetOtpTimer(seconds) {
    resetOtpExpiry = Date.now() + (seconds * 1000);
    
    resetOtpTimer = setInterval(() => {
        const remaining = Math.max(0, resetOtpExpiry - Date.now());
        const minutes = Math.floor(remaining / 60000);
        const secs = Math.floor((remaining % 60000) / 1000);
        
        const timerDisplay = document.getElementById('resetOtpTimer');
        if (timerDisplay) {
            timerDisplay.textContent = `Code expires in: ${minutes}:${secs.toString().padStart(2, '0')}`;
        }
        
        if (remaining <= 0) {
            clearInterval(resetOtpTimer);
            if (timerDisplay) {
                timerDisplay.textContent = 'Code expired - Click resend';
                timerDisplay.style.color = '#dc3545';
            }
        }
    }, 1000);
}

// Initialization is handled in window 'load' event above
