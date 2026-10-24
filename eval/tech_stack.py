"""Public-safe implementation inventory; independent of private data/model loaders."""
from html import escape
from pathlib import Path

REVIEW_DATE = '2026-10-25'
SOURCE_COMMIT = 'bb056a9'
ROWS = [
    ('Web interface', 'HTML5, CSS3, vanilla JavaScript', 'dashboard.html and static/', 'Single-page interface with no frontend compilation step; no React/Next.js dependency in the reviewed application.'),
    ('Mapping', 'Leaflet 1.9.4; topojson-client 3.1.0; OpenStreetMap tiles', 'dashboard.html:222,4165-4167,4586; static/manila-districts.js', 'Map rendering, geographic boundaries and tile display. Spatial interpolation and wind animation use project JavaScript/Python logic, not a radar feed.'),
    ('Charts', 'Chart.js 4.4.0', 'dashboard.html:5841', 'Loaded on demand for weather/climatology charts.'),
    ('Offline and notifications', 'Service Worker, Cache API, Web Push/VAPID', 'static/sw.js; dashboard.html:9251-9261; app.py', 'Browser-native PWA/offline/push capabilities. Browser support and actual delivery require separate integration verification.'),
    ('Backend', 'Python 3.11; Flask 3.1.3; flask-cors 6.0.2; Gunicorn 23.0.0', 'Dockerfile:1,102; requirements.txt; app.py', 'Python JSON API; Gunicorn serves app:app in the Docker image. Python 3.11 is the configured image family, not a newly inspected live runtime.'),
    ('Database access', 'PostgreSQL; SQLAlchemy 2.0.38; psycopg2-binary 2.9.11', 'requirements.txt; app.py; schema.sql', 'Relational observation/forecast storage and SQL access. PostgreSQL server version and hosting provider are not established by dependency pins.'),
    ('Machine learning', 'TensorFlow CPU 2.16.1; Keras model format', 'requirements.txt; app.py; W1 identity manifests', 'W1 is a dual-stream ANN–LSTM–Attention model (40,872 parameters), not a replacement architecture. Keras 3.13.2 is recorded for the research environment/artifact compatibility; it is not separately pinned in the reviewed requirements file.'),
    ('Data processing', 'NumPy 1.26.4; pandas 2.2.2; scikit-learn 1.7.2; joblib 1.5.3', 'requirements.txt; process_weather.py; training/inference scripts', 'Numerical processing, dataframe transformations, preprocessing/scalers and serialized auxiliary artifacts. Installed libraries do not prove validation quality.'),
    ('External data and scheduling', 'requests 2.32.5; truststore 0.10.4; APScheduler 3.10.4; Windows Task Scheduler', 'requirements.txt; app.py; docs/PROJECT_STRUCTURE.md', 'PAGASA retrieval, in-app scheduling and separately configured Windows pipeline tasks. Imported PAGASA forecasts are distinct from model outputs.'),
    ('Push delivery backend', 'pywebpush 2.3.0; py-vapid 1.9.4', 'requirements.txt; app.py', 'Server-side Web Push delivery components; no notification was sent during this inventory.'),
    ('Application hosting', 'Vercel frontend; Docker backend on Hugging Face Spaces', 'docs/PROJECT_STRUCTURE.md; docs/handoff/DEPLOYMENT_AND_GITHUB.md; Dockerfile', 'Documented deployment topology. Configuration and repository identity are not verification of the running container or a new deployment.'),
    ('Research and report tooling', 'Python, Matplotlib, pytest; Git/GitHub; GitHub Pages', 'eval/paper_figures.py; eval/build_site.py; .github/workflows/tests.yml', 'Figures, regression/classification evidence, automated checks, version control and this static report. These are tooling, not the deployed model architecture.'),
]

def markdown():
    lines = ['# Verified implementation technology stack', '',
             f'Reviewed {REVIEW_DATE} against GALE-CAST source commit `{SOURCE_COMMIT}` and existing W1 evaluation evidence.', '',
             'This is an implementation inventory, not evidence that every component described in the thesis works in production. Dependency versions are source pins; live installed versions were not queried. The historical W1 experiment may have used earlier dependency pins.', '',
             '| Layer | Technology / version evidence | Source | Purpose / limits |', '|---|---|---|---|']
    lines += ['| ' + ' | '.join(row) + ' |' for row in ROWS]
    lines += ['', '## Suggested Chapter 3 wording', '',
              'The GALE-CAST prototype uses an HTML, CSS and JavaScript interface, Leaflet for map display, and Chart.js for charts. A Python Flask API connects to PostgreSQL through SQLAlchemy and psycopg2. The W1 model is implemented in TensorFlow/Keras and uses a dual-stream ANN–LSTM–Attention architecture. Data preparation uses NumPy, pandas and scikit-learn. The documented hosting arrangement uses Vercel for the frontend and a Docker-based Hugging Face Space for the backend. Browser service workers support offline handling and Web Push components support notifications. Component behaviour and model forecast accuracy are evaluated separately.', '',
              'Confirm this wording against the final implementation version before submitting the paper. Do not describe the interface as React/Next.js, the database as MySQL, or forecast verification as cross-validation unless separate implementation evidence establishes those claims.', '',
              '## Case-study review', '',
              'The public selection summary reports three correct decisions in each station window and nine correct decisions in the common window. Selection favoured correct event decisions and pressure-fall interpretability. It did not select by larger wind readings or by lower wind/pressure error against baselines. The detailed dates and case figures remain private, so this inventory does not independently verify their values or establish selected-case regression superiority.', '']
    return '\n'.join(lines)

def section_html():
    heads = ''.join(f'<th>{escape(v)}</th>' for v in ['Layer','Technology / version evidence','Source','Purpose / limits'])
    body = ''.join('<tr>'+''.join(f'<td>{escape(v)}</td>' for v in row)+'</tr>' for row in ROWS)
    return (f'<p>Reviewed {REVIEW_DATE} against application source <code>{SOURCE_COMMIT}</code>. Versions below are source/configuration evidence, not a fresh inspection of live installed packages. Historical W1 dependencies may differ.</p>'
            f'<div class="tw"><table><thead><tr>{heads}</tr></thead><tbody>{body}</tbody></table></div>'
            '<p>The technology stack describes how the prototype is implemented. It does not establish forecast accuracy, successful notification delivery, or operational readiness.</p>'
            '<p><a href="data/documentation/TECH_STACK.md">Download the stack summary and suggested Chapter 3 wording</a>.</p>')

def write_documents(root):
    for rel in ('documentation/TECH_STACK.md', 'docs/data/documentation/TECH_STACK.md'):
        p = Path(root)/rel
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(markdown(),encoding='utf-8')

if __name__ == '__main__':
    write_documents(Path(__file__).resolve().parents[1])
