import streamlit as st
import requests
import fitz
import re
import json
import pandas as pd
from streamlit.components.v1 import html

API_URLS = {
    "Liver disease prediction": "https://cts-vibeappso4912-2.azurewebsites.net/api/liver-disease/predict",
    "Heart attack prediction": "https://cts-vibeappso4912-2.azurewebsites.net/api/heart-attack/predict",
    "Diabetes prediction": "https://cts-vibeappso4912-2.azurewebsites.net/api/diabetes-disease/predict"
}

def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with fitz.open(pdf_path) as pdf_document:
            for page in pdf_document:
                text += page.get_text()
    except Exception as e:
        st.error(f"An error occurred while reading the PDF: {e}")
    return text

def refine_medical_report(raw_list):
    refined_list = []
    for item in raw_list:
        if ':' in item:
            # Split only on the first colon to handle cases like "Name: ABC"
            parts = item.split(':', 1)
            refined_list.extend([part.strip() for part in parts])
        else:
            refined_list.append(item.strip())
    return refined_list

def convert_lft_to_api_json(parsed_json):
    patient = parsed_json.get("patient_information", {})
    lft = parsed_json.get("lft_results", {})
    return {
        "Prediction_Type": "Liver disease prediction",
        "Age": float(patient.get("age", 0)),
        "Gender": 1.0 if str(patient.get("gender", "")).lower() == "male" else 0.0,
        "Total_Bilirubin": float(lft.get("total_bilirubin", 0)),
        "Direct_Bilirubin": float(lft.get("direct_bilirubin", 0)),
        "Alkaline_Phosphotase": float(lft.get("alkaline_phosphatase", 0)),
        "Sgpt": float(lft.get("sgpt", 0)),
        "Sgot": float(lft.get("sgot", 0)),
        "Total_Proteins": float(lft.get("total_proteins", 0)),
        "Albumin": float(lft.get("albumin", 0)),
        "Albumin_and_Globulin_Ratio": float(lft.get("albumin_globulin_ratio", 0))
    }

def parse_liver_function_test(lines):
    results = {
        "patient_information": {},
        "lft_results": {}
    }
    lft_keys = {
        "total bilirubin": "total_bilirubin",
        "direct bilirubin": "direct_bilirubin",
        "alkaline phosphatase": "alkaline_phosphatase",
        "sgpt": "sgpt",
        "sgot": "sgot",
        "total proteins": "total_proteins",
        "albumin": "albumin",
        "albumin / globulin ratio": "albumin_globulin_ratio"
    }
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        lower = line.lower()
        if lower.startswith("name"):
            if i+1 < len(lines):
                results["patient_information"]["name"] = lines[i+1].strip()
                i += 1
        elif lower.startswith("age"):
            if i+1 < len(lines):
                try:
                    results["patient_information"]["age"] = int(lines[i+1].strip())
                except ValueError:
                    pass
                i += 1
        elif lower.startswith("gender"):
            if i+1 < len(lines):
                results["patient_information"]["gender"] = lines[i+1].strip().capitalize()
                i += 1
        else:
            for key in lft_keys:
                if lower == key:
                    if i+1 < len(lines):
                        value = lines[i+1].strip()
                        try:
                            num = float(re.findall(r"[\d.]+", value)[0])
                        except Exception:
                            num = None
                        if num is not None:
                            results["lft_results"][lft_keys[key]] = num
                        i += 1
        i += 1
    return results

