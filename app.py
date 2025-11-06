from flask import Flask, render_template, request, redirect, session, url_for
from db_config import get_db_connection, close_db_connection
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Change this to something secure

# ---------------------------
# 🔹 Login Page
# ---------------------------
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
        user = cursor.fetchone()
        close_db_connection(conn)

        if user:
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect('/dashboard')
        else:
            return render_template('login.html', error="Invalid username or password")

    return render_template('login.html')


# ---------------------------
# 🔹 Logout
# ---------------------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


# ---------------------------
# 🔹 Dashboard
# ---------------------------
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect('/login')
    return render_template('dashboard.html')


# ---------------------------
# 🔹 Inventory View
# ---------------------------
@app.route('/inventory')
def inventory():
    if 'username' not in session:
        return redirect('/login')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM inventory")
    items = cursor.fetchall()
    close_db_connection(conn)
    return render_template('inventory.html', items=items)


# ---------------------------
# 🔹 Add New Item (Admin Only)
# ---------------------------
@app.route('/add-item', methods=['GET', 'POST'])
def add_item():
    if 'username' not in session:
        return redirect('/login')
    if session['role'] != 'admin':
        return "Access Denied! Only admin can add items."

    if request.method == 'POST':
        item_name = request.form['item_name']
        quantity = int(request.form['quantity'])
        price = float(request.form['price'])

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO inventory (item_name, quantity, price) VALUES (%s, %s, %s)",
                       (item_name, quantity, price))
        conn.commit()
        close_db_connection(conn)
        return redirect('/inventory')

    return render_template('add_item.html')


# ---------------------------
# 🔹 Sell Item (Staff + Admin)
# ---------------------------
@app.route('/sell-item', methods=['GET', 'POST'])
def sell_item():
    if 'username' not in session:
        return redirect('/login')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        item_id = int(request.form['item_id'])
        quantity_sold = int(request.form['quantity_sold'])

        # Fetch item details
        cursor.execute("SELECT * FROM inventory WHERE id = %s", (item_id,))
        item = cursor.fetchone()

        if item and item['quantity'] >= quantity_sold:
            new_quantity = item['quantity'] - quantity_sold
            total_amount = item['price'] * quantity_sold

            # Update inventory  
            cursor.execute("UPDATE inventory SET quantity = %s WHERE id = %s", (new_quantity, item_id))

            # Record sale
            # Record sale with username
            cursor.execute("""
                INSERT INTO sales (item_id, quantity_sold, total_amount, sold_by)
                VALUES (%s, %s, %s, %s)
            """, (item_id, quantity_sold, total_amount, session['username']))

            conn.commit()
            message = f"✅ Sold {quantity_sold} of {item['item_name']} successfully."
        else:
            message = "❌ Not enough stock available."

        # Reload items list after transaction
        cursor.execute("SELECT * FROM inventory")
        items = cursor.fetchall()
        close_db_connection(conn)
        return render_template('sell_item.html', items=items, message=message)

    # GET request → show form
    cursor.execute("SELECT * FROM inventory")
    items = cursor.fetchall()
    close_db_connection(conn)
    return render_template('sell_item.html', items=items)


# ---------------------------
# 🔹 View Sales Records
# ---------------------------
@app.route('/sales')
def sales():
    if 'username' not in session:
        return redirect('/login')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT s.id, i.item_name, s.quantity_sold, s.total_amount, s.sold_at
        FROM sales s
        JOIN inventory i ON s.item_id = i.id
        ORDER BY s.sold_at DESC
    """)
    sales = cursor.fetchall()
    close_db_connection(conn)
    return render_template('sales.html', sales=sales)


# ---------------------------
# 🔹 Run Flask App
# ---------------------------
if __name__ == '__main__':
    app.run(debug=True)
