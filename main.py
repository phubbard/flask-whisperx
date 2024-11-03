from __future__ import unicode_literals
from multiprocessing import Process
from tempfile import NamedTemporaryFile
from uuid import uuid4
from pathlib import Path

from flask import Flask, request, render_template, url_for, redirect, make_response, abort

from model import save_log_message, get_job, get_job_logs, \
    save_new_job, update_job_status, get_all_jobs


app = Flask('flask-whisperx')
app.logger.setLevel('DEBUG')



# Worker process - single download job
# TODO poll the DB for other new jobs
def worker(audio_file: Path, job_id: str):
    # TODO call whisperX
    log_str = f'Starting WhisperX on {job_id} from {audio_file.name}'
    app.logger.info(log_str)
    save_log_message(job_id, log_str)

    update_job_status(job_id, 'DONE', 0)
    save_log_message(job_id, 'Done')

# Display the to-be-downloaded page (index)
@app.route('/', methods=['GET'])
def index():
    job_list = get_all_jobs(0, 20)
    return render_template('index.html', job_list=job_list)


# Display a single download job
@app.route('/job/<job_id>', methods=['GET'])
def poll_job(job_id):
    job_info = get_job(job_id)
    if job_info is None:
        return make_response(f'Job {job_id} not found', 404)

    title = job_info['title']
    status = job_info['status']
    job_logs = get_job_logs(job_id)
    restart_url = url_for('index')
    return render_template('job.html', job_logs=job_logs,
                           status=status, restart_url=restart_url, title=title)


@app.route('/submit', methods=['POST'])
def submit():
    job_id = uuid4().hex
    filedata = request.files['file']
    filename = filedata.filename
    if filename is None:
        app.logger.error('No file uploaded')
        abort(400, 'No file uploaded')

    title = request.form['title']
    if title == '':
        app.logger.error('No title provided')
        abort(400, 'No title provided')

    # Save filedata to tempfile
    audio_file = Path('/tmp/') / job_id
    audio_file.write_bytes(filedata.read())
    app.logger.info(f'Saved {filename} to {audio_file}')
    # Save to DB
    save_new_job(job_id, title)
    update_job_status(job_id, 'RUNNING', 0)
    # worker(audio_file, job_id)
    p = Process(target=worker, args=(audio_file, job_id))
    p.start()
    # send to new in-process page, job_id as key
    return redirect(f'/job/{job_id}')


@app.route('/retry/<job_id>', methods=['GET'])
def retry(job_id):
    job_info = get_job(job_id)
    if job_info is None:
        return make_response(f'Job {job_id} not found', 404)

    url = job_info['url']
    dest_dir = job_info['dest_dir']
    update_job_status(job_id, 'RUNNING', 0)
    p = Process(target=worker, args=(url, dest_dir, job_id))
    p.start()
    # send to new in-process page, job_id as key
    return redirect(f'/job/{job_id}')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5050)