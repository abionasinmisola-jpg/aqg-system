"""
AQG System - Retrieval & Performance Evaluation Script
Evaluates:
1. Retrieval quality (Table 4.6) - relevance of retrieved chunks
2. System performance (Table 4.13) - timing for each stage

Run: python run_retrieval_performance.py
"""

import os
import sys
import time
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend import create_app, db
from backend.models.upload import Upload
from backend.services.embedder import search_faiss_index
from backend.services.generator import generate_questions
from backend.services.verifier import verify_all_questions

app = create_app()
ctx = app.app_context()
ctx.push()

index_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "indexes")

print("=" * 65)
print("AQG SYSTEM — RETRIEVAL & PERFORMANCE EVALUATION")
print("=" * 65)

# ── RETRIEVAL EVALUATION ──────────────────────────────────────
print("\n📊 RETRIEVAL EVALUATION (Table 4.6)")
print("-" * 50)

# Test queries per domain
math_queries = [
    "What is the definition of a prime number?",
    "How do you calculate the area of a circle?",
    "What is the Pythagorean theorem?",
    "Define a quadratic equation",
    "What is the mean of a dataset?"
]

prog_queries = [
    "What is a recursive function?",
    "How does a for loop work in programming?",
    "What is the difference between a list and a tuple?",
    "Define object oriented programming",
    "What is time complexity of an algorithm?"
]

# Upload IDs from your system
PROG_UPLOAD_ID = 1   # programming_passages.txt
MATH_UPLOAD_ID = 2   # mathematics_passages.txt

def evaluate_retrieval(queries, upload_id, domain, top_k=5):
    total_queries = len(queries)
    total_retrieved = 0
    total_relevant = 0
    retrieval_times = []

    print(f"\n  Domain: {domain}")
    results = []

    for query in queries:
        start = time.time()
        chunks = search_faiss_index(query, upload_id, index_folder, top_k=top_k)
        elapsed = time.time() - start
        retrieval_times.append(elapsed)

        retrieved = len(chunks)
        total_retrieved += retrieved

        # Relevance check: chunk score > 0.3 considered relevant
        relevant = sum(1 for c in chunks if c.get('score', 0) > 0.3)
        total_relevant += relevant

        accuracy = round((relevant / retrieved) * 100, 1) if retrieved > 0 else 0

        results.append({
            "query": query[:60] + "..." if len(query) > 60 else query,
            "retrieved": retrieved,
            "relevant": relevant,
            "accuracy": accuracy
        })

        print(f"    Query: {query[:50]}...")
        print(f"    Retrieved: {retrieved} | Relevant: {relevant} | Accuracy: {accuracy}%")

    avg_accuracy = round((total_relevant / total_retrieved) * 100, 1) if total_retrieved > 0 else 0
    avg_time = round(sum(retrieval_times) / len(retrieval_times) * 1000, 2)  # ms

    print(f"\n  Overall Retrieval Accuracy: {avg_accuracy}%")
    print(f"  Average Retrieval Time: {avg_time}ms")

    return results, avg_accuracy, avg_time

math_results, math_accuracy, math_ret_time = evaluate_retrieval(
    math_queries, MATH_UPLOAD_ID, "Mathematics"
)

prog_results, prog_accuracy, prog_ret_time = evaluate_retrieval(
    prog_queries, PROG_UPLOAD_ID, "Programming"
)

overall_accuracy = round((math_accuracy + prog_accuracy) / 2, 1)
avg_retrieval_time = round((math_ret_time + prog_ret_time) / 2, 2)

print(f"\n  📈 Overall Retrieval Accuracy: {overall_accuracy}%")
print(f"  ⏱️  Average Retrieval Time: {avg_retrieval_time}ms")

# ── PERFORMANCE EVALUATION ────────────────────────────────────
print("\n\n📊 SYSTEM PERFORMANCE EVALUATION (Table 4.13)")
print("-" * 50)
print("\n  Measuring live generation times (GPT-4o, 5 questions)...")
print("  Please wait...")

