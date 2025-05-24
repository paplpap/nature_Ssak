from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from RAG_model import double_rag

load_dotenv()

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/get_answer", methods=["POST"])
def get_answer():
    data = request.json
    question = data["question"]
    answer = double_rag(question)
    return jsonify({"answer": answer})

if __name__ == "__main__":
    app.run(debug=True)


