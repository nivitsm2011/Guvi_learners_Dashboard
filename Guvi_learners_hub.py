import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import date

st.set_page_config(layout="wide")  # ✅ enables wide mode


engine = create_engine("postgresql://postgres:1234@localhost:5432/minipro")


def run_query(query, params=None):
    """Handles both SELECT and DML queries"""
    with engine.connect() as conn:
        result = conn.execute(text(query), params or {})
        try:
            # For SELECT queries
            return pd.DataFrame(result.fetchall(), columns=result.keys())
        except Exception:
            # For INSERT/UPDATE/DELETE queries
            conn.commit()
            return None


# Initialize session state for login tracking
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.username = None

# Inititalising side bar fucntions


def customer_sales_form():
    st.subheader("➕ Add New Customer Sale")

    branch_mapping = {
        1: "Chennai",
        2: "Bangalore",
        3: "Hyderabad",
        4: "Delhi",
        5: "Mumbai",
        6: "Pune",
        7: "Kolkata",
        8: "Ahmedabad",
    }

    branch_name = st.selectbox("Select Branch", list(branch_mapping.values()))
    branch_id = [bid for bid, bname in branch_mapping.items() if bname == branch_name][
        0
    ]

    with st.form("customer_form"):
        customer_name = st.text_input("Student Name")
        mobile_number = st.text_input("Mobile Number")
        product_name = st.radio(
            "Select Product", ["DS", "BA", "DA", "FSD", "ML", "AI", "BI", "SQL"]
        )
        sale_date = st.date_input("Sale Date", date.today())
        gross_sales = st.number_input("Gross Sales", min_value=0.0)
        status = st.selectbox("Status", ["Open", "Close"])

        submitted = st.form_submit_button("Save Entry")

        if submitted:
            if not customer_name or not mobile_number:
                st.error("⚠️ All fields are required.")
            elif not mobile_number.isdigit() or len(mobile_number) != 10:
                st.error("⚠️ Mobile number must be exactly 10 digits.")
            else:
                try:
                    # ✅ Correct column names + commit
                    with engine.begin() as conn:
                        conn.execute(
                            text("""
                                INSERT INTO customer_sales 
                                (branch_id, sale_date, customer_name, mobile_number, product_name, gross_sales, status)
                                VALUES (:branch_id, :sale_date, :customer_name, :mobile_number, :product_name, :gross_sales, :status)
                            """),
                            {
                                "branch_id": branch_id,
                                "sale_date": sale_date,
                                "customer_name": customer_name,
                                "mobile_number": mobile_number,
                                "product_name": product_name,
                                "gross_sales": gross_sales,
                                "status": status,
                            },
                        )
                    st.success(f"✅ Sale entry added for {branch_name} branch!")

                    # Show updated table
                    df_sales = run_query(
                        "SELECT * FROM customer_sales ORDER BY sale_id;"
                    )
                    st.dataframe(df_sales)
                except Exception as e:
                    st.error(f"Error saving data: {e}")


# -------------------------------


