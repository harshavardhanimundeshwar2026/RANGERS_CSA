import streamlit as st
import pandas as pd
import base64
import whisper
import plotly.express as px
import requests
from datetime import datetime, date
from gtts import gTTS
from streamlit_mic_recorder import mic_recorder

# --- 1. INITIALIZATION & WHISPER ---
@st.cache_resource
def load_whisper():
    return whisper.load_model("base")

model = load_whisper()

# --- RANGERS CATEGORIES & QUESTIONS ---
rangers_groups = {
    "RESPECT": [
        "I listen carefully to feedback from coaches and teammates.",
        "I control my reactions when things don’t go my way."
    ],
    "ACCOUNTABILITY": [
        "I take responsibility for my preparation and performance.",
        "When I make mistakes, I own them instead of blaming others."
    ],
    "NO EXCUSES": [
        "I avoid blaming referees, teammates, or circumstances.",
        "I quickly reset my focus when something goes wrong."
    ],
    "GROWTH": [
        "I accept constructive feedback from coaches and teammates.",
        "I challenge myself to improve every practice and game."
    ],
    "EFFORT": [
        "I give my best effort in practices, workouts, and games.",
        "My effort level is something my teammates can rely on."
    ],
    "RESPONSIBILITY": [
        "I represent the Oakville Rangers in a positive way on and off the ice.",
        "I demonstrate discipline in my habits and choices.",
        "I balance hockey, school, and personal responsibilities effectively.",
        "I understand that my behaviour reflects on the entire team."
    ],
    "STANDARDS": [
        "I consistently uphold the RANGERS Standard in my daily behaviour.",
        "I help protect the culture and standards of our team.",
        "I speak up or act when team standards are slipping.",
        "I put the success of the team ahead of personal recognition."
    ],
    "LEADERSHIP": [
        "I am willing to hold teammates accountable to our standards.",
        "Our team culture reflects the RANGERS Standard."
    ],
    "REFLECTION": [
        "Which part of the RANGERS Standard best represents you right now?",
        "Which part of the RANGERS Standard is your biggest opportunity for growth?"
    ]
}

category_list = list(rangers_groups.keys())

