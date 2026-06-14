import time
import random
import os
from backend.services.embedder import search_faiss_index


BLOOMS_TAXONOMY = {
    "remember": {
        "definition": "Retrieving relevant knowledge from long-term memory",
        "cognitive_processes": ["recognising", "recalling"],
        "verbs": ["define", "list", "recall", "name", "identify", "state", "label", "match", "outline"],
        "question_stems": [
            "What is the definition of...?",
            "List the key characteristics of...?",
            "Identify the main components of...?",
            "State the steps involved in...?"
        ],
        "instruction": (
            "You are generating a REMEMBER level question based on Anderson and Krathwohl revised Blooms Taxonomy.\n"
            "REMEMBER level requires students to RETRIEVE factual knowledge directly from memory.\n"
            "This includes:\n"
            "- Recognising: identifying correct information when presented\n"
            "- Recalling: retrieving relevant information from memory\n\n"
            "COGNITIVE DEMAND: The student should be able to answer this question by directly recalling "
            "information stated in the text.\n\n"
            "STEP 1: Identify a specific fact, definition, or concept clearly stated in the context.\n"
            "STEP 2: Formulate a question that requires direct recall of that information.\n"
            "STEP 3: Ensure the question tests memory NOT understanding or application.\n"
            "STEP 4: Create plausible distractors that are related but incorrect."
        ),
        "negative": (
            "Do NOT generate questions that:\n"
            "- Require the student to explain or interpret (that is Understand level)\n"
            "- Require the student to apply knowledge to new situations (that is Apply level)\n"
            "- Can be answered by common sense without reading the text\n"
            "- Are too trivial or obvious"
        )
    },

    "understand": {
        "definition": "Constructing meaning from instructional messages",
        "cognitive_processes": ["interpreting", "exemplifying", "classifying", "summarising", "inferring", "comparing", "explaining"],
        "verbs": ["explain", "summarize", "describe", "interpret", "classify", "compare", "paraphrase", "illustrate"],
        "question_stems": [
            "Explain in your own words how...?",
            "What is the difference between...?",
            "Summarise the main idea of...?",
            "How would you classify...?"
        ],
        "instruction": (
            "You are generating an UNDERSTAND level question based on Anderson and Krathwohl revised Blooms Taxonomy.\n"
            "UNDERSTAND level requires students to CONSTRUCT MEANING from information.\n"
            "This includes:\n"
            "- Interpreting: converting information from one form to another\n"
            "- Exemplifying: finding specific examples of a concept\n"
            "- Classifying: determining which category something belongs to\n"
            "- Summarising: abstracting a general theme\n"
            "- Inferring: drawing logical conclusions from information\n"
            "- Comparing: detecting similarities and differences\n"
            "- Explaining: constructing cause-and-effect models\n\n"
            "COGNITIVE DEMAND: The student must demonstrate they understand the concept, not just memorise it.\n\n"
            "STEP 1: Identify a concept or process in the context that has meaning beyond its definition.\n"
            "STEP 2: Choose ONE cognitive process from the list above.\n"
            "STEP 3: Generate a question that requires the student to demonstrate understanding.\n"
            "STEP 4: Ensure the correct answer cannot be found by simply copying text.\n"
            "STEP 5: Create distractors that represent common misconceptions."
        ),
        "negative": (
            "Do NOT generate questions that:\n"
            "- Can be answered by direct recall (that is Remember level)\n"
            "- Require applying knowledge to solve a problem (that is Apply level)\n"
            "- Have yes/no answers\n"
            "- Can be answered with a single memorised word or phrase"
        )
    },

    "apply": {
        "definition": "Carrying out or using a procedure in a given situation",
        "cognitive_processes": ["executing", "implementing"],
        "verbs": ["solve", "demonstrate", "calculate", "use", "implement", "apply", "execute", "produce"],
        "question_stems": [
            "How would you use... to solve...?",
            "Calculate the... given that...?",
            "Apply the concept of... to the following scenario...?",
            "Demonstrate how... works in the context of...?"
        ],
        "instruction": (
            "You are generating an APPLY level question based on Anderson and Krathwohl revised Blooms Taxonomy.\n"
            "APPLY level requires students to USE knowledge or procedures in a NEW situation.\n"
            "This includes:\n"
            "- Executing: applying a procedure to a familiar task\n"
            "- Implementing: applying a procedure to an unfamiliar task\n\n"
            "COGNITIVE DEMAND: The student must USE knowledge to solve a problem in a NEW context.\n\n"
            "STEP 1: Identify a procedure, method or concept from the context.\n"
            "STEP 2: Create a NEW scenario or problem that is NOT directly in the text.\n"
            "STEP 3: Generate a question that requires the student to apply the knowledge.\n"
            "STEP 4: Ensure the scenario is realistic and relevant to the domain.\n"
            "STEP 5: The correct answer should require actual application, not just recall."
        ),
        "negative": (
            "Do NOT generate questions that:\n"
            "- Can be answered by recalling facts (that is Remember level)\n"
            "- Only require explaining a concept (that is Understand level)\n"
            "- Use the exact same scenario from the text\n"
            "- Are purely theoretical without practical application"
        )
    },

    "analyse": {
        "definition": "Breaking material into parts and detecting how they relate to each other and the whole",
        "cognitive_processes": ["differentiating", "organising", "attributing"],
        "verbs": ["compare", "examine", "differentiate", "break down", "contrast", "analyse", "distinguish", "deconstruct"],
        "question_stems": [
            "Compare and contrast... and...?",
            "What is the relationship between... and...?",
            "Examine the factors that contribute to...?",
            "Differentiate between... in terms of...?"
        ],
        "instruction": (
            "You are generating an ANALYSE level question based on Anderson and Krathwohl revised Blooms Taxonomy.\n"
            "ANALYSE level requires students to BREAK DOWN material and examine relationships between parts.\n"
            "This includes:\n"
            "- Differentiating: distinguishing relevant from irrelevant parts\n"
            "- Organising: determining how elements fit together in a structure\n"
            "- Attributing: determining the point of view or bias behind information\n\n"
            "COGNITIVE DEMAND: The student must examine multiple components and their relationships.\n\n"
            "STEP 1: Identify TWO OR MORE concepts, processes or components in the context.\n"
            "STEP 2: Identify the relationship or structural connection between them.\n"
            "STEP 3: Generate a question that requires the student to EXAMINE that relationship.\n"
            "STEP 4: The question must require the student to BREAK DOWN the topic.\n"
            "STEP 5: Ensure the question cannot be answered by simple recall.\n"
            "STEP 6: Self-check: Would a student need to think critically to answer this? If not, make it harder."
        ),
        "negative": (
            "Do NOT generate questions that:\n"
            "- Can be answered by recalling or explaining a single concept\n"
            "- Only require listing differences without examining WHY they differ\n"
            "- Have a straightforward factual answer\n"
            "- Can be answered without reading the context carefully\n"
            "- Are surface-level comparisons without deeper analysis"
        )
    },

    "evaluate": {
        "definition": "Making judgements based on criteria and standards",
        "cognitive_processes": ["checking", "critiquing"],
        "verbs": ["justify", "assess", "critique", "defend", "argue", "judge", "evaluate", "appraise", "recommend"],
        "question_stems": [
            "Justify why... is more effective than...?",
            "Critique the approach used in...?",
            "Assess the validity of... based on...?",
            "Which approach would you recommend and why...?"
        ],
        "instruction": (
            "You are generating an EVALUATE level question based on Anderson and Krathwohl revised Blooms Taxonomy.\n"
            "EVALUATE level requires students to make JUDGEMENTS based on explicit criteria and standards.\n"
            "This includes:\n"
            "- Checking: detecting inconsistencies or fallacies in information\n"
            "- Critiquing: judging the appropriateness of a method or solution\n\n"
            "COGNITIVE DEMAND: The student must make a DEFENDABLE JUDGEMENT using explicit criteria.\n\n"
            "STEP 1: Identify a concept, method or decision from the context that can be debated.\n"
            "STEP 2: Identify SPECIFIC CRITERIA that can be used to judge it.\n"
            "STEP 3: Generate a question requiring the student to make a judgement AND defend it.\n"
            "STEP 4: The question must have EXPLICIT CRITERIA embedded in it.\n"
            "STEP 5: Ensure there is more than one defensible position.\n"
            "STEP 6: Self-check: Does the question require critical thinking? If not, revise it."
        ),
        "negative": (
            "Do NOT generate questions that:\n"
            "- Have a single correct factual answer\n"
            "- Only require explaining or describing without making a judgement\n"
            "- Ask for personal opinions without requiring justification\n"
            "- Can be answered without engaging critically with the content\n"
            "- Are vague without clear criteria for judgement"
        )
    },

    "create": {
        "definition": "Putting elements together to form a coherent or functional whole",
        "cognitive_processes": ["generating", "planning", "producing"],
        "verbs": ["design", "construct", "formulate", "propose", "develop", "create", "devise", "synthesise", "generate"],
        "question_stems": [
            "Design a system that...?",
            "Propose a solution to... using the principles of...?",
            "Construct a model that demonstrates...?",
            "Develop a plan to... considering...?"
        ],
        "instruction": (
            "You are generating a CREATE level question based on Anderson and Krathwohl revised Blooms Taxonomy.\n"
            "CREATE is the HIGHEST level - it requires students to PUT ELEMENTS TOGETHER to form something NEW.\n"
            "This includes:\n"
            "- Generating: coming up with alternative hypotheses or ideas\n"
            "- Planning: devising a procedure for accomplishing a task\n"
            "- Producing: inventing a product or solution\n\n"
            "COGNITIVE DEMAND: The student must SYNTHESISE knowledge to produce something original.\n\n"
            "STEP 1: Identify the core principles and concepts in the context.\n"
            "STEP 2: Identify a real-world PROBLEM or CHALLENGE that requires combining those concepts.\n"
            "STEP 3: Generate a question that requires the student to DESIGN or CONSTRUCT something new.\n"
            "STEP 4: The question must have NO single correct answer.\n"
            "STEP 5: Include CONSTRAINTS in the question to guide the student.\n"
            "STEP 6: Self-check: Does this require genuine creativity? If not, revise completely."
        ),
        "negative": (
            "Do NOT generate questions that:\n"
            "- Have a single correct answer\n"
            "- Only require applying an existing procedure\n"
            "- Can be answered by summarising or describing the text\n"
            "- Are too vague without clear constraints\n"
            "- Only ask the student to LIST or EXPLAIN without producing something new"
        )
    }
}