def customer_sales_filter():
    st.title("📊 Students Dashboard & Reports")
    st.subheader("Filter Controls")

    # Branch filter
    branch_mapping = {
        1: "Chennai",
        2: "Bangalore",
        3: "Hyderabad",
        4: "Delhi",
        5: "Mumbai",
        6: "Pune",
        7: "Kolkata",
        8: "Ahmedabad",
    }
    branch_name = st.selectbox("Branch Name", list(branch_mapping.values()))
    branch_id = [bid for bid, bname in branch_mapping.items() if bname == branch_name][
        0
    ]

    # Product filter
    product_filter = st.multiselect(
        "Product Name", ["DS", "BA", "DA", "FSD", "ML", "AI", "BI", "SQL"]
    )

    # Date filters
    start_date = st.date_input("Start Date", pd.to_datetime("2000-01-01"))
    end_date = st.date_input("End Date", pd.to_datetime("today"))

    try:
        df_sales = run_query("SELECT * FROM customer_sales ORDER BY sale_id;")
        if df_sales is not None and not df_sales.empty:
            df_sales["sale_date"] = pd.to_datetime(df_sales["sale_date"])

            # Apply filters
            df_filtered = df_sales[
                (df_sales["branch_id"] == branch_id)
                & (df_sales["sale_date"] >= pd.to_datetime(start_date))
                & (df_sales["sale_date"] <= pd.to_datetime(end_date))
            ]

            if product_filter:
                df_filtered = df_filtered[
                    df_filtered["product_name"].isin(product_filter)
                ]

            # --- Financial Summary BEFORE table ---
            if not df_filtered.empty:
                total_revenue = df_filtered["gross_sales"].sum()
                total_received = (
                    df_filtered["received_amount"].sum()
                    if "received_amount" in df_filtered.columns
                    else 0
                )
                total_pending = (
                    df_filtered["pending_amount"].sum()
                    if "pending_amount" in df_filtered.columns
                    else (total_revenue - total_received)
                )
                pending_pct = (
                    (total_pending / total_revenue * 100) if total_revenue > 0 else 0
                )

                st.subheader("💰 Financial Summary")

                # Divide into 4 equal columns across full width

                col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

                with col1:
                    st.metric("Overall Revenue (Gross)", f"₹{total_revenue:,.2f}")
                with col2:
                    st.metric("Total Received Amount", f"₹{total_received:,.2f}")
                with col3:
                    st.metric("Total Pending Amount", f"₹{total_pending:,.2f}")
                with col4:
                    st.metric("Pending Collection %", f"{pending_pct:.1f}%")

            # --- Full filtered customer database (end-to-end width) ---
            st.subheader(
                f"📋 Filtered Customer Database for {branch_name} between {start_date} and {end_date}"
            )

            st.dataframe(df_filtered, use_container_width=True)

            if df_filtered.empty:
                st.warning("⚠️ No records match your filters.")
        else:                           
            st.warning("No sales data found.")
    except Exception as e:
        st.error(f"Error fetching data: {e}")


# -------------------------------


def payment_entry_form():
    st.subheader("💳 Add Payment Entry")

    with st.form("payment_form"):
        sale_id = st.number_input("Sale ID", min_value=1, step=1)
        payment_date = st.date_input("Payment Date", date.today())
        amount_paid = st.number_input("Amount Paid", min_value=0.0, format="%.2f")
        payment_method = st.selectbox(
            "Payment Method", ["Cash", "Card", "UPI", "Bank Transfer"]
        )

        submitted = st.form_submit_button("Save Payment")

        if submitted:
            if amount_paid <= 0:
                st.error("⚠️ Amount must be greater than 0.")
            else:
                try:
                    with engine.begin() as conn:
                        conn.execute(
                            text("""
                                INSERT INTO payment_splits (sale_id, payment_date, amount_paid, payment_method)
                                VALUES (:sale_id, :payment_date, :amount_paid, :payment_method)
                            """),
                            {
                                "sale_id": sale_id,
                                "payment_date": payment_date,
                                "amount_paid": amount_paid,
                                "payment_method": payment_method,
                            },
                        )
                    st.success(
                        f"✅ Payment of ₹{amount_paid:,.2f} recorded for Sale ID {sale_id}!"
                    )

                    # Show updated payments table
                    df_payments = run_query(
                        "SELECT * FROM payment_splits ORDER BY payment_id;"
                    )
                    st.dataframe(df_payments, use_container_width=True)
                except Exception as e:
                    st.error(f"Error saving payment: {e}")

# -------------------------------

