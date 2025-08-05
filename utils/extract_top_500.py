import json
from collections import defaultdict
from wordfreq import iter_wordlist
from pathlib import Path

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)  # Controls the level of console output

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)

logger.addHandler(ch)

EXCLUDED_TAGS = {
    "table-tags", "inflection-template", "archaic", "dated", "obsolete", "alternative"
}

EXCLUDED_FORMS = {
    "e", "ei", "i", "ii", "le", "lor", "ul", "ului"
}

def load_blacklist(blacklist_path):
    if not Path(blacklist_path).exists():
        return set()
    with open(blacklist_path, 'r', encoding='utf-8') as f:
        return set(line.strip() for line in f if line.strip())

def has_no_valid_senses(entry):
    """Return True if all senses in the entry are excluded based on EXCLUDED_TAGS."""
    if "senses" not in entry:
        return False  # If no senses, we don't exclude

    for sense in entry["senses"]:
        tags = set(sense.get("tags", []))
        if not tags.intersection(EXCLUDED_TAGS):
            return False  # Found at least one non-excluded sense

    return True  # All senses are excluded

def build_pos_etym_index(jsonl_path):
    word_to_pos_etym = defaultdict(set)
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            entry = json.loads(line)
            word = entry.get("word")
            pos = entry.get("pos")
            etym = entry.get("etymology_number")
            if word and pos and etym is not None:
                word_to_pos_etym[word].add((pos, etym))
    return word_to_pos_etym

def load_filtered_entries(jsonl_path, blacklist):
    """
    Load entries with etymology_number == 1 and pos == 'noun',
    keeping only those that have at least one valid declension form.
    """
    form_to_entry = {}

    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            entry = json.loads(line)

            # Some entries have etymology_number. For the purpose of figuring out the
            # top X most used words, we assume that etymology_number 1 corresponds to
            # the most frequent usage of that word
            if "etymology_number" in entry and entry.get("etymology_number") != 1:
                continue
            if entry.get("pos") != "noun":
                continue
            # This will exclude entries that only have archaic senses for example
            if has_no_valid_senses(entry):
                continue

            base_word = entry.get("word")
            if not base_word or base_word in blacklist:
                continue

            valid_forms = []

            for form in entry.get("forms", []):
                if form.get("source") != "declension":
                    continue
                # This will exclude tags that are archaic or dated
                tags = set(form.get("tags", []))
                if tags & EXCLUDED_TAGS:
                    continue
                form_word = form.get("form")
                # Some forms don't include the entire word and just mention the ending
                # that should be appended to the root. Unsure if those wiktionary entries
                # are valid or not so skip those forms for now.
                # Example: https://en.wiktionary.org/wiki/avocat#Noun_10
                if form_word in EXCLUDED_FORMS:
                    continue
                if form_word:
                    valid_forms.append(form_word)

            if not valid_forms:
                continue  # Skip entries with no valid forms

            logger.debug(f"Adding {base_word} and its forms to form_to_entry")
            if base_word not in form_to_entry:
                form_to_entry[base_word] = []
            if entry not in form_to_entry[base_word]:
                form_to_entry[base_word].append(entry)
            for form_word in valid_forms:
                if form_word not in form_to_entry:
                    form_to_entry[form_word] = []
                if entry not in form_to_entry[form_word]:
                    form_to_entry[form_word].append(entry)

    return form_to_entry


def generate_top_entries(lang_code, input_jsonl_path, output_path, blacklist_path, limit=500):
    blacklist = load_blacklist(blacklist_path)
    form_to_entry = load_filtered_entries(input_jsonl_path, blacklist)
    word_to_pos_etym = build_pos_etym_index(input_jsonl_path)
    seen_base_words = set()
    result_entries = []

    for word in iter_wordlist(lang_code, wordlist='best'):
        if word in blacklist:
            continue

        entry = form_to_entry.get(word, [])
        if len(entry) > 1:
            logger.debug(f"{word} has multiple entries! \n {[ e.get('word') for e in entry ]}");

        if entry:
            entry = entry[0]
            base_word = entry.get("word")
            if base_word not in seen_base_words:
                if ((not word_to_pos_etym[base_word] or ('noun', 1) in word_to_pos_etym[base_word]) and
                    (not word_to_pos_etym[word] or ('noun', 1) in word_to_pos_etym[word])):
                    logger.debug(f"Adding {base_word} (from word {word})")
                    result_entries.append(entry)
                    seen_base_words.add(base_word)
                else:
                    logger.debug(f"POS mismatch for {base_word}/{word}: {word_to_pos_etym[base_word]} and {word_to_pos_etym[word]}")
            else:
                logger.debug(f"Already added {base_word} (while analyzing {word})")
        else:
            logger.debug(f"Skipping {word}, did not fulfill criteria")

        if len(result_entries) >= limit:
            break

    #logger.debug(f"Final top {limit} list is {sorted([ entry.get('word') for entry in result_entries])}")
    logger.debug(f"Final top {limit} list is {[ entry.get('word') for entry in result_entries]}")
    with open(output_path, 'w', encoding='utf-8') as out_file:
        for entry in result_entries:
            out_file.write(json.dumps(entry, ensure_ascii=False) + '\n')

    logger.info(f"✅ Wrote {len(result_entries)} entries to: {output_path}")

if __name__ == '__main__':
    generate_top_entries(
            lang_code='ro',
            input_jsonl_path='./data/ro.jsonl',
            output_path='top500_ro_nouns.jsonl',
            blacklist_path='./data/top500_ro_nouns_blacklist.txt',
            limit=500)
    generate_top_entries(
            lang_code='sv',
            input_jsonl_path='./data/sv.jsonl',
            output_path='top500_sv_nouns.jsonl',
            blacklist_path='./data/top500_sv_nouns_blacklist.txt',
            limit=500)
    # generate_top_entries(
    #         lang_code='sh',
    #         input_jsonl_path='./data/sh.jsonl',
    #         output_path='top500_sh_nouns.jsonl',
    #         blacklist_path='./data/top500_sv_nouns_blacklist.txt',
    #         limit=500)
