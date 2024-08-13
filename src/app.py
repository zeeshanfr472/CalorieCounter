import streamlit as st
from PIL import Image
import io
import google.generativeai as genai
import os
from dotenv import load_dotenv
from time import sleep

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def get_gemini_response(input_prompt, image):
    model = genai.GenerativeModel('gemini-1.5-flash')
    try:
        response = model.generate_content([input_prompt, image[0]])
        return clean_response(response.text)  # Clean the response
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None

def input_image_setup(uploaded_file, mime_type):
    if uploaded_file is not None:
        bytes_data = uploaded_file.getvalue()
        image_parts = [
            {
                "mime_type": mime_type,  # Use the passed mime_type
                "data": bytes_data
            }
        ]
        return image_parts
    else:
        raise FileNotFoundError("No file uploaded")

def preprocess_image(image):
    return image.resize((800, 800))

def calculate_bmi(weight, height, gender):
    if height <= 0:
        return None, "Unknown"
    bmi = weight / (height ** 2)
    
    # Adjust BMI interpretation based on gender
    if gender == 'Male':
        if bmi < 18.5:
            category = "Underweight"
        elif 18.5 <= bmi < 24.9:
            category = "Normal weight"
        elif 25 <= bmi < 29.9:
            category = "Overweight"
        else:
            category = "Obesity"
    elif gender == 'Female':
        if bmi < 19.0:
            category = "Underweight"
        elif 19.0 <= bmi < 24.0:
            category = "Normal weight"
        elif 24.0 <= bmi < 29.0:
            category = "Overweight"
        else:
            category = "Obesity"
    else:
        category = "Unknown"
    
    return bmi, category

def daily_calorie_needs(weight, height, age, gender, activity_level):
    if gender == 'Male':
        bmr = 10 * weight + 6.25 * height * 100 - 5 * age + 5
    elif gender == 'Female':
        bmr = 10 * weight + 6.25 * height * 100 - 5 * age - 161
    else:
        bmr = 0
    
    # Adjust for activity level
    activity_multipliers = {
        'Sedentary': 1.2,
        'Moderately Active': 1.55,
        'Active': 1.9
    }
    
    multiplier = activity_multipliers.get(activity_level, 1.2)
    daily_calories = bmr * multiplier
    return daily_calories

def generate_nutrition_advice(bmi_status, health_goal, dietary_preference):
    # Provide detailed nutritional advice based on BMI status, health goal, and dietary preference
    advice = []
    
    if bmi_status in ["Underweight", "Normal weight"]:
        if health_goal == "Weight Loss":
            advice.append("To lose weight, focus on a balanced diet with a calorie deficit.")
        elif health_goal == "Muscle Gain":
            advice.append("To gain muscle, ensure adequate protein intake and strength training.")
    elif bmi_status in ["Overweight", "Obesity"]:
        if health_goal == "Weight Loss":
            advice.append("To lose weight, focus on reducing calorie intake and increasing physical activity.")
        elif health_goal == "Muscle Gain":
            advice.append("To gain muscle, incorporate strength training while managing caloric intake.")
    
    if dietary_preference == "Vegetarian":
        advice.append("Include a variety of plant-based proteins and ensure sufficient iron and B12 intake.")
    elif dietary_preference == "Vegan":
        advice.append("Ensure adequate protein intake and consider supplements for B12 and iron.")
    elif dietary_preference == "Gluten-Free":
        advice.append("Focus on naturally gluten-free grains and avoid processed gluten-free products that may be high in sugar.")
    
    return "\n".join(advice)

def clean_response(response_text):
    phrases_to_remove = [
        "It's difficult to determine the exact calorie count",
        "without knowing the specific ingredients and quantities used",
        "A calorie counter would need to know the specific ingredients",
        "accurately calculate the calories"
    ]
    
    for phrase in phrases_to_remove:
        response_text = response_text.replace(phrase, "")
    
    response_text = response_text.replace("However,", "").strip()
    return response_text

# Initialize the Streamlit app
st.set_page_config(page_title="Gemini Health App", layout="wide")

# Inject custom CSS to hide Streamlit specific UI elements
st.markdown(
    """
    <style>
    .css-1u6bn8v {display: none;} /* Hide Streamlit menu */
    .css-1tq3mc4 {display: none;} /* Hide Streamlit footer */
    </style>
    """, unsafe_allow_html=True
)

st.header("Health App by Zeeshan Faraz")

