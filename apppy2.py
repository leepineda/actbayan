from flask import Flask, redirect, render_template, request, url_for, session, jsonify, Response
import mysql.connector
import time
import os
import csv
import io
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'actbayan_secret_key_2026'

def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="actbayan"
    )

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
   
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    con = connect_db()
    cursor = con.cursor(dictionary=True) 
    
    fetch_query = """
        SELECT r.*, a.first_name, a.last_name,
        (SELECT COUNT(*) FROM report_upvotes WHERE report_id = r.report_id) as upvote_total,
        (SELECT COUNT(*) FROM report_comments WHERE report_id = r.report_id) as comment_total
        FROM reports r
        JOIN accounts a ON r.account_id = a.account_id
        ORDER BY r.created_at DESC
    """
    cursor.execute(fetch_query)
    all_concerns = cursor.fetchall()
    # KUNIN ANG MGA COMMENTS PARA SA MGA REPORTS
    cursor.execute("""
        SELECT c.*, a.first_name, a.profile_photo 
        FROM report_comments c
        JOIN accounts a ON c.account_id = a.account_id
        ORDER BY c.created_at ASC
    """)
    raw_comments = cursor.fetchall()
    
    # I-group ang comments base sa kung saang report sila kabilang
    all_comments = {}
    for cmt in raw_comments:
        rid = cmt['report_id']
        if rid not in all_comments:
            all_comments[rid] = []
        all_comments[rid].append(cmt)
    user_query = "SELECT first_name, last_name, address, profile_photo FROM accounts WHERE account_id = %s"
    cursor.execute(user_query, (session['user_id'],))
    user_data = cursor.fetchone()
    
    con.close()
    
    return render_template(
        'dashboard.html', 
        recent=all_concerns, 
        user=user_data, 
        ngalan=session.get('user_name')
    )

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        session.clear()
        
    con = connect_db()
    cursor = con.cursor(buffered=True)

    if request.method == 'POST':
        data = request.form
        u = data.get('e', '').strip()
        p = data.get('pass', '').strip()
        
        if not u or not p:
            return render_template('login.html', error="Please enter email/phone and password")
        
        query_reg = "SELECT registration_id, email_address, phone_number, password FROM registration WHERE email_address = %s OR phone_number = %s"
        cursor.execute(query_reg, (u, u))
        reg_record = cursor.fetchone()
        
        if reg_record and reg_record[3] == p: 
            reg_id = reg_record[0]
            if reg_id:
                return redirect(url_for('cd', reg_id=reg_id))
        
        credquery = """SELECT u.emorph, p.password FROM credentials AS c
                    JOIN usercreds AS u ON u.user_id = c.user_id
                    JOIN password AS p ON p.pass_id = c.pass_id
                    WHERE u.emorph = %s AND p.password = %s
                    """
        cursor.execute(credquery, (u, p))
        creds = cursor.fetchone()
        
        if creds:
            emorph = creds[0]
            # BINAGO: Dinagdag natin ang a.role sa kinukuha sa database
            neym = """SELECT c.account_id, a.first_name, a.role
              FROM accounts a
              JOIN contacts c ON a.account_id = c.account_id
              WHERE c.email = %s OR c.phone_number = %s
           """
            cursor.execute(neym, (emorph, emorph))
            nem = cursor.fetchone()

            if nem:
                account_id = nem[0]
                pangalan = nem[1]
                user_role = nem[2] # Ito ang role (resident o lgu)
                
                # I-save sa session
                session['user_id'] = account_id
                session['user_name'] = pangalan
                session['user_role'] = user_role 
                con.close()
                
                # LOGIC PARA SA REDIRECTION
                if user_role == 'lgu':
                    return redirect(url_for('lgu_dashboard'))
                else:
                    return redirect(url_for('dashboard'))
        
        con.close()
    return render_template('login.html', error="Invalid credentials")