# --- HELPER FUNCTIONS ---
def speak(text):
    try:
        tts = gTTS(text=text, lang='en')
        tts.save("temp_voice.mp3")
        with open("temp_voice.mp3", "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
            md = f'<audio autoplay="true"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'
            st.markdown(md, unsafe_allow_html=True)
    except: pass

def safe_transcribe(audio_bytes):
    if audio_bytes is None or len(audio_bytes) < 1000:
        return None
    with open("temp.wav", "wb") as f:
        f.write(audio_bytes)
    try:
        return model.transcribe("temp.wav")['text'].strip()
    except: return None

# --- 2. SESSION STATE ---
if 'group_index' not in st.session_state:
    st.session_state.update({
        'group_index': 0,
        'all_ratings': {}, 
        'all_reasons': {},  
        'intro_done': False,
        'survey_mode': None,
        'survey_complete': False
    })

st.set_page_config(page_title="CSA Sport Performance", layout="wide")
st.title("🎙️ RANGERS Standard Evaluation Survey")

# --- 3. HOMEPAGE & PROFILE ---
if not st.session_state.intro_done:
    st.write("### 📝 Athlete Profile Setup")
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Full Name")
        email = st.text_input("Email")
        org = st.text_input("Organization", value="Oakville Rangers")
        dob = st.date_input("Date of Birth", value=date(2010, 1, 1))
    with col2:
        gender = st.selectbox("Gender", ["Male", "Female", "Other", "Prefer not to say"])
        comp_level = st.selectbox("Competition Level", ["AAA", "AA", "A", "Other"])
        age_league = st.selectbox("Age/League Level", ["U12", "U13", "U14", "U15", "U16", "U18"])
        st.session_state.survey_mode = st.radio("Choose Evaluation Method:", ["Voice Mode", "Typing Mode"])

    if st.button("Start Evaluation"):
        if name and email:
            st.session_state.profile = {
                "name": name, "email": email, "organization": org, 
                "dob": str(dob), "gender": gender, 
                "competition_level": comp_level, "age_league": age_league
            }
            st.session_state.intro_done = True
            speak(f"Hello {name}. Let's begin.")
            st.rerun()
        else:
            st.warning("Identification required.")

# --- 4. SURVEY CORE ---
elif not st.session_state.survey_complete:
    current_cat = category_list[st.session_state.group_index]
    questions = rangers_groups[current_cat]
    st.subheader(f"Section: {current_cat}")
    st.progress((st.session_state.group_index + 1) / len(category_list))

    is_reflection = (current_cat == "REFLECTION")
    section_answered = True

    for i, q in enumerate(questions):
        st.write(f"---")
        st.write(f"**{i+1}. {q}**")
        
        if not is_reflection:
            if st.session_state.survey_mode == "Voice Mode":
                aud_rat = mic_recorder(start_prompt="⏺️ Record Rating (1-10)", key=f"r_v_{current_cat}_{i}")
                trans_rat = safe_transcribe(aud_rat['bytes'] if aud_rat else None)
                if trans_rat:
                    st.session_state.all_ratings[q] = trans_rat
                    st.success(f"Rating Captured: {trans_rat}")
            else:
                st.session_state.all_ratings[q] = st.selectbox("Rating (1-10)", [None, 1,2,3,4,5,6,7,8,9,10], key=f"r_t_{current_cat}_{i}")
            if st.session_state.all_ratings.get(q) is None: section_answered = False
        else:
            st.session_state.all_ratings[q] = "N/A"

        if st.session_state.survey_mode == "Voice Mode":
            st.write("Provide explanation:")
            aud_res = mic_recorder(start_prompt="⏺️ Record Reason", key=f"e_v_{current_cat}_{i}")
            trans_res = safe_transcribe(aud_res['bytes'] if aud_res else None)
            if trans_res:
                st.session_state.all_reasons[q] = trans_res
                st.info(f"Captured: {trans_res}")
        else:
            st.session_state.all_reasons[q] = st.text_area("Explanation:", key=f"e_t_{current_cat}_{i}")

        if not st.session_state.all_reasons.get(q): section_answered = False

    if st.button("Next Section ➡️"):
        if section_answered:
            if st.session_state.group_index < len(category_list) - 1:
                st.session_state.group_index += 1
                st.rerun()
            else:
                st.session_state.survey_complete = True
                st.rerun()
        else:
            st.error("Complete all items.")

# --- 5. FINAL SUBMISSION (AIRTABLE SYNC) ---
else:
    st.success("🎉 Evaluation Complete!")
    
    # Radar Chart
    scores = []
    for cat, qs in rangers_groups.items():
        cat_vals = [int(st.session_state.all_ratings[q]) for q in qs if str(st.session_state.all_ratings.get(q)).isdigit()]
        if cat_vals:
            scores.append({"Category": cat, "Score": sum(cat_vals)/len(cat_vals)})
    
    if scores:
        st.plotly_chart(px.line_polar(pd.DataFrame(scores), r='Score', theta='Category', line_close=True, range_r=[0,10]))

    if st.button("🚀 Push Data to Coaching Staff", use_container_width=True):
        # 1. Map fields to Airtable Columns
        fields = {
            "Full Name": st.session_state.profile['name'],
            "Email": st.session_state.profile['email'],
            "Organization": st.session_state.profile['organization'],
            "Date of Birth": st.session_state.profile['dob'],
            "Gender": st.session_state.profile['gender'],
            "Competition Level": st.session_state.profile['competition_level'],
            "Age Level": st.session_state.profile['age_league'],
            "Submission Date": datetime.now().strftime("%Y-%m-%d"),
            
            # RESPECT Mapping
            "RESPECT_Score_1": int(st.session_state.all_ratings.get(rangers_groups["RESPECT"][0], 0)),
            "RESPECT_Reason_1": st.session_state.all_reasons.get(rangers_groups["RESPECT"][0], ""),
            "RESPECT_Score_2": int(st.session_state.all_ratings.get(rangers_groups["RESPECT"][1], 0)),
            "RESPECT_Reason_2": st.session_state.all_reasons.get(rangers_groups["RESPECT"][1], ""),
            
            # ACCOUNTABILITY Mapping
            "ACCOUNTABILITY_Score_1": int(st.session_state.all_ratings.get(rangers_groups["ACCOUNTABILITY"][0], 0)),
            "ACCOUNTABILITY_Reason_1": st.session_state.all_reasons.get(rangers_groups["ACCOUNTABILITY"][0], ""),
            "ACCOUNTABILITY_Score_2": int(st.session_state.all_ratings.get(rangers_groups["ACCOUNTABILITY"][1], 0)),
            "ACCOUNTABILITY_Reason_2": st.session_state.all_reasons.get(rangers_groups["ACCOUNTABILITY"][1], ""),
            
            # REFLECTION
            "REFLECTION_Best_Representation": st.session_state.all_reasons.get(rangers_groups["REFLECTION"][0], ""),
            "REFLECTION_Growth_Opportunity": st.session_state.all_reasons.get(rangers_groups["REFLECTION"][1], "")
        }

        # 2. Airtable API Push
        AIR_TOKEN = "patTerc0AbJa1tJKp"
        BASE_ID = "appGGtmK6Zh6fTaLo"
        TABLE_NAME = "Table 1"

        url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"
        headers = {"Authorization": f"Bearer {AIR_TOKEN}", "Content-Type": "application/json"}

        with st.spinner("Syncing..."):
            try:
                response = requests.post(url, json={"fields": fields}, headers=headers)
                if response.status_code == 200:
                    st.success("✅ Permanent Sync Successful!")
                    st.balloons()
                else:
                    st.error(f"Error: {response.text}")
            except Exception as e:
                st.error(f"Failed: {e}")
