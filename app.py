import random
from datetime import datetime
from typing import List

import streamlit as st
import yaml
from pydantic import BaseModel

from db import init_db, create_deployment, list_deployments

DATA_DIR = "data"

# ---------- Models ----------

class Environment(BaseModel):
    name: str
    type: str
    branch: str
    product: str
    deployment_target: str
    ci_system: str

class Dependency(BaseModel):
    product: str
    version: str
    requires: List[str]

class ReleaseWindow(BaseModel):
    name: str
    environments: List[str]
    day_of_week: str
    window_utc: str

# ---------- Helpers ----------

def load_yaml(path):
    with open(path, "r") as f:
        return yaml.safe_load(f)

@st.cache_data
def load_environments() -> List[Environment]:
    raw = load_yaml(f"{DATA_DIR}/environments.yml")
    return [Environment(**e) for e in raw["environments"]]

@st.cache_data
def load_dependencies() -> List[Dependency]:
    raw = load_yaml(f"{DATA_DIR}/dependencies.yml")
    return [Dependency(**d) for d in raw["dependencies"]]

@st.cache_data
def load_cadence() -> List[ReleaseWindow]:
    raw = load_yaml(f"{DATA_DIR}/release_cadence.yml")
    return [ReleaseWindow(**c) for c in raw["cadence"]]

def simulate_build_and_deploy(env: Environment, product: str, version: str, branch: str):
    """
    Purely simulated build + deploy.
    Randomly returns SUCCESS or FAILED.
    """
    # Fake build time
    st.info(f"Simulating build for {product} on branch `{branch}` in CI system `{env.ci_system}`...")
    st.write("Using placeholder URLs only. No real CI calls are made.")
    # Fake outcome
    outcome = random.choices(["SUCCESS", "FAILED"], weights=[0.8, 0.2])[0]
    return outcome

def generate_release_message(env: Environment, product: str, version: str, branch: str, status: str):
    when = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    return f"""
Release update – *{env.name}*

- Product: **{product}**
- Version: **{version}**
- Branch: `{branch}`
- Target: `{env.deployment_target}`
- Status: **{status}**
- Time: {when}

If you see any issues, please raise them in the release channel.
"""

# ---------- Main app ----------

def main():
    st.set_page_config(page_title="GW Release & Deployment Dashboard", layout="wide")
    st.title("Guidewire Release & Deployment Dashboard (Simulated)")

    init_db()

    envs = load_environments()
    deps = load_dependencies()
    cadence = load_cadence()

    tab_envs, tab_build, tab_history, tab_cadence, tab_comms = st.tabs(
        ["Environment registry", "Simulated build & deploy", "Deployment history", "Release cadence", "Comms templates"]
    )

    # --- Environment registry ---
    with tab_envs:
        st.subheader("Environment register")
        st.dataframe([e.model_dump() for e in envs])

        st.subheader("Dependencies")
        st.dataframe([d.model_dump() for d in deps])

    # --- Simulated build & deploy ---
    with tab_build:
        st.subheader("Simulated build & deploy")

        env_names = [e.name for e in envs]
        selected_env_name = st.selectbox("Environment", env_names)
        selected_env = next(e for e in envs if e.name == selected_env_name)

        col1, col2 = st.columns(2)
        with col1:
            product = st.text_input("Product", value=selected_env.product)
            version = st.text_input("Version (tag or artifact version)", value="10.0.0")
        with col2:
            branch = st.text_input("Branch", value=selected_env.branch)
            triggered_by = st.text_input("Triggered by", value="build-coordinator")

        if st.button("Simulate build & deploy"):
            with st.spinner("Running simulated build & deploy..."):
                status = simulate_build_and_deploy(selected_env, product, version, branch)
                rec = create_deployment(
                    environment=selected_env.name,
                    product=product,
                    version=version,
                    branch=branch,
                    status=status,
                    triggered_by=triggered_by,
                )
            if status == "SUCCESS":
                st.success(f"Simulated deployment SUCCESS (id={rec.id})")
            else:
                st.error(f"Simulated deployment FAILED (id={rec.id})")

            st.markdown("#### Generated release message")
            msg = generate_release_message(selected_env, product, version, branch, status)
            st.code(msg, language="markdown")

    # --- Deployment history ---
    with tab_history:
        st.subheader("Deployment history (local SQLite)")
        records = list_deployments(limit=200)
        if not records:
            st.info("No deployments recorded yet. Run a simulated deployment first.")
        else:
            rows = [
                {
                    "id": r.id,
                    "environment": r.environment,
                    "product": r.product,
                    "version": r.version,
                    "branch": r.branch,
                    "status": r.status,
                    "triggered_by": r.triggered_by,
                    "created_at": r.created_at,
                }
                for r in records
            ]
            st.dataframe(rows, use_container_width=True)

    # --- Release cadence ---
    with tab_cadence:
        st.subheader("Release cadence")
        st.dataframe([c.model_dump() for c in cadence])

        st.markdown(
            "Use this to agree **non-prod / pre-prod windows** and freeze periods. "
            "You can extend this with calendar exports later."
        )

    # --- Comms templates ---
    with tab_comms:
        st.subheader("Release communication templates")

        env_names = [e.name for e in envs]
        env_name = st.selectbox("Environment for message", env_names, key="comms_env")
        env = next(e for e in envs if e.name == env_name)

        product = st.text_input("Product", value=env.product, key="comms_product")
        version = st.text_input("Version", value="10.0.0", key="comms_version")
        branch = st.text_input("Branch", value=env.branch, key="comms_branch")
        status = st.selectbox("Status", ["PLANNED", "IN PROGRESS", "SUCCESS", "FAILED"], key="comms_status")

        if st.button("Generate message", key="comms_btn"):
            msg = generate_release_message(env, product, version, branch, status)
            st.markdown("#### Slack / Email body")
            st.code(msg, language="markdown")

if __name__ == "__main__":
    main()