# فایل: app.py

import streamlit as st
import sqlite3
import pandas as pd

st.set_page_config(page_title="مدیریت شارژ ساختمان", layout="wide")
st.title("💰 سیستم مدیریت شارژ ساختمان")

NUM_UNITS = 10
unit_names = [f"واحد {i+1}" for i in range(NUM_UNITS)]
months = ["فروردین","اردیبهشت","خرداد","تیر","مرداد","شهریور",
          "مهر","آبان","آذر","دی","بهمن","اسفند"]

# ------------------ اتصال دیتابیس ------------------

conn = sqlite3.connect("building.db", check_same_thread=False)
cursor = conn.cursor()

# ایجاد جدول‌ها در صورت نبودن
cursor.execute("""
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    month TEXT,
    date TEXT,
    type TEXT,
    amount INTEGER,
    share REAL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    month TEXT,
    unit TEXT,
    amount INTEGER
)
""")

conn.commit()

month_selected = st.sidebar.selectbox("انتخاب ماه", months)

tab1, tab2, tab3 = st.tabs(["ثبت هزینه","ثبت پرداخت","گزارش کلی"])

# ================== تب هزینه ==================
with tab1:
    st.header("ثبت هزینه")

    with st.form("expense_form"):
        date_shamsi = st.text_input("تاریخ شمسی")
        expense_type = st.text_input("نوع هزینه")
        amount = st.number_input("مبلغ کل", min_value=0)
        submit = st.form_submit_button("ثبت")

    if submit and amount > 0:
        share = amount / NUM_UNITS
        cursor.execute(
            "INSERT INTO expenses (month,date,type,amount,share) VALUES (?,?,?,?,?)",
            (month_selected, date_shamsi, expense_type, amount, share)
        )
        conn.commit()
        st.success("هزینه ثبت شد ✅")
        st.rerun()

    # نمایش هزینه‌های ماه
    df_exp = pd.read_sql_query(
        "SELECT * FROM expenses WHERE month=?",
        conn,
        params=(month_selected,)
    )

    st.dataframe(df_exp)

# ================== تب پرداخت ==================
with tab2:
    st.header("ثبت پرداخت")

    unit = st.selectbox("واحد", unit_names)
    pay_amount = st.number_input("مبلغ پرداختی", min_value=0)

    if st.button("ثبت پرداخت"):
        cursor.execute(
            "INSERT INTO payments (month,unit,amount) VALUES (?,?,?)",
            (month_selected, unit, pay_amount)
        )
        conn.commit()
        st.success("پرداخت ثبت شد ✅")
        st.rerun()

    df_pay = pd.read_sql_query(
        "SELECT * FROM payments WHERE month=?",
        conn,
        params=(month_selected,)
    )

    st.dataframe(df_pay)

# ================== گزارش کلی ==================
with tab3:
    st.header("گزارش کلی ساختمان")

    df_all_exp = pd.read_sql_query("SELECT * FROM expenses", conn)
    df_all_pay = pd.read_sql_query("SELECT * FROM payments", conn)

    total_expense = df_all_exp["amount"].sum() if not df_all_exp.empty else 0
    total_paid = df_all_pay["amount"].sum() if not df_all_pay.empty else 0

    share_year = total_expense / NUM_UNITS if total_expense > 0 else 0

    # جدول پرداخت سالانه
    if not df_all_pay.empty:
        pivot = df_all_pay.pivot_table(
            index="unit",
            columns="month",
            values="amount",
            aggfunc="sum",
            fill_value=0
        )
        pivot["جمع پرداخت"] = pivot.sum(axis=1)
        pivot["مانده"] = pivot["جمع پرداخت"] - share_year

        st.subheader("💳 وضعیت پرداخت‌ها")
        st.dataframe(pivot)

    st.divider()

    st.subheader("🧾 وضعیت هزینه‌ها")
    if not df_all_exp.empty:
        expense_summary = df_all_exp.groupby("month")["amount"].sum().reset_index()
        st.dataframe(expense_summary)

    st.divider()

    st.subheader("🏦 وضعیت صندوق")
    balance = total_paid - total_expense

    st.write(f"مجموع هزینه‌ها: {total_expense:,.0f}")
    st.write(f"مجموع پرداخت‌ها: {total_paid:,.0f}")

    if balance >= 0:
        st.success(f"موجودی صندوق: {balance:,.0f}")
    else:
        st.error(f"کسری صندوق: {balance:,.0f}")