# ===== NEW ROUTE PARA SA LGU DASHBOARD =====
@app.route('/lgu_dashboard')
def lgu_dashboard():
    # Siguraduhing LGU lang ang makakapasok dito
    if 'user_id' not in session or session.get('user_role') != 'lgu':
        return redirect(url_for('login'))
        
    con = connect_db()
    cursor = con.cursor(dictionary=True)
    
    # 1. Kunin ang profile ni LGU
    cursor.execute("SELECT first_name, last_name, profile_photo FROM accounts WHERE account_id = %s", (session['user_id'],))
    user_data = cursor.fetchone()
    
    # 2. Kunin ang Analytics / Statistics
    cursor.execute("SELECT COUNT(*) as total FROM reports")
    total = cursor.fetchone()['total']
    
    cursor.execute("SELECT COUNT(*) as total FROM reports WHERE status = 'Pending'")
    pending = cursor.fetchone()['total']
    
    cursor.execute("SELECT COUNT(*) as total FROM reports WHERE status = 'In Progress'")
    progress = cursor.fetchone()['total']
    
    cursor.execute("SELECT COUNT(*) as total FROM reports WHERE status = 'Resolved'")
    resolved = cursor.fetchone()['total']
    
    stats = {'total': total, 'pending': pending, 'progress': progress, 'resolved': resolved}
    
    # 3. Kunin ang listahan ng mga reports para sa Table
    cursor.execute("""
        SELECT r.*, a.first_name, a.last_name 
        FROM reports r
        JOIN accounts a ON r.account_id = a.account_id
        ORDER BY r.created_at DESC
    """)
    reports = cursor.fetchall()
    
    con.close()
    
    # Ipasa ang data sa HTML
    return render_template('lgu_dashboard.html', user=user_data, stats=stats, reports=reports)

@app.route('/file_concern', methods=['GET', 'POST'])
def file_concern():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    con = connect_db()
    cursor = con.cursor(dictionary=True)
    
    # [KEEP YOUR EXISTING POST REQUEST LOGIC HERE]
    if request.method == 'POST':
        data = request.form
        category = data.get('category')
        title = data.get('title') 
        location = data.get('location')
        description = data.get('description')
        
        cursor.execute("SELECT account_id FROM accounts WHERE account_id = %s", (session['user_id'],))
        user_record = cursor.fetchone()

        if not user_record:
            return redirect(url_for('login'))
            
        account_id = user_record['account_id']
        
        image_file = request.files.get('concern_photo')
        img_url = None
        if image_file and image_file.filename:
            os.makedirs('static/uploads/concerns', exist_ok=True)
            filename = f"concern_{account_id}_{int(datetime.now().timestamp())}_{image_file.filename}"
            filepath = f"static/uploads/concerns/{filename}"
            image_file.save(filepath)
            img_url = filepath
            
        query = """
            INSERT INTO reports (account_id, category, title, location, image_url, description, status)
            VALUES (%s, %s, %s, %s, %s, %s, 'Pending')
        """
        cursor.execute(query, (account_id, category, title, location, img_url, description))
        con.commit()
        return redirect(url_for('file_concern'))
    
    # -> NEW: FETCH LOGGED-IN USER DATA FOR SIDEBAR
    cursor.execute("SELECT first_name, last_name, address, profile_photo FROM accounts WHERE account_id = %s", (session['user_id'],))
    user_data = cursor.fetchone()

    # [KEEP YOUR EXISTING FETCH_QUERY FOR CONCERNS & COMMENTS]
    fetch_query = """
        SELECT r.*, a.first_name, a.last_name,
        (SELECT COUNT(*) FROM report_upvotes WHERE report_id = r.report_id) as upvote_total,
        (SELECT COUNT(*) FROM report_comments WHERE report_id = r.report_id) as comment_total
        FROM reports r
        JOIN accounts a ON r.account_id = a.account_id
        ORDER BY r.created_at DESC
    """
    cursor.execute(fetch_query)
    all_concerns = cursor.fetchall()

    cursor.execute("""
        SELECT c.*, a.first_name, a.profile_photo 
        FROM report_comments c
        JOIN accounts a ON c.account_id = a.account_id
        ORDER BY c.created_at ASC
    """)
    raw_comments = cursor.fetchall()
    
    all_comments = {}
    for cmt in raw_comments:
        rid = cmt['report_id']
        if rid not in all_comments:
            all_comments[rid] = []
        all_comments[rid].append(cmt)

    # Fetch the latest LGU update for each report
    cursor.execute("""
        SELECT u.report_id, u.update_text, u.image_url, u.created_at
        FROM report_updates u
        INNER JOIN (
            SELECT report_id, MAX(created_at) as max_date
            FROM report_updates
            GROUP BY report_id
        ) latest ON u.report_id = latest.report_id AND u.created_at = latest.max_date
    """)
    raw_lgu_updates = cursor.fetchall()
    lgu_latest = {}
    for upd in raw_lgu_updates:
        rid = upd['report_id']
        text = upd['update_text']
        img  = upd['image_url']
        if isinstance(text, (bytes, bytearray)):
            text = text.decode('utf-8')
        if isinstance(img, (bytes, bytearray)):
            img = img.decode('utf-8')
        # Clean bytearray string artifacts
        if img:
            img = str(img).replace("bytearray(b'","").replace("b'","").replace("')","").replace("'","").replace("static/","")
        lgu_latest[rid] = {
            'text': text,
            'image': img or '',
            'date': upd['created_at'].strftime('%b %d, %Y') if upd['created_at'] else ''
        }
        
    con.close()
    
    # -> NEW: PASS user=user_data TO THE TEMPLATE
    return render_template('file_concern.html', concerns=all_concerns, all_comments=all_comments, user=user_data, lgu_latest=lgu_latest)
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        con = connect_db()
        cursor = con.cursor()
        data = request.form

        email = data.get('e', '').strip()
        phone = data.get('pn', '').strip()
        password = data.get('pass')
        conpass = data.get('conpass')

        if password != conpass:
            return render_template('register.html', error="Passwords do not match")

        if email:
            query = """
                INSERT INTO registration (email_address, password)
                VALUES (%s, %s)
            """
            values = (email, password)

        elif phone:
            query = """
                INSERT INTO registration (phone_number, password)
                VALUES (%s, %s)
            """
            values = (phone, password)

        else:
            return render_template('register.html', error="Enter email or phone number")

        cursor.execute(query, values)
        con.commit()

        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/complete_details', methods=['GET', 'POST'])
