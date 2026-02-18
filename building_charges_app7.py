# app.py - سیستم مدیریت شارژ ساختمان (اصلاح‌شده - بدون KeyError)

import streamlit as st
import pandas as pd
from supabase import create_client
import os

st.set_page_config(page_title="مدیریت شارژ ساختمان", layout="wide")
st.title("💰 سیستم مدیریت شارژ ساختمان")

# ثابت‌ها
NUM_UNITS = 10
UNIT_NAMES = [f"واحد {i+1}" for i in range(NUM_UNITS)]
MONTHS = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
          "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]

# اتصال به دیتابیس
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ایجاد جدول‌ها
cursor.executescript("""
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    month TEXT NOT NULL,
    date TEXT NOT NULL,
    type TEXT NOT NULL,
    amount INTEGER NOT NULL,
    share REAL NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    month TEXT NOT NULL,
    unit TEXT NOT NULL,
    amount INTEGER NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
""")
conn.commit()

# انتخاب ماه
month_selected = st.sidebar.selectbox("ماه مورد نظر", MONTHS, index=MONTHS.index("بهمن"))

tab1, tab2, tab3 = st.tabs(["ثبت هزینه", "ثبت پرداخت", "گزارش کلی"])

# ── تب ۱: هزینه‌ها ───────────────────────────────────────────
with tab1:
    st.header("ثبت هزینه جدید")

    with st.form("expense_form", clear_on_submit=True):
        col1, col2, col3 = st.columns([2, 4, 3])
        with col1: date_input = st.text_input("تاریخ (مثال: ۱۴۰۴/۱۱/۱۹)")
        with col2: exp_type   = st.text_input("شرح هزینه")
        with col3: amount     = st.number_input("مبلغ کل (تومان)", min_value=0, step=5000)

        if st.form_submit_button("ثبت هزینه", type="primary"):
            if date_input.strip() and exp_type.strip() and amount > 0:
                share = amount / NUM_UNITS
                cursor.execute(
                    "INSERT INTO expenses (month, date, type, amount, share) VALUES (?,?,?,?,?)",
                    (month_selected, date_input.strip(), exp_type.strip(), int(amount), share)
                )
                conn.commit()
                st.success("ثبت شد", icon="✅")
                st.rerun()
            else:
                st.error("فیلدهای ضروری را پر کنید")

    df_exp = pd.read_sql_query(
        "SELECT id, date, type, amount, share FROM expenses WHERE month = ? ORDER BY id DESC",
        conn, params=(month_selected,)
    )

    if not df_exp.empty:
        st.subheader(f"هزینه‌های {month_selected}")
        options = ["─ انتخاب ─"] + [f"{r.id} | {r.date} | {r.type} | {r.amount:,.0f}" for r in df_exp.itertuples()]
        selected = st.selectbox("ویرایش / حذف", options)

        if selected != "─ انتخاب ─":
            sel_id = int(selected.split(" | ")[0])
            row = df_exp[df_exp["id"] == sel_id].iloc[0]

            with st.form("edit_exp"):
                col1e, col2e, col3e = st.columns([2,4,3])
                with col1e: edit_date   = st.text_input("تاریخ", value=row["date"])
                with col2e: edit_type   = st.text_input("شرح",   value=row["type"])
                with col3e: edit_amount = st.number_input("مبلغ", value=int(row["amount"]), step=5000)

                colb1, colb2 = st.columns(2)
                with colb1:
                    if st.form_submit_button("ذخیره", type="primary"):
                        new_share = edit_amount / NUM_UNITS
                        cursor.execute(
                            "UPDATE expenses SET date=?, type=?, amount=?, share=? WHERE id=?",
                            (edit_date.strip(), edit_type.strip(), int(edit_amount), new_share, sel_id)
                        )
                        conn.commit()
                        st.rerun()
                with colb2:
                    if st.form_submit_button("حذف", type="secondary"):
                        cursor.execute("DELETE FROM expenses WHERE id=?", (sel_id,))
                        conn.commit()
                        st.rerun()

        st.dataframe(df_exp.style.format({"amount":"{:,}","share":"{:,}"}))

