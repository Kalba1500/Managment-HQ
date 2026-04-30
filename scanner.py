# ID SCANNER
import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

DB_FILE = "customers.db"

# =========================
# DATABASE SETUP
# =========================
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        BarcodeID TEXT PRIMARY KEY,
        FirstName TEXT,
        LastName TEXT,
        Tier TEXT,
        DateCreated TEXT,
        StoreCredit REAL,
        AmountBought REAL,
        LastVisit TEXT
    )
    """)

    conn.commit()
    conn.close()

# =========================
# FETCH CUSTOMER
# =========================
def get_customer(barcode):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("SELECT * FROM customers WHERE BarcodeID = ?", (barcode,))
    data = c.fetchone()

    conn.close()
    return data

# =========================
# CREATE CUSTOMER
# =========================
def create_customer(barcode, first, last, tier, amount, points):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("""
    INSERT INTO customers VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        barcode,
        first,
        last,
        tier,
        datetime.now(),
        points,
        amount,
        datetime.now()
    ))

    conn.commit()
    conn.close()

# =========================
# UPDATE CUSTOMER
# =========================
def update_customer(barcode, amount, points):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("""
    UPDATE customers
    SET StoreCredit = StoreCredit + ?,
        AmountBought = AmountBought + ?,
        LastVisit = ?
    WHERE BarcodeID = ?
    """, (points, amount, datetime.now(), barcode))

    conn.commit()
    conn.close()

# =========================
# INIT DB
# =========================
init_db()

# =========================
# VIEW ALL CUSTOMERS
# =========================
st.subheader("All Customers")

def load_all_customers():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM customers", conn)
    conn.close()
    return df

if st.button("Show Customers"):
    df = load_all_customers()
    st.dataframe(df)
# =========================
# UI
# =========================
st.title("Customer POS System (SQLite)")

tier_multiplier = {
    "Gold": 3,
    "Silver": 2,
    "Bronze": 1
}

if "new_customer" not in st.session_state:
    st.session_state.new_customer = False

barcode = st.text_input("Scan / Enter Barcode")
amount = st.number_input("Amount Spent ($)", min_value=0.0)

# =========================
# STEP 1: SUBMIT BARCODE
# =========================
if st.button("Submit"):

    customer = get_customer(barcode)

    if customer:
        tier = customer[3]
        multiplier = tier_multiplier.get(tier, 1)
        points = int((amount / 10) * multiplier)

        update_customer(barcode, amount, points)

        st.success(f"Welcome back {customer[1]} {customer[2]} ({tier})")
        st.info(f"Points earned: {points}")

    else:
        st.session_state.new_customer = True

# =========================
# STEP 2: NEW CUSTOMER FORM
# =========================
if st.session_state.new_customer:

    st.warning("New Customer")

    first = st.text_input("First Name")
    last = st.text_input("Last Name")
    tier = st.selectbox("Tier", ["Gold", "Silver", "Bronze"])

    if st.button("Create Customer"):

        multiplier = tier_multiplier[tier]
        points = int((amount / 10) * multiplier)

        create_customer(barcode, first, last, tier, amount, points)

        st.success(f"Customer created! Points: {points}")

        st.session_state.new_customer = False

        # =========================
        # EXISTING CUSTOMER
        # =========================
        if customer:
            tier = customer[3]
            multiplier = tier_multiplier.get(tier, 1)

            points = int((amount / 10) * multiplier)

            update_customer(barcode, amount, points)

            st.success(f"Welcome back {customer[1]} {customer[2]} ({tier})")
            st.info(f"Points earned: {points}")

        # =========================
        # N
