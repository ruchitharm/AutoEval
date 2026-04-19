from flask import Flask, render_template, request
import os
from ocr import extract_text
from similarity import calculate_similarity

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    model_answer = request.form['model_answer']

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    # OCR
    extracted_text = extract_text(filepath)

    # Similarity
    score = calculate_similarity(extracted_text, model_answer)

    # Marks
    marks = round(score * 10, 2)

    return render_template('result.html',
                           extracted_text=extracted_text,
                           score=score,
                           marks=marks)

if __name__ == "__main__":
    app.run(debug=True)