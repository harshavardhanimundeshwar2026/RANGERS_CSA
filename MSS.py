import streamlit as st
import pandas as pd
import os
import base64
import whisper
import plotly.express as px
from datetime import datetime, date
from gtts import gTTS
from streamlit_mic_recorder import mic_recorder

# --- 1. INITIALIZATION & PATHING ---
@st.cache_resource
def load_whisper():
    return whisper.load_model("base")

model = load_whisper()

# --- RANGERS CATEGORIES ---
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
        return model.transcribe("temp.wav")['text'].strip().lower().replace(".", "")
    except Exception as e:
        st.error(f"Whisper Error: {e}")
        return None

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
st.caption("Powered by CSA Sport Performance")

# --- 3. HOMEPAGE ---
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
            st.warning("Please enter your Name and Email.")

# --- 4. SURVEY LOGIC ---
elif not st.session_state.survey_complete:
    current_cat = category_list[st.session_state.group_index]
    questions = rangers_groups[current_cat]
    
    st.subheader(f"Section: {current_cat}")
    st.progress((st.session_state.group_index + 1) / len(category_list))

    is_reflection = current_cat in ["REFLECTION"]
    section_answered = True

    for i, q in enumerate(questions):
        st.write(f"---")
        st.write(f"**{i+1}. {q}**")
        
        is_rating_q = not is_reflection 

        # RATING
        if is_rating_q:
            if st.session_state.survey_mode == "Voice Mode":
                aud_rat = mic_recorder(start_prompt="⏺️ Record Rating (1-10)", stop_prompt="⏹️ Stop", key=f"r_v_{current_cat}_{i}")
                trans_rat = safe_transcribe(aud_rat['bytes'] if aud_rat else None)
                if trans_rat:
                    num_map = {"one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10"}
                    val = num_map.get(trans_rat, trans_rat)
                    if val.isdigit() and 1 <= int(val) <= 10:
                        st.session_state.all_ratings[q] = val
                        st.success(f"Rating: {val}")
            else:
                st.session_state.all_ratings[q] = st.selectbox("Rating (1-10)", [None, 1,2,3,4,5,6,7,8,9,10], key=f"r_t_{current_cat}_{i}")
            
            if st.session_state.all_ratings.get(q) is None: section_answered = False
        else:
            st.session_state.all_ratings[q] = "N/A"

        # REASON
        prompt = "Thank you for your response, please provide a brief explanation."
        if st.session_state.survey_mode == "Voice Mode":
            st.write(prompt)
            aud_res = mic_recorder(start_prompt="⏺️ Record Reason", stop_prompt="⏹️ Stop", key=f"e_v_{current_cat}_{i}")
            trans_res = safe_transcribe(aud_res['bytes'] if aud_res else None)
            if trans_res:
                st.session_state.all_reasons[q] = trans_res
                st.info(f"Captured: {trans_res}")
        else:
            st.session_state.all_reasons[q] = st.text_area(prompt, key=f"e_t_{current_cat}_{i}")

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
            st.error("⚠️ Please complete all ratings and explanations in this section.")

# --- 5. FINAL SUBMISSION ---
else:
    st.success("🎉 Survey Complete!")
    
    # Process scores for Radar Chart
    scores = []
    for cat, qs in rangers_groups.items():
        cat_vals = [int(st.session_state.all_ratings[q]) for q in qs if st.session_state.all_ratings.get(q) not in [None, "N/A"]]
        if cat_vals:
            scores.append({"Category": cat, "Score": sum(cat_vals)/len(cat_vals)})
    
    if scores:
        df_plot = pd.DataFrame(scores)
        fig = px.line_polar(df_plot, r='Score', theta='Category', line_close=True, range_r=[0,10])
        fig.update_traces(fill='toself')
        st.plotly_chart(fig)

    st.divider()
    st.subheader("Final Step: Save to Team Dashboard")
    st.write("Click the button below to synchronize your results with the Oakville Rangers database.")

    # Airtable Submission Link
    airtable_url = "https://airtable.com/invite/l?inviteId=invMxk61zgxvoXS1r&inviteToken=a1e05000257aaa6eaeeaf19454429377ceee59de58f57b0faee31175b1f68bda&utm_medium=email&utm_source=product_team&utm_content=transactional-alerts"

    st.link_button("🚀 Submit to RANGERS Dashboard", airtable_url, use_container_width=True)
