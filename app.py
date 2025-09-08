from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
from datetime import datetime
import os

DB_PATH = os.environ.get("DB_PATH", "data.db")

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret")

OIL_TYPES = ["Groundnut", "Coconut", "Gingelly"]  # 'Gingelly' (Sesame)

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        oil_type TEXT NOT NULL CHECK (oil_type in ('Groundnut','Coconut','Gingelly'))
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS batches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        batch_date TEXT NOT NULL,
        quantity_liters REAL NOT NULL,
        cost_per_liter REAL NOT NULL,
        FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        sale_date TEXT NOT NULL,
        quantity_liters REAL NOT NULL,
        price_per_liter REAL NOT NULL,
        customer TEXT,
        FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
    )""")
    conn.commit()
    conn.close()

@app.before_first_request
def startup():
    init_db()

@app.route("/health")
def health():
    return {"status":"ok"}, 200

@app.route("/")
def index():
    conn = get_conn()
    cur = conn.cursor()
    # simple metrics
    cur.execute("SELECT COUNT(*) as c FROM products")
    products_count = cur.fetchone()["c"]
    cur.execute("SELECT COALESCE(SUM(quantity_liters),0) as q FROM batches")
    total_produced = cur.fetchone()["q"]
    cur.execute("SELECT COALESCE(SUM(quantity_liters),0) as q FROM sales")
    total_sold = cur.fetchone()["q"]
    cur.execute("SELECT p.id, p.name, p.oil_type, COALESCE(SUM(b.quantity_liters),0) as produced FROM products p LEFT JOIN batches b ON b.product_id=p.id GROUP BY p.id")
    produced_by_product = cur.fetchall()
    conn.close()
    return render_template("index.html",
                           products_count=products_count,
                           total_produced=total_produced,
                           total_sold=total_sold,
                           produced_by_product=produced_by_product)

# -------------------- Products --------------------
@app.route("/products", methods=["GET", "POST"])
def products():
    conn = get_conn()
    cur = conn.cursor()
    if request.method == "POST":
        name = request.form.get("name","").strip()
        oil_type = request.form.get("oil_type")
        if not name or oil_type not in OIL_TYPES:
            flash("Invalid input", "error")
        else:
            cur.execute("INSERT INTO products (name, oil_type) VALUES (?,?)", (name, oil_type))
            conn.commit()
            flash("Product added", "success")
        return redirect(url_for("products"))
    cur.execute("SELECT * FROM products ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return render_template("products.html", rows=rows, oil_types=OIL_TYPES)

@app.route("/products/<int:pid>/delete", methods=["POST"])
def delete_product(pid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM products WHERE id=?", (pid,))
    conn.commit()
    conn.close()
    flash("Product deleted", "success")
    return redirect(url_for("products"))

# -------------------- Batches --------------------
@app.route("/batches", methods=["GET", "POST"])
def batches():
    conn = get_conn()
    cur = conn.cursor()
    if request.method == "POST":
        product_id = request.form.get("product_id")
        batch_date = request.form.get("batch_date") or datetime.utcnow().strftime("%Y-%m-%d")
        quantity_liters = request.form.get("quantity_liters")
        cost_per_liter = request.form.get("cost_per_liter")
        try:
            cur.execute("INSERT INTO batches (product_id, batch_date, quantity_liters, cost_per_liter) VALUES (?,?,?,?)",
                        (int(product_id), batch_date, float(quantity_liters), float(cost_per_liter)))
            conn.commit()
            flash("Batch recorded", "success")
        except Exception as e:
            flash(f"Error: {e}", "error")
        return redirect(url_for("batches"))
    cur.execute("SELECT id, name FROM products ORDER BY name")
    products = cur.fetchall()
    cur.execute("""
        SELECT b.id, p.name as product, p.oil_type, b.batch_date, b.quantity_liters, b.cost_per_liter
        FROM batches b JOIN products p ON p.id=b.product_id
        ORDER BY b.id DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return render_template("batches.html", rows=rows, products=products)

# -------------------- Sales --------------------
@app.route("/sales", methods=["GET", "POST"])
def sales():
    conn = get_conn()
    cur = conn.cursor()
    if request.method == "POST":
        product_id = request.form.get("product_id")
        sale_date = request.form.get("sale_date") or datetime.utcnow().strftime("%Y-%m-%d")
        quantity_liters = request.form.get("quantity_liters")
        price_per_liter = request.form.get("price_per_liter")
        customer = request.form.get("customer","").strip() or None
        try:
            cur.execute("INSERT INTO sales (product_id, sale_date, quantity_liters, price_per_liter, customer) VALUES (?,?,?,?,?)",
                        (int(product_id), sale_date, float(quantity_liters), float(price_per_liter), customer))
            conn.commit()
            flash("Sale recorded", "success")
        except Exception as e:
            flash(f"Error: {e}", "error")
        return redirect(url_for("sales"))
    cur.execute("SELECT id, name FROM products ORDER BY name")
    products = cur.fetchall()
    cur.execute("""
        SELECT s.id, p.name as product, p.oil_type, s.sale_date, s.quantity_liters, s.price_per_liter, s.customer
        FROM sales s JOIN products p ON p.id=s.product_id
        ORDER BY s.id DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return render_template("sales.html", rows=rows, products=products)

# -------------------- Simple JSON APIs --------------------
@app.route("/api/summary")
def api_summary():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as products FROM products")
    products = cur.fetchone()["products"]
    cur.execute("SELECT COALESCE(SUM(quantity_liters),0) as produced FROM batches")
    produced = cur.fetchone()["produced"]
    cur.execute("SELECT COALESCE(SUM(quantity_liters),0) as sold FROM sales")
    sold = cur.fetchone()["sold"]
    conn.close()
    return jsonify({"products": products, "produced_liters": produced, "sold_liters": sold})

if __name__ == "__main__":
    # For local dev
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
