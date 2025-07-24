# declinare
App for practicing noun declensions and verb conjugations in different languages.

See it live at <https://declinare.onrender.com/>.

## Dictionaries
The dictionaries currently in use come from <https://kaikki.org/index.html>:
* Swedish - <https://kaikki.org/dictionary/Swedish/index.html>
* Romanian - <https://kaikki.org/dictionary/Romanian/index.html>
* Serbo-Croatian - <https://kaikki.org/dictionary/Serbo-Croatian/index.html>

Those dictionaries, in turn, are based on <https://en.wiktionary.org/>.

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
  ~/git/declinare > gunicorn app:app
  ```
* Use your web browser to go to the address mentioned in `gunicorn`'s output
