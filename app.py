from flask import Flask, render_template, request, redirect, url_for, session
import requests
import PyPDF2
import g4f
from g4f import ChatCompletion
import io
import json
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a secure key in production

# --------------------------
# JSON Database Helper Functions
# --------------------------
def load_users():
    if os.path.exists('users.json'):
        with open('users.json', 'r') as f:
            try:
                users = json.load(f)
            except json.JSONDecodeError:
                users = {}
    else:
        users = {}
    return users

def save_users(users):
    with open('users.json', 'w') as f:
        json.dump(users, f, indent=4)

# --------------------------
# GPT-4 Chat Functionality
# --------------------------
def generate_response(user_input):
    """
    Generate a response using GPT-4 via the g4f library.
    """
    try:
        response = ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": user_input}],
            temperature=0.6,
            top_p=0.9
        )
        return response.strip() if response else "Sorry, I didn't understand that."
    except Exception as e:
        return f"Error: {e}"

# --------------------------
# Document Summarization
# --------------------------
def summarize_text(text):
    """
    Summarize the given text by prompting the GPT-4 agent.
    """
    prompt = f"Please summarize the following document in a concise manner:\n\n{text}"
    summary = generate_response(prompt)
    return summary

# --------------------------
# Image Generation using pollinations.ai
# --------------------------
def generate_image(prompt):
    """
    Generate an image URL using pollinations.ai based on the given prompt.
    """
    image_url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt)}"
    return image_url

# --------------------------
# Routes
# --------------------------
@app.route('/index')
def index():
    return render_template('base.html')

# --- Chatbot Route ---
@app.route('/chatbot', methods=['GET', 'POST'])
def chatbot():
    response = None
    if request.method == 'POST':
        user_input = request.form['user_input']
        response = generate_response(user_input)
    return render_template('chatbot.html', response=response)

# --- Document Summarizer Route ---
@app.route('/document_summarizer', methods=['GET', 'POST'])
def document_summarizer():
    summary = None
    if request.method == 'POST':
        input_type = request.form['input_type']
        if input_type == 'text':
            doc_text = request.form['doc_text']
            summary = summarize_text(doc_text)
        else:
            pdf_file = request.files['pdf_file']
            if pdf_file:
                try:
                    pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_file.read()))
                    text = ""
                    for page in pdf_reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                    summary = summarize_text(text)
                except Exception as e:
                    summary = f"Error processing PDF: {e}"
    return render_template('document_summarizer.html', summary=summary)

# --- Code Assistant Route ---
@app.route('/code_assistant', methods=['GET', 'POST'])
def code_assistant():
    code_response = None
    if request.method == 'POST':
        code_input = request.form['code_input']
        prompt = f"Act as a coding assistant. {code_input}"
        code_response = generate_response(prompt)
    return render_template('code_assistant.html', code_response=code_response)

# --- Image Generator Route ---
@app.route('/image_generator', methods=['GET', 'POST'])
def image_generator():
    img_url = None
    if request.method == 'POST':
        img_prompt = request.form['img_prompt']
        img_url = generate_image(img_prompt)
    return render_template('image_generator.html', img_url=img_url)

# --- Login Route ---
@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = load_users()
        if username in users and users[username]['password'] == password:
            session['username'] = username
            return redirect(url_for('index'))
        else:
            error = "Invalid username or password."
    return render_template('login.html', error=error)

# --- Register Route ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = load_users()
        if username in users:
            error = "User already exists."
        else:
            users[username] = {'password': password}
            save_users(users)
            return redirect(url_for('login'))
    return render_template('register.html', error=error)

if __name__ == '__main__':
    app.run(debug=True)
