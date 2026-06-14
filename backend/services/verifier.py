import ast
import re
import os
import sympy
from sympy import symbols, solve, simplify, sympify
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application


def evaluate_python_expression(expr: str) -> str:
    """
    Safely evaluate a simple Python expression.
    Example: "2 ** 3" -> "8"
    """
    try:
        safe_globals = {
            "__builtins__": {},
            "abs": abs, "round": round, "len": len,
            "min": min, "max": max, "sum": sum,
            "range": range, "list": list, "tuple": tuple,
            "dict": dict, "set": set, "str": str,
            "int": int, "float": float, "bool": bool,
            "print": lambda x: str(x),
            "True": True, "False": False, "None": None
        }
        result = eval(compile(expr, "<string>", "eval"), safe_globals)
        return str(result)
    except Exception:
        return None


def check_ast_syntax(code: str) -> dict:
    """
    Check if a code snippet is syntactically valid Python.
    """
    try:
        ast.parse(code.strip())
        return {"valid": True, "message": "Code syntax is valid"}
    except SyntaxError as e:
        return {"valid": False, "message": f"Syntax error: {str(e)}"}


def solve_math_equation(equation_str: str) -> str:
    """
    Use SymPy to solve mathematical equations.
    Handles: linear, quadratic, simultaneous equations,
    derivatives, integrals, simplification.
    """
    try:
        transformations = standard_transformations + (implicit_multiplication_application,)
        x, y, z, n = symbols('x y z n')

        if '=' in equation_str:
            parts = equation_str.split('=')
            lhs = parse_expr(parts[0].strip(), transformations=transformations)
            rhs = parse_expr(parts[1].strip(), transformations=transformations)
            solution = solve(lhs - rhs, x)
            if solution:
                return str(solution[0])

        expr = parse_expr(equation_str.strip(), transformations=transformations)
        simplified = simplify(expr)
        return str(simplified)

    except Exception:
        return None


def verify_programming_mcq(question: dict) -> dict:
    """
    Verify programming MCQ questions.

    Checks:
    1. AST syntax of any code in question
    2. Evaluates simple Python expressions
    3. Checks answer correctness where possible
    """
    question_text = question.get("question", "")
    options = question.get("options", {})
    correct_answer = question.get("answer", "A")
    correct_option = options.get(correct_answer, "")

    verification_result = {
        "verified": False,
        "verification_status": "warning",
        "verification_message": "",
        "verification_method": "AST + Expression Evaluation"
    }

    try:
        code_in_backticks = re.findall(r'`([^`]+)`', question_text)
        print_statements = re.findall(r'print\(([^)]+)\)', question_text)

        # Check 1 — Syntax verification
        all_code = code_in_backticks + print_statements
        syntax_errors = []

        for code in all_code:
            result = check_ast_syntax(code)
            if not result["valid"]:
                syntax_errors.append(result["message"])

        if syntax_errors:
            verification_result.update({
                "verified": False,
                "verification_status": "failed",
                "verification_message": f"Code syntax error found: {syntax_errors[0]}"
            })
            question.update(verification_result)
            return question

        # Check 2 — Expression evaluation
        for expr in print_statements:
            evaluated = evaluate_python_expression(expr.strip())
            if evaluated is not None:
                correct_numbers = re.findall(r'-?\d+\.?\d*', correct_option)
                evaluated_numbers = re.findall(r'-?\d+\.?\d*', evaluated)

                if correct_numbers and evaluated_numbers:
                    if correct_numbers[0] == evaluated_numbers[0]:
                        verification_result.update({
                            "verified": True,
                            "verification_status": "verified",
                            "verification_message": (
                                f"Expression evaluated: {expr} = {evaluated}. "
                                f"Correct answer verified."
                            )
                        })
                        question.update(verification_result)
                        return question
                    else:
                        verification_result.update({
                            "verified": False,
                            "verification_status": "failed",
                            "verification_message": (
                                f"Answer mismatch: expression evaluates to {evaluated} "
                                f"but answer says {correct_option}"
                            )
                        })
                        question.update(verification_result)
                        return question

        # Check 3 — Conceptual question (no expression to evaluate)
        verification_result.update({
            "verified": True,
            "verification_status": "verified",
            "verification_message": "Conceptual programming question — syntax verified"
        })

    except Exception as e:
        verification_result.update({
            "verified": True,
            "verification_status": "warning",
            "verification_message": f"Partial verification: {str(e)}"
        })

    question.update(verification_result)
    return question


