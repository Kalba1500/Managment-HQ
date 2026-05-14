# ID SCANNER
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from supabase import create_client
 
# =========================
# SUPABASE SETUP
# =========================
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
 
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
 
# =========================
# BUCKET NAME — must match exactly what's in Supabase Storage
# =========================
BUCKET = "Customer pic"
 
# =========================
# TIER CONFIG
# =========================
TIER_CONFIG = {
    "Bronze":    {"dpp": 0.00, "discount": 10, "price": 30},
    "Gold":      {"dpp": 0.10, "discount": 15, "price": 100},
    "Executive": {"dpp": 0.15, "discount": 20, "price": 150},
}
 
# =========================
# PHOTO UPLOAD (CAMERA)
# =========================
def upload_photo(barcode, file):
    file_path = f"{barcode}.png"
    file_bytes = file.getvalue()
 
    try:
        supabase.storage.from_(BUCKET).upload(
            file_path,
            file_bytes,
            file_options={"content-type": "image/png", "upsert": true}
        )
    except Exception as e:
        st.error(f"Photo upload failed: {e}")
        return None
 
    public_url = supabase.storage.from_(BUCKET).get_public_url(file_path)
    return public_url
 
# =========================
# DATABASE FUNCTIONS
# =========================
def get_customer(barcode):
    res = supabase.table("customers") \
        .select("*") \
        .eq("BarcodeID", barcode) \
        .execute()
    return res.data[0] if res.data else None
 
 
def create_customer(barcode, first, last, tier, amount, points, photo_url=None):
    expiry = datetime.now() + timedelta(days=30)
 
    supabase.table("customers").insert({
        "BarcodeID":         barcode,
        "FirstName":         first,
        "LastName":          last,
        "Tier":              tier,
        "DateCreated":       datetime.now().isoformat(),
        "StoreCredit":       points,
        "AmountBought":      amount,
        "LastVisit":         datetime.now().isoformat(),
        "MembershipExpires": expiry.isoformat(),
        "PhotoURL":          photo_url
    }).execute()
 
 
def update_customer(barcode, amount, points):
    customer = get_customer(barcode)
 
    supabase.table("customers").update({
        "StoreCredit":  float(customer["StoreCredit"]) + points,
        "AmountBought": float(customer["AmountBought"]) + amount,
        "LastVisit":    datetime.now().isoformat()
    }).eq("BarcodeID", barcode).execute()
 
 
def load_all_customers():
    res = supabase.table("customers").select("*").execute()
    return pd.DataFrame(res.data)
 
# =========================
# UI
# =========================
st.title("Customer POS System")
 
if "new_customer" not in st.session_state:
    st.session_state.new_customer = False
if "barcode" not in st.session_state:
    st.session_state.barcode = ""
 
# =========================
# VIEW CUSTOMERS
# =========================
if st.button("Show Customers"):
    st.dataframe(load_all_customers())
 
# =========================
# INPUTS
# =========================
barcode = st.text_input("Scan / Enter Barcode")
amount  = st.number_input("Amount Spent ($)", min_value=0.0)
 
# =========================
# SUBMIT FLOW
# =========================
if st.button("Submit"):
 
    customer = get_customer(barcode)
 
    if customer:
 
        expiry = customer.get("MembershipExpires")
 
        if expiry:
            expiry_date = datetime.fromisoformat(expiry)
            days_left   = (expiry_date - datetime.now()).days
 
            if days_left < 0:
                st.error("⚠️ Membership EXPIRED")
 
                if st.button("Renew Membership (30 days)"):
                    new_expiry = datetime.now() + timedelta(days=30)
                    supabase.table("customers").update({
                        "MembershipExpires": new_expiry.isoformat()
                    }).eq("BarcodeID", barcode).execute()
                    st.success("Membership renewed!")
                    st.stop()
 
                st.stop()
 
        tier   = customer["Tier"]
        config = TIER_CONFIG[tier]
 
        points   = amount * config["dpp"]
        discount = config["discount"]
 
        update_customer(barcode, amount, points)
 
        if customer.get("PhotoURL"):
            st.image(customer["PhotoURL"], width=150)
 
        st.success(f"Welcome back {customer['FirstName']} {customer['LastName']} ({tier})")
 
        if expiry:
            if days_left >= 0:
                st.info(f"Membership expires in {days_left} days")
            else:
                st.error("Membership EXPIRED")
 
        st.info(f"Points earned: {points:.2f}")
        st.info(f"Discount applied: {discount}%")
 
    else:
        st.session_state.new_customer = True
        st.session_state.barcode      = barcode
 
# =========================
# NEW CUSTOMER SECTION
# =========================
if st.session_state.new_customer:
 
    st.warning("New Customer Setup")
 
    first = st.text_input("First Name")
    last  = st.text_input("Last Name")
 
    tier = st.selectbox(
        "Select Tier",
        [
            "Bronze — $30/mo | 10% off | 0.00 DPP",
            "Gold — $100/mo | 15% off | 0.10 DPP",
            "Executive — $150/mo | 20% off | 0.15 DPP"
        ]
    )
    tier = tier.split(" — ")[0]
 
    mode = st.radio(
        "Select Action",
        ["Signup Only (No Purchase)", "Signup + Purchase"]
    )
 
    photo = st.camera_input("Take Customer Photo (optional)")
 
    if st.button("Create Customer"):
 
        barcode = st.session_state.barcode
        config  = TIER_CONFIG[tier]
 
        photo_url = None
        if photo:
            photo_url = upload_photo(barcode, photo)
 
        if mode == "Signup Only (No Purchase)":
            amount_value = 0
            points       = 0
        else:
            amount_value = amount
            points       = amount * config["dpp"]
 
        create_customer(barcode, first, last, tier, amount_value, points, photo_url)
 
        st.success(f"{tier} customer created successfully!")
        st.session_state.new_customer = False
