from flask import Flask, request, jsonify
import json
import random

app = Flask(__name__)

def generate_swift_question(platform, topics=None, keywords=None):
    all_topics = ["Memory Management", "Threading & Concurrency", "Swift Performance Optimization", "Error Handling"]
    if topics is None:
        topics = all_topics
    if keywords:
        topics = [topic for topic in all_topics if any(kw.lower() in topic.lower() for kw in keywords)]
        if not topics:
            topics = all_topics

    question_text = "How does ARC (Automatic Reference Counting) work in Swift?"
    tags = ["Memory Management", "ARC", "Retain Cycle", "Performance"]
    
    levels = [
        {"name": "Beginner Level", "answer": "ARC manages memory by tracking references.",
         "tests": [
             {"question": "What does ARC stand for?", "correctAnswer": "Automatic Reference Counting"},
             {"question": "How does ARC manage memory?", "correctAnswer": "By tracking strong references."}
         ]},
        {"name": "Intermediate Level", "answer": "ARC prevents memory leaks but needs careful management.",
         "tests": [
             {"question": "What is a retain cycle?", "correctAnswer": "Two objects holding strong references."},
             {"question": "Which type of reference helps break retain cycles?", "correctAnswer": "Weak reference."}
         ]},
        {"name": "Advanced Level", "answer": "ARC integrates with Swift runtime to optimize performance.",
         "tests": [
             {"question": "Which Swift tool helps debug memory leaks?", "correctAnswer": "Instruments (Memory Graph Debugger)"},
             {"question": "What happens if an unowned reference is accessed after deallocation?", "correctAnswer": "The app crashes."}
         ]}
    ]

    return {
        "id": str(random.randint(100, 999)),
        "topic": [{"name": topic, "platform": platform} for topic in topics],
        "text": question_text,
        "tags": tags,
        "answerLevels": levels
    }

@app.route("/generate_question", methods=["POST"])
def api_generate_question():
    data = request.get_json()
    platform = data.get("platform", "Apple")
    topics = data.get("topics")
    keywords = data.get("keywords")
    question = generate_swift_question(platform, topics, keywords)
    return jsonify(question)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)