DOMAIN_INSTRUCTIONS = {
    "mathematics": (
        "DOMAIN: MATHEMATICS\n"
        "- Questions must involve mathematical concepts, formulas, calculations or proofs\n"
        "- For Remember level: test definitions, formulas, theorems\n"
        "- For Understand level: test interpretation of mathematical concepts\n"
        "- For Apply level: provide numerical problems to solve with specific numbers\n"
        "- For Analyse level: compare mathematical methods or examine relationships\n"
        "- For Evaluate level: judge the efficiency or correctness of mathematical approaches\n"
        "- For Create level: design mathematical models or proofs\n"
        "- Always include specific numbers or mathematical notation where appropriate\n"
        "- Distractors must be mathematically plausible (common calculation errors)\n"
        "- Examples of good topics: algebra, calculus, statistics, geometry, number theory"
    ),
    "programming": (
        "DOMAIN: PROGRAMMING\n"
        "- Questions must involve programming concepts, algorithms, code or software design\n"
        "- For Remember level: test syntax, keywords, data structures definitions\n"
        "- For Understand level: test interpretation of code snippets or algorithms\n"
        "- For Apply level: provide coding scenarios to solve with actual code\n"
        "- For Analyse level: compare algorithms or examine code complexity (Big O notation)\n"
        "- For Evaluate level: judge the efficiency or correctness of code approaches\n"
        "- For Create level: design algorithms or software solutions\n"
        "- Include code snippets where appropriate\n"
        "- Distractors must be syntactically plausible but logically wrong\n"
        "- Examples of good topics: data structures, algorithms, OOP, recursion, complexity"
    )
}


