from flask import Flask, request, render_template_string
import subprocess
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit

HTML_FORM = """
<!DOCTYPE html>
<html>
<head>
    <title>Code Submission</title>
</head>
<body>
    <h2>Submit your Python code</h2>
    <form action="/submit" method="post" enctype="multipart/form-data">
        <label for="problem_number">Problem Number:</label>
        <input type="number" name="problem_number" id="problem_number" required><br><br>
        <input type="file" name="file" accept=".py" required>
        <input type="submit" value="Submit">
    </form>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_FORM)

def run_test_cases(problem_number, script_path):
    test_case_dir = f"problem{problem_number}"
    input_dir = os.path.join(test_case_dir, "inputs")
    output_dir = os.path.join(test_case_dir, "outputs")

    passed_tests = 0
    total_tests = 0

    for input_file in os.listdir(input_dir):
        if input_file.startswith("input") and input_file.endswith(".txt"):
            total_tests += 1
            output_file = input_file.replace("input", "output")

            with open(os.path.join(input_dir, input_file), 'r') as inp:
                expected_output = open(os.path.join(output_dir, output_file), 'r').read().strip()
                process = subprocess.run(['python3', script_path], stdin=inp, capture_output=True, text=True)
                actual_output = process.stdout.strip()

                if actual_output == expected_output:
                    passed_tests += 1

    return passed_tests, total_tests

@app.route('/submit', methods=['POST'])
def submit():
    problem_number = request.form['problem_number']
    file = request.files['file']
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        passed, total = run_test_cases(problem_number, filepath)
        return f'Passed {passed} out of {total} test cases.'

    return 'No file uploaded.'

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)
