# ID SCANNER
import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client

# =========================
# SUPABASE SETUP
# =========================
SUPABASE_URL = "https://rwuepcusnevuaxhdmrgt.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJ3dWVwY3VzbmV2dWF4aGRtcmd0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc1MDM3NjIsImV4cCI6MjA5MzA3OTc2Mn0.Ci7hxwCYJxT8ec7LqseVRHxaYdB4DfBi35OaojTeWSk"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# =========================
# DATABASE FUNCTIONS
# =========================
def get_customer(barcode):
    res = supabase.table("customers") \
        .select("*") \
        .eq("BarcodeID", barcode) \
        .execute()

    return res.data[0] if res.data else None


from datetime import datetime, timedelta

def create_customer(barcode, first, last, tier, amount, points):
    expiry = datetime.now() + timedelta(days=30)

    supabase.table("customers").insert({
        "BarcodeID": barcode,
        "FirstName": first,
        "LastName": last,
        "Tier": tier,
        "DateCreated": datetime.now().isoformat(),
        "StoreCredit": points,
        "AmountBought": amount,
        "LastVisit": datetime.now().isoformat(),
        "MembershipExpires": expiry.isoformat()
    }).execute()


def update_customer(barcode, amount, points):
    customer = get_customer(barcode)

    supabase.table("customers").update({
        "StoreCredit": customer["StoreCredit"] + points,
        "AmountBought": customer["AmountBought"] + amount,
        "LastVisit": datetime.now().isoformat()
    }).eq("BarcodeID", barcode).execute()


def load_all_customers():
    res = supabase.table("customers").select("*").execute()
    return pd.DataFrame(res.data)

# =========================
# UI SETUP
# =========================
st.title("Customer POS System (Supabase)")

tier_multiplier = {
    "Gold": 3,
    "Silver": 2,
    "Bronze": 1
}

if "new_customer" not in st.session_state:
    st.session_state.new_customer = False
if "barcode" not in st.session_state:
    st.session_state.barcode = ""

# =========================
# VIEW CUSTOMERS
# =========================
st.subheader("All Customers")

if st.button("Show Customers"):
    df = load_all_customers()
    st.dataframe(df)

# =========================
# INPUTS
# =========================
barcode = st.text_input("Scan / Enter Barcode")
amount = st.number_input("Amount Spent ($)", min_value=0.0)

# =========================
# SUBMIT FLOW
# =========================
if st.button("Submit"):

    customer = get_customer(barcode)

    if customer:
        from datetime import datetime

if customer:
    expiry = customer.get("MembershipExpires")

    if expiry:
        expiry_date = datetime.fromisoformat(expiry)

        if datetime.now() > expiry_date:
            st.error("Membership expired!")

            if st.button("Renew Membership (30 days)"):
                new_expiry = datetime.now() + timedelta(days=30)

                supabase.table("customers").update({
                    "MembershipExpires": new_expiry.isoformat()
                }).eq("BarcodeID", barcode).execute()

                st.success("Membership renewed!")
                st.stop()
        tier = customer["Tier"]
        multiplier = tier_multiplier.get(tier, 1)

        points = int((amount / 10) * multiplier)

        update_customer(barcode, amount, points)

        st.success(f"Welcome back {customer['FirstName']} {customer['LastName']} ({tier})")
        st.info(f"Points earned: {points}")

    else:
        st.session_state.new_customer = True
        st.session_state.barcode = barcode

# =========================
# NEW CUSTOMER FORM
# =========================
if st.session_state.new_customer:

    st.warning("New Customer")

    first = st.text_input("First Name")
    last = st.text_input("Last Name")
    tier = st.selectbox("Tier", ["Gold", "Silver", "Bronze"])

    mode = st.radio(
        "Select Action",
        ["Signup Only (No Purchase)", "Signup + Purchase"]
    )

    if st.button("Create Customer"):

        barcode = st.session_state.barcode
        multiplier = tier_multiplier[tier]

        if mode == "Signup Only (No Purchase)":
            amount_value = 0
            points = 0
        else:
            amount_value = amount
            points = int((amount / 10) * multiplier)

        create_customer(barcode, first, last, tier, amount_value, points)

        if mode == "Signup Only (No Purchase)":
            st.success("Customer created successfully (no purchase).")
        else:
            st.success(f"Customer created! Points: {points}")

        st.session_state.new_customer = False