st.info("Upload an image of your meal or use the camera to take a photo. Click the button to get nutritional information.")

# Create two columns for layout
col1, col2 = st.columns([2, 1])

with col1:
    # Option for image upload or camera input
    upload_option = st.selectbox("Choose image source", ["Upload an Image", "Take a Photo"])

    uploaded_file = None
    camera_image = None
    mime_type = None

    if upload_option == "Upload an Image":
        uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])
        if uploaded_file is not None:
            mime_type = uploaded_file.type
            image = Image.open(uploaded_file)
            image = preprocess_image(image)  # Optional preprocessing
            st.image(image, caption="Uploaded Image.", use_column_width=True)

    elif upload_option == "Take a Photo":
        camera_image = st.camera_input("Take a photo")

        if camera_image is not None:
            image_bytes = io.BytesIO(camera_image.getvalue())
            mime_type = "image/jpeg"  # Assuming JPEG for camera input
            image_data = input_image_setup(io.BytesIO(image_bytes.getvalue()), mime_type)
            image = Image.open(image_data[0]["data"])
            image = preprocess_image(image)  # Optional preprocessing
            st.image(image, caption="Captured Image.", use_column_width=True)

with col2:
    # BMI Calculator
    st.sidebar.header("BMI Calculator")
    weight = st.sidebar.number_input("Enter your weight (kg):", min_value=0.0, format="%.1f")
    height = st.sidebar.number_input("Enter your height (m):", min_value=0.0, format="%.2f")
    age = st.sidebar.number_input("Enter your age:", min_value=0, format="%d")
    gender = st.sidebar.selectbox("Select your gender:", ["Male", "Female"])
    activity_level = st.sidebar.selectbox("Select your activity level:", ["Sedentary", "Moderately Active", "Active"])
    health_goal = st.sidebar.selectbox("Select your health goal:", ["Maintain Weight", "Weight Loss", "Muscle Gain"])
    dietary_preference = st.sidebar.selectbox("Select your dietary preference:", ["None", "Vegetarian", "Vegan", "Gluten-Free"])

# Default values for BMI calculation
daily_calories = None

if weight > 0 and height > 0:
    bmi, bmi_status = calculate_bmi(weight, height, gender)
    daily_calories = daily_calorie_needs(weight, height, age, gender, activity_level)
    nutrition_advice = generate_nutrition_advice(bmi_status, health_goal, dietary_preference)
    st.sidebar.write(f"Your BMI is: {bmi:.2f}")
    st.sidebar.write(f"BMI Category: {bmi_status}")
    st.sidebar.write(f"Daily Caloric Needs: {daily_calories:.0f} calories")
    st.sidebar.write("Nutrition Advice:")
    st.sidebar.write(nutrition_advice)

# Button to get nutritional information
submit = st.button("Tell me about the total calories")

# Refined prompt for the model
prompt = """
You are an expert in nutrition. Analyze the image provided and identify the food items. Calculate the total calories of the meal based on typical ingredient values and provide the calorie content of each item in the following format:

1. Item 1 - number of calories
2. Item 2 - number of calories
...
Include the total calorie count and give positive, constructive feedback on the meal's healthiness.

If exact calorie counts cannot be determined, use general estimates based on standard ingredient values and provide suggestions to make the meal healthier.
"""

if submit:
    if uploaded_file is not None or camera_image is not None:
        if uploaded_file is not None:
            image_data = input_image_setup(uploaded_file, mime_type)
        else:
            image_data = input_image_setup(io.BytesIO(camera_image.getvalue()), mime_type)

        with st.spinner('Processing...'):
            response = get_gemini_response(prompt, image_data)
            if response:
                st.subheader("The Response is")
                st.write(response)
                if daily_calories is not None:
                    st.write(f"Note: Your daily caloric needs are approximately {daily_calories:.0f} calories.")
                    st.write("Ensure that your daily calorie intake aligns with your health goals.")
            else:
                st.write("The response could not be processed.")
        sleep(1)  # Delay to avoid hitting API limits
    else:
        st.error("Please upload an image or take a photo to proceed.")

# Encourage BMI Calculator Use
if not (weight > 0 and height > 0):
    st.subheader("Get Accurate Caloric Needs")
    st.write("To get personalized daily calorie intake recommendations based on your health profile, please use the BMI calculator in the sidebar.")
    st.write("By entering your weight, height, gender, age, and activity level, you can receive a tailored caloric intake estimate that suits your lifestyle and health goals.")
