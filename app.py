from flask import Flask, request, jsonify
import json
import random

app = Flask(__name__)

def generate_swift_question(platforms, topics=None, keywords=None):
    """
    Генерує повний JSON-запис питання по Swift у потрібному форматі, включаючи унікальні відповіді та тести для кожної теми.
    """
    all_topics = {
        "Threading & Concurrency": {
            "question": "What is `CheckedContinuation` in Swift Concurrency, and how does it work?",
            "tags": ["Swift Concurrency", "CheckedContinuation", "Async/Await", "Threading"],
            "answers": {
                "Beginner Level": "`CheckedContinuation` is a mechanism in Swift Concurrency that allows bridging between synchronous and asynchronous code. It ensures safety by verifying that the continuation is resumed exactly once.",
                "Intermediate Level": "`CheckedContinuation` is used when interfacing with callback-based or delegate-based APIs in an async/await environment. It ensures safety by detecting double-resume or missing resume issues at runtime.",
                "Advanced Level": "`CheckedContinuation` provides a structured way to convert existing callback-based functions to async/await. It ensures that functions follow the Swift Concurrency model by enforcing single-resume rules."
            }
        },
        "Memory Management": {
            "question": "How does ARC (Automatic Reference Counting) work in Swift?",
            "tags": ["Memory Management", "ARC", "Retain Cycle", "Performance"],
            "answers": {
                "Beginner Level": "ARC automatically manages memory by tracking object references.",
                "Intermediate Level": "ARC ensures proper memory management but requires developers to handle retain cycles carefully.",
                "Advanced Level": "ARC integrates with Swift’s runtime to optimize performance and prevent memory leaks."
            }
        },
        "Swift Performance Optimization": {
            "question": "What techniques can be used to optimize Swift code?",
            "tags": ["Performance", "Optimization", "Swift"],
            "answers": {
                "Beginner Level": "Using compiler optimizations and efficient data structures.",
                "Intermediate Level": "Profiling with Instruments and optimizing memory allocation.",
                "Advanced Level": "Advanced techniques like inline caching and concurrency optimizations."
            }
        },
        "Error Handling": {
            "question": "How does Swift handle errors using the 'do-catch' mechanism?",
            "tags": ["Error Handling", "Swift", "Exception Handling"],
            "answers": {
                "Beginner Level": "Swift uses `do-catch` to handle errors gracefully.",
                "Intermediate Level": "Swift allows propagating errors using `throws` and `try` keywords.",
                "Advanced Level": "Advanced techniques include custom error types and recovery strategies."
            }
        }
    }
    
    if topics is None:
        topics = list(all_topics.keys())
    else:
        topics = [topic for topic in topics if topic in all_topics]
    
    if not topics:
        return [{"error": "No valid topics provided."}]
    
    questions = []
    for topic in topics:
        data = all_topics[topic]
        question_text = data["question"]
        tags = data["tags"] + (keywords if keywords else [])
        
        answer_levels = []
        for level, answer in data["answers"].items():
            tests = [
                {"question": f"Sample question 1 for {topic} at {level} level?", "correctAnswer": "Correct answer 1"},
                {"question": f"Sample question 2 for {topic} at {level} level?", "correctAnswer": "Correct answer 2"},
                {"question": f"Sample question 3 for {topic} at {level} level?", "correctAnswer": "Correct answer 3"}
            ]
            answer_levels.append({"name": level, "answer": answer, "tests": tests})
        
        questions.append({
            "id": str(random.randint(100, 999)),
            "topic": [{"name": topic, "platform": platform} for platform in platforms],
            "text": question_text,
            "tags": tags,
            "answerLevels": answer_levels
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
    # Локальний тест генерації питання
    test_data = generate_swift_question(["Apple"], ["Memory Management"], ["ARC", "Retain Cycle"])
    print(json.dumps(test_data, indent=4))
    
    try:
        app.run(host="0.0.0.0", port=10000, debug=False)
    except SystemExit:
        print("Flask application encountered a SystemExit error and was terminated.")
