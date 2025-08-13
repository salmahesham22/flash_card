import streamlit as st
import os
from dotenv import load_dotenv
from pypdf import PdfReader
from openai import OpenAI
import re
import json


load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("API key is not found")


client = OpenAI(api_key=api_key)


def read_pdf(file):
    pdf = PdfReader(file)
    text = ""
    for page in pdf.pages:
        text += page.extract_text() + "\n"
    return text


def generate_flashcards(text, num_cards, language="auto"):
    lang_prompt = "" if language == "auto" else f"Generate in {language}."
    prompt = f"""
    You are a smart assistant. Create {num_cards} flashcards from the text below.

    STRICT RULES:
    - Return ONLY a valid JSON array
    - Each element must have: "question" and "answer"
    - No explanations, no extra text before or after JSON
    - Keep language of output same as input unless specified.

    {lang_prompt}

    Text:
    {text}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    content = response.choices[0].message.content.strip()

    
    try:
        json_match = re.search(r"\[.*\]", content, re.S)
        if json_match:
            content = json_match.group(0)
        cards = json.loads(content)
        if isinstance(cards, dict):
            cards = [cards]
        return [
            {"question": c.get("question", ""), "answer": c.get("answer", "")}
            for c in cards if isinstance(c, dict)
        ]
    except Exception as e:
        print("JSON parsing error:", e)
        return []


st.title("📚 Flash Card Generator")

uploaded_file = st.file_uploader("📂 Upload PDF or enter text", type=["pdf", "txt"])
notes_text = ""

if uploaded_file:
    if uploaded_file.type == "application/pdf":
        notes_text = read_pdf(uploaded_file)
    else:
        notes_text = uploaded_file.read().decode("utf-8")
else:
    notes_text = st.text_area("✏️ Or write your text here:")

num_cards = st.slider("🔢 Number of flashcards", min_value=1, max_value=20, value=5)

if st.button("✨ Generate Flashcards"):
    if notes_text.strip():
        flashcards = generate_flashcards(notes_text, num_cards)

        if flashcards:
            st.session_state["flashcards"] = flashcards
            st.session_state["answers_state"] = [False] * len(flashcards)
        else:
            st.warning("⚠️ Could not generate flashcards in a structured format.")
    else:
        st.warning("⚠️ Please upload a file or write text first.")


if "flashcards" in st.session_state:
    st.subheader("📌 Flashcards:")
    for i, card in enumerate(st.session_state["flashcards"]):
        st.write(f"Q{i+1}: {card['question']}")
        btn_label = "Show Answer" if not st.session_state["answers_state"][i] else "Hide Answer"
        if st.button(btn_label, key=f"btn_{i}"):
            st.session_state["answers_state"][i] = not st.session_state["answers_state"][i]
        if st.session_state["answers_state"][i]:
            st.write(f"A{i+1}: {card['answer']}")
        st.write("---")
