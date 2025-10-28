from flask import Flask, render_template, request, jsonify, g, flash, redirect, url_for
import sqlite3
from datetime import date, datetime, timedelta # --- NEW: Import datetime and timedelta ---
import os
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_super_secret_key_12345'
DB_NAME = 'goodlife_schema.db'

# -------------------- Database Management -------------------- #

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_NAME)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        c = db.cursor()
        
        # --- MODIFIED: Added visit_time ---
        c.execute('''
            CREATE TABLE IF NOT EXISTS visitors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT, aadhar TEXT UNIQUE, age INTEGER, address TEXT,
                purpose TEXT, remarks TEXT, 
                visit_date DATE, 
                visit_time TIME
            )''')
        
        # --- MODIFIED: Added donation_time ---
        c.execute('''
            CREATE TABLE IF NOT EXISTS donations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                donor_name TEXT, amount REAL, items_donated TEXT,
                payment_mode TEXT, payment_detail TEXT, 
                donation_date DATE, 
                donation_time TIME
            )''')
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT, amount REAL, category TEXT,
                details TEXT, expense_date DATE,
                person_id INTEGER, 
                FOREIGN KEY(person_id) REFERENCES people(id)
            )''')
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS people (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                dob DATE,
                category TEXT NOT NULL,
                join_date DATE,
                notes TEXT
            )''')

        c.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                start DATE NOT NULL,
                end DATE,
                details TEXT,
                color TEXT
            )''')

        c.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                person_id INTEGER NOT NULL,
                attendance_date DATE NOT NULL,
                status TEXT NOT NULL,
                UNIQUE(person_id, attendance_date),
                FOREIGN KEY(person_id) REFERENCES people(id)
            )''')
        
        db.commit()

# --- Internal helper function for finance totals (Unchanged) ---
def _get_finance_totals():
    db = get_db()
    c = db.cursor()
    c.execute("SELECT SUM(amount) as total FROM donations")
    donations_result = c.fetchone()
    total_donations = donations_result['total'] if donations_result['total'] else 0
    c.execute("SELECT SUM(amount) as total FROM expenses")
    expenses_result = c.fetchone()
    total_expenses = expenses_result['total'] if expenses_result['total'] else 0
    net_balance = total_donations - total_expenses
    return total_donations, total_expenses, net_balance

# -------------------- Main Routes (Finance, Visitor, Donation) -------------------- #

@app.route('/')
def index():
    return redirect(url_for('finance'))

# --- MODIFIED: /visitor route for Monitor ---
@app.route('/visitor', methods=['GET', 'POST'])
def visitor():
    db = get_db()
    if request.method == 'POST':
        # --- NEW: Capture date and time automatically ---
        visit_date_auto = date.today()
        visit_time_auto = datetime.now().strftime("%H:%M:%S")

        aadhar = request.form.get('aadhar')
        name = request.form.get('name')
        
        existing = db.execute("SELECT * FROM visitors WHERE aadhar=?", (aadhar,)).fetchone()

        if existing:
            # Update purpose, remarks, and recent visit time for existing
            db.execute('''
                UPDATE visitors SET purpose=?, remarks=?, visit_date=?, visit_time=? 
                WHERE aadhar=?
            ''', (request.form.get('purpose'), request.form.get('remarks'), 
                  visit_date_auto, visit_time_auto, aadhar))
        else:
            # Insert new visitor
            db.execute('''
                INSERT INTO visitors (name, aadhar, age, address, purpose, remarks, visit_date, visit_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (name, aadhar, request.form.get('age'), request.form.get('address'), 
                  request.form.get('purpose'), request.form.get('remarks'), 
                  visit_date_auto, visit_time_auto))
        
        db.commit()
        flash("Visitor entry submitted successfully!", "success")
        return redirect(url_for('visitor'))

    # --- NEW: Handle GET request for filtering ---
    filter_option = request.args.get('filter', 'today')
    query = "SELECT * FROM visitors"
    today = date.today()
    
    if filter_option == 'today':
        query += f" WHERE visit_date = '{today}'"
    elif filter_option == 'yesterday':
        yesterday = today - timedelta(days=1)
        query += f" WHERE visit_date = '{yesterday}'"
    elif filter_option == 'year':
        query += f" WHERE strftime('%Y', visit_date) = strftime('%Y', '{today}')"
        
    query += " ORDER BY visit_date DESC, visit_time DESC"
    visitors = db.execute(query).fetchall()

    return render_template('visitor_form.html', visitors=visitors, current_filter=filter_option)

# --- MODIFIED: /donation route for Monitor ---
@app.route('/donation', methods=['GET', 'POST'])
def donation():
    db = get_db()
    if request.method == 'POST':
        # --- NEW: Capture date and time automatically ---
        donation_date_auto = date.today()
        donation_time_auto = datetime.now().strftime("%H:%M:%S")

        db.execute('''
            INSERT INTO donations (donor_name, amount, items_donated, payment_mode, payment_detail, donation_date, donation_time)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (request.form.get('donor_name'), request.form.get('amount'), 
              request.form.get('items_donated'), request.form.get('payment_mode'), 
              request.form.get('payment_detail', ''), 
              donation_date_auto, donation_time_auto))
        db.commit()

        flash("Donation entry submitted successfully!", "success")
        return redirect(url_for('donation'))
    
    # --- NEW: Handle GET request for filtering ---
    filter_option = request.args.get('filter', 'today')
    query = "SELECT * FROM donations"
    today = date.today()
    
    if filter_option == 'today':
        query += f" WHERE donation_date = '{today}'"
    elif filter_option == 'yesterday':
        yesterday = today - timedelta(days=1)
        query += f" WHERE donation_date = '{yesterday}'"
    elif filter_option == 'year':
        query += f" WHERE strftime('%Y', donation_date) = strftime('%Y', '{today}')"
        
    query += " ORDER BY donation_date DESC, donation_time DESC"
    donations = db.execute(query).fetchall()

    return render_template('donation_form.html', donations=donations, current_filter=filter_option)

