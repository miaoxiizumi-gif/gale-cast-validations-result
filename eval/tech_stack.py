"""Public-safe implementation inventory; independent of private data/model loaders.

Version status values:
  pin       = exact version pinned in the application's requirements file or CDN URL at SOURCE_COMMIT (configuration evidence)
  research  = version installed in the evaluation environment used for this repository (checked 2026-10-25)
  artifact  = recorded in a deployed artifact's own metadata (e.g. the Keras archive)
  verified  = checked against the deployment itself (repository/HTTP), as stated in the cited handoff
  none      = no version evidence; not stated
No live package inventory of the running containers was taken.
"""
from html import escape
from pathlib import Path

REVIEW_DATE = '2026-10-25'
SOURCE_COMMIT = 'bb056a9'
HEAD = ['Layer', 'Technology', 'Actual role', 'Source evidence (GALE-CAST @ bb056a9)', 'Version evidence', 'Version status']
ROWS = [
    ('Web interface', 'HTML5, CSS3, vanilla JavaScript', 'Single-page dashboard; no build step', 'dashboard.html (10,586 lines); static/',
     'no framework dependency found (no React/Next.js)', 'none'),
    ('Mapping', 'Leaflet; topojson-client; OpenStreetMap tiles', 'Map display, city/barangay boundaries from TopoJSON, base tiles (two OSM mirrors as fallbacks)',
     'dashboard.html:222, 4165-4166, 4586-4596; barangays-municity-955-manila.topo.0.1.json; static/manila-districts.js',
     'Leaflet 1.9.4; topojson-client 3.1.0 (unpkg URLs)', 'pin'),
    ('Charts', 'Chart.js', 'Weather and climatology charts, loaded on demand', 'dashboard.html:5841', 'Chart.js 4.4.0 (jsDelivr URL)', 'pin'),
    ('Offline and push (browser)', 'Service Worker, Cache API, Push API (VAPID)', 'Offline fallback and push subscription', 'static/sw.js; dashboard.html:9219 (pushManager.subscribe), 9261 (serviceWorker.register)',
     'browser-native APIs', 'none'),
    ('Backend API', 'Python; Flask; flask-cors; Gunicorn', 'JSON API and static serving; Gunicorn runs app:app (gthread, 1 worker × 2 threads by default) in the Docker image',
     'app.py:107-108; Dockerfile:1, 102; requirements.txt', 'Python 3.11 (python:3.11-slim); Flask 3.1.3; flask-cors 6.0.2; gunicorn 23.0.0', 'pin'),
    ('Database', 'PostgreSQL via SQLAlchemy (psycopg2 driver)', 'Observation, prediction and forecast tables; SQL through SQLAlchemy create_engine with a postgresql:// URL',
     'app.py:119, 477; docker/db-init/schema.sql; requirements.txt', 'SQLAlchemy 2.0.38; psycopg2-binary 2.9.11; PostgreSQL server version not recorded; hosted provider (code comments say Supabase) not verified', 'pin'),
    ('Machine learning', 'TensorFlow / Keras; deployed model W1', 'W1: dual-stream ANN–LSTM–Attention, 40,872 parameters: input_normal (32 days × 32 features) → LSTM(64) → Dense(32); input_anomaly (32 × 4) → LSTM → additive attention over time steps → LSTM(32) → Dense(16); merged → dropout → gale_prob (sigmoid) and weather_vars (6 regression outputs)',
     'app.py:49, 120-121; Dockerfile:15-16; evaluation run s1-identity (layer list)', 'tensorflow-cpu 2.16.1 (pin); model saved by Keras 3.13.2 (archive metadata); model SHA-256 f2db5aa9…9d14b0 identical in the Space repository 8ffbbb5', 'pin / artifact / verified'),
    ('Data processing', 'NumPy; pandas; scikit-learn; joblib', 'Feature engineering, min-max scalers, serialized scaler artifacts', 'process_weather.py; app.py:56-58; requirements.txt',
     'numpy 1.26.4; pandas 2.2.2; scikit-learn 1.7.2; joblib 1.5.3 (same versions in the evaluation environment)', 'pin / research'),
    ('Data retrieval and scheduling', 'requests; truststore; APScheduler; Windows Task Scheduler', 'PAGASA ten-day forecast retrieval and import; midnight push-alert job; scheduled local pipeline',
     'fetch_pagasa_tenday.py; run_tenday_pipeline.py; app.py:2593-2594; requirements.txt; docs/PROJECT_STRUCTURE.md', 'requests 2.32.5; truststore 0.10.4; APScheduler 3.10.4', 'pin'),
    ('Push delivery (server)', 'pywebpush; py-vapid', 'Sends Web Push notifications with VAPID keys', 'app.py:114-115, 2313-2340; requirements.txt', 'pywebpush 2.3.0; py-vapid 1.9.4', 'pin'),
    ('Frontend hosting', 'Vercel', 'Serves the dashboard; rewrites /api/* to the backend; old domain redirects', 'hosting/vercel.json; docs/handoff/DEPLOYMENT_AND_GITHUB.md',
     'HTTP 200 on gale-cast.vercel.app recorded in the handoff (deployed from a hand-built folder, not git)', 'verified (handoff)'),
    ('Backend hosting', 'Docker on Hugging Face Spaces', 'Builds the Dockerfile and runs Gunicorn on port 5050', 'Dockerfile; docs/handoff/DEPLOYMENT_AND_GITHUB.md',
     '/healthz 200 recorded in the handoff; running container not inspected', 'verified (handoff)'),
    ('Research, testing and report', 'Python; Matplotlib; pytest; GitHub Actions; Git/GitHub; GitHub Pages', 'Evaluation scripts and figures; automated tests; this static report',
     '.github/workflows/tests.yml (ubuntu, Python 3.11); requirements-dev.txt; this repository eval/', 'pytest 9.1.1; matplotlib 3.9.2 (pins; same in the evaluation environment, Python 3.11.9)', 'pin / research'),
]