SQL_QUESTIONS = {
    # 🔹 Basic Queries
    "Retrieve all records from customer_sales": "SELECT * FROM customer_sales;",
    "Retrieve all records from branches": "SELECT * FROM branches;",
    "Retrieve all records from payment_splits": "SELECT * FROM payment_splits;",
    "Display all sales with status = 'Open'": "SELECT * FROM customer_sales WHERE status = 'Open';",
    "Retrieve all sales belonging to Chennai branch": "SELECT * FROM customer_sales WHERE branch_id = 1;",
    # 🔹 Aggregation Queries
    "Total gross sales across all branches": "SELECT SUM(gross_sales) AS total_gross_sales FROM customer_sales;",
    "Total received amount across all sales": "SELECT SUM(received_amount) AS total_received FROM customer_sales;",
    "Total pending amount across all sales": "SELECT SUM(pending_amount) AS total_pending FROM customer_sales;",
    "Count total number of sales per branch": "SELECT branch_id, COUNT(*) AS total_sales FROM customer_sales GROUP BY branch_id;",
    "Average gross sales amount": "SELECT AVG(gross_sales) AS avg_sales FROM customer_sales;",
    # 🔹 Join-Based Queries
    "Sales details with branch name": """
        SELECT cs.*, b.branch_name 
        FROM customer_sales cs 
        JOIN branches b ON cs.branch_id = b.branch_id;
    """,
    "Sales details with total payment received": """
        SELECT cs.sale_id, cs.customer_name, SUM(ps.amount_paid) AS total_payment
        FROM customer_sales cs
        LEFT JOIN payment_splits ps ON cs.sale_id = ps.sale_id
        GROUP BY cs.sale_id, cs.customer_name;
    """,
    "Branch-wise total gross sales": """
        SELECT b.branch_name, SUM(cs.gross_sales) AS total_sales
        FROM customer_sales cs
        JOIN branches b ON cs.branch_id = b.branch_id
        GROUP BY b.branch_name;
    """,
    "Sales with payment method used": """
        SELECT cs.sale_id, cs.customer_name, ps.payment_method, ps.amount_paid
        FROM customer_sales cs
        JOIN payment_splits ps ON cs.sale_id = ps.sale_id;
    """,
    "Sales with branch admin name": """
        SELECT cs.sale_id, cs.customer_name, b.branch_admin_name
        FROM customer_sales cs
        JOIN branches b ON cs.branch_id = b.branch_id;
    """,
    # 🔹 Financial Tracking Queries
    "Sales with pending amount > 5000": "SELECT * FROM customer_sales WHERE pending_amount > 5000;",
    "Top 3 highest gross sales": "SELECT * FROM customer_sales ORDER BY gross_sales DESC LIMIT 3;",
    "Branch with highest total gross sales": """
        SELECT b.branch_name, SUM(cs.gross_sales) AS total_sales
        FROM customer_sales cs
        JOIN branches b ON cs.branch_id = b.branch_id
        GROUP BY b.branch_name
        ORDER BY total_sales DESC LIMIT 1;
    """,
    "Monthly sales summary": """
        SELECT DATE_TRUNC('month', sale_date) AS month, SUM(gross_sales) AS total_sales
        FROM customer_sales
        GROUP BY month
        ORDER BY month;
    """,
    "Payment method-wise total collection": """
        SELECT payment_method, SUM(amount_paid) AS total_collection
        FROM payment_splits
        GROUP BY payment_method;
    """,
}
# -------------------------------


