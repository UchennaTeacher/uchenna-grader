import streamlit as st
import google.generativeai as genai
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- 1. SETTINGS & CREDENTIALS (THE SECRETS VAULT) ---
# We are now pulling these securely from Streamlit Cloud!
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-2.5-flash", generation_config={"temperature": 0.0})

SENDER_EMAIL = st.secrets["SENDER_EMAIL"]
APP_PASSWORD = st.secrets["APP_PASSWORD"]
TEACHER_EMAIL = st.secrets["TEACHER_EMAIL"]

# --- 2. THE EMAIL FUNCTION (THE POSTMAN) ---
def send_grading_email(student_name, subject, ai_report):
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = TEACHER_EMAIL
        msg['Subject'] = f"🎓 AI Grading Report: {student_name} - {subject}"

        email_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #1d1d1d;">
                <h2 style="color: #7b211f;">Uchenna Academy Grading Platform</h2>
                <p>A new assignment has been processed by the AI.</p>
                <ul>
                    <li><b>Student:</b> {student_name}</li>
                    <li><b>Subject:</b> {subject}</li>
                </ul>
                <hr>
                <h3>AI Feedback:</h3>
                {ai_report}
            </body>
        </html>
        """
        msg.attach(MIMEText(email_body, 'html'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Email failed to send: {e}")
        return False

# --- 3. WEBSITE DESIGN SETUP ---
st.set_page_config(page_title="Uchenna AI Grader", page_icon="🎓", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #0f172a; color: white; font-family: 'Helvetica Neue', sans-serif; }
    h1 { color: #ffffff !important; text-align: center; margin-bottom: 25px; }
    label, .stSelectbox label p, .stFileUploader label p { color: white !important; font-weight: bold !important; text-align: left !important; margin-top: 15px; }
    .input-container { display: flex; flex-direction: column; gap: 10px; margin-bottom: 25px; }
    [data-testid="stFileUploadDropzone"] { background-color: #1e293b; border: 2px dashed #38bdf8; border-radius: 15px; padding: 20px; transition: background-color 0.3s ease; }
    [data-testid="stFileUploadDropzone"]:hover { background-color: #334155; }
    #note-background { background-color: #7b211f; color: white; border-radius: 8px; padding: 15px; font-weight: bold; text-align: center; margin-top: 20px; border: 1px solid #ff4d4d; }
    </style>
""", unsafe_allow_html=True)

# --- 4. LOGO & PAGE CONTENT ---
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.image("uchenna logo 2020.JPG", use_container_width=True)

st.title("Uchenna Academy Grading Platform")
st.write("Welcome! Please select your subject and upload your assignment below.")

with st.form(key="grading_form"):
    st.markdown('<div class="input-container">', unsafe_allow_html=True)
    student_name = st.text_input("Student First and Last Name:")
    subjects = ["Math & Science", "English", "History", "Social Science", "French", "Ballmatics for Schools", "Ballmatics"]
    subject = st.selectbox("Select Subject", subjects)
    uploaded_file = st.file_uploader("Upload your PDF here", type="pdf")
    st.markdown('</div>', unsafe_allow_html=True)
    
    submit_button = st.form_submit_button(label="Grade It! 🚀")

# --- 5. THE MAGIC: GRADING & EMAILING ---
if submit_button:
    if not student_name or not uploaded_file:
        st.error("⚠️ Please provide a student name and upload a PDF file before proceeding.")
    else:
        st.success(f"Successfully received {student_name}'s {subject} assignment! Handing off to AI... 🚀")
        
        with st.spinner("AI is grading the paper... please wait."):
            temp_file_path = "temp_student_upload.pdf"
            with open(temp_file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            html_rule = "Format your response STRICTLY using basic HTML tags (like <b> for bold, <br> for new lines). Address the student by name at the beginning. Do NOT use Markdown."
            
            if subject == "Math & Science":
                prompt = f"""You are an expert Math & Science teacher grading a test for {student_name}. 
                1. FIRST: Scan the entire document and identify the maximum point value assigned to each question (usually found at the end of the question). 
                2. Calculate the TRUE TOTAL possible points for this specific assignment.
                3. Grade every single problem step-by-step. Deduct points specifically based on the value of that individual question.
                4. At the very end, provide a definitive FINAL SCORE as a fraction (Total Earned / True Total Points) and the final percentage.
                {html_rule}"""
            elif subject == "English":
                prompt = f"""You are an expert English teacher grading an assignment for {student_name}. 
                1. Look at the assignment to determine the total possible points. If no points are listed, grade it out of a standard 100-point rubric.
                2. List the point deductions with explanations.
                3. Provide a definitive FINAL SCORE as a fraction and the corresponding Letter Grade.
                {html_rule}"""
            elif "Ballmatics" in subject:
                prompt = f"""You are a Ballmatics Coach and Math Educator grading work for {student_name}. 
                1. FIRST: Scan the document to find the total possible points assigned to each question and add them up.
                2. Grade this worksheet keeping basketball and math concepts in mind. Deduct points based on the value of that specific question.
                3. Give encouraging feedback using basketball analogies.
                4. Provide a definitive FINAL SCORE as a fraction (Total Earned / True Total Points).
                {html_rule}"""
            else:
                prompt = f"""You are an expert {subject} teacher grading work for {student_name}. 
                1. FIRST: Scan the worksheet to find the point values assigned to each question and calculate the TOTAL possible points.
                2. Point out specific errors and deduct points for each based on the question's value.
                3. Provide a definitive FINAL SCORE as a fraction (Total Earned / True Total Points).
                {html_rule}"""
                
            try:
                worksheet_file = genai.upload_file(path=temp_file_path)
                response = model.generate_content([worksheet_file, prompt])
                
                st.markdown("### 📝 Uchenna Academy AI Grading Report")
                st.markdown(f'<div style="background-color: white; color: black; padding: 30px; border-radius: 10px; font-size: 1.1rem; line-height: 1.6; border: 3px solid #38bdf8;">{response.text}</div>', unsafe_allow_html=True) 
                
                st.markdown('<div id="note-background">📬 Please Note: A copy of this preliminary AI report has been automatically sent to your teacher to review and finalize your grade.The AI on this platform is your Preliminary Tutor, not your final Grader. Its job is to give you immediate feedback and estimate a score based on its analysis. Because it acts like a human tutor, it might focus on different errors if you upload the exact same paper twice. Do not try to game the AI. Your official, final grade will strictly be determined by your human teacher who reviews this report.</div>', unsafe_allow_html=True)
                
                with st.spinner("Dispatching report to teacher's inbox..."):
                    email_success = send_grading_email(student_name, subject, response.text)
                    if email_success:
                        st.success("✅ Report successfully emailed to teacher!")
                    else:
                        st.error("⚠️ Grade generated, but the email failed to send. Check your App Password and settings.")
                
            except Exception as e:
                st.error(f"Oh no! An error occurred: {e}")
                
            finally:
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)