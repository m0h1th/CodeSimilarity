from flask import Flask, request, render_template_string, render_template, redirect, url_for
import os
import subprocess
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit
app.config['PROBLEMS_FOLDER'] = 'problems'

@app.route('/')
def index():
    return render_template('index.html')

def run_test_cases(problem_number, script_path):
    test_case_dir = os.path.join(app.config['PROBLEMS_FOLDER'], f"problem{problem_number}")
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
                try:
                    process = subprocess.run(['python', script_path], stdin=inp, capture_output=True, text=True)
                except FileNotFoundError:
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

@app.route('/description/<int:problem_number>')
def get_description(problem_number):
    description_path = os.path.join(app.config['PROBLEMS_FOLDER'], f'problem{problem_number}', 'description.md')
    if os.path.exists(description_path):
        with open(description_path, 'r') as file:
            content = file.read()
        return content
    return 'Description not found.'

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        problem_number = request.form['problem_number']
        description = request.form['description']
        input_examples = request.form.getlist('input')
        output_examples = request.form.getlist('output')

        # Save description
        save_description(problem_number, description, input_examples[0], output_examples[0])

        # Save input and output examples
        save_examples(problem_number, input_examples, output_examples)

        return redirect(url_for('index'))

    return render_template('admin.html')

def save_description(problem_number, description, input_example, output_example):
    problem_dir = os.path.join(app.config['PROBLEMS_FOLDER'], f"problem{problem_number}")
    os.makedirs(problem_dir, exist_ok=True)

    with open(os.path.join(problem_dir, 'description.md'), 'w') as desc_file:
        desc_file.write(f"# Problem: {problem_number}\n\n")
        desc_file.write(f"{description.strip()}\n\n")
        desc_file.write("## Example\n")
        desc_file.write("Input:\n```\n")
        desc_file.write(f"{input_example.strip()}\n")
        desc_file.write("```\n")
        desc_file.write("Output:\n```\n")
        desc_file.write(f"{output_example.strip()}\n")
        desc_file.write("```\n")

def save_examples(problem_number, input_examples, output_examples):
    problem_dir = os.path.join(app.config['PROBLEMS_FOLDER'], f"problem{problem_number}")

    input_dir = os.path.join(problem_dir, 'inputs')
    os.makedirs(input_dir, exist_ok=True)

    output_dir = os.path.join(problem_dir, 'outputs')
    os.makedirs(output_dir, exist_ok=True)

    # Save as many examples as provided by the teacher
    for i, (input_example, output_example) in enumerate(zip(input_examples, output_examples)):
        with open(os.path.join(input_dir, f'input{i+1}.txt'), 'w') as input_file:
            input_file.write(input_example.strip() + '\n')
        with open(os.path.join(output_dir, f'output{i+1}.txt'), 'w') as output_file:
            output_file.write(output_example.strip() + '\n')

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    if not os.path.exists(app.config['PROBLEMS_FOLDER']):
        os.makedirs(app.config['PROBLEMS_FOLDER'])
    app.run(debug=True)
