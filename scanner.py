# ID SCANNER
import pandas as pd
from datetime import datetime

FILE = r"D:\New folder\OneDrive\Personal file\CustomerSystem\1581customers.xlsx"
SHEET = "MYmfCustomers"


def load_data():
    try:
        df = pd.read_excel(FILE, sheet_name=SHEET, dtype=str)
        df["BarcodeID"] = df["BarcodeID"].astype(str).str.strip()
        return df
    except FileNotFoundError:
        return pd.DataFrame(columns=[
            "BarcodeID", "First Name", "Last Name", "ID Number",
            "Tier", "Date Created", "Store Credit",
            "Amount Bought", "Last Visit", "Notes"
        ])


def save_data(df):
    print("Saving to:", FILE)
    with pd.ExcelWriter(FILE, engine="openpyxl", mode="w") as writer:
        df.to_excel(writer, sheet_name=SHEET, index=False)


def update_or_create(barcode):
    df = load_data()
    barcode = barcode.strip()

    match = df[df["BarcodeID"] == barcode]

    try:
        amount = float(input("Enter amount spent: $"))
    except:
        amount = 0

    tier_multiplier = {
        "Gold": 3,
        "Silver": 2,
        "Bronze": 1
    }

    # =========================
    # EXISTING CUSTOMER
    # =========================
    if not match.empty:
        print("Customer found. Updating record...")

        tier = match["Tier"].values[0]
        multiplier = tier_multiplier.get(tier, 1)

        points = int((amount / 10) * multiplier)
        print(f"Points earned: {points}")

        # Update last visit
        df.loc[df["BarcodeID"] == barcode, "Last Visit"] = datetime.now()

        # Update amount bought
        current_amount = df.loc[df["BarcodeID"] == barcode, "Amount Bought"].values[0]
        current_amount = float(current_amount) if current_amount else 0
        df.loc[df["BarcodeID"] == barcode, "Amount Bought"] = current_amount + amount

        # Update store credit
        current_points = df.loc[df["BarcodeID"] == barcode, "Store Credit"].values[0]
        current_points = float(current_points) if current_points else 0
        df.loc[df["BarcodeID"] == barcode, "Store Credit"] = current_points + points

    # NEW CUSTOMER
    else:
        print("New customer. Creating record...")

        first_name = input("Enter First Name: ").strip()
        last_name = input("Enter Last Name: ").strip()

        tier = input("Enter Tier (Gold / Silver / Bronze): ").strip().capitalize()

        if tier not in ["Gold", "Silver", "Bronze"]:
            print("Invalid tier. Defaulting to Bronze.")
            tier = "Bronze"
# CHANGE THE MULTIPLIER
        multiplier = tier_multiplier[tier]
        points = int((amount / 10) * multiplier)

        print(f"Points earned: {points}")

        new_row = {
            "BarcodeID": barcode,
            "First Name": first_name,
            "Last Name": last_name,
            "ID Number": "",
            "Tier": tier,
            "Date Created": datetime.now(),
            "Store Credit": points,
            "Amount Bought": amount,
            "Last Visit": datetime.now(),
            "Notes": ""
        }

        df.loc[len(df)] = new_row

    save_data(df)
    print("Saved successfully.")


def main():
    print("Ready to scan... (Ctrl+C to stop)")

    while True:
        barcode = input("Scan Barcode: ").strip()
        if barcode:
            update_or_create(barcode)


if __name__ == "__main__":
    main()