def customer_sales_form_branch(branch_id, branch_name):
    st.subheader(f"➕ Add New Customer Sale ({branch_name})")

    with st.form("customer_form"):
        customer_name = st.text_input("Customer Name")
        mobile_number = st.text_input("Mobile Number")
        product_name = st.radio(
            "Select Product", ["DS", "BA", "DA", "FSD", "ML", "AI", "BI", "SQL"]
        )
        sale_date = st.date_input("Sale Date", date.today())
        gross_sales = st.number_input("Gross Sales", min_value=0.0)
        status = st.selectbox("Status", ["Open", "Close"])

        submitted = st.form_submit_button("Save Entry")

        if submitted:
            if not customer_name or not mobile_number:
                st.error("⚠️ All fields are required.")
            elif not mobile_number.isdigit() or len(mobile_number) != 10:
                st.error("⚠️ Mobile number must be exactly 10 digits.")
            else:
                try:
                    with engine.begin() as conn:
                        conn.execute(
                            text("""
                                INSERT INTO customer_sales 
                                (branch_id, sale_date, customer_name, mobile_number, product_name, gross_sales, status)
                                VALUES (:branch_id, :sale_date, :customer_name, :mobile_number, :product_name, :gross_sales, :status)
                            """),
                            {
                                "branch_id": branch_id,
                                "sale_date": sale_date,
                                "customer_name": customer_name,
                                "mobile_number": mobile_number,
                                "product_name": product_name,
                                "gross_sales": gross_sales,
                                "status": status,
                            },
                        )
                    st.success(f"✅ Sale entry added for {branch_name} branch!")

                    # Show updated sales table for this branch only
                    df_sales = run_query(
                        "SELECT * FROM customer_sales WHERE branch_id = :branch_id ORDER BY sale_id;",
                        {"branch_id": branch_id},
                    )
                    st.dataframe(df_sales, use_container_width=True)
                except Exception as e:
                    st.error(f"Error saving data: {e}")

# -------------------------------

def payment_entry_form_branch(branch_id, branch_name):
    st.subheader(f"💳 Add Payment Entry ({branch_name})")

    with st.form("payment_form"):
        sale_id = st.number_input("Sale ID", min_value=1, step=1)
        payment_date = st.date_input("Payment Date", date.today())
        amount_paid = st.number_input("Amount Paid", min_value=0.0, format="%.2f")
        payment_method = st.selectbox("Payment Method", ["Cash", "Card", "UPI", "Bank Transfer"])

        submitted = st.form_submit_button("Save Payment")

        if submitted:
            if amount_paid <= 0:
                st.error("⚠️ Amount must be greater than 0.")
            else:
                try:
                    # Insert payment record
                    with engine.begin() as conn:
                        conn.execute(
                            text("""
                                INSERT INTO payment_splits (sale_id, payment_date, amount_paid, payment_method)
                                VALUES (:sale_id, :payment_date, :amount_paid, :payment_method)
                            """),
                            {
                                "sale_id": sale_id,
                                "payment_date": payment_date,
                                "amount_paid": amount_paid,
                                "payment_method": payment_method,
                            },
                        )

                    st.success(f"✅ Payment of ₹{amount_paid:,.2f} recorded for Sale ID {sale_id} in {branch_name} branch!")

                    # Show updated payments table for this branch only
                    df_payments = run_query("""
                        SELECT ps.* 
                        FROM payment_splits ps
                        JOIN customer_sales cs ON ps.sale_id = cs.sale_id
                        WHERE cs.branch_id = :branch_id
                        ORDER BY ps.payment_id;
                    """, {"branch_id": branch_id})

                    st.dataframe(df_payments, use_container_width=True)
                except Exception as e:
                    st.error(f"Error saving payment: {e}")

# -------------------------------


