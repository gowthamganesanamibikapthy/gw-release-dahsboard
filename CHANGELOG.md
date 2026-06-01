# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- **Go-live Manager Tab**: Complete Cloud Go-live management with:
  - **Cutover Plan Generator**: Create detailed cutover plans with checklists, build details, and UTC timing
  - **Rollback Plan Generator**: Document rollback steps with preconditions
  - **Rollout Plan Generator**: Define rollout stages (canary, gradual increase, etc.)
  - **Release Notes Generator**: Auto-generate release notes with build details and integrations
  - **Integration Vault**: Registry of integrations and dependencies
  - **Trackers CSV Export**: Generate CSV for task tracking with status (TODO, DONE, etc.)
  - All templates include:
    - Markdown preview in-app
    - Download buttons (markdown & CSV formats)
    - Pre-populated example data

### Fixed
- **Missing YAML Import**: Uncommented `import yaml` in `app.py` to fix ModuleNotFoundError
- **Tab Unpacking Error**: Fixed `st.tabs()` to properly unpack 6 tab variables for 6 tab labels

### Changed
- Renamed `requirement.txt` → `requirements.txt` (standard naming convention)

### Dependencies
- streamlit==1.34.0
- PyYAML==6.0.1
- pydantic==2.7.1
- sqlalchemy==2.0.29

## Deployment

### Streamlit Cloud (Recommended)
1. Connect GitHub repo: https://github.com/gowthamganesanamibikapthy/gw-release-dahsboard
2. Deploy:
   - Branch: `main`
   - Main file: `app.py`
   - Python version: 3.10+

### Local Testing
```bash
pip install -r requirements.txt
streamlit run app.py
```

### Environment Setup
- No additional environment variables required
- SQLite database (`deployments.db`) auto-creates on first run
- YAML config files required in `data/` folder:
  - `environments.yml`
  - `dependencies.yml`
  - `release_cadence.yml`
