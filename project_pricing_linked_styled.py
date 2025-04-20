
import streamlit as st
import pandas as pd
import requests
from difflib import get_close_matches

st.set_page_config(page_title="تسعير عروض المشاريع - ذكي", layout="wide")
st.title("🤖 تسعير مشاريع المقاولات مع ربط أسعار Google Sheets")

# رابط Google Sheets بصيغة CSV
sheet_url = "https://docs.google.com/spreadsheets/d/1zeZclvD5IuaZRUIDlrg2DNNEoBg4s69AqRFmmsnkzZs/export?format=csv"

@st.cache_data
def load_material_prices():
    return pd.read_csv(sheet_url)

material_prices = load_material_prices()

st.markdown("📤 **ارفع ملف Excel يحتوي على بنود الأعمال والكميات والمواصفات.**")
uploaded_file = st.file_uploader("اختر ملف Excel", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)

        if "بند" not in df.columns or "الوصف" not in df.columns or "الوحدة" not in df.columns or "الكمية" not in df.columns:
            st.error("❌ تأكد أن الملف يحتوي على الأعمدة التالية: بند، الوصف، الوحدة، الكمية.")
        else:
            st.success("✅ تم تحميل الملف. يتم الآن مطابقة الأسعار تلقائيًا من Google Sheets...")

            # مطابقة السعر حسب المادة (الوصف)
            def get_price(desc):
                matches = get_close_matches(str(desc).strip(), material_prices["المادة"].astype(str).str.strip(), n=1, cutoff=0.6)
                if matches:
                    match = material_prices[material_prices["المادة"].str.strip() == matches[0]]
                else:
                    return 0.0
                if not match.empty:
                    return match["السعر الحالي (ريال)"].values[0]
                return 0.0

            df["سعر الوحدة (ريال)"] = df["الوصف"].apply(get_price)
            df["التكلفة الإجمالية"] = df["الكمية"] * df["سعر الوحدة (ريال)"]

            edited_df = st.data_editor(
                df[["بند", "الوصف", "الوحدة", "الكمية", "سعر الوحدة (ريال)", "التكلفة الإجمالية"]],
                num_rows="dynamic",
                use_container_width=True
            )

            st.subheader("📦 ملخص العرض:")
            total_cost = edited_df["التكلفة الإجمالية"].sum()
            st.metric("إجمالي تكلفة العرض", f"{total_cost:,.2f} ريال")

            @st.cache_data
            def convert_to_excel(df):
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name="عرض السعر")
                return output.getvalue()

            import io
            excel_data = convert_to_excel(edited_df)

            st.download_button(
                label="📥 تحميل عرض السعر بصيغة Excel",
                data=excel_data,
                file_name="عرض_السعر_الذكي.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        st.error(f"حدث خطأ أثناء المعالجة: {e}")
