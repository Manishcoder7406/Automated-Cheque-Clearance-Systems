from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd
import streamlit as st

from agent.baseline_agent import BaselineChequeAgent
from server.environment import BankChequeClearingEnv
from reward import derive_expected_action
from vision.cheque_processor import ChequeProcessor

PACKAGE_ROOT = Path(__file__).resolve().parent
UPLOAD_DIR = PACKAGE_ROOT / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

env = BankChequeClearingEnv(difficulty="medium", seed=42)
agent = BaselineChequeAgent()
processor = ChequeProcessor(seed=42)


def configure_page() -> None:
    st.set_page_config(
        page_title="Cheque AI Command Center",
        page_icon="🏦",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(0, 142, 110, 0.15), transparent 28%),
                radial-gradient(circle at top right, rgba(165, 28, 48, 0.14), transparent 26%),
                linear-gradient(180deg, #f4f7f4 0%, #eef3ef 100%);
        }
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        .glass-card {
            background: rgba(255, 255, 255, 0.82);
            border: 1px solid rgba(18, 47, 38, 0.08);
            border-radius: 24px;
            padding: 1.2rem 1.3rem;
            box-shadow: 0 18px 40px rgba(20, 34, 28, 0.08);
        }
        .hero-card {
            background: linear-gradient(135deg, #103d33 0%, #175948 42%, #1d7b60 100%);
            color: white;
            border-radius: 28px;
            padding: 1.5rem 1.6rem;
            box-shadow: 0 22px 55px rgba(16, 61, 51, 0.22);
        }
        .eyebrow {
            display: inline-block;
            padding: 0.3rem 0.7rem;
            border-radius: 999px;
            font-size: 0.78rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            background: rgba(255, 255, 255, 0.18);
        }
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.8rem;
            margin-top: 1rem;
        }
        .summary-box {
            background: rgba(255, 255, 255, 0.12);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 20px;
            padding: 0.9rem 1rem;
        }
        .summary-label {
            opacity: 0.76;
            font-size: 0.82rem;
            margin-bottom: 0.35rem;
        }
        .summary-value {
            font-size: 1.4rem;
            font-weight: 700;
        }
        .badge {
            display: inline-flex;
            align-items: center;
            gap: 0.42rem;
            padding: 0.42rem 0.78rem;
            border-radius: 999px;
            font-size: 0.84rem;
            font-weight: 700;
            border: 1px solid transparent;
        }
        .badge.green {
            color: #0f6b43;
            background: rgba(15, 107, 67, 0.12);
            border-color: rgba(15, 107, 67, 0.18);
        }
        .badge.red {
            color: #a02639;
            background: rgba(160, 38, 57, 0.12);
            border-color: rgba(160, 38, 57, 0.18);
        }
        .badge.yellow {
            color: #8f6300;
            background: rgba(143, 99, 0, 0.14);
            border-color: rgba(143, 99, 0, 0.18);
        }
        .reason-step {
            padding: 0.7rem 0.85rem;
            border-radius: 16px;
            margin-bottom: 0.55rem;
            border: 1px solid rgba(18, 47, 38, 0.08);
            background: rgba(255, 255, 255, 0.78);
        }
        .why-box {
            padding: 1rem 1.05rem;
            border-radius: 18px;
            background: linear-gradient(180deg, rgba(255,255,255,0.94), rgba(244,248,245,0.96));
            border: 1px solid rgba(18, 47, 38, 0.08);
        }
        .mini-title {
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #5d6a63;
            margin-bottom: 0.45rem;
        }
        .image-frame {
            background: white;
            border-radius: 20px;
            padding: 0.8rem;
            border: 1px solid rgba(18, 47, 38, 0.08);
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.8);
        }
        .footnote {
            color: #617069;
            font-size: 0.9rem;
        }
        @media (max-width: 900px) {
            .summary-grid {
                grid-template-columns: 1fr 1fr;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def initialize_state() -> None:
    defaults = {
        "difficulty": "medium",
        "image_path": r"e:\cheque\cheque1.jpg",
        "signature_path": r"e:\cheque\cheque1_signature.jpg",
        "analysis_result": None,
        "history": [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_demo_cases() -> list[Dict[str, str]]:
    known = {Path(item["image_path"]).name: item for item in processor.list_known_samples()}
    return [
        {
            "label": "Valid Cheque",
            "caption": "Clean signature and manageable amount",
            "image_path": known["cheque1.jpg"]["image_path"],
            "signature_path": known["cheque1.jpg"]["signature_path"],
            "difficulty": "easy",
        },
        {
            "label": "Fraud Case",
            "caption": "Huge amount with extreme fraud pressure",
            "image_path": known["cheque3.jpg"]["image_path"],
            "signature_path": known["cheque3.jpg"]["signature_path"],
            "difficulty": "hard",
        },
        {
            "label": "Signature Mismatch",
            "caption": "Suspicious signature mismatch example",
            "image_path": known["cheque2.jpg"]["image_path"],
            "signature_path": known["cheque2.jpg"]["signature_path"],
            "difficulty": "medium",
        },
    ]


def render_header(result: Optional[Dict[str, Any]]) -> None:
    verified = "VERIFIED" if result and result["observation"]["signature_valid"] else "UNDER REVIEW"
    action = result["agent_action"] if result else "WAITING"
    reward = result["reward"] if result else 0.0
    confidence = calculate_confidence(result) if result else 0.0

    st.markdown(
        f"""
        <div class="hero-card">
            <div class="eyebrow">AI-Powered Bank Cheque Intelligence</div>
            <h1 style="margin:0.8rem 0 0.3rem 0; font-size:2.5rem;">Cheque AI Command Center</h1>
            <p style="margin:0; max-width:65ch; opacity:0.85;">
                Run a full cheque inspection workflow with signature verification, risk scoring,
                account checks, and the final agent decision in one demo-ready interface.
            </p>
            <div class="summary-grid">
                <div class="summary-box">
                    <div class="summary-label">Summary</div>
                    <div class="summary-value">{"✅ " + verified if result else "⌛ Waiting"}</div>
                </div>
                <div class="summary-box">
                    <div class="summary-label">Decision</div>
                    <div class="summary-value">{"💳 " + action if result else "💳 -"}</div>
                </div>
                <div class="summary-box">
                    <div class="summary-label">Confidence</div>
                    <div class="summary-value">{"🎯 " + f"{confidence:.0%}" if result else "🎯 0%"}</div>
                </div>
                <div class="summary-box">
                    <div class="summary-label">Reward</div>
                    <div class="summary-value">{"🏆 " + f"{reward:.2f}" if result else "🏆 0.00"}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown("### Demo Controls")
        st.caption("Quick presets for hackathon demos.")

        for demo in get_demo_cases():
            if st.button(demo["label"], use_container_width=True, help=demo["caption"]):
                st.session_state.difficulty = demo["difficulty"]
                st.session_state.image_path = demo["image_path"]
                st.session_state.signature_path = demo["signature_path"]

        st.divider()
        st.markdown("### Input")
        st.session_state.difficulty = st.selectbox(
            "Difficulty",
            ["easy", "medium", "hard"],
            index=["easy", "medium", "hard"].index(st.session_state.difficulty),
        )
        st.session_state.image_path = st.text_input("Cheque image path", st.session_state.image_path)
        st.session_state.signature_path = st.text_input("Signature image path", st.session_state.signature_path)

        st.markdown("### Upload Instead")
        uploaded_cheque = st.file_uploader("Cheque image", type=["png", "jpg", "jpeg"], key="uploaded_cheque")
        uploaded_signature = st.file_uploader(
            "Signature image", type=["png", "jpg", "jpeg"], key="uploaded_signature"
        )
        if uploaded_cheque is not None:
            st.caption("Uploaded files override the path inputs when you analyze.")
        st.session_state["uploaded_bundle"] = (uploaded_cheque, uploaded_signature)


def save_upload(uploaded_file) -> Optional[str]:
    if uploaded_file is None:
        return None
    destination = UPLOAD_DIR / uploaded_file.name
    destination.write_bytes(uploaded_file.getbuffer())
    return str(destination)


def run_analysis() -> None:
    uploaded_cheque, uploaded_signature = st.session_state["uploaded_bundle"]
    image_path = save_upload(uploaded_cheque) if uploaded_cheque is not None else st.session_state.image_path
    signature_path = (
        save_upload(uploaded_signature) if uploaded_signature is not None else st.session_state.signature_path
    )

    with st.status("Analyzing cheque...", expanded=True) as status:
        # UI improvement: loading and AI process animation
        st.write("Extracting data...")
        time.sleep(0.2)
        observation = env.reset(
            difficulty=st.session_state.difficulty,
            image_path=image_path,
            signature_path=signature_path or None,
        )

        st.write("Verifying signature...")
        time.sleep(0.2)
        action = agent.act(observation)

        st.write("Checking fraud...")
        time.sleep(0.2)
        final_observation, reward, done, info = env.step(action)
        status.update(label="Analysis complete", state="complete", expanded=False)

    result = {
        "tested": True,
        "observation": final_observation,
        "agent_action": action.value,
        "reward": reward,
        "done": done,
        "info": info,
        "state": env.state(),
        "image_path": image_path,
        "signature_path": signature_path,
    }
    st.session_state.analysis_result = result
    st.session_state.history.append(
        {
            "Cheque": Path(image_path).name if image_path else "simulated",
            "Reward": reward,
            "Confidence": round(calculate_confidence(result) * 100, 1),
        }
    )


def action_badge(label: str, tone: str) -> str:
    icon = {"green": "✔", "red": "✖", "yellow": "⚠"}.get(tone, "•")
    return f'<span class="badge {tone}">{icon} {label}</span>'


def risk_level(score: float) -> tuple[str, str]:
    if score < 0.35:
        return "Low", "green"
    if score < 0.7:
        return "Medium", "yellow"
    return "High", "red"


def calculate_confidence(result: Optional[Dict[str, Any]]) -> float:
    if not result:
        return 0.0
    observation = result["observation"]
    info = result["info"]
    signature_component = info.get("signature_score", 0.0)
    balance_component = min(1.0, observation["account_balance"] / max(observation["cheque_amount"], 1.0))
    fraud_component = 1.0 - observation["fraud_score"]
    if result["agent_action"] == "REJECT":
        fraud_component = max(fraud_component, observation["fraud_score"])
    confidence = (0.4 * signature_component) + (0.25 * balance_component) + (0.35 * fraud_component)
    return max(0.0, min(1.0, confidence))


def render_badges(result: Dict[str, Any]) -> None:
    observation = result["observation"]
    action = result["agent_action"]
    action_tone = "green" if action == "APPROVE" else "red" if action == "REJECT" else "yellow"
    account_tone = "green" if observation["account_valid"] else "red"
    signature_tone = "green" if observation["signature_valid"] else "red"
    risk_name, risk_tone = risk_level(observation["fraud_score"])

    st.markdown(
        f"""
        <div class="glass-card">
            <div class="mini-title">Decision Status</div>
            {action_badge(f"Agent Decision: {action}", action_tone)}
            &nbsp;&nbsp;
            {action_badge(f"Account {'Valid' if observation['account_valid'] else 'Invalid'}", account_tone)}
            &nbsp;&nbsp;
            {action_badge(f"Signature {'Valid' if observation['signature_valid'] else 'Invalid'}", signature_tone)}
            &nbsp;&nbsp;
            {action_badge(f"Fraud Risk: {risk_name}", risk_tone)}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metric_cards(result: Dict[str, Any]) -> None:
    info = result["info"]
    observation = result["observation"]
    sig_score = float(info.get("signature_score", 0.0))
    fraud_score = float(observation.get("fraud_score", 0.0))
    confidence = calculate_confidence(result)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<div class="glass-card"><div class="mini-title">Signature Score</div></div>', unsafe_allow_html=True)
        st.progress(sig_score, text=f"{sig_score:.0%} match confidence")
    with col2:
        st.markdown('<div class="glass-card"><div class="mini-title">Fraud Score</div></div>', unsafe_allow_html=True)
        st.progress(fraud_score, text=f"{fraud_score:.0%} fraud likelihood")
    with col3:
        st.markdown('<div class="glass-card"><div class="mini-title">Model Confidence</div></div>', unsafe_allow_html=True)
        st.progress(confidence, text=f"{confidence:.0%} confidence")


def render_decision_process(result: Dict[str, Any]) -> None:
    info = result["info"]
    observation = result["observation"]
    balance_ok = observation["account_balance"] >= observation["cheque_amount"]
    risk_name, _ = risk_level(observation["fraud_score"])

    # UI improvement: AI decision explainability
    steps = [
        ("green" if observation["signature_valid"] else "red",
         f"Signature {'Verified' if observation['signature_valid'] else 'Mismatch'} (Score: {info.get('signature_score', 0.0):.2f})"),
        ("green" if observation["account_valid"] else "red",
         f"Account {'Valid' if observation['account_valid'] else 'Invalid'}"),
        ("green" if balance_ok else "red",
         f"Balance Check {'Passed' if balance_ok else 'Failed'} (Balance: {observation['account_balance']:.2f} vs Cheque: {observation['cheque_amount']:.2f})"),
        ("green" if risk_name == "Low" else "yellow" if risk_name == "Medium" else "red",
         f"Fraud Risk: {risk_name} ({observation['fraud_score']:.2f})"),
    ]

    st.markdown("### AI Decision Process")
    for tone, text in steps:
        st.markdown(
            f'<div class="reason-step">{action_badge(text, tone)}</div>',
            unsafe_allow_html=True,
        )


def build_why_decision(result: Dict[str, Any]) -> list[str]:
    observation = result["observation"]
    info = result["info"]
    reasons: list[str] = []

    if observation["signature_valid"]:
        reasons.append(f"Signature matched successfully with score {info.get('signature_score', 0.0):.2f}.")
    else:
        reasons.append(f"Signature verification failed with score {info.get('signature_score', 0.0):.2f}.")

    if observation["account_valid"]:
        reasons.append("Account was found in the bank dataset and marked valid.")
    else:
        reasons.append("Account was missing or invalid in the bank dataset.")

    if observation["account_balance"] >= observation["cheque_amount"]:
        reasons.append("Available balance was sufficient for cheque processing.")
    else:
        reasons.append("Available balance was lower than the cheque amount.")

    risk_name, _ = risk_level(observation["fraud_score"])
    reasons.append(f"Fraud risk evaluated as {risk_name.lower()} at {observation['fraud_score']:.2f}.")
    return reasons


def render_why_decision(result: Dict[str, Any]) -> None:
    # UI improvement: explicit why-this-decision section
    st.markdown("### Why This Decision?")
    reasons = build_why_decision(result)
    heading = {
        "APPROVE": "Why Approved",
        "REJECT": "Why Rejected",
        "FLAG": "Why Flagged",
    }[result["agent_action"]]
    bullets = "".join(f"<li>{reason}</li>" for reason in reasons)
    st.markdown(
        f"""
        <div class="why-box">
            <strong>{heading}</strong>
            <ul style="margin-top:0.75rem;">
                {bullets}
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_image_preview(result: Dict[str, Any]) -> None:
    # UI improvement: cheque and signature preview side-by-side
    st.markdown("### Image Preview")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="mini-title">Cheque Image</div>', unsafe_allow_html=True)
        st.markdown('<div class="image-frame">', unsafe_allow_html=True)
        st.image(result["image_path"], use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="mini-title">Signature Image</div>', unsafe_allow_html=True)
        st.markdown('<div class="image-frame">', unsafe_allow_html=True)
        if result.get("signature_path"):
            st.image(result["signature_path"], use_container_width=True)
        else:
            st.info("No signature image provided.")
        st.markdown("</div>", unsafe_allow_html=True)


def render_details(result: Dict[str, Any]) -> None:
    info = result["info"]
    expected = derive_expected_action(env.current_state.observation).value if env.current_state else "-"

    col1, col2 = st.columns([1.15, 0.85])
    with col1:
        render_image_preview(result)
    with col2:
        st.markdown("### Cheque Snapshot")
        st.markdown(
            f"""
            <div class="glass-card">
                <div class="mini-title">Core Fields</div>
                <p><strong>Payee:</strong> {info.get('payee_name', '-')}</p>
                <p><strong>Account Number:</strong> {info.get('account_number', '-')}</p>
                <p><strong>Account Holder:</strong> {info.get('account_name', '-')}</p>
                <p><strong>Cheque Amount:</strong> INR {info.get('cheque_amount', 0.0):,.2f}</p>
                <p><strong>Available Balance:</strong> INR {info.get('account_balance', 0.0):,.2f}</p>
                <p><strong>Expected Action:</strong> {expected}</p>
                <p><strong>Reward:</strong> {result['reward']:.2f}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_history_chart() -> None:
    # Optional improvement: reward/confidence chart
    if not st.session_state.history:
        return
    st.markdown("### Demo Performance")
    history_df = pd.DataFrame(st.session_state.history)
    st.line_chart(history_df.set_index("Cheque")[["Reward", "Confidence"]], height=220)


def render_empty_state() -> None:
    st.markdown(
        """
        <div class="glass-card">
            <h3 style="margin-top:0;">Run a cheque analysis</h3>
            <p class="footnote">
                Use the demo buttons on the left or provide a cheque path and signature path.
                The dashboard will show the AI decision process, visual badges, image previews,
                and an explanation of why the agent approved, rejected, or flagged the cheque.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    configure_page()
    inject_styles()
    initialize_state()

    result = st.session_state.analysis_result
    render_header(result)
    render_sidebar()

    top_left, top_right = st.columns([0.68, 0.32])
    with top_left:
        st.markdown("### Control Panel")
        st.caption("Run the existing cheque AI backend without changing its logic.")
    with top_right:
        if st.button("Analyze Cheque", use_container_width=True, type="primary"):
            run_analysis()
            result = st.session_state.analysis_result

    if result is None:
        render_empty_state()
        return

    render_badges(result)
    render_metric_cards(result)

    left, right = st.columns([0.58, 0.42])
    with left:
        render_decision_process(result)
        render_why_decision(result)
    with right:
        render_details(result)

    render_history_chart()


if __name__ == "__main__":
    main()
