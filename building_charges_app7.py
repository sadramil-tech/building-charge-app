# فایل: app.py

import streamlit as st
import pandas as pd
import psycopg2
import os

st.set_page_config(page_title="مدیریت شارژ ساختمان", layout="wide")
st.title("💰 سیستم مدیریت شارژ ساختمان")

NUM_UNITS = 10
unit_names = [f"واحد {i+1}" for i in range(NUM_UNITS)]
months = ["فروردین","اردیبهشت","خرداد","تیر","مرداد","شهریور",
          "مهر","آبان","آذر","دی","بهمن","اسفند"]

# ------------------ اتصال دیتابیس ------------------

DATABASE_URL = os.environ.get("DATABASE_URL")

conn = psycopg2.connect(DATABASE_URL)
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
        st.experimental_rerun()

    # نمایش هزینه‌های ماه با امکان انتخاب برای ویرایش/حذف
    df_exp = pd.read_sql_query(
        "SELECT * FROM expenses WHERE month=?",
        conn,
        params=(month_selected,)
    )

    if not df_exp.empty:
        st.subheader("لیست هزینه‌های ماه")
        selected_id = st.selectbox("انتخاب هزینه برای ویرایش/حذف", df_exp["id"])
        selected_row = df_exp[df_exp["id"] == selected_id].iloc[0]

        st.write("جزئیات هزینه انتخاب شده:")
        st.write(selected_row)

        # ویرایش هزینه
        with st.form("edit_form"):
            new_date = st.text_input("تاریخ شمسی", value=selected_row["date"])
            new_type = st.text_input("نوع هزینه", value=selected_row["type"])
            new_amount = st.number_input("مبلغ کل", min_value=0, value=selected_row["amount"])
            edit_submit = st.form_submit_button("ویرایش هزینه")

        if edit_submit:
            new_share = new_amount / NUM_UNITS
            cursor.execute(
                "UPDATE expenses SET date=?, type=?, amount=?, share=? WHERE id=?",
                (new_date, new_type, new_amount, new_share, selected_id)
            )
            conn.commit()
            st.success("هزینه ویرایش شد ✅")
            st.experimental_rerun()

        # حذف هزینه
        if st.button("حذف هزینه"):
            cursor.execute("DELETE FROM expenses WHERE id=?", (selected_id,))
            conn.commit()
            st.success("هزینه حذف شد ✅")
            st.experimental_rerun()

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
        st.experimental_rerun()

    # نمایش پرداخت‌ها و انتخاب برای ویرایش/حذف
    df_pay = pd.read_sql_query(
        "SELECT * FROM payments WHERE month=?",
        conn,
        params=(month_selected,)
    )

    if not df_pay.empty:
        st.subheader("لیست پرداخت‌های ماه")
        selected_pay_id = st.selectbox("انتخاب پرداخت برای ویرایش/حذف", df_pay["id"])
        selected_pay_row = df_pay[df_pay["id"] == selected_pay_id].iloc[0]

        st.write("جزئیات پرداخت انتخاب شده:")
        st.write(selected_pay_row)

        # ویرایش پرداخت
        with st.form("edit_pay_form"):
            new_unit = st.selectbox("واحد", unit_names, index=unit_names.index(selected_pay_row["unit"]))
            new_amount = st.number_input("مبلغ پرداختی", min_value=0, value=selected_pay_row["amount"])
            edit_pay_submit = st.form_submit_button("ویرایش پرداخت")

        if edit_pay_submit:
            cursor.execute(
                "UPDATE payments SET unit=?, amount=? WHERE id=?",
                (new_unit, new_amount, selected_pay_id)
            )
            conn.commit()
            st.success("پرداخت ویرایش شد ✅")
            st.experimental_rerun()

        # حذف پرداخت
        if st.button("حذف پرداخت"):
            cursor.execute("DELETE FROM payments WHERE id=?", (selected_pay_id,))
            conn.commit()
            st.success("پرداخت حذف شد ✅")
            st.experimental_rerun()

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

