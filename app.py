from flask import Flask, request, jsonify
import json
import random

app = Flask(__name__)

def generate_swift_question(platforms, topics=None, keywords=None):
    """
    Генерує повний JSON-запис питання по Swift у потрібному форматі.
    """
    all_topics = {
        "Threading & Concurrency": "What is `CheckedContinuation` in Swift Concurrency, and how does it work?",
        "Memory Management": "How does ARC (Automatic Reference Counting) work in Swift?",
        "Swift Performance Optimization": "What techniques can be used to optimize Swift code?",
        "Error Handling": "How does Swift handle errors using the 'do-catch' mechanism?"
    }
    
    if topics is None:
        topics = list(all_topics.keys())
    else:
        topics = [topic for topic in topics if topic in all_topics]
    
    if not topics:
        return {"error": "No valid topics provided."}
    
    questions = []
    for topic in topics:
        question_text = all_topics[topic]
        tags = [topic, "Swift"] + (keywords if keywords else [])
        
        levels = [
            {
                "name": "Beginner Level",
                "answer": f"{question_text} - basic explanation.",
                "tests": [
                    {"question": "What is the purpose of this concept in Swift?", "correctAnswer": "To improve efficiency and safety."},
                    {"question": "Which Swift feature supports this concept?", "correctAnswer": "Async/Await."},
                    {"question": "How does it affect performance?", "correctAnswer": "It optimizes memory and execution flow."}
                ]
            },
            {
                "name": "Intermediate Level",
                "answer": f"{question_text} - deeper insight with practical examples.",
                "tests": [
                    {"question": "How is this implemented in Swift?", "correctAnswer": "Using specific API calls."},
                    {"question": "What common issues can occur?", "correctAnswer": "Deadlocks and race conditions."},
                    {"question": "How can developers optimize it?", "correctAnswer": "By using best practices and debugging tools."}
                ]
            },
            {
                "name": "Advanced Level",
                "answer": f"{question_text} - detailed analysis and performance considerations.",
                "tests": [
                    {"question": "What advanced techniques improve this?", "correctAnswer": "Custom thread management."},
                    {"question": "What are potential drawbacks?", "correctAnswer": "Increased complexity and debugging difficulty."},
                    {"question": "How does Swift handle edge cases?", "correctAnswer": "Through specific runtime checks."}
                ]
            }
        ]
        
        questions.append({
            "id": str(random.randint(100, 999)),
            "topic": [{"name": topic, "platform": platform} for platform in platforms],
            "text": question_text,
            "tags": tags,
            "answerLevels": levels
        })
    
    return questions

@app.route("/generate_question", methods=["POST"])
def api_generate_question():
    data = request.get_json()
    platforms = data.get("platforms", ["Apple"])
    topics = data.get("topics")
    keywords = data.get("keywords")
    
    if not isinstance(platforms, list):
        platforms = [platforms]
    
    questions = generate_swift_question(platforms, topics, keywords)
    return jsonify(questions)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
