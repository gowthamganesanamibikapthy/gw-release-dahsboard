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

def generate_cutover_plan(env: Environment, product: str, version: str, branch: str, build_details: str, checklist: List[str]):
    when = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    checklist_md = "\n".join([f"- {c}" for c in checklist]) if checklist else "- (no checklist items)"
    return f"""
# Cutover Plan – {product} {version} -> {env.name}

- Environment: **{env.name}**
- Product: **{product}**
- Version: **{version}**
- Branch: `{branch}`
- Time (UTC): {when}

## Build details

{build_details}

## Cutover checklist

{checklist_md}
"""

def generate_rollback_plan(env: Environment, product: str, version: str, branch: str, rollback_steps: List[str]):
    steps_md = "\n".join([f"1. {s}" for s in rollback_steps]) if rollback_steps else "1. (no rollback steps specified)"
    return f"""
# Rollback Plan – {product} {version} on {env.name}

## Preconditions
- Environment: **{env.name}**
- Product: **{product}**
- Version: **{version}**

## Rollback steps

{steps_md}
"""

def generate_rollout_plan(env: Environment, product: str, version: str, branch: str, stages: List[str]):
    stages_md = "\n".join([f"- {s}" for s in stages]) if stages else "- (no rollout stages specified)"
    return f"""
# Rollout Plan – {product} {version}

- Environment: **{env.name}**
- Product: **{product}**
- Version: **{version}**
- Branch: `{branch}`

## Rollout stages

{stages_md}
"""

def generate_integration_vault(env: Environment, integrations_text: str, dependencies_text: str):
    return f"""
# Integration Vault – {env.name}

## Integrations

{integrations_text}

## Dependencies

{dependencies_text}
"""

def generate_trackers_csv(items: List[str]):
    # Simple CSV: id,task,status
    lines = ["id,task,status"]
    for i, t in enumerate(items, start=1):
        lines.append(f"{i},{t},TODO")
    return "\n".join(lines)

# ---------- Main app ----------

def main():
    st.set_page_config(page_title="GW Release & Deployment Dashboard", layout="wide")
    st.title("Guidewire Release & Deployment Dashboard (Simulated)")

    init_db()

    envs = load_environments()
    deps = load_dependencies()
    cadence = load_cadence()

    tab_envs, tab_build, tab_history, tab_cadence, tab_comms, tab_golive = st.tabs(
        ["Environment registry", "Simulated build & deploy", "Deployment history", "Release cadence", "Comms templates", "Go-live manager"]
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

    # --- Go-live manager ---
    with tab_golive:
        st.subheader("Go-live manager: templates and trackers")

        env_names = [e.name for e in envs]
        sel_env_name = st.selectbox("Environment", env_names, key="golive_env")
        sel_env = next(e for e in envs if e.name == sel_env_name)

        product = st.text_input("Product", value=sel_env.product, key="golive_product")
        version = st.text_input("Version", value="10.0.0", key="golive_version")
        branch = st.text_input("Branch", value=sel_env.branch, key="golive_branch")

        st.markdown("---")
        st.subheader("Build & integration details")
        build_details = st.text_area("Build details (CI links, artifact locations)", value="- CI: https://ci.example.com/job/123\n- Artifact: s3://bucket/artifact-10.0.0.zip", height=120)
        integrations = st.text_area("Integrations (one per line, include endpoints/contacts)", value="ServiceA - https://api.servicea.local - ops@servicea", height=120)
        dependencies = st.text_area("Dependencies (one per line)", value="lib-foo: 1.2.3\nlib-bar: 4.5.6", height=120)

        st.markdown("---")
        st.subheader("Plans & checklists")
        checklist_txt = st.text_area("Cutover checklist (one per line)", value="Notify stakeholders\nQuiesce traffic\nDeploy artifacts", height=120)
        rollback_txt = st.text_area("Rollback steps (one per line)", value="Restore DB snapshot\nRedeploy previous artifact", height=120)
        rollout_txt = st.text_area("Rollout stages (one per line)", value="Canary - 5%\nGradual increase to 100%", height=120)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Generate Cutover Plan"):
                checklist = [l.strip() for l in checklist_txt.splitlines() if l.strip()]
                md = generate_cutover_plan(sel_env, product, version, branch, build_details, checklist)
                st.markdown("#### Cutover plan")
                st.code(md, language="markdown")
                st.download_button("Download cutover plan", md, file_name=f"cutover-{product}-{version}-{sel_env.name}.md", mime="text/markdown")

            if st.button("Generate Rollback Plan"):
                steps = [l.strip() for l in rollback_txt.splitlines() if l.strip()]
                md = generate_rollback_plan(sel_env, product, version, branch, steps)
                st.markdown("#### Rollback plan")
                st.code(md, language="markdown")
                st.download_button("Download rollback plan", md, file_name=f"rollback-{product}-{version}-{sel_env.name}.md", mime="text/markdown")

        with col2:
            if st.button("Generate Rollout Plan"):
                stages = [l.strip() for l in rollout_txt.splitlines() if l.strip()]
                md = generate_rollout_plan(sel_env, product, version, branch, stages)
                st.markdown("#### Rollout plan")
                st.code(md, language="markdown")
                st.download_button("Download rollout plan", md, file_name=f"rollout-{product}-{version}-{sel_env.name}.md", mime="text/markdown")

            if st.button("Generate Release Notes"):
                md = generate_release_message(sel_env, product, version, branch, "PLANNED")
                # append build/integration summary
                md_full = md + "\n\n" + "## Build & integrations\n\n" + build_details + "\n\n" + integrations + "\n\n" + dependencies
                st.markdown("#### Release notes")
                st.code(md_full, language="markdown")
                st.download_button("Download release notes", md_full, file_name=f"release-notes-{product}-{version}-{sel_env.name}.md", mime="text/markdown")

        st.markdown("---")
        st.subheader("Integration vault & trackers")
        if st.button("Generate Integration Vault"):
            md = generate_integration_vault(sel_env, integrations, dependencies)
            st.code(md, language="markdown")
            st.download_button("Download integration vault", md, file_name=f"integration-vault-{sel_env.name}.md", mime="text/markdown")

        tracker_items = checklist_txt.splitlines() + rollback_txt.splitlines() + rollout_txt.splitlines()
        tracker_items = [t.strip() for t in tracker_items if t.strip()]
        if st.button("Generate Trackers CSV"):
            csv = generate_trackers_csv(tracker_items)
            st.download_button("Download trackers CSV", csv, file_name=f"trackers-{product}-{version}.csv", mime="text/csv")

if __name__ == "__main__":
    main()