import json
import re

EXCLUDED_TAGS = {"table-tags", "inflection-template", "archaic", "dated", "obsolete", "alternative"}

def is_all_senses_excluded(entry):
    senses = entry.get("senses", [])
    if not senses:
        return False  # keep entries with no senses
    for sense in senses:
        tags = set(sense.get("tags", []))
        if not tags & EXCLUDED_TAGS:
            return False  # found at least one normal sense
    return True  # all senses are excluded

def split_by_pos(input_path, lang_code):
    output_files = {
        "noun": open(f"{lang_code}_nouns.jsonl", "w", encoding="utf-8"),
        "verb": open(f"{lang_code}_verbs.jsonl", "w", encoding="utf-8"),
        "adj": open(f"{lang_code}_adjs.jsonl", "w", encoding="utf-8"),
    }

    def contains_cyrillic(text):
        return bool(re.search(r'[\u0400-\u04FF]', text or ""))

    def is_form_of(entry):
        return any("form_of" in sense for sense in entry.get("senses", []))

    with open(input_path, "r", encoding="utf-8") as infile:
        for line in infile:
            try:
                entry = json.loads(line)

                if (
                    entry.get("lang_code") == lang_code
                    and entry.get("pos") in output_files
                    and not is_form_of(entry)
                    and not contains_cyrillic(entry.get("word", ""))
                    and not is_all_senses_excluded(entry)
                ):
                    # Filter valid forms
                    valid_forms = [
                        form for form in entry.get("forms", [])
                        if not set(form.get("tags", [])) & EXCLUDED_TAGS
                    ]

                    # Skip if no valid forms remain
                    if not valid_forms:
                        continue

                    # Keep only the needed fields
                    trimmed = {
                        "word": entry.get("word"),
                        "lang_code": entry.get("lang_code"),
                        "pos": entry.get("pos"),
                        "forms": valid_forms,
                        "head_templates": entry.get("head_templates", []),
                        "senses": [
                            {"glosses": sense.get("glosses", [])}
                            for sense in entry.get("senses", [])
                            if "glosses" in sense
                        ]
                        }

                    json.dump(trimmed, output_files[entry["pos"]], ensure_ascii=False)
                    output_files[entry["pos"]].write("\n")
            except json.JSONDecodeError:
                continue

    for f in output_files.values():
        f.close()

    print("✅ Split complete.")

split_by_pos("data/sv.jsonl", "sv")
split_by_pos("data/ro.jsonl", "ro")
split_by_pos("data/sh.jsonl", "sh")