def measure_performance(upload_id, domain, llm="gpt4o"):
    # Retrieval timing
    query = f"remember level {domain} questions about main concepts"
    ret_start = time.time()
    chunks = search_faiss_index(query, upload_id, index_folder, top_k=5)
    retrieval_time = round((time.time() - ret_start) * 1000, 2)

    if not chunks:
        return None

    # Generation timing
    from backend.services.generator import build_prompt, generate_with_gpt4o, parse_questions
    prompt = build_prompt(chunks, "remember", domain, 5, "mcq")

    gen_start = time.time()
    try:
        response = generate_with_gpt4o(prompt)
        questions = parse_questions(response, "remember", domain, "mcq")
    except Exception as e:
        print(f"    ⚠️ Generation error: {e}")
        return None
    generation_time = round((time.time() - gen_start) * 1000, 2)

    # Moderation timing
    mod_start = time.time()
    verify_all_questions(questions)
    moderation_time = round((time.time() - mod_start) * 1000, 2)

    total_time = round(retrieval_time + generation_time + moderation_time, 2)

    return {
        "retrieval_time_ms": retrieval_time,
        "generation_time_ms": generation_time,
        "moderation_time_ms": moderation_time,
        "total_time_ms": total_time
    }

# Run performance measurement for both domains
math_perf = measure_performance(MATH_UPLOAD_ID, "mathematics")
prog_perf = measure_performance(PROG_UPLOAD_ID, "programming")

if math_perf and prog_perf:
    avg_ret  = round((math_perf['retrieval_time_ms'] + prog_perf['retrieval_time_ms']) / 2, 2)
    avg_gen  = round((math_perf['generation_time_ms'] + prog_perf['generation_time_ms']) / 2, 2)
    avg_mod  = round((math_perf['moderation_time_ms'] + prog_perf['moderation_time_ms']) / 2, 2)
    avg_total = round((math_perf['total_time_ms'] + prog_perf['total_time_ms']) / 2, 2)

    print(f"\n  Mathematics:")
    print(f"    Retrieval:  {math_perf['retrieval_time_ms']}ms")
    print(f"    Generation: {math_perf['generation_time_ms']}ms")
    print(f"    Moderation: {math_perf['moderation_time_ms']}ms")
    print(f"    Total:      {math_perf['total_time_ms']}ms")

    print(f"\n  Programming:")
    print(f"    Retrieval:  {prog_perf['retrieval_time_ms']}ms")
    print(f"    Generation: {prog_perf['generation_time_ms']}ms")
    print(f"    Moderation: {prog_perf['moderation_time_ms']}ms")
    print(f"    Total:      {prog_perf['total_time_ms']}ms")

    print(f"\n  📈 AVERAGES (Table 4.13):")
    print(f"    Average Retrieval Time:   {avg_ret}ms")
    print(f"    Average Generation Time:  {avg_gen}ms")
    print(f"    Average Moderation Time:  {avg_mod}ms")
    print(f"    Average Total Time:       {avg_total}ms")

# ── SAVE RESULTS ──────────────────────────────────────────────
retrieval_summary = {
    "mathematics": {
        "queries": math_results,
        "overall_accuracy": math_accuracy,
        "avg_retrieval_time_ms": math_ret_time
    },
    "programming": {
        "queries": prog_results,
        "overall_accuracy": prog_accuracy,
        "avg_retrieval_time_ms": prog_ret_time
    },
    "overall_accuracy": overall_accuracy,
    "avg_retrieval_time_ms": avg_retrieval_time
}

performance_summary = {
    "mathematics": math_perf,
    "programming": prog_perf,
    "averages": {
        "retrieval_time_ms": avg_ret if math_perf and prog_perf else None,
        "generation_time_ms": avg_gen if math_perf and prog_perf else None,
        "moderation_time_ms": avg_mod if math_perf and prog_perf else None,
        "total_time_ms": avg_total if math_perf and prog_perf else None
    }
} if math_perf and prog_perf else {}

with open("evaluation_data/retrieval_results.json", "w") as f:
    json.dump(retrieval_summary, f, indent=2)

with open("evaluation_data/performance_results.json", "w") as f:
    json.dump(performance_summary, f, indent=2)

print("\n" + "=" * 65)
print("✅ Results saved to evaluation_data/")
print("   - retrieval_results.json")
print("   - performance_results.json")
print("\nNEXT STEP: Use these numbers for Tables 4.6 and 4.13")
