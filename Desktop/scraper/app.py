import streamlit as st
import requests
import unicodedata
from bs4 import BeautifulSoup
import openai
from dotenv import load_dotenv
import os
import pandas as pd

# Load environment variables from .env file
load_dotenv()

# Get the API key from the environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")

def chat_with_gpt(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        st.error(f"Error in chat_with_gpt: {e}")
        return f"Error: {e}"

def scrape_content(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        if 'text/html' in response.headers['Content-Type']:
            if "Zscaler" in response.text:
                return "Blocked by Zscaler"
            soup = BeautifulSoup(response.text, 'html.parser')
            paragraphs = soup.select('p, ul li')
            content = ' '.join([paragraph.get_text() for paragraph in paragraphs])
            content = unicodedata.normalize('NFKD', content).encode('ascii', 'ignore').decode()
            return content
        else:
            return f"Unexpected content type: {response.headers['Content-Type']}"
    except Exception as e:
        st.error(f"Error in scrape_content: {e}")
        return f"Error: {e}"

def read_excel(file):
    try:
        df = pd.read_excel(file, engine='openpyxl')
        questions = df['summarizedQuestion'].tolist()
        responses = df['FirstReply'].tolist()
        return questions, responses
    except Exception as e:
        st.error(f"Error in read_excel: {e}")
        return [], []

def generate_faqs(content, source_type='web'):
    if source_type == 'web' and content == "Blocked by Zscaler":
        return "The request was blocked by Zscaler. Please try using a different network or a VPN."
    
    if source_type == 'web':
        prompt = f"Read the following content and generate 20 detailed FAQs with answers that a merchant could ask tech support:\n\n{content}"
    else:
        prompt = "Based on the following questions and responses, generate simplified questions and their detailed answers:\n\n"
        for question, response in content:
            prompt += f"Summarized Question: {question}\nEngineer Reply: {response}\n\n"
    
    st.write("### Debug: Generated Prompt")
    st.write(prompt)
    faqs = chat_with_gpt(prompt)
    st.write("### Debug: API Response")
    st.write(faqs)
    return faqs

# Streamlit UI
st.set_page_config(page_title="FAQ Wizard with GPT-3.5 Turbo", page_icon="🤖")

# Display the PayPal logo and title
st.image("/Users/asadrizvi/Desktop/scraper/Paypal.png", width=50)
st.title("FAQ Wizard")
st.write("Enter the URL of the document you want to scrape and generate FAQs from, or upload an Excel file.")

# URL input for scraping
url_input = st.text_input("Document URL: ", key="url_input")

if st.button("Scrape and Generate FAQs"):
    if url_input:
        with st.spinner("Scraping content and generating FAQs..."):
            try:
                content = scrape_content(url_input)
                st.write("### Debug: Scraped Content")
                st.write(content[:2000] + '...')  # Display a preview of the content

                if content and "Error" not in content:
                    faqs = generate_faqs(content)
                    st.write("### Generated FAQs with Answers")
                    st.write(faqs)
                else:
                    st.error(content)  # Show the error message directly
            except Exception as e:
                st.error(f"An error occurred: {e}")

# File upload for Excel files
uploaded_file = st.file_uploader("Choose an Excel file", type="xlsx")

if st.button("Read Excel and Generate FAQs"):
    if uploaded_file:
        with st.spinner("Reading Excel file and generating FAQs..."):
            try:
                questions, responses = read_excel(uploaded_file)
                if questions and responses:
                    content = list(zip(questions, responses))
                    faqs = generate_faqs(content, source_type='excel')
                    st.write("### Generated FAQs with Answers")
                    st.write(faqs)
                else:
                    st.error("Failed to read content from the provided Excel file.")
            except Exception as e:
                st.error(f"An error occurred: {e}")

# Initialize session state for chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Function to display chat history
def display_chat():
    for message in st.session_state.chat_history:
        st.write(message)

# Sidebar for chat toggle
with st.sidebar:
    if st.button("Chat with AI Assistant"):
        st.session_state.show_chat = not st.session_state.get("show_chat", False)

# Chat interface
if st.session_state.get("show_chat", False):
    st.markdown("<div class='chat-popup show' id='chatPopup'>", unsafe_allow_html=True)
    st.markdown("<div class='chat-container' id='chatContainer'>", unsafe_allow_html=True)
    display_chat()
    st.markdown("</div>", unsafe_allow_html=True)
    user_input = st.text_input("Type your message here...", key="chat_input")
    if st.button("Send", key="send_button"):
        if user_input:
            st.session_state.chat_history.append(f"You: {user_input}")
            response = chat_with_gpt(user_input)
            st.session_state.chat_history.append(f"Chatbot: {response}")
            st.experimental_rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# Clear chat history button
if st.sidebar.button("Clear Chat"):
    st.session_state.chat_history = []
    st.experimental_rerun()
