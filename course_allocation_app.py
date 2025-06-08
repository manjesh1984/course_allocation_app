import streamlit as st
import pandas as pd
from collections import defaultdict

st.set_page_config(page_title="STCP UGP Course Allocation 2025", layout="wide")
st.title("🎓 STCP UGP Course Allocation 2025")

# --- Upload Excel file ---
uploaded_file = st.file_uploader("📁 Upload Excel File with Course Details", type=['xlsx'])

if uploaded_file:
    # Load sheets
    xl = pd.ExcelFile(uploaded_file)
    sheet_names = xl.sheet_names
    try:
        majors_df = xl.parse(sheet_names[0])
        slot1_df = xl.parse(sheet_names[1])
        slot2_df = xl.parse(sheet_names[2])
        eligibility_df = xl.parse(sheet_names[3])
        capacity_df = xl.parse(sheet_names[4])
    except Exception as e:
        st.error(f"Error loading sheets: {e}")
        st.stop()

    major_list = majors_df.iloc[:, 0].dropna().unique().tolist()
    slot1_courses = dict(zip(slot1_df.iloc[:, 0], slot1_df.iloc[:, 1]))
    slot2_courses = dict(zip(slot2_df.iloc[:, 0], slot2_df.iloc[:, 1]))

    slot1_display = [f"{code} - {name}" for code, name in slot1_courses.items()]
    slot2_display = [f"{code} - {name}" for code, name in slot2_courses.items()]
    name_to_code = {v: k for k, v in {**slot1_courses, **slot2_courses}.items()}

    eligibility_df['Minor_Code'] = eligibility_df.iloc[:, 1].map(name_to_code)
    capacity_df['Minor_Code'] = capacity_df.iloc[:, 0].map(name_to_code)
    capacity_map = dict(zip(capacity_df['Minor_Code'], capacity_df.iloc[:, 1]))

    students_data = []

    with st.form("student_form"):
        st.subheader("📋 Student Selection Form")
        col1, col2, col3 = st.columns(3)
        with col1:
            name = st.text_input("Student Name")
        with col2:
            uid = st.text_input("UID")
        with col3:
            index = st.number_input("Index Mark", min_value=0.0, format="%.2f")

        major = st.selectbox("Major Programme", major_list)
        slot1_prefs = st.multiselect("Slot 1: Minor Preferences (in priority order)", slot1_display)
        slot2_prefs = st.multiselect("Slot 2: Minor Preferences (in priority order)", slot2_display)

        submit = st.form_submit_button("Submit")

        if submit:
            if not name or not uid or not slot1_prefs or not slot2_prefs:
                st.warning("⚠️ Please fill all fields.")
            else:
                students_data.append({
                    "name": name,
                    "uid": uid,
                    "major": major,
                    "index": index,
                    "slot1": slot1_prefs,
                    "slot2": slot2_prefs
                })
                st.success("✅ Submission recorded. Click 'Run Allocation' when ready.")

    if students_data:
        if st.button("🚀 Run Allocation"):
            eligibility_map = defaultdict(set)
            for _, row in eligibility_df.iterrows():
                eligibility_map[row[0]].add(row['Minor_Code'])

            filled = defaultdict(int)
            results = []

            for s in sorted(students_data, key=lambda x: -x['index']):
                res = {'UID': s['uid'], 'Name': s['name'], 'Major': s['major'], 'Index': s['index']}
                for slot in ['slot1', 'slot2']:
                    assigned = None
                    for pref in s[slot]:
                        code = pref.split(" - ")[0]
                        if code in eligibility_map[s['major']] and filled[code] < capacity_map.get(code, 0):
                            assigned = pref
                            filled[code] += 1
                            break
                    res[f'Minor_{slot}'] = assigned
                results.append(res)

            df = pd.DataFrame(results)
            st.success("🎉 Allocation complete!")

            st.download_button("📥 Download Full Allocation", df.to_csv(index=False), file_name="full_allocation.csv")

            minor_wise = pd.concat([
                df[['Minor_slot1', 'UID', 'Major']].rename(columns={'Minor_slot1': 'Minor'}),
                df[['Minor_slot2', 'UID', 'Major']].rename(columns={'Minor_slot2': 'Minor'})
            ]).dropna().sort_values('Minor')

            major_wise = df[['Major', 'UID', 'Minor_slot1', 'Minor_slot2']].sort_values('Major')

            st.download_button("📥 Download Minor-wise Allocation", minor_wise.to_csv(index=False), file_name="minor_wise_allocation.csv")
            st.download_button("📥 Download Major-wise Allocation", major_wise.to_csv(index=False), file_name="major_wise_allocation.csv")
