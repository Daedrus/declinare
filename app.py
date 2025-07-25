from flask import Flask, render_template, request, redirect, url_for
import itertools
import json
import os
import random
import re
import time
import cProfile
import pstats
import io
from functools import wraps
from collections import defaultdict
import threading

app = Flask(__name__)

LANG_FILES = {
    "sv": {"name": "Swedish", "file": "data/sv_nouns.jsonl", "lines": 37484},
    "ro": {"name": "Romanian", "file": "data/ro_nouns.jsonl", "lines": 55202},
    "sh": {"name": "Serbo-Croatian", "file": "data/sh_nouns.jsonl", "lines": 29093}
}

EXCLUDED_TAGS = {"table-tags", "inflection-template", "archaic", "dated", "obsolete"}

# Performance monitoring
performance_stats = defaultdict(list)
stats_lock = threading.Lock()

def profile_function(func_name):
    """Decorator to profile individual functions"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()

            with stats_lock:
                performance_stats[func_name].append(end_time - start_time)

            return result
        return wrapper
    return decorator

def profile_route(f):
    """Decorator to profile Flask routes with cProfile"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        pr = cProfile.Profile()
        pr.enable()

        start_time = time.time()
        result = f(*args, **kwargs)
        end_time = time.time()

        pr.disable()

        # Print timing info
        print(f"\n=== Route {f.__name__} took {end_time - start_time:.4f} seconds ===")

        # Print detailed profiling stats
        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
        ps.print_stats(20)  # Top 20 functions
        print(s.getvalue())

        return result
    return decorated_function

@profile_function("contains_cyrillic")
def contains_cyrillic(text):
    return bool(re.search(r'[\u0400-\u04FF]', text))

@profile_function("get_valid_declension")
def get_valid_declensions(entry):
    return [
        form for form in entry.get("forms", [])
        if (
            form.get("source") == "declension"
            and "form" in form
            and not set(form.get("tags", [])) & EXCLUDED_TAGS
        )
    ]

@profile_function("get_senses")
def get_senses(entry):
    """Flatten and return glosses from non-obsolete senses."""
    return list(itertools.chain.from_iterable(
        sense.get("glosses", [])
        for sense in entry.get("senses", [])
        if not set(sense.get("tags", [])) & EXCLUDED_TAGS
    ))

@profile_function("get_random_noun_entry")
def get_random_noun_entry(lang_code, max_tries=50):
    info = LANG_FILES.get(lang_code)
    if not info:
        return None, []

    file_path = info["file"]
    total_lines = info["lines"]

    for attempt in range(max_tries):
        line_num = random.randint(0, total_lines - 1)
        file_read_start = time.time()

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for i, line in enumerate(f):
                    if i == line_num:
                        parse_start = time.time()
                        entry = json.loads(line)

                        validation_start = time.time()
                        if (
                            entry.get("lang_code") == lang_code
                            and not contains_cyrillic(entry.get("word", ""))
                        ):
                            decls = get_valid_declensions(entry)
                            if decls:
                                file_read_time = parse_start - file_read_start
                                parse_time = validation_start - parse_start
                                validation_time = time.time() - validation_start

                                print(f"Attempt {attempt + 1}: File read: {file_read_time:.4f}s, "
                                      f"Parse: {parse_time:.4f}s, Validation: {validation_time:.4f}s")
                                return entry, decls
                        break
        except Exception as e:
            print(f"Error on attempt {attempt + 1}: {e}")
            continue

    print(f"Failed to find valid entry after {max_tries} attempts")
    return None, []

@app.route("/stats")
def performance_stats_route():
    """Route to view performance statistics"""
    with stats_lock:
        stats_summary = {}
        for func_name, times in performance_stats.items():
            if times:
                stats_summary[func_name] = {
                    'count': len(times),
                    'total_time': sum(times),
                    'avg_time': sum(times) / len(times),
                    'min_time': min(times),
                    'max_time': max(times)
                }

    return f"<pre>{json.dumps(stats_summary, indent=2)}</pre>"

@app.route("/", methods=["GET", "POST"])
@profile_route
def quiz():
    lang = request.form.get("lang") or request.args.get("lang") or "sv"

    if lang not in LANG_FILES:
        lang = "sv"

    if request.method == "POST":
        if "word" in request.form and "correct_answer" in request.form:
            word = request.form["word"]
            correct_answer = request.form["correct_answer"]
            tags = request.form["tags"]
            senses = request.form["senses"]
            user_answer = request.form["user_answer"].strip()

            is_correct = user_answer.lower() == correct_answer.lower()

            return render_template(
                "quiz.html",
                word=word,
                tags=tags,
                senses=senses,
                correct_answer=correct_answer,
                feedback=True,
                is_correct=is_correct,
                user_answer=user_answer,
                selected_lang=lang,
                languages=LANG_FILES
            )
        else:
            # User submitted only a language switch — refresh question
            return redirect(url_for("quiz", lang=lang))

    print(f"\n=== Starting new quiz question for language: {lang} ===")
    entry_start = time.time()
    entry, declensions = get_random_noun_entry(lang)
    entry_time = time.time() - entry_start
    print(f"get_random_noun_entry took: {entry_time:.4f} seconds")

    if not entry or not declensions:
        return "No valid entry found", 500

    form = random.choice(declensions)
    tags = ", ".join(form.get("tags", []))
    senses = ", ".join(get_senses(entry))
    return render_template(
        "quiz.html",
        word=entry.get("word"),
        tags=tags,
        senses=senses,
        correct_answer=form["form"],
        feedback=False,
        selected_lang=lang,
        languages=LANG_FILES
    )

if __name__ == "__main__":
    print("Starting Flask app with profiling enabled")
    print("Visit /stats to see performance statistics")
    app.run(debug=True, host='0.0.0.0', port=int(os.getenv('PORT')))