def cd():
    con = connect_db()
    cursor = con.cursor()
    reg_id = request.args.get('reg_id') or request.form.get('reg_id')
    
    if not reg_id:
        return redirect(url_for('login'))
    
    # Fetch reg_user data for display
    cred = "SELECT email_address, phone_number FROM registration WHERE registration_id = %s"
    cursor.execute(cred, (reg_id,))
    reg_user = cursor.fetchone()
    
    if request.method == 'GET':
        if reg_user:
            u = reg_user[0] or reg_user[1]
            return render_template('complete_details.html', u=u, reg_id=reg_id, email=reg_user[0] or '', phone=reg_user[1] or '')
        return redirect(url_for('login'))
    
    else:  # POST
        data = request.form
        # Handle profile photo
        profile_photo = request.files.get('profile_photo')
        pp_path = None
        if profile_photo and profile_photo.filename:
            os.makedirs('static/uploads', exist_ok=True)
            pp_path = f"static/uploads/{profile_photo.filename}"
            profile_photo.save(pp_path)
              
        # FIX: Added profile_photo to the insert query so the image actually saves to the DB!
        cursor.execute("""
            INSERT INTO accounts (account_id, first_name, last_name, middle_name, dob, profile_photo) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (reg_id, data.get('fname'), data.get('lname'), data.get('mname'), data.get('dob'), pp_path))
        
        cursor.execute("SELECT account_id FROM accounts WHERE account_id = %s", (reg_id,))
        newid = cursor.fetchone()[0]
        
        # Add contacts for email if not exists
        if reg_user[0]:  
            cursor.execute("INSERT INTO contacts (account_id, email) VALUES (%s, %s)", (newid, reg_user[0]))
        
        # Add contacts for phone if not exists
        if reg_user[1]:
            cursor.execute("INSERT INTO contacts (account_id, phone_number) VALUES (%s, %s)", (newid, reg_user[1]))
        
        # FIX THE GHOST ACCOUNT BUG: Properly map the user credentials
        # 1. Copy password to password table and grab the pass_id
        cursor.execute("""
            INSERT INTO password (password) 
            SELECT password FROM registration WHERE registration_id = %s
        """, (reg_id,))
        cursor.execute("SELECT LAST_INSERT_ID()")
        pass_id = cursor.fetchone()[0]
        
        # 2. Insert into usercreds and get the new u_id
        emorph = reg_user[0] or reg_user[1]
        cursor.execute("INSERT INTO usercreds (emorph) VALUES (%s)", (emorph,))
        cursor.execute("SELECT LAST_INSERT_ID()")
        u_id = cursor.fetchone()[0]
        
        # 3. Link them in credentials so the user can log in later
        cursor.execute("INSERT INTO credentials (user_id, pass_id) VALUES (%s, %s)", (u_id, pass_id))
        
        # FIX: LOG THE NEW USER IN by setting the session before redirecting
        session['user_id'] = newid
        session['user_name'] = data.get('fname')
        
        # Finally delete registration record
        cursor.execute("DELETE FROM registration WHERE registration_id = %s", (reg_id,))
        con.commit()
        con.close()
        return redirect(url_for('dashboard'))
@app.route('/upvote/<int:report_id>', methods=['POST'])
def upvote(report_id):
    if 'user_id' not in session:
        return {"error": "Unauthorized"}, 401
    
    con = connect_db()
    cursor = con.cursor(dictionary=True)
    user_id = session['user_id']
    
    # Check kung naka-upvote na
    cursor.execute("SELECT upvote_id FROM report_upvotes WHERE report_id = %s AND account_id = %s", (report_id, user_id))
    existing = cursor.fetchone()
    
    if existing:
        cursor.execute("DELETE FROM report_upvotes WHERE report_id = %s AND account_id = %s", (report_id, user_id))
        status = "removed"
    else:
        cursor.execute("INSERT INTO report_upvotes (report_id, account_id) VALUES (%s, %s)", (report_id, user_id))
        status = "added"
        
    con.commit()
    
    # Return updated count
    cursor.execute("SELECT COUNT(*) as total FROM report_upvotes WHERE report_id = %s", (report_id,))
    new_count = cursor.fetchone()['total']
    con.close()
    
    return {"status": status, "new_count": new_count}

@app.route('/comment/<int:report_id>', methods=['POST'])
def add_comment(report_id):
    if 'user_id' not in session:
        return {"error": "Unauthorized"}, 401
    
    data = request.json
    text = data.get('text')
    if not text:
        return {"error": "Empty comment"}, 400
        
    con = connect_db()
    cursor = con.cursor()
    cursor.execute("INSERT INTO report_comments (report_id, account_id, comment_text) VALUES (%s, %s, %s)", 
                   (report_id, session['user_id'], text))
    con.commit()
    con.close()
    
    return {"status": "success"}
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/announcements')
def announcements():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    con = connect_db()
    cursor = con.cursor(dictionary=True)
    cursor.execute("SELECT first_name, last_name, address, profile_photo FROM accounts WHERE account_id = %s", (session['user_id'],))
    user_data = cursor.fetchone()
    con.close()
    
    return render_template('announcements.html', user=user_data)

@app.route('/barangay_map')
def barangay_map():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    con = connect_db()
    cursor = con.cursor(dictionary=True)
    cursor.execute("SELECT first_name, last_name, address, profile_photo FROM accounts WHERE account_id = %s", (session['user_id'],))
    user_data = cursor.fetchone()
    con.close()
    
    return render_template('barangay_map.html', user=user_data)

@app.route('/bayan_guide')
def bayan_guide():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    con = connect_db()
    cursor = con.cursor(dictionary=True)
    cursor.execute("SELECT first_name, last_name, address, profile_photo FROM accounts WHERE account_id = %s", (session['user_id'],))
    user_data = cursor.fetchone()
    con.close()
    
    return render_template('bayan_guide.html', user=user_data)

@app.route('/account', methods=['GET', 'POST'])
def account():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    con = connect_db()
    cursor = con.cursor(dictionary=True)
    
    # Fetch User Account & Contact Info
    account_query = """
        SELECT a.*, c.email, c.phone_number 
        FROM accounts a
        LEFT JOIN contacts c ON a.account_id = c.account_id
        WHERE a.account_id = %s
    """
    cursor.execute(account_query, (session['user_id'],))
    user_data = cursor.fetchone()
    
    # Fetch user's personal concern history for the Activity Tab
    concern_query = "SELECT * FROM reports WHERE account_id = %s ORDER BY created_at DESC"
    cursor.execute(concern_query, (session['user_id'],))
    user_concerns = cursor.fetchall()
    
    con.close()
    return render_template('account.html', user=user_data, concerns=user_concerns)

# ===== NEW API ROUTES FOR UPVOTES AND COMMENTS =====

@app.route('/api/toggle_upvote/<int:report_id>', methods=['POST'])
def toggle_upvote(report_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    account_id = session['user_id']
    con = connect_db()
    cursor = con.cursor(dictionary=True)
    
    # Check if upvote exists
    cursor.execute("SELECT * FROM report_upvotes WHERE report_id = %s AND account_id = %s", (report_id, account_id))
    existing = cursor.fetchone()
    
    if existing:
        cursor.execute("DELETE FROM report_upvotes WHERE report_id = %s AND account_id = %s", (report_id, account_id))
        status = 'removed'
    else:
        cursor.execute("INSERT INTO report_upvotes (report_id, account_id) VALUES (%s, %s)", (report_id, account_id))
        status = 'added'
        
    con.commit()
    
    # Get new count
    cursor.execute("SELECT COUNT(*) AS total FROM report_upvotes WHERE report_id = %s", (report_id,))
    total = cursor.fetchone()['total']
    con.close()
    
    return jsonify({'status': status, 'upvotes': total})

@app.route('/api/comments/<int:report_id>', methods=['GET', 'POST'])
def handle_comments(report_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    con = connect_db()
    cursor = con.cursor(dictionary=True)
    
    if request.method == 'POST':
        data = request.json
        text = data.get('text', '').strip()
        parent_id = data.get('parent_id') # None if it's a main comment
        
        if not text:
            return jsonify({'error': 'Empty comment'}), 400
            
        cursor.execute("""
            INSERT INTO report_comments (report_id, account_id, parent_id, comment_text) 
            VALUES (%s, %s, %s, %s)
        """, (report_id, session['user_id'], parent_id, text))
        con.commit()
        
    # Fetch all comments for this report
    cursor.execute("""
        SELECT c.*, a.first_name, a.last_name 
        FROM report_comments c
        JOIN accounts a ON c.account_id = a.account_id
        WHERE c.report_id = %s
        ORDER BY c.created_at ASC
    """, (report_id,))
    comments = cursor.fetchall()
    con.close()
    
    # Format datetime for JSON response
    for c in comments:
        c['created_at'] = c['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        
    return jsonify(comments)

# ==========================================
#           LGU OFFICIAL ROUTES
# ==========================================

@app.route('/lgu_reports', methods=['GET', 'POST'])
def lgu_reports():
    if 'user_id' not in session or session.get('user_role') != 'lgu':
        return redirect(url_for('login'))
        
    con = connect_db()
    cursor = con.cursor(dictionary=True)
    
    cursor.execute("SELECT first_name, last_name, profile_photo FROM accounts WHERE account_id = %s", (session['user_id'],))
    user_data = cursor.fetchone()
    
    # Fetch all reports for the table
    cursor.execute("""
        SELECT r.*, a.first_name, a.last_name,
        (SELECT COUNT(*) FROM report_upvotes WHERE report_id = r.report_id) as upvote_total,
        (SELECT COUNT(*) FROM report_comments WHERE report_id = r.report_id) as comment_total
        FROM reports r
        JOIN accounts a ON r.account_id = a.account_id
        ORDER BY r.created_at DESC
    """)
    reports = cursor.fetchall()
    con.close()
    
    return render_template('lgu_reports.html', user=user_data, reports=reports)

@app.route('/lgu_announcements')
def lgu_announcements():
    if 'user_id' not in session or session.get('user_role') != 'lgu':
        return redirect(url_for('login'))
    
    con = connect_db()
    cursor = con.cursor(dictionary=True)
    cursor.execute("SELECT first_name, last_name, profile_photo FROM accounts WHERE account_id = %s", (session['user_id'],))
    user_data = cursor.fetchone()
    con.close()
    
    return render_template('lgu_announcements.html', user=user_data)

@app.route('/lgu_map')
def lgu_map():
    if 'user_id' not in session or session.get('user_role') != 'lgu':
        return redirect(url_for('login'))
        
    con = connect_db()
    cursor = con.cursor(dictionary=True)
    cursor.execute("SELECT first_name, last_name, profile_photo FROM accounts WHERE account_id = %s", (session['user_id'],))
    user_data = cursor.fetchone()
    con.close()
    
    return render_template('lgu_map.html', user=user_data)

@app.route('/lgu_account')
def lgu_account():
    if 'user_id' not in session or session.get('user_role') != 'lgu':
        return redirect(url_for('login'))
        
    con = connect_db()
    cursor = con.cursor(dictionary=True)
    
    account_query = """
        SELECT a.*, c.email, c.phone_number 
        FROM accounts a
        LEFT JOIN contacts c ON a.account_id = c.account_id
        WHERE a.account_id = %s
    """
    cursor.execute(account_query, (session['user_id'],))
    user_data = cursor.fetchone()
    con.close()
    
    return render_template('lgu_account.html', user=user_data)
@app.route('/update_report_status/<int:report_id>', methods=['POST'])
def update_report_status(report_id):
    if 'user_id' not in session or session.get('user_role') != 'lgu':
        return jsonify({'success': False, 'message': 'Unauthorized. LGU access required.'}), 401
        
    # Using request.form and request.files instead of request.json for file uploads
    new_status = request.form.get('status')
    update_text = request.form.get('update_text', 'Status updated.')
    image_file = request.files.get('update_photo')
    
    if new_status not in ['Pending', 'In Progress', 'Resolved', 'Denied']:
        return jsonify({'success': False, 'message': 'Invalid status'}), 400
        
    con = connect_db()
    cursor = con.cursor()
    
    # Process Image Upload
    img_url = None
    if image_file and image_file.filename:
        os.makedirs('static/uploads/updates', exist_ok=True)
        # Unique filename
        filename = f"update_{report_id}_{int(datetime.now().timestamp())}_{image_file.filename}"
        filepath = f"static/uploads/updates/{filename}"
        image_file.save(filepath)
        img_url = filepath

    # Update main report status
    cursor.execute("UPDATE reports SET status = %s WHERE report_id = %s", (new_status, report_id))
        
    # Log the detailed update with the photo
    cursor.execute("""
        INSERT INTO report_updates (report_id, account_id, update_text, image_url) 
        VALUES (%s, %s, %s, %s)
    """, (report_id, session['user_id'], update_text, img_url))
    
    con.commit()
    con.close()
    
    return jsonify({'success': True, 'message': f'Progress recorded and status updated to {new_status}'})


@app.route('/api/report_updates/<int:report_id>')
def get_report_updates(report_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    con = connect_db()
    cursor = con.cursor(dictionary=True, buffered=True)
    cursor.execute("""
        SELECT u.*, a.first_name, a.last_name, a.profile_photo 
        FROM report_updates u
        JOIN accounts a ON u.account_id = a.account_id
        WHERE u.report_id = %s
        ORDER BY u.created_at DESC
    """, (report_id,))
    updates = cursor.fetchall()
    con.close()
    
    # FORMATTER & UNIVERSAL BYTEARRAY + BYTES CLEANER
    for u in updates:
        # Pormatin ang date
        u['created_at_formatted'] = u['created_at'].strftime('%B %d, %Y %I:%M %p') if u['created_at'] else 'Recently'
        
        # Awtomatikong linisin LAHAT ng bytearray/bytes data bago maging JSON
        for key in list(u.keys()):
            value = u[key]
            if isinstance(value, (bytearray, bytes)):
                u[key] = value.decode('utf-8')
                
    return jsonify(updates)

@app.route('/export_reports_excel')
def export_reports_excel():
    if 'user_id' not in session or session.get('user_role') != 'lgu':
        return redirect(url_for('login'))
        
    con = connect_db()
    cursor = con.cursor(dictionary=True)
    cursor.execute("""
        SELECT r.report_id, a.first_name, a.last_name, r.category, r.title, r.location, r.description, r.status, r.denial_reason, r.created_at
        FROM reports r
        JOIN accounts a ON r.account_id = a.account_id
        ORDER BY r.created_at DESC
    """)
    reports = cursor.fetchall()
    con.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Report ID', 'Resident Name', 'Category', 'Title', 'Location', 'Description', 'Status', 'Denial Reason', 'Date Submitted'])
    
    for r in reports:
        name = f"{r['first_name']} {r['last_name']}".strip()
        date_str = r['created_at'].strftime('%Y-%m-%d %H:%M:%S') if r['created_at'] else ''
        writer.writerow([r['report_id'], name, r['category'], r['title'], r['location'], r['description'], r['status'], r['denial_reason'] or '', date_str])
        
    response = Response(output.getvalue(), mimetype='text/csv')
    response.headers['Content-Disposition'] = 'attachment; filename=actbayan_reports.csv'
    return response
if __name__ == '__main__':
    app.run(debug=True)