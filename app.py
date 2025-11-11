from flask import Flask, render_template, request, jsonify
import os

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
    Analyzes resume using Hugging Face's free AI models
    """
    from huggingface_hub import InferenceClient
    import json
    import re
    
    # Rule-based fallback function
    def rule_based_analysis(text, role):
        word_count = len(text.split())
        has_metrics = bool(re.search(r'\d+%|\d+x|\d+\+', text))
        has_projects = 'project' in text.lower()
        has_email = bool(re.search(r'\S+@\S+', text))
        
        score = 6
        if word_count > 200: score += 1
        if has_metrics: score += 1.5
        if has_projects: score += 1
        if has_email: score += 0.5
        
        return {
            'score': round(min(10, score), 1),
            'strengths': [
                f'Resume length is appropriate ({word_count} words)',
                'Contact information included' if has_email else 'Clear structure',
                'Shows relevant experience' if has_projects else 'Professional formatting'
            ],
            'weaknesses': [
                'Add more quantifiable achievements with numbers' if not has_metrics else 'Could include more metrics',
                'Include specific projects with tech stack' if not has_projects else 'Expand on project impact',
                f'Optimize for {role} keywords and ATS systems'
            ],
            'suggestions': [
                'Add 2-3 technical projects with GitHub links',
                'Include metrics (e.g., "Improved performance by 40%")',
                'Add a professional summary (3-4 lines) at the top',
                f'Include {role}-specific technical keywords',
                'Ensure all sections have quantifiable achievements'
            ]
        }
    
    try:
        client = InferenceClient(token="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")  # Replace with your token
        
        prompt = f"""You are an expert technical recruiter. Analyze this resume for a {job_role} position and provide structured feedback.

Resume text:
{resume_text[:1500]}

Provide your analysis ONLY as valid JSON with no other text:
{{
  "score": <number 0-10>,
  "strengths": ["strength 1", "strength 2", "strength 3"],
  "weaknesses": ["weakness 1", "weakness 2", "weakness 3"],
  "suggestions": ["specific tip 1", "specific tip 2", "specific tip 3", "specific tip 4", "specific tip 5"]
}}"""

        response = client.text_generation(
            prompt,
            model="mistralai/Mistral-7B-Instruct-v0.2",
            max_new_tokens=800,
            temperature=0.7
        )
        
        # Try to extract JSON from response
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response, re.DOTALL)
        
        if json_match:
            result = json.loads(json_match.group())
            # Validate the structure
            if all(key in result for key in ['score', 'strengths', 'weaknesses', 'suggestions']):
                return result
        
        # If AI parsing fails, use rule-based
        print("AI response couldn't be parsed, using rule-based analysis")
        return rule_based_analysis(resume_text, job_role)
        
    except Exception as e:
        print(f"AI analysis error: {e}, falling back to rule-based")
        return rule_based_analysis(resume_text, job_role)

if __name__ == '__main__':
    app.run(debug=True, port=5000)