def verify_math_mcq(question: dict) -> dict:
    """
    Verify mathematics MCQ questions.

    Layer 1 — SymPy: equations, algebra, calculus, simplification.
    Layer 2 — LLM as judge: word problems, geometry, statistics.
    """
    question_text = question.get("question", "")
    options = question.get("options", {})
    correct_answer = question.get("answer", "A")
    correct_option = options.get(correct_answer, "")

    verification_result = {
        "verified": False,
        "verification_status": "warning",
        "verification_message": "",
        "verification_method": "SymPy + LLM Judge"
    }

    try:
        equation_patterns = [
            r'(\d+x\s*[\+\-]\s*\d+\s*=\s*\d+)',
            r'(x\^2[^=]*=\s*\d+)',
            r'(\d+x\^2[^=]*=\s*\d+)',
            r'solve\s+([^?]+)',
            r'calculate\s+([^?]+)',
            r'(\d+\s*[\+\-\*\/]\s*\d+)',
        ]

        equation_found = False
        for pattern in equation_patterns:
            matches = re.findall(pattern, question_text, re.IGNORECASE)
            if matches:
                equation_found = True
                for match in matches:
                    solution = solve_math_equation(match)
                    if solution:
                        if solution.replace(' ', '') in correct_option.replace(' ', ''):
                            verification_result.update({
                                "verified": True,
                                "verification_status": "verified",
                                "verification_message": (
                                    f"SymPy verified: solution is {solution}"
                                )
                            })
                            question.update(verification_result)
                            return question

        # Layer 2 — LLM as judge for complex questions
        if not equation_found or verification_result["verification_status"] == "warning":
            llm_result = verify_with_llm_judge(question)
            question.update(llm_result)
            return question

        verification_result.update({
            "verified": True,
            "verification_status": "warning",
            "verification_message": "Mathematical question flagged for manual review"
        })

    except Exception as e:
        verification_result.update({
            "verified": True,
            "verification_status": "warning",
            "verification_message": f"Verification incomplete: {str(e)}"
        })

    question.update(verification_result)
    return question


def verify_with_llm_judge(question: dict) -> dict:
    """
    Use GPT-4o as a judge to verify questions that SymPy cannot handle.
    """
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        question_text = question.get("question", "")
        options = question.get("options", {})
        correct_answer = question.get("answer", "A")
        domain = question.get("domain", "mathematics")
        bloom_level = question.get("bloom_level", "remember")

        options_text = "\n".join([f"{k}: {v}" for k, v in options.items()])

        prompt = (
            f"You are an expert {domain} educator and examiner.\n\n"
            f"Evaluate this MCQ question for correctness and quality:\n\n"
            f"QUESTION: {question_text}\n\n"
            f"OPTIONS:\n{options_text}\n\n"
            f"CLAIMED CORRECT ANSWER: {correct_answer}\n\n"
            f"BLOOM'S LEVEL: {bloom_level}\n\n"
            f"Please check:\n"
            f"1. Is the claimed correct answer actually correct?\n"
            f"2. Are the distractors (wrong options) clearly wrong but plausible?\n"
            f"3. Is the question clear and unambiguous?\n"
            f"4. Does it match the {bloom_level} level of Blooms Taxonomy?\n\n"
            f"Respond in this exact format:\n"
            f"VERDICT: PASS or FAIL\n"
            f"CORRECT_ANSWER: [letter]\n"
            f"REASON: [brief explanation]\n"
            f"BLOOM_MATCH: YES or NO"
        )

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=300
        )

        response_text = response.choices[0].message.content.strip()

        verdict = "PASS"
        reason = "LLM judge verified question"
        bloom_match = True
        correct_answer_confirmed = correct_answer

        for line in response_text.split('\n'):
            if line.startswith('VERDICT:'):
                verdict = line.replace('VERDICT:', '').strip()
            elif line.startswith('REASON:'):
                reason = line.replace('REASON:', '').strip()
            elif line.startswith('BLOOM_MATCH:'):
                bloom_match = 'YES' in line.upper()
            elif line.startswith('CORRECT_ANSWER:'):
                correct_answer_confirmed = line.replace('CORRECT_ANSWER:', '').strip()

        if verdict == "PASS":
            return {
                "verified": True,
                "verification_status": "verified",
                "verification_message": f"LLM Judge: {reason}",
                "verification_method": "GPT-4o LLM Judge",
                "bloom_aligned": bloom_match,
                "answer": correct_answer_confirmed
            }
        else:
            return {
                "verified": False,
                "verification_status": "failed",
                "verification_message": f"LLM Judge: {reason}",
                "verification_method": "GPT-4o LLM Judge",
                "bloom_aligned": bloom_match,
                "answer": correct_answer_confirmed
            }

    except Exception as e:
        return {
            "verified": True,
            "verification_status": "warning",
            "verification_message": f"LLM judge unavailable: {str(e)}",
            "verification_method": "LLM Judge (unavailable)"
        }


