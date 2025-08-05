# declinare
App for practicing noun declensions and verb conjugations in different languages.

See it live at <https://declinare.onrender.com/>.

## Dictionaries
The dictionaries currently in use come from <https://kaikki.org/index.html>:
* Swedish - <https://kaikki.org/dictionary/Swedish/index.html>
* Romanian - <https://kaikki.org/dictionary/Romanian/index.html>
* Serbo-Croatian - <https://kaikki.org/dictionary/Serbo-Croatian/index.html>

Those dictionaries, in turn, are based on <https://en.wiktionary.org/>.

The dictionaries are parsed by the `split_by_pos.py` script in order to
create separate smaller dictionaries containing only nouns, verbs and
adjectives. It is these smaller dictionaries which are used by the app.

### Top X most frequently used nouns/verbs/adjectives

When starting to learn a language it is beneficial to focus on learning the most
commonly used words in that language. The purpose of the checkbox on the website
is to pull words from the top 500 most frequently used words of the selected
language instead of the entire dictionary.

Creating a list of the top 500 most frequently used nouns/verbs/adjectives for a
specific language is not trivial. Simplified, the approach taken here is to use
the wordfreq library <https://github.com/rspeer/wordfreq> and traverse in
descending frequency order the list of the most common words in a given language,
and filter the parts of speech one is interested in by using the dictionaries
mentioned above.

The problem is that languages have words which can be different parts of speech,
depending on the context. For example, the word `care` in Romanian can be a
determiner, a pronoun, or the plural form of the noun `car`. Which of these is
most common when encountering the word in the wordfreq list? It is impossible to
say. I have had to "cheat" and use pre-existing knowledge of the language and
create blacklists to ignore specific words when building Top X lists. For `care`
I assume that it is most commonly used as a determiner and a pronoun so when
building the Top 500 Romanian nouns, I added it to the blacklist so that it is
ignored.

This means that the Top 500 nouns/verbs/adjectives dictionaries are far from
perfect since the blacklists are manually maintained and the `extract_top_500.py`
script makes a bunch of assumptions which can fail and lead to words missing
from or being erroneously added to the list.

## Running locally
If you want to run the app locally then you can use the following commands:
* Set up a separate Python virtual environment and install all dependencies in it
  ```
  ~/git/declinare > python3 -m venv .venv
  ~/git/declinare > source .venv/bin/activate
  ~/git/declinare > pip install -r requirements.txt
  ```
* Run the web server
  ```
  ~/git/declinare > SECRET_KEY="aaaa" gunicorn app:app
  ```
* Use your web browser to go to the address mentioned in `gunicorn`'s output
