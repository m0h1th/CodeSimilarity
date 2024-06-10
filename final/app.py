from flask import Flask, request, render_template_string, render_template, redirect, url_for
import os
import subprocess
import time
from werkzeug.utils import secure_filename
from language_parser.driver import run_test

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit
app.config['PROBLEMS_FOLDER'] = 'problems'

difficulty_to_marks = {
    'easy': 1,
    'medium': 2,
    'hard': 3
}

@app.route('/')
def index():
    return render_template('index.html')

def run_test_cases(problem_number, script_path):
    test_case_dir = os.path.join(app.config['PROBLEMS_FOLDER'], f"problem{problem_number}")
    input_dir = os.path.join(test_case_dir, "inputs")
    output_dir = os.path.join(test_case_dir, "outputs")
    metadata_dir = os.path.join(test_case_dir, "metadata")

    total_marks = 0
    obtained_marks = 0

    script_extension = os.path.splitext(script_path)[1]
    is_python = script_extension == ".py"
    is_c = script_extension == ".c"
    
    if is_c:
        executable_path = script_path.replace(".c", "")
        compile_start_time = time.time()
        compile_process = subprocess.run(['gcc', script_path, '-o', executable_path], capture_output=True, text=True)
        compile_end_time = time.time()
        compile_time = compile_end_time - compile_start_time
        if compile_process.returncode != 0:
            return f"Compilation failed: {compile_process.stderr}", 0, 0

    for input_file in os.listdir(input_dir):
        if input_file.startswith("input") and input_file.endswith(".txt"):
            test_index = input_file.replace("input", "").replace(".txt", "")
            output_file = f"output{test_index}.txt"
            metadata_file = f"metadata{test_index}.txt"

            with open(os.path.join(input_dir, input_file), 'r') as inp:
                expected_output = open(os.path.join(output_dir, output_file), 'r').read().strip()
                with open(os.path.join(metadata_dir, metadata_file), 'r') as meta:
                    difficulty, marks = meta.read().strip().split('\n')
                    marks = int(marks)
                    total_marks += marks

                if is_python:
                    start_time = time.time()
                    try:
                        process = subprocess.run(['python', script_path], stdin=inp, capture_output=True, text=True)
                    except FileNotFoundError:
                        process = subprocess.run(['python3', script_path], stdin=inp, capture_output=True, text=True)
                    end_time = time.time()
                elif is_c:
                    start_time = time.time()
                    process = subprocess.run([executable_path], stdin=inp, capture_output=True, text=True)
                    end_time = time.time()

                runtime = end_time - start_time
                actual_output = process.stdout.strip()

                if actual_output == expected_output:
                    obtained_marks += marks

                print(f"Test case {test_index}: runtime = {runtime:.4f} seconds")

    if is_c:
        return obtained_marks, total_marks, compile_time
    else:
        return obtained_marks, total_marks, 0

@app.route('/submit', methods=['POST'])
def submit():
    problem_number = request.form['problem_number']
    file = request.files['file']
    if file:
        filename = secure_filename(file.filename)
        if not os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], f'problem{problem_number}')):
            os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], f'problem{problem_number}'))
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], f'problem{problem_number}', filename)
        file.save(filepath)

        obtained_marks, total_marks, compile_time = run_test_cases(problem_number, filepath)
        return f'You scored {obtained_marks} out of {total_marks} marks.\nCompilation time: {compile_time:.4f} seconds.'

    return 'No file uploaded.'

@app.route('/description/<int:problem_number>')
def get_description(problem_number):
    description_path = os.path.join(app.config['PROBLEMS_FOLDER'], f'problem{problem_number}', 'description.md')
    if os.path.exists(description_path):
        with open(description_path, 'r') as file:
            content = file.read()
        return content
    return 'Description not found.'

@app.route('/result/<int:problem_number>')
def get_result(problem_number):
    try:
        data_python, data_c = run_test(f'uploads/problem{problem_number}')
        return render_template('result.html', data_python=data_python, data_c=data_c)
    except:
        return "No results found."

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        problem_number = request.form['problem_number']
        description = request.form['description']
        input_examples = request.form.getlist('input')
        output_examples = request.form.getlist('output')
        difficulties = request.form.getlist('difficulty')

        # Save description
        save_description(problem_number, description, input_examples[0], output_examples[0])

        # Save input and output examples, and difficulties
        save_examples(problem_number, input_examples, output_examples, difficulties)

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

def save_examples(problem_number, input_examples, output_examples, difficulties):
    problem_dir = os.path.join(app.config['PROBLEMS_FOLDER'], f"problem{problem_number}")

    input_dir = os.path.join(problem_dir, 'inputs')
    os.makedirs(input_dir, exist_ok=True)

    output_dir = os.path.join(problem_dir, 'outputs')
    os.makedirs(output_dir, exist_ok=True)

    metadata_dir = os.path.join(problem_dir, 'metadata')
    os.makedirs(metadata_dir, exist_ok=True)

    # Save as many examples as provided by the teacher
    for i, (input_example, output_example, difficulty) in enumerate(zip(input_examples, output_examples, difficulties)):
        marks = difficulty_to_marks[difficulty]
        with open(os.path.join(input_dir, f'input{i+1}.txt'), 'w') as input_file:
            input_file.write(input_example.strip() + '\n')
        with open(os.path.join(output_dir, f'output{i+1}.txt'), 'w') as output_file:
            output_file.write(output_example.strip() + '\n')
        with open(os.path.join(metadata_dir, f'metadata{i+1}.txt'), 'w') as metadata_file:
            metadata_file.write(f"{difficulty.strip()}\n{marks}\n")

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    if not os.path.exists(app.config['PROBLEMS_FOLDER']):
        os.makedirs(app.config['PROBLEMS_FOLDER'])
    app.run(debug=True)