def parse_diabetes_report(lines):
    results = {
        "patient_information": {},
        "diabetes_results": {}
    }
    diabetes_keys = {
        "age": "Age",
        "sex": "Sex",
        "bmi": "BMI",
        "bp": "BP",
        "tc": "TC",
        "ldl": "LDL",
        "hdl": "HDL",
        "tch": "TCH",
        "ltg": "LTG",
        "glu": "GLU",
        "diabetes value": "Diabetes_Value"
    }
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        lower = line.lower()
        if lower.startswith("name"):
            if i+1 < len(lines):
                results["patient_information"]["Name"] = lines[i+1].strip()
                i += 1
        elif lower.startswith("age"):
            if i+1 < len(lines):
                try:
                    results["patient_information"]["Age"] = int(lines[i+1].strip())
                except ValueError:
                    pass
                i += 1
        elif lower.startswith("sex"):
            if i+1 < len(lines):
                results["patient_information"]["Sex"] = lines[i+1].strip().capitalize()
                i += 1
        else:
            for key in diabetes_keys:
                if lower == key:
                    if i+1 < len(lines):
                        value = lines[i+1].strip()
                        try:
                            num = float(re.findall(r"[\d.]+", value)[0])
                        except Exception:
                            num = None
                        if num is not None:
                            results["diabetes_results"][diabetes_keys[key]] = num
                        i += 1
        i += 1
    return results

def convert_diabetes_to_api_json(parsed_json):
    patient = parsed_json.get("patient_information", {})
    diabetes_results = parsed_json.get("diabetes_results", {})
    return {
        "Prediction_Type": "Diabetes prediction",
        "Age": patient.get("Age", 0),
        "Sex": 1.0 if str(patient.get("Sex")).lower() == "male" else 0.0,
        "BMI": diabetes_results.get("BMI", 0.0),
        "BP": diabetes_results.get("BP", 0.0),
        "TC": diabetes_results.get("TC", 0.0),
        "LDL": diabetes_results.get("LDL", 0.0),
        "HDL": diabetes_results.get("HDL", 0.0),
        "TCH": diabetes_results.get("TCH", 0.0),
        "LTG": diabetes_results.get("LTG", 0.0),
        "GLU": diabetes_results.get("GLU", 0.0),
        "Diabetes_Value": diabetes_results.get("Diabetes_Value", 0.0)
    }

def parse_heart_attack_report(lines):
    results = {
        "patient_information": {},
        "heart_results": {}
    }
    heart_keys = {
        "ldl": "LDL",
        "hdl": "HDL",
        "triglycerides": "Triglycerides",
        "fasting blood sugar": "Fasting_Blood_Sugar",
        "complete blood count": "Complete_Blood_Count",
        "total cholesterol": "Total_Cholesterol",
        "non hdl cholesterol": "Non_HDL_Cholesterol",
        "c reactive protein": "C_Reactive_Protein",
        "lipoprotein": "Lipoprotein",
        "plasma ceramides": "Plasma_Ceramides",
        "natriuretic peptides": "Natriuretic_Peptides",
        "troponin t": "Troponin_T"
    }
     
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        lower = line.lower()
        if lower.startswith("name"):
            if i+1 < len(lines):
                results["patient_information"]["Name"] = lines[i+1].strip()
                i += 1
        elif lower.startswith("age"):
            if i+1 < len(lines):
                try:
                    results["patient_information"]["Age"] = int(lines[i+1].strip())
                except ValueError:
                    pass
                i += 1
        elif lower.startswith("sex"):
            if i+1 < len(lines):
                results["patient_information"]["Sex"] = lines[i+1].strip().capitalize()
                i += 1
        else:
            for key in heart_keys:
                if lower == key:
                    if i+1 < len(lines):
                        value = lines[i+1].strip()
                        try:
                            num = float(re.findall(r"[\d.]+", value)[0])
                        except Exception:
                            num = None
                        if num is not None:
                            results["heart_results"][heart_keys[key]] = num
                        i += 1
        i += 1
    return results

