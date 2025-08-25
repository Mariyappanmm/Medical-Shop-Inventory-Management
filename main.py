from flask import Flask, render_template, request, redirect,session,url_for
import sqlite3
from datetime import datetime, timedelta
from flask import jsonify


app = Flask(__name__)

app.secret_key = 'HelloWorld'

def get_db_connection():
    conn = sqlite3.connect('medical_shop.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Simple static authentication — you can make this dynamic later
        if username == 'admin' and password == 'admin123':
            session['logged_in'] = True
            return redirect(url_for('admin'))
        else:
            error = 'Invalid credentials. Try again.'

    return render_template('login.html', error=error)



@app.route('/admin')
def admin():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    conn = get_db_connection()

    total_users = conn.execute('SELECT COUNT(*) FROM staff').fetchone()[0]
    total_zones = conn.execute('SELECT COUNT(*) FROM storage').fetchone()[0]
    total_medicines = conn.execute('SELECT COUNT(*) FROM medicine').fetchone()[0]
    low_stock_items = conn.execute('SELECT COUNT(*) FROM medicine WHERE quantity < 10').fetchone()[0]

    staff = conn.execute('SELECT * FROM staff').fetchall()
    zones = conn.execute('SELECT * FROM storage').fetchall()
    medicines = conn.execute('SELECT * FROM medicine').fetchall()
    conn.close()

    return render_template('index.html',
                           staff=staff,
                           zones=zones,
                           medicines=medicines,
                           total_users=total_users,
                           total_zones=total_zones,
                           total_medicines=total_medicines,
                           low_stock_items=low_stock_items)



@app.route('/')
@app.route('/st')
def st():
    conn = get_db_connection()
    zones = conn.execute('SELECT * FROM storage').fetchall()
    medicines = conn.execute('SELECT * FROM medicine').fetchall()
    conn.close()
    return render_template('medicine.html',
                           zones=zones,
                           medicines=medicines, now=datetime.now(), timedelta=timedelta)



@app.route('/bill')
def bill():
    conn = get_db_connection()

    bills = conn.execute('''
        SELECT 
            b.bill_id,
            b.customer_name,
            b.billing_date,
            b.total_amount,
            COUNT(bi.item_id) AS item_count
        FROM bills b
        LEFT JOIN bill_items bi ON b.bill_id = bi.bill_id
        GROUP BY b.bill_id
        ORDER BY b.bill_id DESC
    ''').fetchall()
    
    
    bill_items_count = {}
    for row in conn.execute('SELECT bill_id, COUNT(*) as count FROM bill_items GROUP BY bill_id'):
        bill_items_count[row['bill_id']] = row['count']

    medicines = conn.execute('SELECT * FROM medicine').fetchall()
    conn.close()
    return render_template('bill.html', medicines=medicines,bills=bills,bill_items_count=bill_items_count)

@app.route('/generate_bill', methods=['POST'])
def generate_bill():
    data = request.get_json()
    items = data['items']
    discount = data.get('discount', 0)
    tax = data.get('tax', 0)
    
    subtotal = sum([item['price'] * item['quantity'] for item in items])
    total_amount = subtotal - (subtotal * discount / 100) + (subtotal * tax / 100)
    
    conn = get_db_connection()
    cursor = conn.cursor()

    # Insert into bills table
    cursor.execute('''
        INSERT INTO bills (customer_name, customer_phone, billing_date, discount, tax, total_amount)
        VALUES (?, ?, DATE('now'), ?, ?, ?)
    ''', (data['customer_name'], data['customer_phone'], discount, tax, total_amount))
    
    bill_id = cursor.lastrowid  # get the ID of the inserted bill
    
    # Insert each item
    for item in items:
        cursor.execute('''
            INSERT INTO bill_items (bill_id, medicine_id, quantity, unit_price)
            VALUES (?, ?, ?, ?)
        ''', (bill_id, item['id'], item['quantity'], item['price']))

    conn.commit()
    conn.close()

    return {'status': 'success', 'bill_id': bill_id}



@app.route('/submit_bill', methods=['POST'])
def submit_bill():
    data = request.get_json()

    customer_name = data['customer_name']
    customer_phone = data['customer_phone']
    discount = float(data['discount'])
    tax = float(data['tax'])
    total_amount = float(data['total_amount'])
    items = data['items']  # list of {medicine_id, quantity, unit_price}

    billing_date = datetime.now().strftime("%Y-%m-%d")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO bills (customer_name, customer_phone, billing_date, discount, tax, total_amount)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (customer_name, customer_phone, billing_date, discount, tax, total_amount))

    bill_id = cursor.lastrowid

    for item in items:
        cursor.execute('''
            INSERT INTO bill_items (bill_id, medicine_id, quantity, unit_price)
            VALUES (?, ?, ?, ?)
        ''', (bill_id, item['medicine_id'], item['quantity'], item['unit_price']))

    conn.commit()
    conn.close()
    return jsonify({'status': 'success', 'bill_id': bill_id})



