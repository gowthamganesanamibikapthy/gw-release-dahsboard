# GW Release & Deployment Dashboard (Simulated)

This is a simulated dashboard for Guidewire release and deployment.

## How to run

1. Clone the repository:

   ```bash
   git clone <repository_url>
   cd gw-release-dahsboard
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Run the Streamlit app:

   ```bash
   streamlit run app.py
   ```

## Project Structure

```
.github/
├── workflows/
│   └── main.yml
├── ISSUE_TEMPLATE.md
└── PULL_REQUEST_TEMPLATE.md
.gitignore
data/
├── dependencies.yml
├── environments.yml
└── release_cadence.yml
db.py
app.py
requirements.txt
README.md
```
