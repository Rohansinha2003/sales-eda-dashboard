import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import sqlite3
import hashlib

# --- DATABASE SETUP ---
conn = sqlite3.connect('users.db', check_same_thread=False)
c = conn.cursor()

def create_usertable():
    c.execute('CREATE TABLE IF NOT EXISTS userstable(username TEXT, password TEXT)')

def add_userdata(username, password):
    c.execute('INSERT INTO userstable(username, password) VALUES (?,?)', (username, password))
    conn.commit()

def login_user(username, password):
    c.execute('SELECT * FROM userstable WHERE username =? AND password =?', (username, password))
    return c.fetchall()

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# --- APP UI ---
def main():
    st.set_page_config(page_title="Business EDA Portal", layout="wide")
    st.title("📊 Business Intelligence EDA Portal")

    menu = ["Home", "Login", "SignUp"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Home":
        st.subheader("Welcome to the EDA Tool")
        st.write("Please login to upload your datasets and generate insights.")

    elif choice == "SignUp":
        st.subheader("Create New Account")
        new_user = st.text_input("Username")
        new_password = st.text_input("Password", type='password')

        if st.button("Signup"):
            create_usertable()
            add_userdata(new_user, make_hashes(new_password))
            st.success("Account created successfully! Go to Login.")

    elif choice == "Login":
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type='password')

        if st.sidebar.checkbox("Login"):
            create_usertable()
            hashed_pswd = make_hashes(password)
            result = login_user(username, hashed_pswd)

            if result:
                st.success(f"Logged in as {username}")
                run_eda_dashboard()
            else:
                st.warning("Incorrect Username/Password")

# --- EDA DASHBOARD ---
def run_eda_dashboard():
    st.divider()
    uploaded_file = st.file_uploader("Upload your Business Dataset (CSV)", type=["csv"])

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        
        st.subheader("1. Data Preview")
        st.dataframe(df.head())

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("2. Data Statistics")
            st.write(df.describe())

        with col2:
            st.subheader("3. Missing Values")
            st.write(df.isnull().sum())

        st.subheader("4. Dynamic Visualization")
        columns = df.columns.tolist()
        x_axis = st.selectbox("Select X-axis column", columns)
        y_axis = st.selectbox("Select Y-axis column", columns)
        chart_type = st.radio("Select Chart Type", ("Scatter", "Line", "Bar"))

        plt.figure(figsize=(10, 5))
        if chart_type == "Scatter":
            sns.scatterplot(data=df, x=x_axis, y=y_axis)
        elif chart_type == "Line":
            sns.lineplot(data=df, x=x_axis, y=y_axis)
        else:
            sns.barplot(data=df, x=x_axis, y=y_axis)
        
        st.pyplot(plt)

if __name__ == '__main__':
    main()