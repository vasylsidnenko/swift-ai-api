import os
import json

# Get the absolute path to the test data file
current_dir = os.path.dirname(os.path.abspath(__file__))
test_data_path = os.path.join(current_dir, 'test_data', 'generate_test_result.json')

with open(test_data_path, 'r') as file:
    generated = json.load(file) 