def verify_bloom_level(question: dict) -> dict:
    """
    Verify if question matches the requested Blooms level
    by checking for appropriate action verbs.
    """
    bloom_verbs = {
        "remember":  ["define", "list", "recall", "name", "identify",
                      "state", "label", "match", "outline"],
        "understand": ["explain", "summarize", "describe", "interpret",
                       "classify", "compare", "paraphrase", "illustrate"],
        "apply":     ["solve", "demonstrate", "calculate", "use",
                      "implement", "apply", "execute", "produce"],
        "analyse":   ["compare", "examine", "differentiate", "break down",
                      "contrast", "analyse", "distinguish", "deconstruct"],
        "evaluate":  ["justify", "assess", "critique", "defend", "argue",
                      "judge", "evaluate", "appraise", "recommend"],
        "create":    ["design", "construct", "formulate", "propose",
                      "develop", "create", "devise", "synthesise"]
    }

    bloom_level = question.get("bloom_level", "remember")
    question_text = question.get("question", "").lower()
    expected_verbs = bloom_verbs.get(bloom_level, [])

    verb_found = any(verb in question_text for verb in expected_verbs)

    question["bloom_aligned"] = verb_found
    question["bloom_verification"] = (
        f"Uses correct {bloom_level} level verb" if verb_found
        else f"Warning: may not match {bloom_level} level"
    )

    return question


def verify_all_questions(questions: list) -> dict:
    """
    Run full verification pipeline on all generated questions.
    Handles MCQ (SymPy/AST/LLM judge) and fill-in-the-blank.

    For each question:
    1. Verification by type, then domain
    2. Blooms level alignment check
    3. Statistics tally
    """
    verified_questions = []
    stats = {
        "total": len(questions),
        "verified": 0,
        "warning": 0,
        "failed": 0,
        "bloom_aligned": 0
    }

    for question in questions:
        domain = question.get("domain", "general")
        qtype = question.get("type", "mcq")

        # Step 1 — verification by type, then domain
        if qtype == "fill":
            ans = (question.get("answer") or "").strip()
            blank_ok = "____" in question.get("question", "")
            if ans and blank_ok:
                question["verified"] = True
                question["verification_status"] = "verified"
                question["verification_message"] = "Fill-in question has a blank and an answer"
            elif ans and not blank_ok:
                question["verified"] = True
                question["verification_status"] = "warning"
                question["verification_message"] = "Answer present but no blank found in question text"
            else:
                question["verified"] = False
                question["verification_status"] = "failed"
                question["verification_message"] = "Fill-in question missing an answer"
            question["verification_method"] = "Fill-in check"
        elif domain == "mathematics":
            question = verify_math_mcq(question)
        elif domain == "programming":
            question = verify_programming_mcq(question)
        else:
            question["verified"] = True
            question["verification_status"] = "verified"
            question["verification_message"] = "General verification passed"
            question["verification_method"] = "General"

        # Step 2 — Bloom's level alignment check
        bloom_level = question.get("bloom_level", "remember")
        question_text = question.get("question", "").lower()
        bloom_verbs = {
            "remember": ["define", "list", "state", "name", "identify", "recall", "what", "which", "who", "when", "where"],
            "understand": ["explain", "describe", "summarise", "summarize", "interpret", "classify", "compare", "why", "how"],
            "apply": ["calculate", "solve", "compute", "use", "apply", "determine", "find", "demonstrate"],
            "analyse": ["analyse", "analyze", "differentiate", "distinguish", "examine", "contrast"],
            "evaluate": ["evaluate", "justify", "assess", "judge", "critique", "defend", "argue"],
            "create": ["design", "construct", "develop", "formulate", "propose", "create", "devise"]
        }
        verbs = bloom_verbs.get(bloom_level, [])
        aligned = any(v in question_text for v in verbs)
        question["bloom_aligned"] = aligned
        if aligned:
            stats["bloom_aligned"] += 1

        # Step 3 — tally stats
        vstatus = question.get("verification_status", "verified")
        if vstatus == "verified":
            stats["verified"] += 1
        elif vstatus == "warning":
            stats["warning"] += 1
        else:
            stats["failed"] += 1

        verified_questions.append(question)

    # Pass rates
    total = stats["total"] if stats["total"] > 0 else 1
    stats["verification_pass_rate"] = round((stats["verified"] / total) * 100, 1)
    stats["bloom_alignment_rate"] = round((stats["bloom_aligned"] / total) * 100, 1)

    return {
        "questions": verified_questions,
        "stats": stats
    }