CH3 = ('GALE-CAST is implemented as a single-page web dashboard written in HTML, CSS and JavaScript, using Leaflet for maps and Chart.js for '
       'charts, with a browser service worker for offline use and the Web Push API for notifications. A Python Flask API, served by Gunicorn in a '
       'Docker container, reads and writes a PostgreSQL database through SQLAlchemy. The forecasting model (W1) is a dual-stream ANN–LSTM–Attention '
       'network built with TensorFlow/Keras; data preparation uses NumPy, pandas and scikit-learn. PAGASA forecasts are retrieved with scheduled '
       'Python jobs. The interface is hosted on Vercel and the API on Hugging Face Spaces. These components describe how the prototype is built; '
       'the accuracy of the model\'s forecasts is assessed separately (retrospective forecast verification with persistence and climatology benchmarking).')


def markdown():
    lines = ['# Verified implementation technology stack', '',
             f'Reviewed {REVIEW_DATE} against GALE-CAST source commit `{SOURCE_COMMIT}` (application repository) and this repository\'s evaluation records. '
             'First compiled by Tinenen-cs (commit 8b32465); verified and extended on the same date.', '',
             'This is an implementation inventory, not evidence that every component works in production or that forecasts are accurate. '
             '"Version status": **pin** = exact version in the application\'s requirements file or CDN URL; **research** = installed in the evaluation '
             'environment used here; **artifact** = recorded inside a deployed file; **verified (handoff)** = deployment checked in the cited handoff; '
             '**none** = no version evidence. No live package inventory of the running services was taken.', '',
             '| ' + ' | '.join(HEAD) + ' |', '|' + '|'.join('---' for _ in HEAD) + '|']
    lines += ['| ' + ' | '.join(row) + ' |' for row in ROWS]
    lines += ['', '## Chapter 3 implementation paragraph (proposed)', '', CH3, '',
              'Revision-ledger entry P-37 places this paragraph in Chapter 3. Do not describe the interface as React/Next.js or the database as MySQL, '
              'and do not present the technology list as validation evidence.', '']
    return '\n'.join(lines)


def section_html():
    heads = ''.join(f'<th>{escape(v)}</th>' for v in HEAD)
    body = ''.join('<tr>' + ''.join(f'<td>{escape(v)}</td>' for v in row) + '</tr>' for row in ROWS)
    return (f'<p>Reviewed {REVIEW_DATE} against application source <code>{SOURCE_COMMIT}</code>. <b>Version status</b>: pin = exact version in the '
            'requirements file or CDN URL; research = installed in this evaluation environment; artifact = recorded in a deployed file; verified (handoff) = '
            'deployment checked in the project handoff; none = no version evidence. No live package inventory was taken.</p>'
            f'<div class="tw"><table><thead><tr>{heads}</tr></thead><tbody>{body}</tbody></table></div>'
            f'<h3>Chapter 3 implementation paragraph (proposed)</h3><p class="para">{escape(CH3)}</p>'
            '<p>The technology stack describes how the prototype is implemented. It does not establish forecast accuracy, successful notification delivery, or operational readiness.</p>'
            '<p><a href="data/documentation/TECH_STACK.md">Download the stack summary</a>.</p>')


def write_documents(root):
    for rel in ('documentation/TECH_STACK.md', 'docs/data/documentation/TECH_STACK.md'):
        p = Path(root) / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(markdown(), encoding='utf-8')


if __name__ == '__main__':
    write_documents(Path(__file__).resolve().parents[1])
