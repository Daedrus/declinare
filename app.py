from flask import Flask, render_template, request, redirect, url_for
import itertools
import json
import random
import re

app = Flask(__name__)

LANG_FILES = {
    "sv": {"name": "Swedish", "file": "data/sv.jsonl", "lines": 300280},
    "ro": {"name": "Romanian", "file": "data/ro.jsonl", "lines": 126022},
    "sh": {"name": "Serbo-Croatian", "file": "data/sh.jsonl", "lines": 66848}
}

EXCLUDED_TAGS = {"table-tags", "inflection-template", "archaic", "dated", "obsolete"}

def is_form_of(entry):
    return any("form_of" in sense for sense in entry.get("senses", []))

def contains_cyrillic(text):
    return bool(re.search(r'[\u0400-\u04FF]', text))

def get_valid_declensions(entry):
    return [
        form for form in entry.get("forms", [])
        if (
            form.get("source") == "declension"
            and "form" in form
            and not set(form.get("tags", [])) & EXCLUDED_TAGS
        )
    ]

def get_senses(entry):
    """Flatten and return glosses from non-obsolete senses."""
    return list(itertools.chain.from_iterable(
        sense.get("glosses", [])
        for sense in entry.get("senses", [])
        if not set(sense.get("tags", [])) & EXCLUDED_TAGS
    ))

def get_random_noun_entry(lang_code, max_tries=50):
    info = LANG_FILES.get(lang_code)
    if not info:
        return None, []

    file_path = info["file"]
    total_lines = info["lines"]

    for _ in range(max_tries):
        line_num = random.randint(0, total_lines - 1)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for i, line in enumerate(f):
                    if i == line_num:
                        entry = json.loads(line)
                        if (
                            entry.get("lang_code") == lang_code
                            and entry.get("pos") == "noun"
                            and not is_form_of(entry)
                            and not contains_cyrillic(entry.get("word", ""))
                        ):
                            decls = get_valid_declensions(entry)
                            if decls:
                                return entry, decls
                        break
        except Exception:
            continue

    return None, []

@app.route("/", methods=["GET", "POST"])
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

    entry, declensions = get_random_noun_entry(lang)
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
    app.run(debug=True)