def build_prompt(chunks: list, bloom_level: str, domain: str, num_questions: int, question_type: str) -> str:
    bloom = BLOOMS_TAXONOMY[bloom_level]
    verbs = ", ".join(bloom["verbs"])
    stems = "\n".join([f"  - {s}" for s in bloom["question_stems"]])
    if question_type == "mcq":
        q_format = "multiple-choice questions, each with exactly 4 options (A, B, C, D) and one correct answer"
        format_block = (
            "OUTPUT FORMAT for each question (follow exactly):\n"
            "Q1: [a clear, grammatically correct question]\n"
            "TYPE: mcq\n"
            "A: [option]\n"
            "B: [option]\n"
            "C: [option]\n"
            "D: [option]\n"
            "ANSWER: [correct letter A, B, C or D]\n"
            "---"
        )
    elif question_type == "fill":
        q_format = "fill-in-the-blank questions, each a sentence with one blank shown as ________"
        format_block = (
            "OUTPUT FORMAT for each question (follow exactly):\n"
            "Q1: [a sentence containing exactly one blank written as ________]\n"
            "TYPE: fill\n"
            "ANSWER: [the single word or short phrase that fills the blank, in lowercase]\n"
            "---"
        )
    else:  # combination
        q_format = "a mix of multiple-choice (MCQ) and fill-in-the-blank questions"
        format_block = (
            "Produce a MIX of two question types. For each question choose either mcq or fill.\n"
            "OUTPUT FORMAT for an MCQ question:\n"
            "Q1: [a clear, grammatically correct question]\n"
            "TYPE: mcq\n"
            "A: [option]\nB: [option]\nC: [option]\nD: [option]\n"
            "ANSWER: [correct letter A, B, C or D]\n"
            "---\n"
            "OUTPUT FORMAT for a fill-in-the-blank question:\n"
            "Q2: [a sentence containing exactly one blank written as ________]\n"
            "TYPE: fill\n"
            "ANSWER: [the single word or short phrase that fills the blank, in lowercase]\n"
            "---"
        )
    context = "\n\n".join([c["chunk"] for c in chunks[:5]])
    domain_guide = DOMAIN_INSTRUCTIONS.get(domain, "")

    prompt = (
        f"You are an expert educator and assessment designer specialising in "
        f"Blooms Taxonomy (Anderson and Krathwohl Revised Edition) "
        f"with deep expertise in {domain}.\n\n"

        f"LECTURE CONTEXT:\n"
        f"{context}\n\n"

        f"YOUR TASK:\n"
        f"Generate exactly {num_questions} {q_format} questions "
        f"at the {bloom_level.upper()} cognitive level "
        f"for the domain of {domain.upper()}.\n\n"

        f"DOMAIN SPECIFIC INSTRUCTIONS:\n"
        f"{domain_guide}\n\n"

        f"BLOOMS LEVEL: {bloom_level.upper()}\n"
        f"Definition: {bloom['definition']}\n"
        f"Cognitive Processes to target: {', '.join(bloom['cognitive_processes'])}\n\n"

        f"{bloom['instruction']}\n\n"

        f"WHAT TO AVOID:\n"
        f"{bloom['negative']}\n\n"

        f"REQUIRED ACTION VERBS (use at least one per question):\n"
        f"{verbs}\n\n"

        f"SUGGESTED QUESTION STEMS:\n"
        f"{stems}\n\n"

        f"SELF-VERIFICATION (do this before outputting):\n"
        f"For each question ask yourself:\n"
        f"1. Does this question genuinely require {bloom_level} level thinking?\n"
        f"2. Is it based on the provided context?\n"
        f"3. Is it specific to {domain}?\n"
        f"4. Are the distractors plausible but clearly wrong?\n"
        f"5. Does it use one of the required action verbs?\n"
        f"If the answer to any is NO - revise the question before outputting.\n\n"

        f"IMPORTANT — WRITE NATURAL ENGLISH:\n"
        f"Each question must be a complete, grammatically correct sentence. "
        f"Do NOT start a question with a bare command verb like 'List' or 'Define' as the first word. "
        f"Instead phrase it naturally, e.g. 'Which of the following are...?' or "
        f"'What is the term for...?' — while still testing the {bloom_level} cognitive level.\n\n"
        f"{format_block}\n\n"
        f"Generate exactly {num_questions} {q_format} now. "
        f"Separate every question with a line containing only ---:"
    )

    return prompt

