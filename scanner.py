# ID SCANNER
import streamlit as st
import pandas as pd
import bcrypt
from datetime import datetime, timedelta
from supabase import create_client

# =========================
# LOGIN
# =========================
USERS = {
    username: st.secrets["credentials"]["usernames"][username]["password"]
    for username in st.secrets["credentials"]["usernames"]
}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username in USERS and bcrypt.checkpw(password.encode(), USERS[username].encode()):
            st.session_state.logged_in = True
            st.session_state.username = username
            st.rerun()
        else:
            st.error("❌ Incorrect username or password")
    st.stop()

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;800&display=swap');

html, body, [class*="css"], .stApp {
    background-color: #ffffff !important;
    color: #1a1a1a !important;
    font-family: 'Syne', sans-serif !important;
}
section[data-testid="stSidebar"] {
    background-color: #f0f0f0 !important;
}
div[data-testid="metric-container"] {
    background-color: #ffffff !important;
    border: 1px solid #ddd !important;
    border-radius: 8px !important;
}
.stButton > button {
    background-color: #1a1a1a !important;
    color: #ffffff !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 4px !important;
}
.stButton > button:hover {
    background-color: #333333 !important;
}
div[data-testid="stSidebar"] button {
    background-color: #ff4444 !important;
    color: #ffffff !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 4px !important;
    width: 100% !important;
}
div[data-testid="stSidebar"] button:hover {
    background-color: #cc0000 !important;
}
.stTextInput input, .stNumberInput input {
    background-color: #ffffff !important;
    color: #1a1a1a !important;
    border: 1px solid #ccc !important;
}
</style>
""", unsafe_allow_html=True)

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()
    
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
    "Bronze":    {"cashback": 0.00,  "discount": 10, "price": 30},
    "Gold":      {"cashback": 0.075, "discount": 15, "price": 100},
    "Executive": {"cashback": 0.10,  "discount": 20, "price": 150},
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
            file_options={"content-type": "image/png", "upsert": "true"}
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
st.title("Cigar Membership System")
 
if "new_customer" not in st.session_state:
    st.session_state.new_customer = False
if "barcode" not in st.session_state:
    st.session_state.barcode = ""
if "expired_customer" not in st.session_state:
    st.session_state.expired_customer = False
if "expired_barcode" not in st.session_state:
    st.session_state.expired_barcode = ""
 
# =========================
# VIEW CUSTOMERS
# =========================
if st.button("Show Customers"):
    st.table(load_all_customers())
 
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
                st.session_state.expired_customer = True
                st.session_state.expired_barcode = barcode
 
        tier   = customer["Tier"]
        config = TIER_CONFIG[tier]
 
        cashback = amount * config["cashback"]
        discount = config["discount"]
 
        update_customer(barcode, amount, cashback)
 
        col_img, col_info = st.columns([1, 2])

        with col_img:
            if customer.get("PhotoURL"):
                st.image(customer["PhotoURL"], width=300)

        with col_info:
            st.markdown(f"## **Welcome back {customer['FirstName']} {customer['LastName']}!**")
            st.markdown(f"### **{tier} Member**")

            if expiry:
                if days_left > 3:
                    st.markdown(f"### **🟢 Membership expires in {days_left} days**")
                elif days_left >= 0:
                    st.markdown(f"### **🟡 Membership expires in {days_left} days — Expiring Soon!**")
                else:
                    st.markdown(f"### **🔴 Membership EXPIRED**")

            st.info(f"💰 Cash Back Earned: ${cashback:.2f}")
            st.info(f"🏷️ Discount: {discount}%")
            st.info(f"🛍️ Amount Spent: ${amount:.2f}")
 
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
            f"Bronze — ${TIER_CONFIG['Bronze']['price']}/mo | {TIER_CONFIG['Bronze']['discount']}% off | {TIER_CONFIG['Bronze']['cashback']*100:.1f}% Cash Back",
            f"Gold — ${TIER_CONFIG['Gold']['price']}/mo | {TIER_CONFIG['Gold']['discount']}% off | {TIER_CONFIG['Gold']['cashback']*100:.1f}% Cash Back",
            f"Executive — ${TIER_CONFIG['Executive']['price']}/mo | {TIER_CONFIG['Executive']['discount']}% off | {TIER_CONFIG['Executive']['cashback']*100:.1f}% Cash Back",
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
            points       = amount * config["cashback"]
 
        create_customer(barcode, first, last, tier, amount_value, cashback, photo_url)
 
        st.success(f"{tier} customer created successfully!")
        st.session_state.new_customer = False
        
# =========================
# REJOIN SECTION
# =========================
if st.session_state.expired_customer:
    st.error("⚠️ Membership EXPIRED")
    st.markdown("### Would this customer like to rejoin?")

    new_tier = st.selectbox(
        "Select New Tier",
        [
            f"Bronze — ${TIER_CONFIG['Bronze']['price']}/mo | {TIER_CONFIG['Bronze']['discount']}% off | {TIER_CONFIG['Bronze']['cashback']*100:.1f}% Cash Back",
            f"Gold — ${TIER_CONFIG['Gold']['price']}/mo | {TIER_CONFIG['Gold']['discount']}% off | {TIER_CONFIG['Gold']['cashback']*100:.1f}% Cash Back",
            f"Executive — ${TIER_CONFIG['Executive']['price']}/mo | {TIER_CONFIG['Executive']['discount']}% off | {TIER_CONFIG['Executive']['cashback']*100:.1f}% Cash Back",
        ],
        key="rejoin_tier_select"
    )
    new_tier_name = new_tier.split(" — ")[0]

    if st.button("✅ Confirm Rejoin", key="confirm_rejoin_btn"):
        new_expiry = datetime.now() + timedelta(days=30)
        supabase.table("customers").update({
            "MembershipExpires": new_expiry.isoformat(),
            "Tier": new_tier_name
        }).eq("BarcodeID", st.session_state.expired_barcode).execute()
        st.success(f"✅ Rejoined as {new_tier_name} member for 30 days!")
        st.session_state.expired_customer = False
        st.session_state.expired_barcode = ""
        st.rerun()