@app.route('/add_bill', methods=['POST'])
def add_bill():
    customer_name = request.form['customer_name']
    customer_phone = request.form['customer_phone']
    medicine = request.form['medicine']
    quantity = int(request.form['quantity'])
    item = int(request.form['item'])
    billing_date = datetime.now().strftime('%Y-%m-%d')

    # 🔍 Get unit price from medicine table
    conn = get_db_connection()
    med_row = conn.execute('SELECT unit_price FROM medicine WHERE medicine_name = ?', (medicine,)).fetchone()

    if med_row is None:
        conn.close()
        return "Medicine not found", 400

    unit_price = med_row['unit_price']
    total = quantity * unit_price

    conn.execute('''
        INSERT INTO bill (customer_name, billing_date, customer_phone, item, medicine, quantity, total)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (customer_name, billing_date, customer_phone, item, medicine, quantity, total))
    conn.commit()
    conn.close()

    return redirect('/bill')



@app.route('/sale')
def sale():
    conn = get_db_connection()

    # Recent Sales (Join bills + bill_items + medicine)
    recent_sales = conn.execute('''
        SELECT 
            b.billing_date AS date,
            b.customer_name,
            m.medicine_name,
            bi.quantity AS quantity_sold,
            bi.unit_price,
            (bi.quantity * bi.unit_price) AS total
        FROM bill_items bi
        JOIN bills b ON bi.bill_id = b.bill_id
        JOIN medicine m ON bi.medicine_id = m.id
        ORDER BY b.billing_date DESC
        LIMIT 50
    ''').fetchall()

    # Stats
    today = datetime.now().strftime('%Y-%m-%d')
    week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    month_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

    today_total = conn.execute('''
        SELECT SUM(bi.quantity * bi.unit_price) FROM bill_items bi
        JOIN bills b ON bi.bill_id = b.bill_id
        WHERE b.billing_date = ?
    ''', (today,)).fetchone()[0] or 0

    week_total = conn.execute('''
        SELECT SUM(bi.quantity * bi.unit_price) FROM bill_items bi
        JOIN bills b ON bi.bill_id = b.bill_id
        WHERE b.billing_date BETWEEN ? AND ?
    ''', (week_ago, today)).fetchone()[0] or 0

    month_total = conn.execute('''
        SELECT SUM(bi.quantity * bi.unit_price) FROM bill_items bi
        JOIN bills b ON bi.bill_id = b.bill_id
        WHERE b.billing_date BETWEEN ? AND ?
    ''', (month_ago, today)).fetchone()[0] or 0

    items_today = conn.execute('''
        SELECT SUM(bi.quantity) FROM bill_items bi
        JOIN bills b ON bi.bill_id = b.bill_id
        WHERE b.billing_date = ?
    ''', (today,)).fetchone()[0] or 0

    # Top Selling Items
    top_items = conn.execute('''
        SELECT m.medicine_name, SUM(bi.quantity) as total_sold
        FROM bill_items bi
        JOIN medicine m ON bi.medicine_id = m.id
        GROUP BY bi.medicine_id
        ORDER BY total_sold DESC
        LIMIT 5
    ''').fetchall()

    conn.close()
    return render_template('sales.html',
                           recent_sales=recent_sales,
                           today_total=today_total,
                           week_total=week_total,
                           month_total=month_total,
                           items_today=items_today,
                           top_items=top_items)


@app.route('/add_staff', methods=['POST'])
def add_staff():
    name = request.form['staff_name']
    email = request.form['email']
    role = request.form['role']

    conn = get_db_connection()
    conn.execute(
        'INSERT INTO staff (staff_name, email, role) VALUES (?, ?, ?)',
        (name, email, role)
    )
    conn.commit()
    conn.close()
    return redirect('/admin')

@app.route('/add_zone', methods=['POST'])
def add_zone():
    name = request.form['zone_name']
    ztype = request.form['zone_type']
    capacity = request.form['capacity']

    conn = get_db_connection()
    conn.execute(
        'INSERT INTO storage (zone_name, zone_type, capacity) VALUES (?, ?, ?)',
        (name, ztype, capacity)
    )
    conn.commit()
    conn.close()
    return redirect('/admin')

@app.route('/add_medicine', methods=['POST'])
def add_medicine():
    medicine_name = request.form['medicine_name']
    generic_name = request.form['generic_name']
    batch_no = request.form['batch_no']
    quantity = request.form['quantity']
    mfg_date = request.form['mfg_date']
    expiry_date = request.form['expiry_date']
    storage_location = request.form['storage_location']
    unit_price = request.form['unit_price']

    conn = get_db_connection()
    conn.execute('''
        INSERT INTO medicine (
            medicine_name, generic_name, batch_no, quantity,
            mfg_date, expiry_date, storage_location, unit_price
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        medicine_name, generic_name, batch_no, quantity,
        mfg_date, expiry_date, storage_location, unit_price
    ))
    conn.commit()
    conn.close()

    return redirect('/st')  # redirect to your inventory page

