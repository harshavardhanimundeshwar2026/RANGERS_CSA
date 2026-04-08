# RANGERS_CSA
# RANGERS Standard Evaluation System
### Athlete Performance & Self-Assessment Pipeline

This project is a high-fidelity web application built for the **Oakville Rangers**. It digitizes the "RANGERS Standard" evaluation process, allowing athletes to provide feedback via **Voice** or **Text**, while automatically syncing data to a cloud-based database for coaching analysis.

---

## Key Features
* **Multimodal Input:** Uses **OpenAI Whisper** for high-accuracy voice-to-text transcription of athlete reflections.
* **Interactive UI:** Built with **Streamlit**, featuring an integrated "How-to-Use" guide and real-time progress tracking.
* **Visual Analytics:** Automatically generates a **Plotly Radar Chart** upon completion to visualize the athlete’s strengths and growth opportunities.
* **Secure Cloud Backend:** REST API integration with **Airtable** for persistent, centralized data storage.
* **Crash-Proof Logic:** Robust numeric extraction ensures speech-to-text ratings (1-10) are captured accurately without system crashes.

---

## Technical Stack
* **Frontend:** Streamlit
* **AI/ML:** OpenAI Whisper (Base Model)
* **Speech Synthesis:** gTTS (Google Text-to-Speech)
* **Database:** Airtable REST API
* **Visualization:** Plotly Express
* **Language:** Python 3.9+

---

## Installation & Setup

### 1. Clone the Repository
```bash
*git clone [https://github.com/harshavardhanimundeshwar2026/RANGERS_CSA.git](https://github.com/harshavardhanimundeshwar2026/RANGERS_CSA.git)
cd rangers-csa

### 2. Install Dependencies
pip install -r requirements.txt

### 3. Configure Secrets
AIR_TOKEN = "your_airtable_personal_access_token"
BASE_ID = "your_base_id"
TABLE_NAME = "Table 1"

### 4. Run the Application
streamlit run MSS.py
