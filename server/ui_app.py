from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import streamlit as st

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from bank_env.server.environment import BankChequeClearingEnv
from bank_env.tasks.easy import get_cases as get_easy_cases
from bank_env.tasks.hard import get_cases as get_hard_cases
from bank_env.tasks.medium import get_cases as get_medium_cases

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
UPLOAD_DIR = PACKAGE_ROOT / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def save_upload(uploaded_file) -> Optional[str]:
    if uploaded_file is None:
        return None
    output = UPLOAD_DIR / uploaded_file.name
    output.write_bytes(uploaded_file.getbuffer())
    return str(output)


def demo_cases() -> dict[str, dict]:
    return {
        "Valid Cheque": get_easy_cases()[0],
        "Fraud Case": get_hard_cases()[0],
        "Signature Mismatch": get_medium_cases()[0],
    }


def tone(status: str) -> str:
    return {"PASS": "green", "WARN": "orange", "FAIL": "red"}.get(status, "gray")


def render_badge(label: str, status: str) -> None:
    colors = {
        "green": "#d1fae5",
        "orange": "#fef3c7",
        "red": "#fee2e2",
        "gray": "#e5e7eb",
    }
    st.markdown(
        f"<div style='padding:0.55rem 0.8rem;border-radius:12px;background:{colors[tone(status)]};"
        f"margin-bottom:0.5rem;'><strong>{label}</strong>: {status}</div>",
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(page_title="Multi-Agent Cheque Clearing", page_icon=":bank:", layout="wide")
    st.title("Multi-Agent Bank Cheque Clearing OpenEnv")
    st.caption("Upload a cheque and the agents verify it against backend account records, signatures, balance checks, settlement rules, and final approval logic.")

    if "result" not in st.session_state:
        st.session_state.result = None

    env = BankChequeClearingEnv(seed=42)
    demos = demo_cases()

    with st.sidebar:
        st.header("Run Analysis")
        selected_demo = st.radio("Demo buttons", list(demos.keys()))
        case = demos[selected_demo]
        cheque_path = st.text_input("Cheque image path", case["cheque_image_path"])
        uploaded_cheque = st.file_uploader("Upload cheque image", type=["png", "jpg", "jpeg"])
        run_clicked = st.button("Run Agents", use_container_width=True)
        st.caption("Only upload the cheque. The system automatically matches it with backend cheque records and stored account signatures.")

    if run_clicked:
        env.reset()
        action = {
            "cheque_image_path": save_upload(uploaded_cheque) or cheque_path,
        }
        state, reward, _, info = env.step(action)
        st.session_state.result = {
            "state": state,
            "reward": reward,
            "info": info,
            "action": action,
        }

    result = st.session_state.result
    if result is None:
        st.info("Choose a demo or upload a cheque image, then click Run Agents.")
        return

    state = result["state"]
    info = result["info"]
    action = result["action"]

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Summary", state["final_decision"])
    m2.metric("Confidence", f"{state['confidence']:.0%}")
    m3.metric("Reward", f"{state['reward']:.2f}")
    m4.metric("Matched Account", info.get("matched_account_number", "Not found") or "Not found")

    st.subheader("Backend Match")
    st.write(
        f"Cheque uploaded: `{Path(action['cheque_image_path']).name}` | "
        f"Matched backend case: `{state['cheque_id']}` | "
        f"Inferred difficulty: `{state['difficulty']}`"
    )

    st.subheader("AI Agent Pipeline View")
    st.markdown("Agent 1 -> Agent 2 -> Agent 3 -> Agent 4 -> Agent 5 -> Agent 6")

    st.subheader("Per-Agent Result Cards")
    labels = {
        "agent1_result": "Agent 1 — Cheque Data Validator",
        "agent2_result": "Agent 2 — Signature Verifier",
        "agent3_result": "Agent 3 — Account Holder Verifier",
        "agent4_result": "Agent 4 — Balance & Behaviour Checker",
        "agent5_result": "Agent 5 — Inter-bank Transfer Bridge",
    }
    for key, label in labels.items():
        data = state[key]
        with st.expander(label, expanded=(key == "agent1_result")):
            render_badge("Status", data["status"])
            render_badge("Confidence", f"{data['confidence']:.2f}")
            if "issues" in data and data["issues"]:
                st.warning(data["issues"])
            st.json(data["details"])

    st.subheader("Reason Summary")
    st.write(info["orchestrator_result"]["details"]["reason_summary"])
    if info["issues"]:
        st.subheader("Issues List")
        st.write(info["issues"])

    left, right = st.columns(2)
    with left:
        st.image(action["cheque_image_path"], caption="Cheque Image", use_container_width=True)
    with right:
        st.write("Backend Signatures Used")
        preview_paths = info["extracted_signature_paths"][:4]
        if preview_paths:
            st.image(preview_paths, width=140, caption=[Path(path).name for path in preview_paths])
        else:
            st.info("No backend signatures were available for this cheque.")


if __name__ == "__main__":
    main()
