# ============================================================
# INVENTORY MANAGEMENT SYSTEM
# Tech Stack: Python, Streamlit, SQLite
# Beginner-Friendly Version
# ============================================================

# --- IMPORTS ---
import streamlit as st   # Streamlit: turns Python scripts into web apps
import sqlite3           # SQLite: a lightweight built-in database (no server needed)
import pandas as pd      # Pandas: helps display data as nice tables


# ============================================================
# SECTION 1: DATABASE SETUP
# We create the database and table if they don't exist yet.
# This runs every time the app starts, but CREATE IF NOT EXISTS
# means it won't overwrite existing data.
# ============================================================

def init_db():
    # sqlite3.connect() creates a database file called 'inventory.db'
    # If the file doesn't exist, SQLite creates it automatically
    conn = sqlite3.connect("inventory.db")

    # cursor() lets us send SQL commands to the database
    cursor = conn.cursor()

    # CREATE TABLE IF NOT EXISTS = make this table only if it's not already there
    # Each line inside is a column with its data type:
    #   id INTEGER PRIMARY KEY AUTOINCREMENT = unique ID, auto-assigned
    #   name TEXT NOT NULL                   = product name, can't be empty
    #   category TEXT                        = e.g. "Electronics", "Food"
    #   quantity INTEGER                     = how many units in stock
    #   low_stock_threshold INTEGER          = alert if quantity drops below this
    #   price REAL                           = price per unit (REAL = decimal number)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            quantity INTEGER,
            low_stock_threshold INTEGER,
            price REAL
        )
    """)

    # Save (commit) the changes to the database file
    conn.commit()

    # Close the connection — good practice to free resources
    conn.close()


# ============================================================
# SECTION 2: DATABASE HELPER FUNCTIONS
# These are small reusable functions that talk to the database.
# Each one opens a connection, does one job, then closes it.
# ============================================================

def get_all_items():
    """Fetch every product from the database and return as a DataFrame."""
    conn = sqlite3.connect("inventory.db")

    # pd.read_sql_query() runs a SQL query and puts the result in a pandas DataFrame
    # "SELECT * FROM inventory" = get all columns from all rows
    df = pd.read_sql_query("SELECT * FROM inventory", conn)

    conn.close()
    return df  # Returns a table-like object Streamlit can display nicely


def add_item(name, category, quantity, threshold, price):
    """Insert a new product into the database."""
    conn = sqlite3.connect("inventory.db")
    cursor = conn.cursor()

    # INSERT INTO adds a new row
    # The ? marks are placeholders — safer than putting values directly in the string
    # (prevents SQL injection, a common security issue)
    cursor.execute("""
        INSERT INTO inventory (name, category, quantity, low_stock_threshold, price)
        VALUES (?, ?, ?, ?, ?)
    """, (name, category, quantity, threshold, price))
    # The tuple (name, category, ...) fills in the ? placeholders in order

    conn.commit()
    conn.close()


def update_quantity(item_id, new_quantity):
    """Change the stock quantity of an existing product."""
    conn = sqlite3.connect("inventory.db")
    cursor = conn.cursor()

    # UPDATE changes data in existing rows
    # WHERE id = ? makes sure we only update the specific product we want
    cursor.execute("""
        UPDATE inventory SET quantity = ? WHERE id = ?
    """, (new_quantity, item_id))

    conn.commit()
    conn.close()


def delete_item(item_id):
    """Remove a product from the database permanently."""
    conn = sqlite3.connect("inventory.db")
    cursor = conn.cursor()

    # DELETE FROM removes the row where the id matches
    cursor.execute("DELETE FROM inventory WHERE id = ?", (item_id,))

    conn.commit()
    conn.close()


def get_low_stock_items(df):
    """
    Filter the DataFrame to only show items that are low on stock.
    An item is 'low stock' if its quantity <= its low_stock_threshold.
    """
    # Boolean indexing: keep rows where the condition is True
    return df[df["quantity"] <= df["low_stock_threshold"]]


# ============================================================
# SECTION 3: STREAMLIT UI
# This is where we build the visual interface.
# Streamlit reads the script top-to-bottom and renders each element.
# ============================================================

def main():
    # --- PAGE CONFIG ---
    # Must be the very first Streamlit call
    # Sets the browser tab title and layout
    st.set_page_config(
        page_title="Group 7's Inventory Manager",  # Browser tab title
        page_icon="7️⃣📦",                  # Emoji favicon
        layout="wide"                    # Use full width of the browser
    )

    # --- CUSTOM CSS ---
    # st.markdown() can inject raw HTML/CSS into the page
    # unsafe_allow_html=True is required to render actual HTML tags
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

    # --- HEADER ---
    st.title("7️⃣📦 Group 7's Inventory Management System")
    st.markdown("*Track stock, manage products, and get low-stock alerts — all in one place.*")

    # A horizontal divider line
    st.divider()

    # --- INITIALIZE DATABASE ---
    # Call our setup function so the DB/table exists before we do anything else
    init_db()

    # --- LOAD DATA ---
    # Fetch all inventory items into a DataFrame so we can use it throughout the page
    df = get_all_items()


    # ============================================================
    # SECTION 3A: SUMMARY METRICS (Top of page)
    # st.columns() creates side-by-side layout sections
    # ============================================================

    col1, col2, col3, col4 = st.columns(4)
    # col1..col4 are now 4 equal-width columns we can put content into

    with col1:
        # len(df) = total number of rows = total products
        st.metric("🛍️ Total Products", len(df))

    with col2:
        # .sum() adds up all values in the "quantity" column
        total_stock = int(df["quantity"].sum()) if not df.empty else 0
        st.metric("📊 Total Stock Units", total_stock)

    with col3:
        # Filter for low stock and count them
        low_stock_count = len(get_low_stock_items(df)) if not df.empty else 0
        st.metric("⚠️ Low Stock Alerts", low_stock_count)

    with col4:
        # Calculate total inventory value: price × quantity for each row, then sum
        total_value = (df["price"] * df["quantity"]).sum() if not df.empty else 0
        st.metric("💰 Inventory Value", f"${total_value:,.2f}")
        # f"${total_value:,.2f}" formats the number with commas and 2 decimal places


    st.divider()


    # ============================================================
    # SECTION 3B: LOW STOCK ALERTS
    # Show a warning box if any items are running low
    # ============================================================

    if not df.empty:
        low_stock = get_low_stock_items(df)

        if not low_stock.empty:
            # st.warning() shows a yellow warning box
            st.warning(f"⚠️ **{len(low_stock)} item(s) are low on stock!**")

            # Show just the important columns for the alert table
            st.dataframe(
                low_stock[["name", "category", "quantity", "low_stock_threshold"]],
                use_container_width=True  # Stretch table to full width
            )
        else:
            # st.success() shows a green success box
            st.success("✅ All items are sufficiently stocked!")


    st.divider()


    # ============================================================
    # SECTION 3C: SIDEBAR — ADD NEW PRODUCT
    # st.sidebar puts elements in a collapsible panel on the left
    # ============================================================

    st.sidebar.header("➕ Add New Product")

    # st.sidebar.text_input() = a text box in the sidebar
    # The string argument is the label shown above the input
    item_name = st.sidebar.text_input("Product Name")
    item_category = st.sidebar.selectbox(
        "Category",
        ["Electronics", "Food & Beverage", "Clothing", "Office Supplies",
         "Health & Beauty", "Tools & Hardware", "Other"]
    )
    # st.sidebar.number_input() = number field with up/down arrows
    # min_value stops the user from entering negative numbers
    item_quantity = st.sidebar.number_input("Initial Quantity", min_value=0, value=0)
    item_threshold = st.sidebar.number_input("Low Stock Alert Threshold", min_value=0, value=5)
    item_price = st.sidebar.number_input("Price per Unit ($)", min_value=0.0, value=0.0, step=0.01)
    # step=0.01 means the up/down arrow changes the value by $0.01

    # st.sidebar.button() = a clickable button; returns True when clicked
    if st.sidebar.button("Add Product", type="primary"):
        if item_name.strip() == "":
            # .strip() removes whitespace; warn if name is blank
            st.sidebar.error("❌ Product name cannot be empty!")
        else:
            # Call our helper function to save to the database
            add_item(item_name, item_category, item_quantity, item_threshold, item_price)
            st.sidebar.success(f"✅ '{item_name}' added successfully!")
            # st.rerun() refreshes the entire app so new data shows up immediately
            st.rerun()


    # ============================================================
    # SECTION 3D: MAIN TABLE — VIEW ALL INVENTORY
    # ============================================================

    st.subheader("📋 All Inventory Items")

    if df.empty:
        # st.info() shows a blue info box
        st.info("No products yet. Use the sidebar to add your first product!")
    else:
        # Display the full inventory table
        # use_container_width=True makes it fill the page width
        st.dataframe(df, use_container_width=True)


    st.divider()


    # ============================================================
    # SECTION 3E: UPDATE STOCK QUANTITY
    # Let the user pick a product and change its quantity
    # ============================================================

    st.subheader("🔄 Update Stock Quantity")

    if not df.empty:
        # Build a dictionary mapping "ID - Name" → ID for the dropdown
        # This makes the dropdown human-readable but still gives us the ID
        item_options = {f"{row['id']} - {row['name']}": row['id'] for _, row in df.iterrows()}
        # iterrows() loops through each row of the DataFrame as (index, row) pairs

        selected_label = st.selectbox("Select Product to Update", list(item_options.keys()))
        selected_id = item_options[selected_label]  # Get the numeric ID from our dict

        new_qty = st.number_input("New Quantity", min_value=0, value=0)

        if st.button("Update Quantity"):
            update_quantity(selected_id, new_qty)
            st.success(f"✅ Quantity updated to {new_qty}!")
            st.rerun()  # Refresh the page to show updated data
    else:
        st.info("Add products first to update their stock.")


    st.divider()


    # ============================================================
    # SECTION 3F: DELETE A PRODUCT
    # Remove a product permanently from the database
    # ============================================================

    st.subheader("🗑️ Delete a Product")

    if not df.empty:
        del_options = {f"{row['id']} - {row['name']}": row['id'] for _, row in df.iterrows()}

        del_label = st.selectbox("Select Product to Delete", list(del_options.keys()), key="del_select")
        # key="del_select" gives this widget a unique ID so Streamlit doesn't confuse
        # it with the selectbox in the Update section above

        if st.button("Delete Product", type="secondary"):
            delete_item(del_options[del_label])
            st.success("🗑️ Product deleted.")
            st.rerun()
    else:
        st.info("No products to delete.")


    # ============================================================
    # SECTION 3G: SEARCH & FILTER
    # ============================================================

    st.divider()
    st.subheader("🔍 Search & Filter Inventory")

    if not df.empty:
        # Two columns: one for search box, one for category filter
        search_col, filter_col = st.columns(2)

        with search_col:
            search_term = st.text_input("Search by product name")

        with filter_col:
            # Get unique categories that actually exist in the data
            # ["All"] + list(...) adds "All" as the first option
            categories = ["All"] + list(df["category"].unique())
            selected_category = st.selectbox("Filter by Category", categories)

        # Start with the full DataFrame, then apply filters one at a time
        filtered_df = df.copy()  # .copy() avoids modifying the original df

        if search_term:
            # .str.contains() checks if the name column contains the search term
            # case=False = case-insensitive
            filtered_df = filtered_df[
                filtered_df["name"].str.contains(search_term, case=False, na=False)
            ]

        if selected_category != "All":
            filtered_df = filtered_df[filtered_df["category"] == selected_category]

        st.dataframe(filtered_df, use_container_width=True)
        # Show how many results matched
        st.caption(f"Showing {len(filtered_df)} of {len(df)} products")
    else:
        st.info("Add products to use search and filter.")


# ============================================================
# ENTRY POINT
# This is standard Python: only run main() if this file is
# executed directly (not imported as a module).
# When you run: streamlit run inventory_app.py
# Python sets __name__ to "__main__", so main() gets called.
# ============================================================

if __name__ == "__main__":
    main()