# ── تب ۲: پرداخت‌ها ──────────────────────────────────────────
with tab2:
    st.header("ثبت پرداخت")

    colu, cola = st.columns([3,2])
    with colu: unit = st.selectbox("واحد", UNIT_NAMES)
    with cola: pay_amount = st.number_input("مبلغ (تومان)", min_value=0, step=10000)

    if st.button("ثبت پرداخت", type="primary"):
        if pay_amount > 0:
            cursor.execute(
                "INSERT INTO payments (month, unit, amount) VALUES (?,?,?)",
                (month_selected, unit, int(pay_amount))
            )
            conn.commit()
            st.success("ثبت شد")
            st.rerun()
        else:
            st.warning("مبلغ باید مثبت باشد")

    df_pay = pd.read_sql_query(
        "SELECT id, unit, amount FROM payments WHERE month = ? ORDER BY id DESC",
        conn, params=(month_selected,)
    )

    if not df_pay.empty:
        st.subheader(f"پرداخت‌های {month_selected}")
        pay_opts = ["─ انتخاب ─"] + [f"{r.id} | {r.unit} | {r.amount:,.0f}" for r in df_pay.itertuples()]
        selp = st.selectbox("ویرایش/حذف پرداخت", pay_opts)

        if selp != "─ انتخاب ─":
            pid = int(selp.split(" | ")[0])
            prow = df_pay[df_pay["id"] == pid].iloc[0]

            with st.form("edit_pay"):
                new_unit = st.selectbox("واحد", UNIT_NAMES, index=UNIT_NAMES.index(prow["unit"]))
                new_amnt = st.number_input("مبلغ", value=int(prow["amount"]), step=10000)

                c1, c2 = st.columns(2)
                with c1:
                    if st.form_submit_button("ذخیره", type="primary"):
                        cursor.execute("UPDATE payments SET unit=?, amount=? WHERE id=?", (new_unit, int(new_amnt), pid))
                        conn.commit()
                        st.rerun()
                with c2:
                    if st.form_submit_button("حذف", type="secondary"):
                        cursor.execute("DELETE FROM payments WHERE id=?", (pid,))
                        conn.commit()
                        st.rerun()

        st.dataframe(df_pay.style.format({"amount":"{:,}"}))

# ── تب ۳: گزارش کلی (بخش مشکل‌دار - کاملاً اصلاح شد) ───────
with tab3:
    st.header("گزارش کلی")

    df_exp = pd.read_sql("SELECT month, SUM(amount) as total FROM expenses GROUP BY month", conn)
    df_pay = pd.read_sql("SELECT unit, month, SUM(amount) as paid FROM payments GROUP BY unit, month", conn)

    total_exp_all = df_exp["total"].sum() if not df_exp.empty else 0
    total_paid_all = df_pay["paid"].sum() if not df_pay.empty else 0
    balance_all = total_paid_all - total_exp_all

    if df_exp.empty:
        st.info("هنوز هزینه‌ای ثبت نشده است.")
        df_balance = pd.DataFrame(index=UNIT_NAMES, columns=MONTHS + ["مانده کل"]).fillna(0)
    else:
        # سهم هر واحد در هر ماه
        monthly_share = df_exp.set_index("month")["total"] / NUM_UNITS

        # سری تجمعی هزینه (برای همه واحدها یکسان)
        cum_exp = monthly_share.reindex(MONTHS).cumsum().fillna(method="ffill").fillna(0)

        # جدول پرداخت‌ها
        pay_table = df_pay.pivot(index="unit", columns="month", values="paid") \
                          .reindex(index=UNIT_NAMES, columns=MONTHS).fillna(0)

        cum_pay = pay_table.cumsum(axis=1)

        # مانده = پرداخت تجمعی - هزینه تجمعی
        df_balance = cum_pay.subtract(cum_exp, axis=1)
        df_balance["مانده کل"] = df_balance.sum(axis=1)

    st.subheader("مانده هر واحد (تجمعی)")
    st.dataframe(
        df_balance.style
          .format("{:,.0f}")
          .background_gradient(cmap="RdYlGn_r", axis=None, vmin=-10000000, vmax=10000000),
        use_container_width=True
    )

    st.divider()
    c1, c2, c3 = st.columns(3)
    c1.metric("کل هزینه‌ها", f"{total_exp_all:,.0f} تومان")
    c2.metric("کل دریافتی",  f"{total_paid_all:,.0f} تومان")
    if balance_all >= 0:
        c3.metric("موجودی", f"{balance_all:,.0f} تومان")
    else:
        c3.metric("کسری", f"{balance_all:,.0f} تومان", delta_color="inverse")

st.caption("نسخه اصلاح‌شده — بدون KeyError")