# --- MODIFIED: /expense route to pass people list (for form linking) ---
@app.route('/expense', methods=['GET', 'POST'])
def expense():
    _, _, net_balance = _get_finance_totals()
    db = get_db()
    people = db.execute("SELECT id, name, category FROM people ORDER BY name").fetchall()

    if request.method == 'POST':
        amount = request.form.get('amount')
        
        if not amount or float(amount) <= 0:
            flash(f"Error: Expense amount must be greater than zero.", "danger")
            return render_template('expense_form.html', net_balance=net_balance, people=people)
        if float(amount) > net_balance:
            flash(f"Error: Expense (₹{amount}) exceeds available balance (₹{net_balance}).", "danger")
            return render_template('expense_form.html', net_balance=net_balance, people=people)
        
        person_id = request.form.get('person_id')
        person_id = int(person_id) if person_id else None

        db.execute('''
            INSERT INTO expenses (item_name, amount, category, details, expense_date, person_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (request.form.get('item_name'), amount, request.form.get('category'), 
              request.form.get('details', ''), date.today(), person_id))
        db.commit()

        flash("Expense entry submitted successfully!", "success")
        return redirect(url_for('expense'))
    
    return render_template('expense_form.html', net_balance=net_balance, people=people)

# --- (Finance Routes are Unchanged) ---
@app.route('/finance')
def finance():
    return render_template('finance_dashboard.html')

@app.route('/get_financial_data')
def get_financial_data():
    total_donations, total_expenses, net_balance = _get_finance_totals()
    db = get_db()
    category_rows = db.execute("SELECT category, SUM(amount) as total FROM expenses GROUP BY category").fetchall()
    expense_categories = {row['category']: row['total'] for row in category_rows}
    return jsonify({
        'total_donations': total_donations,
        'total_expenses': total_expenses,
        'net_balance': net_balance,
        'expense_categories': expense_categories
    })

# -------------------- People Management Routes (Unchanged) -------------------- #
@app.route('/people')
def people_list():
    db = get_db()
    people = db.execute("SELECT * FROM people ORDER BY category, name").fetchall()
    return render_template('people_list.html', people=people)

@app.route('/add_person', methods=['GET', 'POST'])
def add_person():
    if request.method == 'POST':
        db = get_db()
        db.execute('''
            INSERT INTO people (name, dob, category, join_date, notes)
            VALUES (?, ?, ?, ?, ?)
        ''', (request.form.get('name'), request.form.get('dob'), 
              request.form.get('category'), request.form.get('join_date'),
              request.form.get('notes')))
        db.commit()
        flash(f"{request.form.get('name')} added successfully!", "success")
        return redirect(url_for('people_list'))
    return render_template('add_person.html')

@app.route('/person/<int:person_id>')
def person_profile(person_id):
    db = get_db()
    person = db.execute("SELECT * FROM people WHERE id = ?", (person_id,)).fetchone()
    if not person:
        flash("Person not found.", "danger")
        return redirect(url_for('people_list'))
    expenses = db.execute('''
        SELECT item_name, amount, category, expense_date 
        FROM expenses WHERE person_id = ?
        ORDER BY expense_date DESC
    ''', (person_id,)).fetchall()
    total_spent_row = db.execute("SELECT SUM(amount) as total FROM expenses WHERE person_id = ?", (person_id,)).fetchone()
    total_spent = total_spent_row['total'] or 0
    return render_template('person_profile.html', person=person, expenses=expenses, total_spent=total_spent)

# -------------------- Calendar, Events, Attendance Routes (Unchanged) -------------------- #

@app.route('/calendar')
def calendar():
    return render_template('calendar.html')

@app.route('/get_calendar_events')
def get_calendar_events():
    db = get_db()
    events = db.execute("SELECT id, title, start, end, color, details FROM events").fetchall()
    event_list = [dict(row) for row in events]
    return jsonify(event_list)

@app.route('/add_event', methods=['POST'])
def add_event():
    db = get_db()
    db.execute('''
        INSERT INTO events (title, start, end, details, color)
        VALUES (?, ?, ?, ?, ?)
    ''', (request.form.get('title'), request.form.get('start'),
          request.form.get('end') or None, request.form.get('details'),
          request.form.get('color')))
    db.commit()
    flash("Event added successfully!", "success")
    return redirect(url_for('calendar'))

@app.route('/get_attendance_data')
def get_attendance_data():
    day = request.args.get('date')
    if not day:
        return jsonify({'error': 'Date is required'}), 400
    db = get_db()
    people = db.execute('''
        SELECT p.id, p.name, p.category, a.status 
        FROM people p
        LEFT JOIN attendance a ON p.id = a.person_id AND a.attendance_date = ?
        ORDER BY p.category, p.name
    ''', (day,)).fetchall()
    return jsonify([dict(row) for row in people])

@app.route('/save_attendance', methods=['POST'])
def save_attendance():
    data = request.json
    day = data.get('date')
    attendance_records = data.get('attendance')
    if not day or not attendance_records:
        return jsonify({'error': 'Missing data'}), 400
    db = get_db()
    for person_id, status in attendance_records.items():
        db.execute('''
            REPLACE INTO attendance (person_id, attendance_date, status)
            VALUES (?, ?, ?)
        ''', (int(person_id), day, status))
    db.commit()
    return jsonify({'status': 'success', 'message': f'Attendance for {day} saved.'})

# -------------------- Run App -------------------- #
if __name__ == '__main__':
    init_db()
    app.run(debug=True, use_reloader=False)