def convert_heart_attack_to_api_json(parsed_json):
    patient = parsed_json.get("patient_information", {})
    heart_results = parsed_json.get("heart_results", {})
    return {
        "Prediction_Type": "Heart attack prediction",
        "Age": patient.get("Age", 0),
        "Sex": 1.0 if str(patient.get("Sex")).lower() == "male" else 0.0,
        "LDL": heart_results.get("LDL", 0.0),
        "HDL": heart_results.get("HDL", 0.0),
        "Triglycerides": heart_results.get("Triglycerides", 0.0),
        "Fasting_Blood_Sugar": heart_results.get("Fasting_Blood_Sugar", 0.0),
        "Complete_Blood_Count": heart_results.get("Complete_Blood_Count", 0.0),
        "Total_Cholesterol": heart_results.get("Total_Cholesterol", 0.0),
        "Non_HDL_Cholesterol": heart_results.get("Non_HDL_Cholesterol", 0.0),
        "C_Reactive_Protein": heart_results.get("C_Reactive_Protein", 0.0),
        "Lipoprotein": heart_results.get("Lipoprotein", 0.0),
        "Plasma_Ceramides": heart_results.get("Plasma_Ceramides", 0.0),
        "Natriuretic_Peptides": heart_results.get("Natriuretic_Peptides", 0.0),
        "Troponin_T": heart_results.get("Troponin_T", 0.0)
    }

# Sidebar menu options
diseases = [
    "Liver disease prediction",
    "Heart attack prediction",
    "Diabetes prediction"
]

st.set_page_config(page_title="Health Support App", layout="wide")

# Collapsible sidebar
with st.sidebar:
    st.title("Health Support App")
    st.markdown("---")
    page = st.radio("Choose view:", ["Prediction", "Chatbot"], key="main_toggle")
    st.markdown("---")
    if page == "Prediction":
        selected_disease = st.selectbox("Select Prediction Type", diseases)
    else:
        selected_disease = None

