from flask import Flask, request, jsonify, render_template, session
from flask import send_from_directory
from flask_cors import CORS
from functools import wraps
from connector import get_db_connection
from datetime import datetime
import os
from werkzeug.utils import secure_filename
import uuid

app = Flask(__name__)
CORS(app)
app.secret_key = 'your_super_secret_key_change_this'

# ======================
# FILE UPLOAD CONFIG
# ======================
UPLOAD_FOLDER = 'static/uploads/resumes'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Create upload folder if not exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ======================
# HELPER FUNCTIONS
# ======================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return jsonify({"success": False, "message": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated_function

def is_logged_in():
    """Helper function to check if admin is logged in"""
    return 'admin_logged_in' in session

# ======================
# PAGE ROUTES (Serve HTML Files)
# ======================

@app.route('/')
def login_page():
    return render_template("login.html")

@app.route('/dashboard')
def dashboard_page():
    return render_template("dashboard.html")

@app.route('/careers')
def careers_page():
    return render_template("careers.html")

@app.route('/careers/add')
def career_add_page():
    return render_template("career_add.html")

@app.route('/careers/edit/<int:id>')
def career_edit_page(id):
    return render_template("career_edit.html")

@app.route('/contacts')
def contacts_page():
    return render_template("contacts.html")

@app.route('/contacts/view/<int:id>')
def contact_view_page(id):
    return render_template("contact_view.html")

@app.route('/applications')
def applications_page():
    return render_template("applications.html")

@app.route('/applications/view/<int:id>')
def application_view_page(id):
    return render_template("application_view.html")

# ======================
# AUTH APIs
# ======================

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM admins WHERE username = %s AND password = %s", (username, password))
        admin = cursor.fetchone()
        conn.close()
        
        if admin:
            session['admin_logged_in'] = True
            session['admin_id'] = admin['id']
            session['admin_username'] = admin['username']
            return jsonify({"success": True, "message": "Login successful!"}), 200
        else:
            return jsonify({"success": False, "message": "Invalid username or password"}), 401
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({"success": True, "message": "Logged out successfully!"}), 200

@app.route('/api/check-auth', methods=['GET'])
def check_auth():
    if 'admin_logged_in' in session:
        return jsonify({
            "success": True, 
            "logged_in": True,
            "username": session.get('admin_username')
        }), 200
    return jsonify({"success": False, "logged_in": False}), 200

# ======================
# DASHBOARD APIs
# ======================

