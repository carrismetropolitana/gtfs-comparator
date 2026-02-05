# Copilot Instructions for GTFS Comparator

## Project Overview
- This project compares GTFS (General Transit Feed Specification) offer vs operation plans and exports results to Excel, supporting contract validation and operational analysis.
- The main orchestration script is `run_analysis.py`, which coordinates configuration, data loading, analysis, alerting, and export.
- All core logic is modularized under the `analysis/` directory, with each file handling a specific comparison or export task.

## Key Components
- **Configuration**: Interactive, session-only config via `config/cli.py` (`configurar()`), with global access managed by `config/runtime.py` (`init_config`, `get`).
- **Analysis Modules**: Each file in `analysis/` (e.g., `compare_routes.py`, `compare_extension.py`, `summaries.py`) implements a single responsibility, returning DataFrames and updating a shared alerts DataFrame.
- **Alerting**: All inconsistencies and errors are logged to a central DataFrame using helpers from `analysis/alerts.py`.
- **Exports**: Results are written to Excel using `analysis/exports.py`, with multiple sheets and optional extra files for stop sequences and circulation summaries.

## Developer Workflow
- **Setup**: Use a virtual environment and install dependencies from `requirements.txt` (pandas, numpy, openpyxl).
- **Run**: Execute `python run_analysis.py` and follow the CLI prompts for configuration. No persistent config files are used.
- **Outputs**: Main results are saved as Excel files in the user-specified target folder. Alert and summary DataFrames are always included.

## Project Conventions
- **Portuguese Naming**: Most code, comments, and CLI prompts are in Portuguese. Variable and function names are descriptive and domain-specific.
- **DataFrames**: All data processing is pandas-based. Each analysis step returns or updates DataFrames.
- **No Hardcoded Paths**: All file paths and names are provided interactively at runtime.
- **Single Responsibility**: Each module in `analysis/` should only handle one aspect of the comparison or export.
- **Alert Severity**: Alerts are classified by severity (e.g., "MUITO GRAVE") and always include plan context.

## Examples
- To add a new comparison, create a new module in `analysis/`, ensure it returns DataFrames, and update `run_analysis.py` to integrate it.
- To add a new export, extend `analysis/exports.py` and call it conditionally in `run_analysis.py`.

## Key Files
- `run_analysis.py`: Main entry point and workflow orchestrator.
- `config/cli.py`, `config/runtime.py`: Interactive config and global state.
- `analysis/`: All comparison, alert, and export logic.

## External Integration
- No external APIs or persistent databases are used. All data is local and user-provided at runtime.

---
For any unclear conventions or missing patterns, please review the latest code in `run_analysis.py` and `analysis/` modules.