# Main content area
if page == "Prediction":
    if selected_disease:
        # Main Body
        st.markdown(f"## {selected_disease}")

        api_under_development = []
        option = st.radio(
                "Choose input method:",
                ("Upload blood test report", "Enter blood parameters")
            )

        prediction_result = None
        if selected_disease in api_under_development:
            st.warning(f"API for {selected_disease} is under development.")
            st.button("Submit", key="submit_disabled", disabled=True)
            st.file_uploader("Choose a PDF file", type=["pdf"], key="pdf_uploader_disabled", disabled=True)
        else:
            # Case 1: Manual Entry
            if option == "Enter blood parameters":
                st.subheader("Enter Blood Parameters")
                if selected_disease == "Liver disease prediction":
                    TB = st.number_input("Total Bilirubin", min_value=0.0)
                    DB = st.number_input("Direct Bilirubin", min_value=0.0)
                    Alkphos = st.number_input("Alkaline Phosphatase", min_value=0.0)
                    Sgpt = st.number_input("SGPT", min_value=0.0)
                    Sgot = st.number_input("SGOT", min_value=0.0)
                    TP = st.number_input("Total Proteins", min_value=0.0)
                    ALB = st.number_input("Albumin", min_value=0.0)
                    AG_Ratio = st.number_input("Albumin/Globulin Ratio", min_value=0.0)
                    Age = st.number_input("Age", min_value=0)
                    Gender = st.selectbox("Gender", ["Male", "Female"])
                    if st.button("Submit", key="submit_params"):
                        json_data = {
                            "Prediction_Type": "Liver disease prediction",
                            "Age": Age,
                            "Gender": 1.0 if Gender == "Male" else 0.0,
                            "Total_Bilirubin": TB,
                            "Direct_Bilirubin": DB,
                            "Alkaline_Phosphotase": Alkphos,
                            "Sgpt": Sgpt,
                            "Sgot": Sgot,
                            "Total_Proteins": TP,
                            "Albumin": ALB,
                            "Albumin_and_Globulin_Ratio": AG_Ratio
                        }
                        response = requests.post(API_URLS[selected_disease], json=json_data)
                        prediction_result = response.json()
                elif selected_disease == "Heart attack prediction":
                    Age = st.number_input("Age", min_value=0)
                    Sex = st.selectbox("Sex", ["Male", "Female"])
                    LDL = st.number_input("LDL", min_value=0.0)
                    HDL = st.number_input("HDL", min_value=0.0)
                    Triglycerides = st.number_input("Triglycerides", min_value=0.0)
                    Fasting_Blood_Sugar = st.number_input("Fasting Blood Sugar", min_value=0.0)
                    Complete_Blood_Count = st.number_input("Complete Blood Count", min_value=0.0)
                    Total_Cholesterol = st.number_input("Total Cholesterol", min_value=0.0)
                    Non_HDL_Cholesterol = st.number_input("Non-HDL Cholesterol", min_value=0.0)
                    C_Reactive_Protein = st.number_input("C-Reactive Protein", min_value=0.0)
                    Lipoprotein = st.number_input("Lipoprotein", min_value=0.0)
                    Plasma_Ceramides = st.number_input("Plasma Ceramides", min_value=0.0)
                    Natriuretic_Peptides = st.number_input("Natriuretic Peptides", min_value=0.0)
                    Troponin_T = st.number_input("Troponin T", min_value=0.0)
                    if st.button("Submit", key="submit_heart_attack"):
                        json_data = {
                            "Prediction_Type": "Heart attack prediction",
                            "Age": Age,
                            "Sex": 1 if Sex == "Male" else 0,
                            "LDL": LDL,
                            "HDL": HDL,
                            "Triglycerides": Triglycerides,
                            "Fasting_Blood_Sugar": Fasting_Blood_Sugar,
                            "Complete_Blood_Count": Complete_Blood_Count,
                            "Total_Cholesterol": Total_Cholesterol,
                            "Non_HDL_Cholesterol": Non_HDL_Cholesterol,
                            "C_Reactive_Protein": C_Reactive_Protein,
                            "Lipoprotein": Lipoprotein,
                            "Plasma_Ceramides": Plasma_Ceramides,
                            "Natriuretic_Peptides": Natriuretic_Peptides,
                            "Troponin_T": Troponin_T
                        }
                        response = requests.post(API_URLS[selected_disease], json=json_data)
                        prediction_result = response.json()
                elif selected_disease == "Diabetes prediction":
                    Age = st.number_input("Age", min_value=0)
                    Sex = st.selectbox("Sex", ["Male", "Female"])
                    BMI = st.number_input("BMI", min_value=0.0)
                    BP = st.number_input("BP", min_value=0.0)
                    TC = st.number_input("TC", min_value=0.0)
                    LDL = st.number_input("LDL", min_value=0.0)
                    HDL = st.number_input("HDL", min_value=0.0)
                    TCH = st.number_input("TCH", min_value=0.0)
                    LTG = st.number_input("LTG", min_value=0.0)
                    GLU = st.number_input("GLU", min_value=0.0)
                    Diabetes_Value = st.number_input("Diabetes Value", min_value=0.0)
                    if st.button("Submit", key="submit_diabetes"):
                        json_data = {
                            "Prediction_Type": "Diabetes prediction",
                            "Age": Age,
                            "Sex": 1 if Sex == "Male" else 0,
                            "BMI": BMI,
                            "BP": BP,
                            "TC": TC,
                            "LDL": LDL,
                            "HDL": HDL,
                            "TCH": TCH,
                            "LTG": LTG,
                            "GLU": GLU,
                            "Diabetes_Value": Diabetes_Value
                        }
                        response = requests.post(API_URLS[selected_disease], json=json_data)
                        prediction_result = response.json()
            # Case 2: PDF Upload
            elif option == "Upload blood test report":
                st.subheader("Upload Blood Test Report (PDF)")
                uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"], key="pdf_uploader")
                if uploaded_file is not None:
                    st.success("File uploaded successfully!")
                if st.button("Submit", key="submit_pdf") and uploaded_file is not None:
                    with open("temp_report.pdf", "wb") as f:
                        f.write(uploaded_file.read())
                    extracted_text = extract_text_from_pdf("temp_report.pdf")
                    lines = [line.strip() for line in extracted_text.split('\n') if line.strip()]
                    lines = refine_medical_report(lines)
                    if selected_disease == "Liver disease prediction":
                        parsed_json = parse_liver_function_test(lines)
                        json_data = convert_lft_to_api_json(parsed_json)
                        print(json_data)
                    elif selected_disease == "Diabetes prediction":
                        parsed_json = parse_diabetes_report(lines)
                        json_data = convert_diabetes_to_api_json(parsed_json)
                        print(json_data)
                    elif selected_disease == "Heart attack prediction":
                        parsed_json = parse_heart_attack_report(lines)
                        json_data = convert_heart_attack_to_api_json(parsed_json)
                        print(json_data)
                    else:
                        st.warning("PDF parsing for this disease is not implemented.")
                        json_data = None
                    if json_data:
                        response = requests.post(API_URLS[selected_disease], json=json_data)
                        prediction_result = response.json()

        # Output bar for prediction
        st.markdown("---")
        st.subheader("Prediction Output")
        if prediction_result:
            st.markdown(f"**Prediction:** {prediction_result.get('prediction', '')}")
            # st.markdown(f"**Probability:** {prediction_result.get('probability', 0):.3f}")
            st.markdown(f"**Message:** {prediction_result.get('message', '')}")