def customer_sales_filter_branch(branch_id, branch_name):
    st.title(f"📊 {branch_name} Enrollment Dashboard")
    st.subheader("Filter Controls")

    # Product filter
    product_filter = st.multiselect(
        "Product Name", ["DS", "BA", "DA", "FSD", "ML", "AI", "BI", "SQL"]
    )

    # Date filters
    start_date = st.date_input("Start Date", pd.to_datetime("2020-01-01"))
    end_date = st.date_input("End Date", pd.to_datetime("today"))

    try:
        # ✅ Only fetch sales for this branch
        df_sales = run_query(
            "SELECT * FROM customer_sales WHERE branch_id = :branch_id ORDER BY sale_id;",
            {"branch_id": branch_id},
        )

        if df_sales is not None and not df_sales.empty:
            df_sales["sale_date"] = pd.to_datetime(df_sales["sale_date"])

            # Apply date filter
            df_filtered = df_sales[
                (df_sales["sale_date"] >= pd.to_datetime(start_date))
                & (df_sales["sale_date"] <= pd.to_datetime(end_date))
            ]

            # Apply product filter
            if product_filter:
                df_filtered = df_filtered[
                    df_filtered["product_name"].isin(product_filter)
                ]

            # --- Financial Summary ---
            if not df_filtered.empty:
                total_revenue = df_filtered["gross_sales"].sum()
                total_received = (
                    df_filtered["received_amount"].sum()
                    if "received_amount" in df_filtered.columns
                    else 0
                )
                total_pending = (
                    df_filtered["pending_amount"].sum()
                    if "pending_amount" in df_filtered.columns
                    else (total_revenue - total_received)
                )
                pending_pct = (
                    (total_pending / total_revenue * 100) if total_revenue > 0 else 0
                )

                st.subheader("💰 Financial Summary")
                col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
                with col1:
                    st.metric("Overall Revenue (Gross)", f"₹{total_revenue:,.2f}")
                with col2:
                    st.metric("Total Received Amount", f"₹{total_received:,.2f}")
                with col3:
                    st.metric("Total Pending Amount", f"₹{total_pending:,.2f}")
                with col4:
                    st.metric("Pending Collection %", f"{pending_pct:.1f}%")

            # --- Filtered Table ---
            st.subheader(
                f"📋 Filtered Customer Database for {branch_name}"
            )
            st.dataframe(df_filtered, width="stretch")

            if df_filtered.empty:
                st.warning("⚠️ No records match your filters.")
        else:
            st.warning("No sales data found for this branch.")
    except Exception as e:
        st.error(f"Error fetching data: {e}")


# -------------------------------