def parse_questions(response_text, bloom_level, domain, question_type):
    questions = []
    blocks = response_text.strip().split('---')

    for block in blocks:
        lines = [l.strip() for l in block.strip().split('\n') if l.strip()]
        if not lines:
            continue

        q = {
            'question': '',
            'options': {},
            'answer': '',
            'type': 'mcq',
            'bloom_level': bloom_level,
            'domain': domain,
            'verified': False
        }

        for line in lines:
            if line.upper().startswith('Q') and ':' in line and not line.upper().startswith('QUESTION TYPE'):
                head = line.split(':', 1)[0].strip().upper()
                if head.startswith('Q') and head[1:].isdigit():
                    q['question'] = line.split(':', 1)[1].strip()
            elif line.upper().startswith('TYPE:'):
                t = line.split(':', 1)[1].strip().lower()
                q['type'] = 'fill' if 'fill' in t else 'mcq'
            elif line.startswith('A:'):
                q['options']['A'] = line[2:].strip()
            elif line.startswith('B:'):
                q['options']['B'] = line[2:].strip()
            elif line.startswith('C:'):
                q['options']['C'] = line[2:].strip()
            elif line.startswith('D:'):
                q['options']['D'] = line[2:].strip()
            elif line.upper().startswith('ANSWER:'):
                ans = line.split(':', 1)[1].strip()
                q['answer'] = ans

        if not q['question']:
            continue

        if q['type'] == 'mcq':
            q['answer'] = q['answer'][0].upper() if q['answer'] else 'A'
            if not q['options']:
                continue
        else:
            q['answer'] = q['answer'].strip().lower()
            q['options'] = {}

        q['id'] = len(questions) + 1
        questions.append(q)

    return questions

