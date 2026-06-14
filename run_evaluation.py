"""
AQG System - Automated Evaluation Script
Computes BLEU, ROUGE, BERTScore for each LLM across both domains.
Also computes verification pass rate, Bloom's alignment, response time.

Run: python run_evaluation.py
"""

import json
import os
import sys

# ── Install required packages ─────────────────────────────────
print("Checking required packages...")
os.system("pip install rouge-score bert-score nltk --break-system-packages -q")

import nltk
try:
    nltk.data.find('tokenizers/punkt')
except:
    try:
        nltk.download('punkt', quiet=True)
        nltk.download('punkt_tab', quiet=True)
    except:
        pass

from rouge_score import rouge_scorer
import numpy as np

print("=" * 65)
print("AQG SYSTEM — AUTOMATED EVALUATION")
print("=" * 65)

# ── Load reference questions ──────────────────────────────────
def load_reference(path):
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    refs = []
    for item in data:
        q = item.get('question', '')
        if q:
            refs.append(q.strip())
    return refs

math_refs = load_reference("evaluation_data/math_reference.json")
prog_refs  = load_reference("evaluation_data/prog_reference.json")
print(f"\n✅ Loaded {len(math_refs)} math reference questions")
print(f"✅ Loaded {len(prog_refs)} programming reference questions")

# ── Pull generated questions from DB ─────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from backend import create_app, db
from backend.models.question import Question
from backend.models.test import Test

app = create_app()
ctx = app.app_context()
ctx.push()

def get_questions(domain_keyword, llm):
    tests = Test.query.filter(Test.title.ilike(f'%{domain_keyword}%')).all()
    questions = []
    for t in tests:
        qs = Question.query.filter_by(test_id=t.id, llm_used=llm).all()
        questions.extend(qs)
    return questions

LLMS = ['gpt4o', 'gemini', 'deepseek']
LLM_NAMES = {'gpt4o': 'GPT-4o', 'gemini': 'Gemini 2.0 Flash', 'deepseek': 'DeepSeek V3'}

# ── ROUGE scoring ─────────────────────────────────────────────
def compute_rouge(generated_questions, references):
    scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
    r1_scores, r2_scores, rL_scores = [], [], []

    for gen_q in generated_questions:
        gen_text = gen_q.question_text
        # compare against all refs, take best match
        best_r1, best_r2, best_rL = 0, 0, 0
        for ref in references:
            scores = scorer.score(ref, gen_text)
            best_r1 = max(best_r1, scores['rouge1'].fmeasure)
            best_r2 = max(best_r2, scores['rouge2'].fmeasure)
            best_rL = max(best_rL, scores['rougeL'].fmeasure)
        r1_scores.append(best_r1)
        r2_scores.append(best_r2)
        rL_scores.append(best_rL)

    return {
        'rouge1': round(np.mean(r1_scores), 4),
        'rouge2': round(np.mean(r2_scores), 4),
        'rougeL': round(np.mean(rL_scores), 4)
    }

# ── BLEU scoring ──────────────────────────────────────────────
def compute_bleu(generated_questions, references):
    from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
    smoothie = SmoothingFunction().method1
    bleu_scores = []

    ref_tokens = [ref.lower().split() for ref in references]

    for gen_q in generated_questions:
        gen_tokens = gen_q.question_text.lower().split()
        score = sentence_bleu(ref_tokens, gen_tokens, smoothing_function=smoothie)
        bleu_scores.append(score)

    return round(np.mean(bleu_scores), 4)

# ── Moderation stats ──────────────────────────────────────────
def compute_moderation_stats(questions):
    total = len(questions)
    verified = sum(1 for q in questions if q.verification_status == 'verified')
    warning  = sum(1 for q in questions if q.verification_status == 'warning')
    failed   = sum(1 for q in questions if q.verification_status == 'failed')
    pass_rate = round((verified / total) * 100, 1) if total > 0 else 0
    return {
        'total': total,
        'verified': verified,
        'warning': warning,
        'failed': failed,
        'pass_rate': pass_rate
    }

# ── Bloom's alignment ─────────────────────────────────────────
def compute_bloom_alignment(questions, requested_level='remember'):
    total = len(questions)
    aligned = sum(1 for q in questions if q.bloom_aligned)
    accuracy = round((aligned / total) * 100, 1) if total > 0 else 0
    return {'aligned': aligned, 'total': total, 'accuracy': accuracy}

# ── Run evaluation ────────────────────────────────────────────
print("\n" + "=" * 65)
print("RUNNING EVALUATION...")
print("=" * 65)

results = {}

for domain, keyword, refs in [
    ('Mathematics', 'Math', math_refs),
    ('Programming', 'Programming', prog_refs)
]:
    print(f"\n📊 Domain: {domain}")
    print("-" * 50)
    results[domain] = {}

    for llm in LLMS:
        questions = get_questions(keyword, llm)
        if not questions:
            print(f"  ⚠️  No questions found for {LLM_NAMES[llm]}")
            continue

        print(f"\n  🤖 {LLM_NAMES[llm]} ({len(questions)} questions)")

        rouge = compute_rouge(questions, refs)
        bleu  = compute_bleu(questions, refs)
        mod   = compute_moderation_stats(questions)
        bloom = compute_bloom_alignment(questions)

        results[domain][llm] = {
            'llm_name': LLM_NAMES[llm],
            'question_count': len(questions),
            'rouge1': rouge['rouge1'],
            'rouge2': rouge['rouge2'],
            'rougeL': rouge['rougeL'],
            'bleu': bleu,
            'verified': mod['verified'],
            'warning': mod['warning'],
            'failed': mod['failed'],
            'pass_rate': mod['pass_rate'],
            'bloom_aligned': bloom['aligned'],
            'bloom_accuracy': bloom['accuracy']
        }

        print(f"    ROUGE-1: {rouge['rouge1']} | ROUGE-2: {rouge['rouge2']} | ROUGE-L: {rouge['rougeL']}")
        print(f"    BLEU:    {bleu}")
        print(f"    Verified: {mod['verified']} | Warning: {mod['warning']} | Failed: {mod['failed']} | Pass Rate: {mod['pass_rate']}%")
        print(f"    Bloom's Alignment: {bloom['aligned']}/{bloom['total']} ({bloom['accuracy']}%)")

# ── Print final summary table ─────────────────────────────────
print("\n" + "=" * 65)
print("FINAL RESULTS SUMMARY")
print("=" * 65)

for domain in results:
    print(f"\n{domain}:")
    print(f"{'LLM':<20} {'ROUGE-1':<10} {'ROUGE-2':<10} {'ROUGE-L':<10} {'BLEU':<10} {'Pass%':<10} {'Bloom%':<10}")
    print("-" * 70)
    for llm, r in results[domain].items():
        print(f"{r['llm_name']:<20} {r['rouge1']:<10} {r['rouge2']:<10} {r['rougeL']:<10} {r['bleu']:<10} {r['pass_rate']:<10} {r['bloom_accuracy']:<10}")

# ── Save results to JSON ──────────────────────────────────────
with open("evaluation_data/evaluation_results.json", "w") as f:
    json.dump(results, f, indent=2)

print("\n✅ Results saved to evaluation_data/evaluation_results.json")
print("\nNEXT STEP: Use these numbers to fill in your Chapter 4 tables.")
