import streamlit as st
import requests
import unicodedata
from bs4 import BeautifulSoup
import openai

openai.api_key = "sk-proj-NYCYBw8aL6fLdGxYF6jnT3BlbkFJOUzlBuYU9iOjqJD854oW"

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

def generate_faqs(content):
    if content == "Blocked by Zscaler":
        return "The request was blocked by Zscaler. Please try using a different network or a VPN."
    prompt = f"Read the following content and generate potential FAQs that a merchant could ask tech support:\n\n{content}"
    st.write("### Debug: Generated Prompt")
    st.write(prompt)
    faqs = chat_with_gpt(prompt)
    st.write("### Debug: API Response")
    st.write(faqs)
    return faqs

# Streamlit UI
st.set_page_config(page_title="Web Scraper with GPT-3.5 Turbo", page_icon="🤖")

st.title("🤖 Web Scraper with GPT-3.5 Turbo")
st.write("Enter the URL of the document you want to scrape and generate FAQs from.")

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
                    st.write("### Generated FAQs")
                    st.write(faqs)
                else:
                    st.error(content)  # Show the error message directly
            except Exception as e:
                st.error(f"An error occurred: {e}")

# Initialize session state for chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Text input for user prompt
user_input = st.text_input("Chat with GPT-3.5 Turbo: ", key="input")

# Submit button to process the user input
if st.button("Send"):
    if user_input:
        response = chat_with_gpt(user_input)
        st.session_state.chat_history.append(f"You: {user_input}")
        st.session_state.chat_history.append(f"Chatbot: {response}")
        st.experimental_rerun()

# Display chat history
if st.session_state.chat_history:
    for message in st.session_state.chat_history:
        st.write(message)

# Clear chat history button
if st.button("Clear Chat"):
    st.session_state.chat_history = []
    st.experimental_rerun()
