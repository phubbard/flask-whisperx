# flask-whisperx

Web page and REST API for calling WhisperX (speech-to-text with speaker diarization).

POST endpoint, logging to sqlite, index page with previous jobs - started from the [ytdl](https://github.com/yt-dlp/yt-dlp) project.

## Project goals
- Lightweight web pages that load fast, render properly on desktop, mobile and tablet. 
- No javascript
- hands-off operation
- DIY the SQL part, just to learn it myself
- SQLite for jobs and logging

## Current status

Works as intended:
- Basic Bootstrap v4 CSS, explicitly _without_ JS. Input validation is most-basic, but looks OK.
- No file management, I expect clutter to accumulate.
- Utterly insecure - no input validation, so internal-network use only. [Little Bobby Tables risk](https://xkcd.com/327/)
- Added 'retry' button to failed downloads
 
### Next steps
- Add pagination to index table
- Add intelligence to log display - collapse the middle if too long (accordion maybe)
- Widen margins on log display
- Add 'retry this download IFF rc != 0' kind of thing
- Parse debug logs or API to include download bytes and percentage to poll/detail. Progress bar!
- Move ad-hoc test code into proper unit tests.
- For iOS, add manifest or whatever so it looks a proper home screen icon.
- Productionize it - WSGI, debug off, reverse proxy. Cannot currently be exposed to the internet.
- Some sort of temp directory with automatic cleanup would be cool.
- Try [v2 Flask beta?](https://www.reddit.com/r/Python/comments/msbt3p/flask_20_is_coming_please_help_us_test/)

## Installation

	python3 -m venv venv
	source venv/bin/activate
	pip install -r requirements.txt
	
## Run it

	source venv/bin/activate
	python main.py

There's also run.sh for in the background.

## Tools and libraries

FastAPI lacks the built-in templates and html support, so Flask is perfect. Loguru is nice for logging.

## Docs

- [Flask](https://flask.palletsprojects.com/en/1.1.x/) for fastest dev
- [Loguru](https://loguru.readthedocs.io/en/stable/index.html) for logging
- CSS styles from [Bootstrap v4](https://getbootstrap.com/docs/5.0/forms/overview/)
- Film icon from [here](https://icons.getbootstrap.com/icons/film/)
- Reset icon from [here](https://icons.getbootstrap.com/icons/x-circle/)  
- Favicon from [here](https://www.favicon.cc/?action=icon&file_id=993509)
- Form styled using [this documentation](https://getbootstrap.com/docs/5.0/forms/overview/)
