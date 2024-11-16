from __future__ import unicode_literals

import gc
# from multiprocessing import Process
# import gc

import os
from uuid import uuid4
from pathlib import Path
import time

import torch.cuda
from dotenv import load_dotenv

from flask import Flask, request, render_template, url_for, redirect, make_response, abort, jsonify
import whisperx

from model import save_log_message, get_job, get_job_logs, \
    save_new_job, update_job_status, get_all_jobs

app = Flask('flask-whisperx')
app.logger.setLevel('DEBUG')

load_dotenv()  # take environment variables from .env.
HF_TOKEN = os.getenv('HF_TOKEN')

def dual_log(job_id: str, log_str: str):
    app.logger.info(log_str)
    save_log_message(job_id, log_str)


# Worker process - single download job
# TODO poll the DB for other new jobs
def worker(audio_file: Path, job_id: str, podcast: str, episode_number: str):
    dual_log(job_id, f'Starting WhisperX on {job_id} from {podcast} episode {episode_number}')

    device = "cuda"
    batch_size = 16  # reduce if low on GPU mem
    compute_type = "float16"  # change to "int8" if low on GPU mem (may reduce accuracy)

    dual_log(job_id, 'Loading model')
    # 1. Transcribe with original whisper (batched)
    model = whisperx.load_model("large-v2", device, compute_type=compute_type, language='en')

    # save model to local path (optional)
    # model_dir = "/path/"
    # model = whisperx.load_model("large-v2", device, compute_type=compute_type, download_root=model_dir)

    dual_log(job_id, 'Loading audio file')
    audio = whisperx.load_audio(audio_file)

    dual_log(job_id, 'Transcribing')
    result = model.transcribe(audio, batch_size=batch_size, language='en')

    # print(result["segments"])  # before alignment

    # delete model if low on GPU resources
    # import gc; gc.collect(); torch.cuda.empty_cache(); del model

    # 2. Align whisper output
    dual_log(job_id, 'Aligning timestamps')
    model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=device)
    result = whisperx.align(result["segments"], model_a, metadata, audio, device, return_char_alignments=False)

    # print(result["segments"])  # after alignment

    # delete model if low on GPU resources
    # import gc; gc.collect(); torch.cuda.empty_cache(); del model_a
    dual_log(job_id, 'Freeing up memory')
    gc.collect()
    torch.cuda.empty_cache()
    del model_a

    # 3. Assign speaker labels
    dual_log(job_id, 'Attributing speakers')
    diarize_model = whisperx.DiarizationPipeline(use_auth_token=HF_TOKEN, device=device)

    dual_log(job_id, 'Diarizing')
    # add min/max number of speakers if known
    diarize_segments = diarize_model(audio)
    # diarize_model(audio, min_speakers=min_speakers, max_speakers=max_speakers)

    dual_log(job_id, 'Assigning word speakers')
    result = whisperx.assign_word_speakers(diarize_segments, result)
    # print(diarize_segments)
    # print(result["segments"])  # segments are now assigned speaker IDs

    update_job_status(job_id, 'DONE', 0)
    dual_log(job_id, f'Done with {job_id}')
    # FIXME
    dual_log(job_id, 'Saving output to /tmp/transcript')
    open('/tmp/transcript', 'w').write(str(result))

    return jsonify(result)


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


@app.route('/submit/<podcast>/<episode_number>', methods=['POST'])
def submit(podcast: str, episode_number: str):
    job_id = uuid4().hex
    filedata = request.files['file']
    filename = filedata.filename
    if filename is None:
        app.logger.error('No file uploaded')
        abort(400, 'No file uploaded')

    if not podcast:
        app.logger.error('No podcast name provided')
        abort(400, 'No podcast name provided')
    if not episode_number:
        app.logger.error('No episode number provided')
        abort(400, 'No episode number provided')

    # Save filedata to tempfile
    audio_file = Path('/tmp/') / job_id
    audio_file.write_bytes(filedata.read())
    app.logger.info(f'Saved {filename} to {audio_file}')
    # Save to DB
    save_new_job(job_id, podcast, episode_number, title)
    update_job_status(job_id, 'RUNNING', 0)
    return(worker(audio_file, job_id, podcast, episode_number))
    # NB Process commented out - with just the 2080 we are limited to one job at a time,
    # so its best to block on completion
    # p = Process(target=worker, args=(audio_file, job_id, title))
    # p.start()
    # send to new in-process page, job_id as key
    # return redirect(f'/job/{job_id}')


@app.route('/retry/<job_id>', methods=['GET'])
def retry(job_id):
    job_info = get_job(job_id)
    if job_info is None:
        return make_response(f'Job {job_id} not found', 404)

    audio_file = Path('/tmp/') / job_id
    job_id = job_info['job_id']
    title = job_info['title']

    update_job_status(job_id, 'RUNNING', 0)
    # p = Process(target=worker, args=(url, dest_dir, job_id))
    # p.start()
    worker(audio_file, job_id, title)
    # send to new in-process page, job_id as key
    return redirect(f'/job/{job_id}')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5050)
