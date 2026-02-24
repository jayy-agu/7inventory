# ============================================================
# INVENTORY MANAGEMENT SYSTEM
# Tech Stack: Python, Streamlit, SQLite
# ============================================================

import streamlit as st
import sqlite3
import pandas as pd


# We create the database and table if they don't exist yet.ru

def init_db():
    conn = sqlite3.connect("inventory.db")

    # cursor() lets us send SQL commands to the database
    cursor = conn.cursor()

    # CREATE TABLE IF NOT EXISTS = make this table only if it's not already there
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS inventory
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       name
                       TEXT
                       NOT
                       NULL,
                       category
                       TEXT,
                       quantity
                       INTEGER,
                       low_stock_threshold
                       INTEGER,
                       price
                       REAL
                   )
                   """)

    # Save (commit) the changes to the database file
    conn.commit()

    # Close the connection
    conn.close()


# These are small reusable functions that work in the database.
# Each one opens a connection, does one job, then closes it

def get_all_items():
    """Fetch every product from the database and return as a DataFrame"""
    conn = sqlite3.connect("inventory.db")

    df = pd.read_sql_query("SELECT * FROM inventory", conn)

    conn.close()
    return df  # Returns a table-like object Streamlit can display


def add_item(name, category, quantity, threshold, price):
    """Insert a new product into the database."""
    conn = sqlite3.connect("inventory.db")
    cursor = conn.cursor()

    # INSERT INTO adds a new row
    cursor.execute("""
                   INSERT INTO inventory (name, category, quantity, low_stock_threshold, price)
                   VALUES (?, ?, ?, ?, ?)
                   """, (name, category, quantity, threshold, price))

    conn.commit()
    conn.close()


def update_quantity(item_id, new_quantity):
    """Change the stock quantity of an existing product."""
    conn = sqlite3.connect("inventory.db")
    cursor = conn.cursor()

    cursor.execute("""
                   UPDATE inventory
                   SET quantity = ?
                   WHERE id = ?
                   """, (new_quantity, item_id))

    conn.commit()
    conn.close()


def delete_item(item_id):
    """Remove a product from the database"""
    conn = sqlite3.connect("inventory.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM inventory WHERE id = ?", (item_id,))

    conn.commit()
    conn.close()


def get_low_stock_items(df):
    """
    Filter the DataFrame to only show items that are low on stock.
    """

    return df[df["quantity"] <= df["low_stock_threshold"]]


# This is where we build the visual interface.

def main():
    st.set_page_config(
        page_title="Group 7's Inventory Manager",
        page_icon="7️⃣📦",
        layout="wide"
    )
    st.markdown("""
        <style>
        /* Style the main app background */
        .stApp {
            background-color: #f0f4f8;
        }
        /* Style metric boxes (the summary cards at the top) */
        .metric-card {
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            text-align: center;
        }
        /* Low stock warning badge style */
        .low-stock-badge {
            background: #fff3cd;
            border: 1px solid #ffc107;
            border-radius: 8px;
            padding: 10px 15px;
            color: #856404;
        }
        </style>
    """, unsafe_allow_html=True)

    # HEADER
    st.title("7️⃣📦 Group 7's Inventory Management System")
    st.markdown("*Track stock, manage products, and get low-stock alerts — all in one place.*")

    st.divider()

    # LOAD DATA

    init_db()

    df = get_all_items()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("🛍️ Total Products", len(df))

    with col2:
        total_stock = int(df["quantity"].sum()) if not df.empty else 0
        st.metric("📊 Total Stock Units", total_stock)

    with col3:
        low_stock_count = len(get_low_stock_items(df)) if not df.empty else 0
        st.metric("⚠️ Low Stock Alerts", low_stock_count)

    with col4:
        total_value = (df["price"] * df["quantity"]).sum() if not df.empty else 0
        st.metric("💰 Inventory Value", f"₦{total_value:,.2f}")

        st.divider()

    # LOW STOCK ALERTS

    if not df.empty:
       low_stock = get_low_stock_items(df)
       if not low_stock.empty:
            st.warning(f"⚠️ **{len(low_stock)} item(s) are low on stock!**")
            st.dataframe(
                low_stock[["name", "category", "quantity", "low_stock_threshold"]],
                use_container_width=True
            )
       else:
                st.success("✅ All items are sufficiently stocked!")

    st.divider()

    # SIDEBAR
    st.sidebar.header("➕ Add New Product")
    item_name = st.sidebar.text_input("Product Name")
    item_category = st.sidebar.selectbox(
            "Category",
            ["Electronics", "Food & Beverage", "Clothing", "Office Supplies",
             "Health & Beauty", "Tools & Hardware", "Other"]
        )
    item_quantity = st.sidebar.number_input("Initial Quantity", min_value=0, value=0)
    item_threshold = st.sidebar.number_input("Low Stock Alert Threshold", min_value=0, value=7)
    item_price = st.sidebar.number_input("Price per Unit (₦)", min_value=0.0, value=0.0, step=0.01)

    if st.sidebar.button("Add Product", type="primary"):
            if item_name.strip() == "":
                st.sidebar.error("❌ Product name cannot be empty!")
            else:
                add_item(item_name, item_category, item_quantity, item_threshold, item_price)
                st.sidebar.success(f"✅ '{item_name}' added successfully!")
                st.rerun()

        # MAIN TABLE
    st.subheader("📋 All Inventory Items")
    if df.empty:
            st.info("No products yet. Use the sidebar to add your first product!")
    else:
            st.dataframe(df, use_container_width=True)

    st.divider()

    # UPDATE STOCKS
    st.subheader("🔄 Update Stock Quantity")
    if not df.empty:
            item_options = {f"{row['id']} - {row['name']}": row['id'] for _, row in df.iterrows()}
            selected_label = st.selectbox("Select Product to Update", list(item_options.keys()))
            selected_id = item_options[selected_label]
            new_qty = st.number_input("New Quantity", min_value=0, value=0)
            if st.button("Update Quantity"):
                update_quantity(selected_id, new_qty)
                st.success(f"✅ Quantity updated to {new_qty}!")
                st.rerun()
    else:
            st.info("Add products first to update their stock.")

    st.divider()

    # DELETE A PRODUCT
    st.subheader("🗑️ Delete a Product")
    if not df.empty:
            del_options = {f"{row['id']} - {row['name']}": row['id'] for _, row in df.iterrows()}
            del_label = st.selectbox("Select Product to Delete", list(del_options.keys()), key="del_select")
            if st.button("Delete Product", type="secondary"):
                delete_item(del_options[del_label])
                st.success("🗑️ Product deleted.")
                st.rerun()
    else:
            st.info("No products to delete.")

        # SEARCH & FILTER
    st.divider()
    st.subheader("🔍 Search & Filter Inventory")
    if not df.empty:
            search_col, filter_col = st.columns(2)
            with search_col:
                search_term = st.text_input("Search by product name")
            with filter_col:
                categories = ["All"] + list(df["category"].unique())
                selected_category = st.selectbox("Filter by Category", categories)

            filtered_df = df.copy()
            if search_term:
                filtered_df = filtered_df[
                    filtered_df["name"].str.contains(search_term, case=False, na=False)
                ]
            if selected_category != "All":
                filtered_df = filtered_df[filtered_df["category"] == selected_category]

            st.dataframe(filtered_df, use_container_width=True)
            st.caption(f"Showing {len(filtered_df)} of {len(df)} products")
    else:
            st.info("Add products to use search and filter.")

if __name__ == "__main__":
        main()