@app.route('/search_medicine')
def search_medicine():
    query = request.args.get('query')

    conn = get_db_connection()
    medicines = conn.execute(
        "SELECT * FROM medicine WHERE medicine_name LIKE ? OR generic_name LIKE ?",
        ('%' + query + '%', '%' + query + '%')
    ).fetchall()
    conn.close()

    from datetime import datetime, timedelta
    return render_template('medicine.html', medicines=medicines, now=datetime.now(), timedelta=timedelta)

@app.route('/update_medicine/<int:medicine_id>', methods=['POST'])
def update_medicine(medicine_id):
    data = request.form
    conn = get_db_connection()
    conn.execute('''
        UPDATE medicine SET
        medicine_name = ?, generic_name = ?, batch_no = ?, quantity = ?,
        mfg_date = ?, expiry_date = ?, storage_location = ?, unit_price = ?
        WHERE id = ?
    ''', (
        data['medicine_name'],
        data['generic_name'],
        data['batch_no'],
        data['quantity'],
        data['mfg_date'],
        data['expiry_date'],
        data['storage_location'],
        data['unit_price'],
        medicine_id
    ))
    conn.commit()
    conn.close()
    return redirect('/st')

@app.route('/delete_medicine/<int:medicine_id>')
def delete_medicine(medicine_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM medicine WHERE id = ?', (medicine_id,))
    conn.commit()
    conn.close()
    return redirect('/st')  # Redirect back to medicine page

@app.route('/edit_medicine/<int:medicine_id>')
def edit_medicine(medicine_id):
    conn = get_db_connection()
    medicine = conn.execute('SELECT * FROM medicine WHERE id = ?', (medicine_id,)).fetchone()
    zones = conn.execute('SELECT * FROM storage').fetchall()
    conn.close()
    return render_template('edit.html', medicine=medicine, zones=zones)


@app.route('/filter_sales')
def filter_sales():
    from_date = request.args.get('from')
    to_date = request.args.get('to')
    category = request.args.get('category')

    conn = get_db_connection()
    query = '''
        SELECT b.billing_date as date, m.medicine_name, bi.quantity, bi.unit_price,
               (bi.quantity * bi.unit_price) as total_amount, b.customer_name as customer
        FROM bill_items bi
        JOIN bills b ON b.bill_id = bi.bill_id
        JOIN medicine m ON m.id = bi.medicine_id
        WHERE 1=1
    '''
    params = []

    if from_date:
        query += ' AND b.billing_date >= ?'
        params.append(from_date)
    if to_date:
        query += ' AND b.billing_date <= ?'
        params.append(to_date)
    if category:
        query += ' AND m.generic_name = ?'
        params.append(category)

    rows = conn.execute(query, params).fetchall()
    conn.close()

    results = [{
        "date": row["date"],
        "medicine_name": row["medicine_name"],
        "quantity": row["quantity"],
        "unit_price": row["unit_price"],
        "total_amount": row["total_amount"],
        "customer": row["customer"]
    } for row in rows]

    return jsonify(results)



if __name__ == '__main__':
    app.run(debug=True)

