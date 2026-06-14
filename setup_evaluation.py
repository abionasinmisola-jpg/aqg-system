"""
AQG System - Evaluation Dataset Setup Script
Downloads and prepares reference questions for BLEU/ROUGE/BERTScore evaluation.

Mathematics: Uses AQuA-RAT dataset (maths word problems with rationale)
Programming: Uses CodeQA / manually curated CS questions from SciQ

Run: python setup_evaluation.py
"""

import json
import os

# Install required packages
os.system("pip install datasets rouge-score bert-score nltk --break-system-packages -q")

import nltk
nltk.download('punkt', quiet=True)
nltk.download('punkt_tab', quiet=True)

from datasets import load_dataset

print("=" * 60)
print("AQG EVALUATION DATASET SETUP")
print("=" * 60)

# ── MATHEMATICS: AQuA-RAT ─────────────────────────────────────
print("\n[1/2] Loading Mathematics dataset (AQuA-RAT)...")
try:
    math_dataset = load_dataset("aqua_rat", "raw", split="test", trust_remote_code=True)
    
    math_samples = []
    for item in math_dataset:
        if len(math_samples) >= 30:
            break
        # Each item has: question, options, correct, rationale
        if item.get('question') and item.get('rationale') and len(item['rationale']) > 100:
            math_samples.append({
                "support_passage": item['rationale'],  # use as "note" to feed system
                "question": item['question'],
                "options": item.get('options', []),
                "correct_answer": item.get('correct', ''),
                "domain": "mathematics"
            })
    
    print(f"    ✅ Loaded {len(math_samples)} mathematics reference questions")

except Exception as e:
    print(f"    ❌ AQuA-RAT failed: {e}")
    print("    Trying fallback...")
    math_samples = []

# ── PROGRAMMING: Manual curated CS questions ──────────────────
print("\n[2/2] Loading Programming dataset...")
try:
    # Use SciQ but filter for CS/computing questions
    sciq = load_dataset("allenai/sciq", split="test", trust_remote_code=True)
    
    cs_keywords = [
        'algorithm', 'programming', 'computer', 'software', 'code', 
        'function', 'data structure', 'variable', 'loop', 'recursion',
        'array', 'list', 'binary', 'database', 'network', 'memory',
        'cpu', 'processor', 'operating system', 'compiler', 'python',
        'java', 'class', 'object', 'method', 'sorting', 'searching'
    ]
    
    prog_samples = []
    for item in sciq:
        if len(prog_samples) >= 30:
            break
        question_lower = item['question'].lower()
        support_lower = item.get('support', '').lower()
        
        # Check if it's CS/programming related
        if any(kw in question_lower or kw in support_lower for kw in cs_keywords):
            if item.get('support') and len(item['support']) > 50:
                prog_samples.append({
                    "support_passage": item['support'],
                    "question": item['question'],
                    "correct_answer": item['correct_answer'],
                    "distractor1": item.get('distractor1', ''),
                    "distractor2": item.get('distractor2', ''),
                    "distractor3": item.get('distractor3', ''),
                    "domain": "programming"
                })
    
    print(f"    ✅ Loaded {len(prog_samples)} programming reference questions")

except Exception as e:
    print(f"    ❌ SciQ failed: {e}")
    prog_samples = []

# ── SAVE TO FILES ─────────────────────────────────────────────
os.makedirs("evaluation_data", exist_ok=True)

with open("evaluation_data/math_reference.json", "w") as f:
    json.dump(math_samples, f, indent=2)

with open("evaluation_data/prog_reference.json", "w") as f:
    json.dump(prog_samples, f, indent=2)

# ── SAVE SUPPORT PASSAGES AS TEXT FILES (to upload as notes) ──
os.makedirs("evaluation_data/notes", exist_ok=True)

# Combine math passages into one text file
math_text = "\n\n".join([
    f"Problem {i+1}:\n{s['support_passage']}" 
    for i, s in enumerate(math_samples)
])
with open("evaluation_data/notes/mathematics_passages.txt", "w", encoding='utf-8') as f:
    f.write(math_text)

# Combine programming passages into one text file  
prog_text = "\n\n".join([
    f"Topic {i+1}:\n{s['support_passage']}" 
    for i, s in enumerate(prog_samples)
])
with open("evaluation_data/notes/programming_passages.txt", "w", encoding='utf-8') as f:
    f.write(prog_text)

print("\n" + "=" * 60)
print("SETUP COMPLETE")
print("=" * 60)
print(f"✅ Mathematics reference questions: {len(math_samples)}")
print(f"✅ Programming reference questions: {len(prog_samples)}")
print(f"\nFiles saved to: evaluation_data/")
print(f"  - math_reference.json ({len(math_samples)} questions)")
print(f"  - prog_reference.json ({len(prog_samples)} questions)")
print(f"  - notes/mathematics_passages.txt (upload this as a note)")
print(f"  - notes/programming_passages.txt (upload this as a note)")
print(f"\nNEXT STEP:")
print(f"  1. Upload mathematics_passages.txt into your system as a note")
print(f"  2. Upload programming_passages.txt into your system as a note")
print(f"  3. Generate 30 questions from each using GPT-4o, Gemini, DeepSeek")
print(f"  4. Run: python run_evaluation.py")
