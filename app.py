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
        return [{"error": "No valid topics provided."}]
    
    questions = []
    for topic in topics:
        question_text = all_topics[topic]
        tags = [topic, "Swift"] + (keywords if keywords else [])
        
        answer_levels = [
            {
                "name": "Beginner Level",
                "answer": "`CheckedContinuation` is a mechanism in Swift Concurrency that allows bridging between synchronous and asynchronous code. It ensures safety by verifying that the continuation is resumed exactly once.",
                "tests": [
                    {"question": "Which of the following best describes `CheckedContinuation`?\n\na) A way to call synchronous functions inside `async` code.\nb) A mechanism to transition from callback-based APIs to async/await.\nc) A tool for executing code on the main thread.\nd) A type used for thread synchronization.", "correctAnswer": "b) A mechanism to transition from callback-based APIs to async/await."}
                ]
            },
            {
                "name": "Intermediate Level",
                "answer": "`CheckedContinuation` is used when interfacing with callback-based or delegate-based APIs in an async/await environment. It ensures safety by detecting double-resume or missing resume issues at runtime.",
                "tests": [
                    {"question": "How does `CheckedContinuation` differ from `UnsafeContinuation` in Swift?\n\na) `CheckedContinuation` enforces safety checks to ensure proper usage.\nb) `UnsafeContinuation` is recommended for all cases.\nc) `CheckedContinuation` runs only on the main thread.\nd) `CheckedContinuation` allows multiple resumptions.", "correctAnswer": "a) `CheckedContinuation` enforces safety checks to ensure proper usage."}
                ]
            },
            {
                "name": "Advanced Level",
                "answer": "`CheckedContinuation` provides a structured way to convert existing callback-based functions to async/await. It ensures that functions follow the Swift Concurrency model by enforcing single-resume rules.",
                "tests": [
                    {"question": "What does `CheckedContinuation` do if a continuation is never resumed?\n\na) The task waits indefinitely.\nb) The app crashes immediately.\nc) A runtime warning is logged, and the app may hang.\nd) Swift automatically cancels the operation.", "correctAnswer": "c) A runtime warning is logged, and the app may hang."}
                ]
            }
        ]
        
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
    
    app.run(host="0.0.0.0", port=10000, debug=False)
