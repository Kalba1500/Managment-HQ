# ID SCANNER
import streamlit as st
import pandas as pd
from datetime import datetime
import os

FILE = "customers.xlsx"

def load_data():
    if os.path.exists(FILE):
        df = pd.read_excel(FILE)
        df["BarcodeID"] = df["BarcodeID"].astype(str)
        return df
    else:
        return pd.DataFrame(columns=[
            "BarcodeID", "First Name", "Last Name", "Tier",
            "Date Created", "Store Credit", "Amount Bought", "Last Visit"
        ])

def save_data(df):
    df.to_excel(FILE, index=False)

tier_multiplier = {
    "Gold": 3,
    "Silver": 2,
    "Bronze": 1
}

# =========================
# SESSION STATE
# =========================
if "new_customer" not in st.session_state:
    st.session_state.new_customer = False

# =========================
# UI
# =========================
st.title("Customer POS System")

barcode = st.text_input("Scan / Enter Barcode")
amount = st.number_input("Amount Spent ($)", min_value=0.0)

# =========================
# SUBMIT BUTTON
# =========================
if st.button("Submit"):
    df = load_data()

    if not barcode:
        st.error("Enter a barcode")
    else:
        match = df[df["BarcodeID"] == barcode]

        if not match.empty:
            tier = match["Tier"].values[0]
            multiplier = tier_multiplier.get(tier, 1)
            points = int((amount / 10) * multiplier)

            st.success(f"Welcome back {match['First Name'].values[0]} ({tier})")
            st.info(f"Points earned: {points}")

            df.loc[df["BarcodeID"] == barcode, "Store Credit"] += points
            df.loc[df["BarcodeID"] == barcode, "Amount Bought"] += amount
            df.loc[df["BarcodeID"] == barcode, "Last Visit"] = datetime.now()

            save_data(df)

        else:
            st.session_state.new_customer = True

# =========================
# NEW CUSTOMER FORM
# =========================
if st.session_state.new_customer:
    st.warning("New Customer")

    first_name = st.text_input("First Name")
    last_name = st.text_input("Last Name")
    tier = st.selectbox("Tier", ["Gold", "Silver", "Bronze"])

    if st.button("Create Customer"):
        df = load_data()

        multiplier = tier_multiplier[tier]
        points = int((amount / 10) * multiplier)

        new_row = {
            "BarcodeID": barcode,
            "First Name": first_name,
            "Last Name": last_name,
            "Tier": tier,
            "Date Created": datetime.now(),
            "Store Credit": points,
            "Amount Bought": amount,
            "Last Visit": datetime.now()
        }

        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        save_data(df)

        st.success(f"Customer created! Points: {points}")

        # Reset state
        st.session_state.new_customer = False