@app.route('/api/dashboard/stats', methods=['GET'])
@login_required
def api_dashboard_stats():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Total careers
        cursor.execute("SELECT COUNT(*) as count FROM careers")
        total_careers = cursor.fetchone()['count']
        
        # Active careers
        cursor.execute("SELECT COUNT(*) as count FROM careers WHERE status = 'active'")
        active_careers = cursor.fetchone()['count']
        
        # Total contacts
        cursor.execute("SELECT COUNT(*) as count FROM contacts")
        total_contacts = cursor.fetchone()['count']
        
        # Total applications
        cursor.execute("SELECT COUNT(*) as count FROM applications")
        total_applications = cursor.fetchone()['count']
        
        # Pending applications
        cursor.execute("SELECT COUNT(*) as count FROM applications WHERE status = 'pending'")
        pending_applications = cursor.fetchone()['count']
        
        # Reviewed applications
        cursor.execute("SELECT COUNT(*) as count FROM applications WHERE status = 'reviewed'")
        reviewed_applications = cursor.fetchone()['count']
        
        # Shortlisted applications
        cursor.execute("SELECT COUNT(*) as count FROM applications WHERE status = 'shortlisted'")
        shortlisted_applications = cursor.fetchone()['count']
        
        # Hired applications
        cursor.execute("SELECT COUNT(*) as count FROM applications WHERE status = 'hired'")
        hired_applications = cursor.fetchone()['count']
        
        # Rejected applications
        cursor.execute("SELECT COUNT(*) as count FROM applications WHERE status = 'rejected'")
        rejected_applications = cursor.fetchone()['count']
        
        # =====================
        # UNREAD COUNTS FOR DASHBOARD DISPLAY
        # =====================
        cursor.execute("SELECT COUNT(*) as count FROM applications WHERE is_read = FALSE")
        unread_applications = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM contacts WHERE is_read = FALSE")
        unread_contacts = cursor.fetchone()['count']
        
        # =====================
        # RECENT DATA
        # =====================
        
        # Recent careers
        cursor.execute("SELECT * FROM careers ORDER BY created_at DESC LIMIT 5")
        recent_careers = cursor.fetchall()
        
        # Recent contacts
        cursor.execute("SELECT * FROM contacts ORDER BY created_at DESC LIMIT 5")
        recent_contacts = cursor.fetchall()
        
        # Recent applications with job title
        cursor.execute("""
            SELECT a.*, c.title as job_title 
            FROM applications a 
            LEFT JOIN careers c ON a.career_id = c.id 
            ORDER BY a.created_at DESC 
            LIMIT 5
        """)
        recent_applications = cursor.fetchall()
        
        conn.close()
        
        # Convert datetime to string for careers
        for career in recent_careers:
            if career.get('created_at'):
                career['created_at'] = career['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        # Convert datetime to string for contacts
        for contact in recent_contacts:
            if contact.get('created_at'):
                contact['created_at'] = contact['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        # Convert datetime to string for applications
        for application in recent_applications:
            if application.get('created_at'):
                application['created_at'] = application['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify({
            "success": True,
            "data": {
                # Career stats
                "total_careers": total_careers,
                "active_careers": active_careers,
                
                # Contact stats
                "total_contacts": total_contacts,
                
                # Application stats
                "total_applications": total_applications,
                "pending_applications": pending_applications,
                "reviewed_applications": reviewed_applications,
                "shortlisted_applications": shortlisted_applications,
                "hired_applications": hired_applications,
                "rejected_applications": rejected_applications,
                
                # Unread counts
                "unread_applications": unread_applications,
                "unread_contacts": unread_contacts,
                
                # Recent data
                "recent_careers": recent_careers,
                "recent_contacts": recent_contacts,
                "recent_applications": recent_applications
            }
        }), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# ======================
# CAREER APIs (Admin)
# ======================

@app.route('/api/admin/careers', methods=['GET'])
@login_required
def api_get_all_careers():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM careers ORDER BY created_at DESC")
        careers = cursor.fetchall()
        conn.close()
        
        for career in careers:
            if career.get('created_at'):
                career['created_at'] = career['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify({"success": True, "data": careers}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/admin/careers/<int:id>', methods=['GET'])
@login_required
def api_get_career(id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM careers WHERE id = %s", (id,))
        career = cursor.fetchone()
        conn.close()
        
        if not career:
            return jsonify({"success": False, "message": "Career not found"}), 404
        
        if career.get('created_at'):
            career['created_at'] = career['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify({"success": True, "data": career}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/admin/careers', methods=['POST'])
@login_required
def api_create_career():
    try:
        data = request.get_json()
        title = data.get('title')
        description = data.get('description')
        location = data.get('location')
        job_type = data.get('job_type')
        status = data.get('status', 'active')
        
        if not all([title, description, location, job_type]):
            return jsonify({"success": False, "message": "All fields are required"}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO careers (title, description, location, job_type, status)
            VALUES (%s, %s, %s, %s, %s)
        """, (title, description, location, job_type, status))
        conn.commit()
        new_id = cursor.lastrowid
        conn.close()
        
        return jsonify({
            "success": True, 
            "message": "Job posted successfully!",
            "id": new_id
        }), 201
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/admin/careers/<int:id>', methods=['PUT'])
@login_required
def api_update_career(id):
    try:
        data = request.get_json()
        title = data.get('title')
        description = data.get('description')
        location = data.get('location')
        job_type = data.get('job_type')
        status = data.get('status')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE careers 
            SET title = %s, description = %s, location = %s, job_type = %s, status = %s
            WHERE id = %s
        """, (title, description, location, job_type, status, id))
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "message": "Job updated successfully!"}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/admin/careers/<int:id>', methods=['DELETE'])
@login_required
def api_delete_career(id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM careers WHERE id = %s", (id,))
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "message": "Job deleted successfully!"}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/admin/careers/<int:id>/toggle-status', methods=['PUT'])
@login_required
def api_toggle_career_status(id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM careers WHERE id = %s", (id,))
        career = cursor.fetchone()
        
        if not career:
            conn.close()
            return jsonify({"success": False, "message": "Career not found"}), 404
        
        new_status = 'inactive' if career['status'] == 'active' else 'active'
        cursor.execute("UPDATE careers SET status = %s WHERE id = %s", (new_status, id))
        conn.commit()
        conn.close()
        
        return jsonify({
            "success": True, 
            "message": f"Status changed to {new_status}",
            "new_status": new_status
        }), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# ======================
# CONTACT APIs (Admin)
# ======================

@app.route('/api/admin/contacts', methods=['GET'])
@login_required
def api_get_all_contacts():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM contacts ORDER BY created_at DESC")
        contacts = cursor.fetchall()
        conn.close()
        
        for contact in contacts:
            if contact.get('created_at'):
                contact['created_at'] = contact['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            if contact.get('read_at'):
                contact['read_at'] = contact['read_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify({"success": True, "data": contacts}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/admin/contacts/<int:id>', methods=['GET'])
@login_required
def api_get_contact(id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM contacts WHERE id = %s", (id,))
        contact = cursor.fetchone()
        
        if not contact:
            conn.close()
            return jsonify({"success": False, "message": "Contact not found"}), 404
        
        # ✅ AUTO MARK AS READ when admin views it
        if not contact.get('is_read'):
            cursor.execute(
                "UPDATE contacts SET is_read = TRUE, read_at = NOW() WHERE id = %s",
                (id,)
            )
            conn.commit()
        
        conn.close()
        
        if contact.get('created_at'):
            contact['created_at'] = contact['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        if contact.get('read_at'):
            contact['read_at'] = contact['read_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify({"success": True, "data": contact}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/admin/contacts/<int:id>', methods=['DELETE'])
@login_required
def api_delete_contact(id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM contacts WHERE id = %s", (id,))
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "message": "Contact deleted successfully!"}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# ======================
# APPLICATION APIs (Admin)
# ======================

@app.route('/api/admin/applications', methods=['GET'])
@login_required
def api_get_all_applications():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.*, c.title as job_title, c.location as job_location
            FROM applications a 
            JOIN careers c ON a.career_id = c.id 
            ORDER BY a.created_at DESC
        """)
        applications = cursor.fetchall()
        conn.close()
        
        for app_item in applications:
            if app_item.get('created_at'):
                app_item['created_at'] = app_item['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            if app_item.get('read_at'):
                app_item['read_at'] = app_item['read_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify({"success": True, "data": applications}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/admin/applications/<int:id>', methods=['GET'])
@login_required
def api_get_application(id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.*, c.title as job_title, c.location as job_location, c.job_type
            FROM applications a 
            JOIN careers c ON a.career_id = c.id 
            WHERE a.id = %s
        """, (id,))
        application = cursor.fetchone()
        
        if not application:
            conn.close()
            return jsonify({"success": False, "message": "Application not found"}), 404
        
        # ✅ AUTO MARK AS READ when admin views it
        if not application.get('is_read'):
            cursor.execute(
                "UPDATE applications SET is_read = TRUE, read_at = NOW() WHERE id = %s",
                (id,)
            )
            conn.commit()
        
        conn.close()
        
        if application.get('created_at'):
            application['created_at'] = application['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        if application.get('read_at'):
            application['read_at'] = application['read_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify({"success": True, "data": application}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/admin/applications/<int:id>/status', methods=['PUT'])
@login_required
def api_update_application_status(id):
    try:
        data = request.get_json()
        status = data.get('status')
        
        if status not in ['pending', 'reviewed', 'shortlisted', 'rejected', 'hired']:
            return jsonify({"success": False, "message": "Invalid status"}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE applications SET status = %s WHERE id = %s", (status, id))
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "message": f"Status updated to {status}"}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/admin/applications/<int:id>', methods=['DELETE'])
@login_required
def api_delete_application(id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get resume filename to delete
        cursor.execute("SELECT resume FROM applications WHERE id = %s", (id,))
        application = cursor.fetchone()
        
        if application and application.get('resume'):
            resume_path = os.path.join(app.config['UPLOAD_FOLDER'], application['resume'])
            if os.path.exists(resume_path):
                os.remove(resume_path)
        
        cursor.execute("DELETE FROM applications WHERE id = %s", (id,))
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "message": "Application deleted successfully!"}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/admin/applications/<int:id>/resume', methods=['GET'])
@login_required
def api_download_resume(id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT resume, applicant_name FROM applications WHERE id = %s", (id,))
        application = cursor.fetchone()
        conn.close()
        
        if not application or not application.get('resume'):
            return jsonify({"success": False, "message": "Resume not found"}), 404
        
        file_ext = os.path.splitext(application['resume'])[1]
        download_name = f"{application['applicant_name']}_resume{file_ext}"
        
        return send_from_directory(
            app.config['UPLOAD_FOLDER'], 
            application['resume'],
            as_attachment=True,
            download_name=download_name
        )
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# ======================
# PUBLIC APIs (For Your Static Website)
# ======================

@app.route('/api/careers', methods=['GET'])
def api_public_careers():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM careers WHERE status = 'active' ORDER BY created_at DESC")
        careers = cursor.fetchall()
        conn.close()
        
        for career in careers:
            if career.get('created_at'):
                career['created_at'] = career['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify({"success": True, "data": careers}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/contact', methods=['POST'])
def api_submit_contact():
    try:
        data = request.get_json()
        name = data.get('name')
        email = data.get('email')
        message = data.get('message')
        
        if not all([name, email, message]):
            return jsonify({"success": False, "message": "All fields are required"}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        # ✅ is_read defaults to FALSE in database, so new contacts are unread
        cursor.execute("""
            INSERT INTO contacts (name, email, message)
            VALUES (%s, %s, %s)
        """, (name, email, message))
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "message": "Message sent successfully!"}), 201
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# ======================
# PUBLIC API - Apply for Job
# ======================

@app.route('/api/apply', methods=['POST'])
def api_apply_job():
    try:
        career_id = request.form.get('career_id')
        applicant_name = request.form.get('applicant_name')
        applicant_email = request.form.get('applicant_email')
        phone = request.form.get('phone', '')
        cover_letter = request.form.get('cover_letter', '')
        
        if not all([career_id, applicant_name, applicant_email]):
            return jsonify({"success": False, "message": "Name, email and job are required"}), 400
        
        if 'resume' not in request.files:
            return jsonify({"success": False, "message": "Resume file is required"}), 400
        
        resume_file = request.files['resume']
        
        if resume_file.filename == '':
            return jsonify({"success": False, "message": "No file selected"}), 400
        
        if not allowed_file(resume_file.filename):
            return jsonify({"success": False, "message": "Only PDF, DOC, DOCX files allowed"}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if job exists
        cursor.execute("SELECT * FROM careers WHERE id = %s AND status = 'active'", (career_id,))
        career = cursor.fetchone()
        
        if not career:
            conn.close()
            return jsonify({"success": False, "message": "Job not found"}), 404
        
        # Check if already applied
        cursor.execute(
            "SELECT * FROM applications WHERE career_id = %s AND applicant_email = %s",
            (career_id, applicant_email)
        )
        if cursor.fetchone():
            conn.close()
            return jsonify({"success": False, "message": "You already applied for this job"}), 400
        
        # Save resume file
        filename = secure_filename(resume_file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        resume_file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
        
        # ✅ Save to database - is_read defaults to FALSE so new applications are unread
        cursor.execute("""
            INSERT INTO applications (career_id, applicant_name, applicant_email, phone, resume, cover_letter, status)
            VALUES (%s, %s, %s, %s, %s, %s, 'pending')
        """, (career_id, applicant_name, applicant_email, phone, unique_filename, cover_letter))
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "message": "Application submitted successfully!"}), 201
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# ============================================
# 🔔 NOTIFICATION APIs
# ============================================

# ---- GET NOTIFICATION COUNTS ----
@app.route('/api/notifications/count', methods=['GET'])
@login_required
def get_notification_count():
    """Returns unread counts for applications and contacts"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Count unread applications
        cursor.execute("SELECT COUNT(*) as count FROM applications WHERE is_read = FALSE")
        unread_applications = cursor.fetchone()['count']
        
        # Count unread contacts
        cursor.execute("SELECT COUNT(*) as count FROM contacts WHERE is_read = FALSE")
        unread_contacts = cursor.fetchone()['count']
        
        total_unread = unread_applications + unread_contacts
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'total_unread': total_unread,
                'unread_applications': unread_applications,
                'unread_contacts': unread_contacts
            }
        }), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# ---- GET LATEST NOTIFICATIONS (for dropdown) ----
@app.route('/api/notifications/latest', methods=['GET'])
@login_required
def get_latest_notifications():
    """Returns latest unread notifications for the bell dropdown"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        notifications = []
        
        # Get latest unread applications (max 5)
        cursor.execute("""
            SELECT a.id, a.applicant_name, a.applicant_email, a.created_at, 
                   COALESCE(c.title, 'Unknown') as job_title
            FROM applications a
            LEFT JOIN careers c ON a.career_id = c.id
            WHERE a.is_read = FALSE
            ORDER BY a.created_at DESC
            LIMIT 5
        """)
        apps = cursor.fetchall()
        
        for app_item in apps:
            created_at_str = ''
            if app_item['created_at']:
                created_at_str = app_item['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            
            notifications.append({
                'id': app_item['id'],
                'type': 'application',
                'title': f"{app_item['applicant_name']} applied",
                'subtitle': f"Applied for: {app_item['job_title']}",
                'email': app_item['applicant_email'],
                'created_at': created_at_str,
                'icon': 'fa-file-alt',
                'color': '#3b82f6',
                'url': f"/applications/view/{app_item['id']}"
            })
        
        # Get latest unread contacts (max 5)
        cursor.execute("""
            SELECT id, name, email, message, created_at
            FROM contacts
            WHERE is_read = FALSE
            ORDER BY created_at DESC
            LIMIT 5
        """)
        contacts = cursor.fetchall()
        
        for contact in contacts:
            created_at_str = ''
            if contact['created_at']:
                created_at_str = contact['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            
            msg = contact['message'] or ''
            subtitle = msg[:60] + '...' if len(msg) > 60 else msg
            
            notifications.append({
                'id': contact['id'],
                'type': 'contact',
                'title': f"{contact['name']} sent a message",
                'subtitle': subtitle,
                'email': contact['email'],
                'created_at': created_at_str,
                'icon': 'fa-envelope',
                'color': '#f59e0b',
                'url': f"/contacts/view/{contact['id']}"
            })
        
        # Sort all by created_at descending
        notifications.sort(key=lambda x: x['created_at'], reverse=True)
        
        # Take only top 8
        notifications = notifications[:8]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': notifications
        }), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# ---- MARK SINGLE NOTIFICATION AS READ ----
@app.route('/api/notifications/mark-read', methods=['POST'])
@login_required
def mark_notification_read():
    """Mark a single notification as read"""
    try:
        data = request.get_json()
        notif_type = data.get('type')   # 'application' or 'contact'
        notif_id = data.get('id')
        
        if not notif_type or not notif_id:
            return jsonify({'success': False, 'message': 'Missing type or id'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if notif_type == 'application':
            cursor.execute(
                "UPDATE applications SET is_read = TRUE, read_at = NOW() WHERE id = %s",
                (notif_id,)
            )
        elif notif_type == 'contact':
            cursor.execute(
                "UPDATE contacts SET is_read = TRUE, read_at = NOW() WHERE id = %s",
                (notif_id,)
            )
        else:
            conn.close()
            return jsonify({'success': False, 'message': 'Invalid type'}), 400
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Marked as read'}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# ---- MARK ALL NOTIFICATIONS AS READ ----
@app.route('/api/notifications/mark-all-read', methods=['POST'])
@login_required
def mark_all_notifications_read():
    """Mark all notifications as read"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE applications SET is_read = TRUE, read_at = NOW() WHERE is_read = FALSE"
        )
        cursor.execute(
            "UPDATE contacts SET is_read = TRUE, read_at = NOW() WHERE is_read = FALSE"
        )
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'All notifications marked as read'}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# ======================
# MAIN
# ======================

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)