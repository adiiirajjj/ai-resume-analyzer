from flask import Flask, render_template, request, jsonify
import os
from anthropic import Anthropic

app = Flask(__name__)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze_resume():
    try:
        # Get resume text from the form
        resume_text = request.form.get('resume_text', '')
        
        if not resume_text or resume_text.strip() == '':
            return jsonify({'error': 'Please paste your resume text'}), 400
        
        # Get job role
        job_role = request.form.get('job_role', 'Software Developer')
        
        # Call AI to analyze
        analysis = analyze_with_ai(resume_text, job_role)
        
        return jsonify({'success': True, 'analysis': analysis})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def analyze_with_ai(resume_text, job_role):
    """
    Analyzes resume text and provides feedback.
    Currently using rule-based analysis.
    """
    import re
    
    # Simple analysis based on content
    word_count = len(resume_text.split())
    has_email = bool(re.search(r'\S+@\S+', resume_text))
    has_phone = bool(re.search(r'\d{10}|\d{3}[-.\s]\d{3}[-.\s]\d{4}', resume_text))
    has_projects = 'project' in resume_text.lower()
    has_metrics = bool(re.search(r'\d+%|\d+x', resume_text))
    
    # Calculate score
    score = 5
    if word_count > 200: score += 1
    if has_email: score += 1
    if has_phone: score += 0.5
    if has_projects: score += 1
    if has_metrics: score += 1.5
    
    score = min(10, score)
    
    return {
        'score': round(score, 1),
        'strengths': [
            f'Resume length is {"appropriate" if 200 < word_count < 800 else "could be optimized"} ({word_count} words)',
            'Clear structure and organization' if word_count > 100 else 'Basic information provided',
            'Contact information included' if has_email or has_phone else 'Professional format used'
        ],
        'weaknesses': [
            'Add quantifiable achievements (e.g., "Increased efficiency by 40%")' if not has_metrics else 'Could include more specific metrics',
            'Include relevant projects with links' if not has_projects else 'Add more technical details to projects',
            f'Missing {"email" if not has_email else "phone number"}' if not (has_email and has_phone) else 'Consider adding more keywords for ATS systems'
        ],
        'suggestions': [
            'Add 2-3 strong projects with GitHub links and tech stack',
            'Include metrics and numbers (e.g., "Built app used by 500+ users")',
            'Add a professional summary at the top (3-4 lines)',
            f'Optimize for {job_role} role by including relevant keywords',
            'Ensure all contact information is current and professional'
        ]
    }

if __name__ == '__main__':
    app.run(debug=True, port=5000)