def generate_with_gpt4o(prompt: str) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert educator specialising in Blooms Taxonomy "
                    "assessment design for Mathematics and Programming. "
                    "Always follow the output format exactly."
                )
            },
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=4000
    )
    return response.choices[0].message.content


def generate_with_gemini(prompt: str) -> str:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=(
                "You are an expert educator specialising in Blooms Taxonomy "
                "assessment design for Mathematics and Programming. "
                "Always follow the output format exactly."
            )
        ),
    )
    return response.text

def generate_with_deepseek(prompt: str) -> str:
    from openai import OpenAI
    client = OpenAI(
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com"
    )
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert educator specialising in Blooms Taxonomy "
                    "assessment design for Mathematics and Programming. "
                    "Always follow the output format exactly."
                )
            },
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=4000
    )
    return response.choices[0].message.content


def generate_mock_questions(chunks: list, bloom_level: str, domain: str, num_questions: int, question_type: str) -> list:
    bloom = BLOOMS_TAXONOMY[bloom_level]
    verbs = bloom["verbs"]

    mock_templates = {
        "mathematics": [
            (
                "Calculate the value of x if 2x + 5 = 15",
                {"A": "x = 5", "B": "x = 10", "C": "x = 7", "D": "x = 3"},
                "A"
            ),
            (
                "Define the Pythagorean theorem",
                {"A": "a^2 + b^2 = c^2", "B": "a + b = c", "C": "a^2 - b^2 = c^2", "D": "a x b = c"},
                "A"
            ),
            (
                "Compare the time complexity of O(n) and O(n^2) algorithms",
                {"A": "O(n) is faster for large inputs", "B": "O(n^2) is faster", "C": "They are always equal", "D": "Cannot be compared"},
                "A"
            ),
        ],
        "programming": [
            (
                "Identify the output of: print(2 ** 3)",
                {"A": "8", "B": "6", "C": "9", "D": "5"},
                "A"
            ),
            (
                "Define what a recursive function is",
                {"A": "A function that calls itself", "B": "A function with no return value", "C": "A function with parameters", "D": "A function inside a loop"},
                "A"
            ),
            (
                "Compare a list and a tuple in Python",
                {"A": "Lists are mutable, tuples are immutable", "B": "Tuples are mutable, lists are immutable", "C": "Both are mutable", "D": "Both are immutable"},
                "A"
            ),
        ]
    }

    templates = mock_templates.get(domain, mock_templates["mathematics"])
    questions = []

    for i in range(num_questions):
        verb = random.choice(verbs)
        template = templates[i % len(templates)]

        if question_type == "mcq":
            questions.append({
                "id": i + 1,
                "question": f"{verb.capitalize()}: {template[0]}",
                "options": template[1],
                "answer": template[2],
                "bloom_level": bloom_level,
                "domain": domain,
                "type": "mcq",
                "verified": False
            })
        else:
            chunk = chunks[i % len(chunks)]["chunk"][:80] if chunks else "the concept"
            questions.append({
                "id": i + 1,
                "question": f"{verb.capitalize()} the following {domain} concept: {chunk}...",
                "answer": "Sample answer based on lecture content",
                "bloom_level": bloom_level,
                "domain": domain,
                "type": "fill",
                "verified": False
            })

    return questions


