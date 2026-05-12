from flask import Flask, redirect, render_template, request, url_for, session
import mysql.connector
import time
import os
from datetime import datetime


app =Flask(__name__)
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

@app.route('/lgu', methods=['GET', 'POST'])
def lgu():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    account_id = session.get('user_id')

    # Fetch data for GET (and for re-render if needed)
    sql_reps = """
        SELECT r.*, a.first_name, a.last_name
        FROM reports r
        JOIN accounts a ON r.account_id = a.account_id
        ORDER BY r.created_at DESC
    """

    if request.method == 'POST':
        data = request.form
        report_id = data.get('report_id')
        description = data.get('update_description', '').strip()

        # Basic validation
        if not report_id or not description:
            return redirect(url_for('lgu'))

        # Optional image upload
        image_url = None
        update_photo = request.files.get('update_photo')
        if update_photo and update_photo.filename:
            os.makedirs('static/uploads', exist_ok=True)
            filename = f"update_{report_id}_{int(datetime.now().timestamp())}_{update_photo.filename}"
            filepath = f"static/uploads/{filename}"
            update_photo.save(filepath)
            image_url = filepath

        con = connect_db()
        cursor = con.cursor()
        query = """
            INSERT INTO report_update (account_id, report_id, image_url, description, submitted_at)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            account_id,
            report_id,
            image_url,
            description,
            datetime.now()
        ))
        con.commit()
        con.close()
        return redirect(url_for('lgu'))

    # GET
    con = connect_db()
    cursor = con.cursor(dictionary=True)
    cursor.execute(sql_reps)
    reps = cursor.fetchall()
    con.close()
    return render_template("lgu.html", reps=reps)


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    con = connect_db()
    cursor = con.cursor()

    account_id = session.get('user_id')
    user_name = session.get('user_name')

    sql_recent = """
        SELECT r.*, a.first_name, a.last_name 
        FROM reports r
        JOIN accounts a ON r.account_id = a.account_id
        ORDER BY r.created_at DESC
    """
    cursor.execute(sql_recent)
    all_concerns = cursor.fetchall()
    con.close()

    return render_template(
        'dashboard.html',
        recent=all_concerns,
        ngalan=user_name,
        user={'first_name': user_name, 'last_name': '', 'address': 'Picaleon'}
    )


@app.route('/login', methods=['GET', 'POST'])
def login():
    con = connect_db()
    cursor = con.cursor()

    if request.method == 'POST':
        data = request.form
        u = data.get('e', '').strip()
        p = data.get('pass', '').strip()
        
        if not u or not p:
            return render_template('login.html', error="Please enter email/phone and password")
        
        # Fetch registration record
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

            neym = """SELECT c.account_id, a.first_name
              FROM accounts a
              JOIN contacts c ON a.account_id = c.account_id
              WHERE c.email = %s OR c.phone_number = %s
           """
            cursor.execute(neym, (emorph, emorph))
            nem = cursor.fetchone()

            if nem:
                account_id = nem[0]
                pangalan = nem[1]

                rowl = """
                    SELECT u.user_id, r.role
                    FROM user_role u
                    JOIN role r ON u.role_id = r.role_id
                    WHERE u.user_id = %s
                """
                cursor.execute(rowl, (account_id,))
                rul = cursor.fetchone()

                role_value = ""
                if rul and len(rul) > 1 and rul[1] is not None:
                    role_value = str(rul[1]).strip().casefold()

                session['user_id'] = account_id
                session['user_name'] = pangalan

                if role_value == 'lgu official':
                    con.close()
                    return redirect(url_for("lgu"))

                # Resident and any unknown role: dashboard
                con.close()
                return redirect(url_for("dashboard"))
        
        con.close()
    return render_template('login.html', error="Invalid credentials")


@app.route('/file_concern', methods=['GET', 'POST'])
def file_concern():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    con = connect_db()
    cursor = con.cursor(dictionary=True)

    if request.method == 'POST':
        con.autocommit = False
        data = request.form
        fn = request.form.get("fn")
        
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
        # For fn==pc (posting feedback), do NOT insert a new report
        if fn == "pc":
            feedback = (data.get('comment') or '').strip()
            report_id = data.get('report_id')

            if report_id and feedback:
                comque = """
                    INSERT INTO feedbacks (account_id, report_id, feedback, uploaded_at)
                    VALUES (%s, %s, %s, %s)
                """
                cursor.execute(comque, (account_id, report_id, feedback, datetime.now()))

        else:
            cursor.execute(query, (account_id, category, title, location, img_url, description))

        con.commit()
        con.close()
        return redirect(url_for('file_concern'))
        
    fetch_query = """
        SELECT r.*, a.first_name, a.last_name 
        FROM reports r
        JOIN accounts a ON r.account_id = a.account_id
        ORDER BY r.created_at DESC
    """
    cursor.execute(fetch_query)
    all_concerns = cursor.fetchall()

    # Fetch all updates and group them by report_id for per-card rendering
    cursor.execute("""
        SELECT 
        CONCAT(a.first_name, ' ', a.last_name) AS fullname,
        rp.report_id,
        rp.image_url,
        rp.description,
        rp.submitted_at
        FROM report_update rp
        JOIN accounts a ON a.account_id = rp.account_id
        ORDER BY rp.submitted_at DESC;
    """)
    all_updates = cursor.fetchall()

    # Fetch feedbacks for all reports in one query and group them by report_id
    report_ids = [c.get('report_id') for c in all_concerns if c.get('report_id') is not None]
    feedbacks_by_report = {}
    feedback_counts_by_report = {}

    if report_ids:
        placeholders = ",".join(["%s"] * len(report_ids))
        feedback_query = f"""
            SELECT 
                f.feedback_id,
                f.report_id,
                f.account_id,
                f.feedback,
                f.uploaded_at,
                CONCAT(a.first_name, ' ', a.last_name) AS fullname
            FROM feedbacks f
            LEFT JOIN accounts a ON a.account_id = f.account_id
            WHERE f.report_id IN ({placeholders})
            ORDER BY f.feedback_id DESC
        """
        cursor.execute(feedback_query, tuple(report_ids))
        all_feedbacks = cursor.fetchall()
        for fb in all_feedbacks:
            rid = fb.get('report_id')
            feedbacks_by_report.setdefault(rid, []).append(fb)

    # Build counts for comment badges
    for rid, fbs in feedbacks_by_report.items():
        feedback_counts_by_report[rid] = len(fbs)

    con.close()

    updates_by_report = {}
    for upd in all_updates:
        rid = upd.get('report_id')
        if rid is None:
            continue
        updates_by_report.setdefault(rid, []).append(upd)

    return render_template(
        'file_concern.html',
        concerns=all_concerns,
        updates_by_report=updates_by_report,
        feedbacks_by_report=feedbacks_by_report,
        feedback_counts_by_report=feedback_counts_by_report
    )

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
              
        # Simple account insert (user preference)
        cursor.execute("""
            INSERT INTO accounts (account_id, first_name, last_name, middle_name, dob) 
            VALUES (%s, %s, %s, %s, %s)
        """, (reg_id, data.get('fname'), data.get('lname'), data.get('mname'), data.get('dob')))
        
        cursor.execute("SELECT account_id FROM accounts WHERE account_id = %s", (reg_id,))
        newid = cursor.fetchone()[0]
        
        # Add contacts for email if not exists
        if reg_user[0]:  # email exists in registration
                cursor.execute(
                    "INSERT INTO contacts (account_id, email) VALUES (%s, %s)", 
                    (newid, reg_user[0])
                )
        
        # Add contacts for phone if not exists
        if reg_user[1]:
                cursor.execute(
                    "INSERT INTO contacts (account_id, phone_number) VALUES (%s, %s)", 
                    (newid, reg_user[1])
                )
        
        # Copy password to passwords table (password table has only password column, pass_id PK auto)
        cursor.execute("""
            INSERT INTO password (password) 
            SELECT password FROM registration WHERE registration_id = %s
        """, (reg_id,))
        
        # Finally delete registration record
        cursor.execute("DELETE FROM registration WHERE registration_id = %s", (reg_id,))
        con.commit()
        con.close()
        return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