def sql_question_runner_branch(branch_id, branch_name):
    st.subheader(f"🗄️ SQL Question Bank ({branch_name})")

    selected_question = st.selectbox(
        "Choose a SQL Question", list(SQL_QUESTIONS.keys())
    )
    query = SQL_QUESTIONS[selected_question]

    # 🔒 Restrict queries to this branch
    # If the query references customer_sales, wrap it with a branch filter
    if "customer_sales" in query.lower():
        query = query.replace(
            "customer_sales",
            f"(SELECT * FROM customer_sales WHERE branch_id = {branch_id}) AS customer_sales",
        )

    st.write("📜 Selected Query:")
    st.code(query, language="sql")

    # Orange styled Execute button
    st.markdown(
        """
        <style>
        div.stButton > button:first-child {
            background-color: orange;
            color: white;
            font-weight: bold;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    if st.button("🚀 Execute Query"):
        try:
            df_result = run_query(query)
            if df_result is not None and not df_result.empty:
                st.success(f"✅ Query executed successfully for {branch_name} branch!")
                st.dataframe(df_result, use_container_width=True)
            else:
                st.warning("⚠️ Query returned no results.")
        except Exception as e:
            st.error(f"Error executing query: {e}")

# -------------------------------


def branch_dashboard(branch_id, branch_name):
    st.title("📚 Guvi Learners Dashboard")
    st.write(f"Welcome Admin {branch_name}! (Branch ID {branch_id})")

    action = st.sidebar.radio(
        "Choose Action",
        [
            "View Sales Table",
            "New Form",
            "Filter Reports",
            "New Payment",
            "SQL Questions",
        ],
    )

    if action == "View Sales Table":
        df_sales = run_query(
            "SELECT * FROM customer_sales WHERE branch_id = :branch_id ORDER BY sale_id;",
            {"branch_id": branch_id},
        )
        st.dataframe(df_sales, width="stretch")

    elif action == "New Form":
        customer_sales_form_branch(branch_id, branch_name)

    elif action == "Filter Reports":
        customer_sales_filter_branch(branch_id, branch_name)

    elif action == "New Payment":
        payment_entry_form_branch(branch_id, branch_name)

    elif action == "SQL Questions":
        sql_question_runner_branch(branch_id, branch_name)


# -------------------------------


def sql_question_runner():
    st.subheader("🗄️ Live SQL Business Analytics Engine")

    selected_question = st.selectbox(
        "Choose a SQL Question", list(SQL_QUESTIONS.keys())
    )
    query = SQL_QUESTIONS[selected_question]

    st.write("📜 Executing Query:")
    st.code(query, language="sql")

    execute = st.markdown(
        """
        <style>
        div.stButton > button:first-child {
            background-color: orange;
            color: white;
            font-weight: bold;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    if st.button("🚀 Execute Live Analysis"):
        try:
            df_result = run_query(query)
            if df_result is not None and not df_result.empty:
                st.success("✅ Query executed successfully!")
                st.dataframe(df_result, width="stretch")
            else:
                st.warning("⚠️ Query returned no results.")
        except Exception as e:
            st.error(f"Error executing query: {e}")


# -------------------------------


# --- UNIQUE DASHBOARD FUNCTIONS ---
def dashboard_1():
    st.title("📚 Guvi Learners dashboard ")
    st.write("Welcome Super Admin!.")

    # ✅ Add "Reports" to the sidebar radio
    action = st.sidebar.radio(
        "Choose Action", ["View Sales Table", "New Form", "Filter Reports","New Payment Form","SQL Live Analytics"]
    )

    if action == "View Sales Table":
        try:
            df_sales = run_query("SELECT * FROM customer_sales ORDER BY sale_id;")
            st.dataframe(df_sales,use_container_width=True)
        except Exception as e:
            st.error(f"Error fetching data: {e}")

    elif action == "New Form":
        customer_sales_form()

    elif action == "Filter Reports":
        customer_sales_filter()  # ✅ call the separate filter function

    elif action == "New Payment Form":
        payment_entry_form()  # ✅ Call the new payment form

    elif action == "SQL Live Analytics":
        sql_question_runner()


def dashboard_2():
    branch_dashboard(1, "Chennai")


def dashboard_3():
    branch_dashboard(2, "Bangalore")


def dashboard_4():
    branch_dashboard(3, "Hyderabad")


def dashboard_5():
    branch_dashboard(4, "Delhi")


def dashboard_6():
    branch_dashboard(5, "Mumbai")


def dashboard_7():
    branch_dashboard(6, "Pune")


def dashboard_8():
    branch_dashboard(7, "Kolkata")


def dashboard_9():
    branch_dashboard(8, "Ahmedabad")


# --- LOGIN SCREEN ---
def login_page():
    st.title(" 📚 WElCOME TO GUVI LEARNERS DASHBOARD")
    st.subheader("LOGIN TO ENTER YOUR DASHBOARD")

    username_input = st.text_input("Username")
    password_input = st.text_input("Password", type="password")

    if st.button("Login"):
        # Fetch user details safely using query parameters to avoid SQL injection
        query = "SELECT user_id, username, password FROM users WHERE username = :user"
        df = run_query(query, params={"user": username_input})

        if not df.empty:
            db_password = df.iloc[0]["password"]
            newuser_id = df.iloc[0]["user_id"]

            # Simple direct match (For production, use libraries like bcrypt to check hashed passwords)
            if password_input == db_password:
                st.session_state.logged_in = True
                st.session_state.user_id = newuser_id
                st.session_state.username = username_input
                st.rerun()
            else:
                st.error("Incorrect password.")
        else:
            st.error("User not found.")

# --- MAIN APP LOGIC ---
if not st.session_state.logged_in:
    login_page()
else:
    # Sidebar navigation & logout option
    st.sidebar.write(f"Logged in as: **{st.session_state.username}**")
    if st.sidebar.button("Log Out"):
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.username = None
        st.rerun()

    # Route to the correct dashboard based on User ID
    current_user = st.session_state.user_id

    if current_user == 1:
        dashboard_1()
           
    elif current_user == 2:
        dashboard_2()
    elif current_user == 3:
        dashboard_3()
    elif current_user == 4:
        dashboard_4()
    elif current_user == 5:
        dashboard_5()
    elif current_user == 6:
        dashboard_6()
    elif current_user == 7:
        dashboard_7()
    elif current_user == 8:
        dashboard_8()
    elif current_user == 9:
        dashboard_9()
    else:
        st.error("please enter a valid user ID and Password")