def generate_questions(
    upload_id: int,
    bloom_level: str,
    domain: str,
    num_questions: int,
    question_type: str,
    index_folder: str,
    llm: str = "mock"
) -> dict:
    start_time = time.time()

    # Retrieve relevant chunks via hybrid search
    query = f"{bloom_level} level {domain} questions about main concepts and key ideas"
    chunks = search_faiss_index(query, upload_id, index_folder, top_k=10)
    print("\n----- DEBUG: RETRIEVED CHUNKS -----")
    for i, c in enumerate(chunks[:3]):
        print(f"[{i}] {c['chunk'][:200]}")
    print("----- END DEBUG -----\n")
    if not chunks:
        return {"success": False, "message": "No index found. Please process the file first."}

    try:
        if llm == "mock":
            questions = generate_mock_questions(
                chunks, bloom_level, domain, num_questions, question_type
            )
            llm_used = "Mock (Testing Mode)"
        else:
            prompt = build_prompt(chunks, bloom_level, domain, num_questions, question_type)

            if llm == "gpt4o":
                response = generate_with_gpt4o(prompt)
                llm_used = "GPT-4o"
            elif llm == "gemini":
                response = generate_with_gemini(prompt)
                llm_used = "Gemini 2.0 Flash"
            elif llm == "deepseek":
                response = generate_with_deepseek(prompt)
                llm_used = "DeepSeek V3"
            else:
                response = generate_with_gpt4o(prompt)
                llm_used = "GPT-4o"

            questions = parse_questions(response, bloom_level, domain, question_type)

            if not questions:
                print("!!! PARSE FAILED. RAW RESPONSE:", response[:500])
                return {
                    "success": False,
                    "message": "Could not parse LLM response. Please try again."
                }

    except Exception as e:
        print("!!! GENERATION ERROR:", str(e))
        return {"success": False, "message": f"LLM Error: {str(e)}"}

    end_time = time.time()
    response_time = round(end_time - start_time, 2)

    return {
        "success": True,
        "questions": questions,
        "metadata": {
            "bloom_level": bloom_level,
            "domain": domain,
            "num_questions": len(questions),
            "question_type": question_type,
            "response_time": response_time,
            "llm_used": llm_used,
            "chunks_used": len(chunks),
            "bloom_definition": BLOOMS_TAXONOMY[bloom_level]["definition"]
        }
    }