import streamlit as st
import pandas as pd
import sqlite3
import streamlit_authenticator as stauth
import plotly.express as px
from scipy import stats
import yaml
from yaml.loader import SafeLoader

# --- 1. USER AUTHENTICATION CONFIG ---
# In a production app, keep these in a separate config.yaml or secrets manager
names = ["Data Analyst", "Admin User"]
usernames = ["analyst", "admin"]
passwords = ["123", "456"] # In real use, use hashed passwords

hashed_passwords = stauth.Hasher(passwords).generate()

credentials = {"usernames": {}}
for i in range(len(usernames)):
    credentials["usernames"][usernames[i]] = {
        "name": names[i],
        "password": hashed_passwords[i]
    }

authenticator = stauth.Authenticate(
    credentials,
    "sales_dashboard",
    "auth_key",
    cookie_expiry_days=30
)

# Render Login Widget
name, authentication_status, username = authenticator.login('main')

# --- 2. DATABASE LOGIC ---
def init_db():
    conn = sqlite3.connect('sales_data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS sales 
                 (Region TEXT, Category TEXT, Sales REAL, Profit REAL, Order_Date DATE)''')
    conn.commit()
    return conn

def add_data(region, cat, sales, profit, date):
    conn = sqlite3.connect('sales_data.db')
    c = conn.cursor()
    c.execute("INSERT INTO sales VALUES (?, ?, ?, ?, ?)", (region, cat, sales, profit, date))
    conn.commit()
    conn.close()

# --- 3. THE APP CONTENT (Only visible if logged in) ---
if authentication_status:
    authenticator.logout('Logout', 'sidebar')
    st.title(f"Welcome, {name}")
    
    init_db()

    # --- DATA INPUT SECTION ---
    with st.expander("➕ Add New Sales Record"):
        with st.form("input_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                in_region = st.selectbox("Region", ["North", "South", "East", "West"])
                in_cat = st.selectbox("Category", ["Electronics", "Furniture", "Clothing", "Groceries"])
                in_date = st.date_input("Order Date")
            with col2:
                in_sales = st.number_input("Sales Amount", min_value=0.0)
                in_profit = st.number_input("Profit Amount")
            
            submit = st.form_submit_button("Save to Database")
            if submit:
                add_data(in_region, in_cat, in_sales, in_profit, in_date)
                st.success("Record saved successfully!")

    # --- DATA LOADING & VISUALIZATION ---
    conn = sqlite3.connect('sales_data.db')
    df = pd.read_sql_query("SELECT * FROM sales", conn)
    conn.close()

    if not df.empty:
        # Sidebar Filters
        st.sidebar.header("Dashboard Filters")
        sel_region = st.sidebar.multiselect("Region", df['Region'].unique(), default=df['Region'].unique())
        
        filtered_df = df[df['Region'].isin(sel_region)]

        # KPIs
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Sales", f"${filtered_df['Sales'].sum():,.2f}")
        m2.metric("Total Profit", f"${filtered_df['Profit'].sum():,.2f}")
        m3.metric("Entry Count", len(filtered_df))

        # Dynamic Chart
        st.subheader("Sales Distribution by Category")
        fig = px.bar(filtered_df, x='Category', y='Sales', color='Region', barmode='group')
        st.plotly_chart(fig, use_container_width=True)

        # Statistical Insight
        if len(filtered_df) > 1:
            st.divider()
            st.subheader("Quick Analysis")
            corr = filtered_df[['Sales', 'Profit']].corr().iloc[0,1]
            st.write(f"The correlation between Sales and Profit for selected data is **{corr:.2f}**.")
    else:
        st.info("The database is currently empty. Add your first record above!")

elif authentication_status == False:
    st.error('Username/password is incorrect')
elif authentication_status == None:
    st.warning('Please enter your username and password')