elif page == "Chatbot":
    import json
    import re
    import pandas as pd
    import ast # For safely evaluating Python literals

    st.markdown("---")
    st.title("Welcome to Your AI Assistant")
    st.subheader("Smart Appointment Assistant Chat")

    # Display output area (above chatbox)
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # def extract_json_from_text(text):
    #     # Find JSON array or object in the text
    #     match = re.search(r'(\[.*?\]|\{.*?\})', text, re.DOTALL)
    #     if match:
    #         json_str = match.group(1)
    #         try:
    #             data = json.loads(json_str)
    #             if isinstance(data, dict):
    #                 data = [data]
    #             # Get text before and after JSON
    #             before = text[:match.start()].strip()
    #             after = text[match.end():].strip()
    #             return before, data, after
    #         except Exception:
    #             pass
    #     return text, None, None
    
    def extract_json_from_text(text):
    # Find JSON array or object in the text
        match = re.search(r'(\[.*?\]|\{.*?\})', text, re.DOTALL)
        if match:
            json_str = match.group(1)
            try:
                data = json.loads(json_str)
                # If the value is a stringified Python dict, parse it
                if isinstance(data, dict) and "agent_output" in data:
                    try:
                        inner_data = ast.literal_eval(data["agent_output"])
                        if isinstance(inner_data, dict):
                            data = [inner_data]
                    except Exception:
                        pass
                elif isinstance(data, dict):
                    data = [data]
                before = text[:match.start()].strip()
                after = text[match.end():].strip()
                return before, data, after
            except Exception:
                pass
        return text, None, None

    for i, (user_msg, bot_msg) in enumerate(st.session_state.chat_history):
        st.markdown(f"**You:** {user_msg}")
        before, json_data, after = extract_json_from_text(bot_msg)
        if json_data:
            if before:
                st.markdown(f"**Bot:** {before}")
            st.table(pd.DataFrame(json_data))
            if after:
                st.markdown(f"**Bot:** {after}")
        else:
            st.markdown(f"**Bot:** {bot_msg}")
    
    def handle_chat_input():
        user_input = st.session_state.chat_input
        if user_input:
            ## Replace with actual API Url
            api_url = "https://cts-vibeappso4912-2.azurewebsites.net/api/appointment-booking-and-checking"
            payload = {"user_query": user_input}
            try:
                response = requests.post(api_url, json=payload)
                if response.status_code == 200:
                    # bot_response = response.json.get("response", "No response from bot.")
                    bot_response = response.text
                else:
                    bot_response = f"Error: {response.status_code} - {response.text}"
            except Exception as e:
                bot_response = f"Error connecting to API: {str(e)}"
            st.session_state.chat_history.append((user_input, bot_response))
            st.session_state.chat_input = ""    

    # Chat input
    st.text_input("You:", key="chat_input", on_change=handle_chat_input)
