# comparador_gtfs (refactor) ola

Project to compare GTFS offer vs operation and upload results to SharePoint.

## Setup

1. Create virtualenv and install dependencies:

```bash
python -m venv .venv
.venv\Scripts\activate    # Windows
pip install -r requirements.txt
```

2. Edit `config.py` if you need to change the SharePoint site or GTFS folder names.

3. Run the analysis:

```bash
python gtfs_analysis.py
```

The script will prompt for SharePoint credentials (unless provided via `SP_USER` and `SP_PASS` environment variables).
