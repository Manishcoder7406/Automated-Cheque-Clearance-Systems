from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd
import streamlit as st

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parent.parent))

from bank_env.server.environment import BankChequeClearingEnv
from bank_env.vision.cheque_processor import ChequeProcessor

PACKAGE_ROOT = Path(__file__).resolve().parent
UPLOAD_DIR = PACKAGE_ROOT / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
DATASET_PATH = Path(r"e:\cheque\cheque_data.xlsx")

env = BankChequeClearingEnv(seed=42)
processor = ChequeProcessor(seed=42)


def configure_page() -> None:
    st.set_page_config(
        page_title="Cheque AI Command Center",
        page_icon="🏦",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def inject_styles() -> None:
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background: linear-gradient(135deg, #0a0f1e 0%, #0d1b2a 50%, #0a1628 100%);
        min-height: 100vh;
    }

    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
        max-width: 1400px;
    }

    .hero-card {
        background: linear-gradient(135deg, #0d3b2e 0%, #0f4d3b 40%, #1a6b52 100%);
        border: 1px solid rgba(52, 211, 153, 0.2);
        border-radius: 24px;
        padding: 2rem 2.2rem;
        box-shadow: 0 25px 60px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(52,211,153,0.08);
        margin-bottom: 1.5rem;
        position: relative;
        overflow: hidden;
    }
    .hero-card::before {
        content: "";
        position: absolute;
        top: -60px; right: -60px;
        width: 220px; height: 220px;
        background: radial-gradient(circle, rgba(52,211,153,0.12) 0%, transparent 70%);
        border-radius: 50%;
    }

    .glass-card {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 20px;
        padding: 1.4rem 1.5rem;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        margin-bottom: 1rem;
    }

    .stats-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1rem;
        margin-top: 1.2rem;
    }
    .stat-item {
        background: rgba(255,255,255,0.07);
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 16px;
        padding: 1rem 1.2rem;
        text-align: center;
    }
    .stat-label {
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: rgba(255,255,255,0.55);
        margin-bottom: 0.4rem;
    }
    .stat-value {
        font-size: 1.5rem;
        font-weight: 800;
        color: #fff;
    }

    .badge {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        padding: 0.35rem 0.75rem;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 600;
        border: 1px solid transparent;
        white-space: nowrap;
    }
    .badge-green {
        color: #34d399;
        background: rgba(52, 211, 153, 0.12);
        border-color: rgba(52, 211, 153, 0.25);
    }
    .badge-red {
        color: #f87171;
        background: rgba(248, 113, 113, 0.12);
        border-color: rgba(248, 113, 113, 0.25);
    }
    .badge-yellow {
        color: #fbbf24;
        background: rgba(251, 191, 36, 0.12);
        border-color: rgba(251, 191, 36, 0.25);
    }
    .badge-blue {
        color: #60a5fa;
        background: rgba(96, 165, 250, 0.12);
        border-color: rgba(96, 165, 250, 0.25);
    }
    .decision-approved {
        font-size: 1.1rem;
        font-weight: 800;
        color: #34d399;
    }
    .decision-rejected {
        font-size: 1.1rem;
        font-weight: 800;
        color: #f87171;
    }

    .pipeline-row {
        display: flex;
        align-items: stretch;
        gap: 0;
        margin: 1rem 0;
    }
    .pipeline-node {
        flex: 1;
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px;
        padding: 1rem 0.8rem;
        text-align: center;
        position: relative;
        transition: all 0.3s ease;
    }
    .pipeline-node.pass { border-color: rgba(52,211,153,0.35); background: rgba(52,211,153,0.05); }
    .pipeline-node.warn { border-color: rgba(251,191,36,0.35); background: rgba(251,191,36,0.05); }
    .pipeline-node.fail { border-color: rgba(248,113,113,0.35); background: rgba(248,113,113,0.05); }
    .pipeline-arrow {
        display: flex;
        align-items: center;
        padding: 0 0.2rem;
        color: rgba(255,255,255,0.25);
        font-size: 1.2rem;
    }
    .pipeline-title { font-size: 0.7rem; font-weight: 600; color: rgba(255,255,255,0.5); text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.5rem; }
    .pipeline-status { font-size: 0.75rem; font-weight: 700; }
    .pipeline-status.pass { color: #34d399; }
    .pipeline-status.warn { color: #fbbf24; }
    .pipeline-status.fail { color: #f87171; }

    .sig-panel {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 20px;
        padding: 1.2rem;
        text-align: center;
    }
    .sig-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        font-weight: 600;
        margin-bottom: 0.7rem;
    }
    .sig-label.extracted { color: #60a5fa; }
    .sig-label.reference { color: #34d399; }

    .rejection-box {
        background: rgba(248, 113, 113, 0.07);
        border: 1px solid rgba(248,113,113,0.3);
        border-left: 4px solid #f87171;
        border-radius: 16px;
        padding: 1.2rem 1.4rem;
        margin: 1rem 0;
    }
    .rejection-title {
        color: #f87171;
        font-weight: 700;
        font-size: 1rem;
        margin-bottom: 0.6rem;
    }
    .rejection-item {
        color: rgba(255,255,255,0.7);
        font-size: 0.88rem;
        padding: 0.3rem 0;
        display: flex;
        align-items: flex-start;
        gap: 0.5rem;
    }

    .section-title {
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        font-weight: 700;
        color: rgba(255,255,255,0.4);
        margin-bottom: 0.8rem;
        margin-top: 0.2rem;
    }

    .cheque-frame {
        border-radius: 16px;
        overflow: hidden;
        border: 1px solid rgba(255,255,255,0.12);
        box-shadow: 0 12px 40px rgba(0,0,0,0.5);
    }

    .score-bar-bg {
        background: rgba(255,255,255,0.08);
        border-radius: 999px;
        height: 8px;
        margin-top: 0.4rem;
        overflow: hidden;
    }
    .score-bar-fill-green { background: linear-gradient(90deg, #059669, #34d399); height: 100%; border-radius: 999px; }
    .score-bar-fill-yellow { background: linear-gradient(90deg, #d97706, #fbbf24); height: 100%; border-radius: 999px; }
    .score-bar-fill-red { background: linear-gradient(90deg, #dc2626, #f87171); height: 100%; border-radius: 999px; }

    [data-testid="stSidebar"] {
        background: rgba(10, 15, 30, 0.95) !important;
        border-right: 1px solid rgba(255,255,255,0.08) !important;
    }
    [data-testid="stSidebar"] * { color: rgba(255,255,255,0.85) !important; }
    [data-testid="stSidebar"] h3 { color: rgba(255,255,255,0.95) !important; font-size: 0.85rem !important; text-transform: uppercase; letter-spacing: 0.08em; }

    .stButton > button {
        background: linear-gradient(135deg, #059669, #0d9488);
        color: white !important;
        border: none;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.9rem;
        padding: 0.55rem 1rem;
        transition: all 0.2s ease;
        box-shadow: 0 4px 15px rgba(5,150,105,0.3);
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 8px 25px rgba(5,150,105,0.4);
    }

    div[data-testid="stFileUploader"] {
        background: rgba(255,255,255,0.04);
        border: 1px dashed rgba(255,255,255,0.2);
        border-radius: 14px;
        padding: 0.5rem;
    }

    .empty-state {
        background: rgba(255,255,255,0.03);
        border: 1px dashed rgba(255,255,255,0.12);
        border-radius: 20px;
        padding: 3rem 2rem;
        text-align: center;
        color: rgba(255,255,255,0.4);
    }
    .empty-icon { font-size: 3rem; margin-bottom: 1rem; }
    .empty-title { font-size: 1.2rem; font-weight: 600; color: rgba(255,255,255,0.6); margin-bottom: 0.5rem; }
    .empty-desc { font-size: 0.88rem; max-width: 40ch; margin: 0 auto; }
    </style>
    """, unsafe_allow_html=True)


def initialize_state() -> None:
    defaults = {
        "difficulty": "medium",
        "image_path": "",
        "analysis_result": None,
        "history": [],
        "uploaded_bundle": None,
        "dataset_df": None,
        "dataset_name": str(DATASET_PATH),
        "dataset_error": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    if st.session_state.dataset_df is None and not st.session_state.dataset_error:
        load_default_dataset()


def get_demo_cases() -> list[Dict[str, str]]:
    known = {Path(item["image_path"]).name: item for item in processor.list_known_samples()}
    return [
        {"label": "✅  Valid Cheque", "caption": "Clean signature, approved scenario", "image_path": known["cheque1.jpg"]["image_path"], "difficulty": "easy"},
        {"label": "🚨  Fraud Case", "caption": "High-risk, large amount fraud case", "image_path": known["cheque3.jpg"]["image_path"], "difficulty": "hard"},
        {"label": "⚠️  Sig Mismatch", "caption": "Suspicious signature mismatch", "image_path": known["cheque2.jpg"]["image_path"], "difficulty": "medium"},
    ]


def normalize_dataset_df(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()
    normalized.columns = [
        str(column).strip().lower().replace("\n", " ").replace("-", " ")
        for column in normalized.columns
    ]
    normalized = normalized.rename(
        columns={
            "bank name": "bank_name",
            "payee name": "payee_name",
            "amount (words)": "amount_words",
            "amount words": "amount_words",
            "amount (numbers)": "amount_numbers",
            "amount numbers": "amount_numbers",
            "amount number": "amount_numbers",
            "account number": "account_number",
            "cheque number": "cheque_number",
            "ifsc": "ifsc_code",
        }
    )
    required = [
        "bank_name",
        "date",
        "payee_name",
        "amount_words",
        "amount_numbers",
        "account_number",
        "ifsc_code",
        "cheque_number",
    ]
    missing = [column for column in required if column not in normalized.columns]
    if missing:
        raise ValueError(f"Dataset is missing required columns: {', '.join(missing)}")
    return normalized


def load_default_dataset() -> None:
    if not DATASET_PATH.exists():
        st.session_state.dataset_df = None
        st.session_state.dataset_error = f"Dataset not found at {DATASET_PATH}"
        return

    try:
        dataset_df = normalize_dataset_df(pd.read_excel(DATASET_PATH))
    except Exception as exc:
        st.session_state.dataset_df = None
        st.session_state.dataset_error = f"Dataset load failed: {exc}"
        return

    st.session_state.dataset_df = dataset_df
    st.session_state.dataset_name = DATASET_PATH.name
    st.session_state.dataset_error = ""


def save_upload(uploaded_file) -> Optional[str]:
    if uploaded_file is None:
        return None
    destination = UPLOAD_DIR / uploaded_file.name
    destination.write_bytes(uploaded_file.getbuffer())
    return str(destination)


def tone_for_status(status: str) -> str:
    return {"PASS": "green", "WARN": "yellow"}.get(status, "red")


def badge(label: str, tone: str) -> str:
    icon = {"green": "🟢", "red": "🔴", "yellow": "🟡", "blue": "🔵"}.get(tone, "•")
    return f'<span class="badge badge-{tone}">{icon} {label}</span>'


def score_bar(score: float, tone: str) -> str:
    pct = int(min(max(score, 0.0), 1.0) * 100)
    return f"""
    <div class="score-bar-bg">
        <div class="score-bar-fill-{tone}" style="width:{pct}%"></div>
    </div>"""


def render_header(result: Optional[Dict[str, Any]]) -> None:
    dataset_loaded = st.session_state.get("dataset_df") is not None
    dataset_note = (
        f"Validation dataset ready: {st.session_state.get('dataset_name', DATASET_PATH.name)}"
        if dataset_loaded
        else st.session_state.get("dataset_error", "Validation dataset not loaded")
    )
    if result:
        outputs = result["info"]["agent_outputs"]
        decision = outputs["agent6"].get("final_decision", "-")
        confidence = float(outputs["agent6"].get("confidence", 0.0))
        reward = result["reward"]
        dec_class = "decision-approved" if decision == "APPROVED" else "decision-rejected"
        dec_icon = "✅" if decision == "APPROVED" else "❌"
    else:
        decision, confidence, reward, dec_class, dec_icon = "-", 0.0, 0.0, "", "⌛"

    st.markdown(f"""
    <div class="hero-card">
        <div style="font-size:0.72rem;text-transform:uppercase;letter-spacing:0.12em;color:rgba(255,255,255,0.5);margin-bottom:0.5rem;">🏦 AI-Powered Bank Cheque Intelligence</div>
        <h1 style="margin:0 0 0.3rem;font-size:2rem;font-weight:800;color:#fff;letter-spacing:-0.02em;">Cheque AI Command Center</h1>
        <p style="margin:0;color:rgba(255,255,255,0.6);font-size:0.9rem;max-width:60ch;">
            Upload a cheque image and the pipeline will extract fields, verify the signature, validate the cheque against the bank dataset, and issue a final decision.
        </p>
        <div style="margin-top:0.8rem;color:rgba(255,255,255,0.75);font-size:0.85rem;">
            {dataset_note}
        </div>
        <div class="stats-grid">
            <div class="stat-item">
                <div class="stat-label">Final Decision</div>
                <div class="{dec_class}">{dec_icon} {decision}</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">AI Confidence</div>
                <div class="stat-value">{"🎯 " + f"{confidence:.0%}" if result else "—"}</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">Reward Score</div>
                <div class="stat-value">{"🏆 " + f"{reward:.2f}" if result else "—"}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown("### 🎯 Quick Demos")
        for demo in get_demo_cases():
            if st.button(demo["label"], use_container_width=True, help=demo["caption"]):
                st.session_state.difficulty = demo["difficulty"]
                st.session_state.image_path = demo["image_path"]
                st.session_state.uploaded_bundle = None

        st.markdown("---")
        st.markdown("### 📤 Upload Cheque")
        uploaded = st.file_uploader("Cheque image only", type=["png", "jpg", "jpeg"], key="uploaded_cheque")
        st.session_state.uploaded_bundle = uploaded
        if uploaded:
            st.caption(f"📎 {uploaded.name}")

        st.markdown("---")
        st.markdown("### ⚙️ Settings")
        st.session_state.difficulty = st.selectbox(
            "Difficulty Level",
            ["easy", "medium", "hard"],
            index=["easy", "medium", "hard"].index(st.session_state.difficulty),
        )
        if st.session_state.get("dataset_df") is not None:
            st.success(f"Dataset ready: {st.session_state.get('dataset_name', DATASET_PATH.name)}")
        elif st.session_state.get("dataset_error"):
            st.error(st.session_state.dataset_error)


def run_analysis() -> None:
    uploaded = st.session_state.uploaded_bundle
    image_path = save_upload(uploaded) if uploaded is not None else st.session_state.image_path
    dataset_df = st.session_state.get("dataset_df")
    if dataset_df is None or dataset_df.empty:
        st.warning(st.session_state.get("dataset_error") or "Validation dataset is not available.")
        return
    if not image_path:
        st.warning("Upload a cheque image before running analysis.")
        return
    sig_source = "Internal Dataset"

    with st.status("🔄 Running Multi-Agent Pipeline...", expanded=True) as status:
        st.write("⚙️ Initializing agents...")
        env.reset(seed=42)
        time.sleep(0.2)
        st.write("📑 Agent 1 → Extracting cheque fields via OCR...")
        time.sleep(0.2)
        st.write(f"✍️ Agent 2 → Comparing signature against {sig_source}...")
        time.sleep(0.2)
        st.write("🏦 Agent 3 → Verifying account details...")
        time.sleep(0.2)
        st.write("💰 Agent 4 → Checking balance & behaviour...")
        time.sleep(0.15)
        st.write("🔄 Agent 5 → Simulating interbank transfer...")
        time.sleep(0.15)
        st.write("🧠 Agent 6 → Orchestrating final decision...")

        action = {
            "cheque_image_path": image_path,
            "difficulty": st.session_state.difficulty,
            "dataset_df": dataset_df,
        }
        _, reward, done, info = env.step(action)
        status.update(label="✅ Analysis complete", state="complete", expanded=False)

    outputs = info.get("agent_outputs", {})
    result = {
        "tested": True,
        "reward": reward,
        "done": done,
        "info": info,
        "image_path": image_path,
        "sig_source": sig_source,
        "sig_count": None,
    }
    st.session_state.analysis_result = result
    st.session_state.history.append({
        "Cheque": Path(image_path).name if image_path else "simulated",
        "Reward": reward,
        "Confidence": round(float(outputs.get("agent6", {}).get("confidence", 0.0)) * 100, 1),
    })


def render_pipeline(result: Dict[str, Any]) -> None:
    outputs = result["info"].get("agent_outputs", {})
    agents = [
        ("1", "OCR Extract", "agent1"),
        ("2", "Sig Verify", "agent2"),
        ("3", "Account", "agent3"),
        ("4", "Balance", "agent4"),
        ("5", "Transfer", "agent5"),
        ("6", "Decision", "agent6"),
    ]

    st.markdown('<div class="section-title">Agent Pipeline Flow</div>', unsafe_allow_html=True)
    cols = st.columns([1, 0.15, 1, 0.15, 1, 0.15, 1, 0.15, 1, 0.15, 1])
    agent_cols = [cols[0], cols[2], cols[4], cols[6], cols[8], cols[10]]
    arrow_cols = [cols[1], cols[3], cols[5], cols[7], cols[9]]

    for arrow_col in arrow_cols:
        arrow_col.markdown("<div style='text-align:center;color:rgba(255,255,255,0.25);padding-top:2.5rem;font-size:1.2rem;'>→</div>", unsafe_allow_html=True)

    for col, (num, label, key) in zip(agent_cols, agents):
        data = outputs.get(key, {})
        if key == "agent6":
            decision = data.get("final_decision", "FAIL")
            status_str = "PASS" if decision == "APPROVED" else "WARN" if decision == "REVIEW" else "FAIL"
        else:
            status_str = data.get("status", "FAIL")
        tone = tone_for_status(status_str)
        icon = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌"}.get(status_str, "❌")

        with col:
            with st.container():
                st.markdown(f"""
                <div class="pipeline-node {tone.lower()}">
                    <div style="font-size:1.4rem;margin-bottom:0.3rem;">{icon}</div>
                    <div class="pipeline-title">Agent {num}</div>
                    <div style="font-size:0.78rem;font-weight:600;color:rgba(255,255,255,0.8);">{label}</div>
                    <div class="pipeline-status {tone.lower()}" style="margin-top:0.4rem;">{status_str}</div>
                </div>
                """, unsafe_allow_html=True)


def render_signature_comparison(result: Dict[str, Any]) -> None:
    outputs = result["info"].get("agent_outputs", {})
    agent2 = outputs.get("agent2", {})

    stored_sig_path = agent2.get("stored_signature_path", "")
    matched_path = agent2.get("matched_signature_path", "")
    score = agent2.get("best_match_score", 0.0)
    status = agent2.get("status", "FAIL")
    matched_name = agent2.get("matched_signature", "None")
    tone = tone_for_status(status)
    cheque_path = result.get("image_path", "")
    sig_source = result.get("sig_source", "Dataset")

    score_tone = "green" if score >= 0.75 else "yellow" if score >= 0.45 else "red"
    verdict_text = "✅ Signature Verified" if status == "PASS" else "⚠️ Borderline Match" if status == "WARN" else "❌ Signature Mismatch"
    verdict_icon = "🔗" if status == "PASS" else "⚠️" if status == "WARN" else "❌"
    verdict_color = "#34d399" if score_tone == "green" else "#fbbf24" if score_tone == "yellow" else "#f87171"

    st.markdown('<div class="section-title">Signature Verification — Cheque Image vs Stored Signature</div>', unsafe_allow_html=True)

    col1, col_mid, col2 = st.columns([5, 1, 5])

    with col1:
        st.markdown('<div class="sig-label extracted">🧾 Uploaded Cheque</div>', unsafe_allow_html=True)
        if cheque_path and Path(cheque_path).exists():
            st.image(cheque_path, use_container_width=True)
        else:
            st.info("Cheque image not available.")

    with col_mid:
        st.markdown(f"""
        <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;padding-top:3.5rem;">
            <div style="font-size:2rem;">{verdict_icon}</div>
            <div style="font-size:0.6rem;text-align:center;color:rgba(255,255,255,0.35);margin-top:0.4rem;">SSIM<br>COMPARE</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        display_sig = stored_sig_path or matched_path
        display_name = Path(display_sig).name if display_sig else matched_name
        st.markdown(f'<div class="sig-label reference">📁 Stored Signature: {display_name}</div>', unsafe_allow_html=True)
        if display_sig and Path(display_sig).exists():
            st.image(display_sig, use_container_width=True)
        else:
            st.info("No matching signature found in dataset.")

    st.markdown(f"""
    <div class="glass-card" style="margin-top:0.8rem;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.6rem;">
            <span style="font-size:0.9rem;font-weight:600;color:rgba(255,255,255,0.85);">SSIM Similarity Score</span>
            {badge(verdict_text, score_tone)}
        </div>
        <div style="display:flex;align-items:center;gap:1.2rem;">
            <div style="flex:1;">{score_bar(score, score_tone)}</div>
            <span style="font-size:1.3rem;font-weight:800;color:{verdict_color};">{score:.1%}</span>
        </div>
        <div style="margin-top:0.5rem;font-size:0.78rem;color:rgba(255,255,255,0.4);">
            Compared against: <strong style="color:rgba(255,255,255,0.6);">{display_name or '—'}</strong>
            &nbsp;|&nbsp; Source: <strong style="color:rgba(255,255,255,0.6);">{sig_source}</strong>
            &nbsp;|&nbsp; Threshold: PASS >= 65%, WARN >= 45%, FAIL &lt; 45%
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_rejection_reason(result: Dict[str, Any]) -> None:
    outputs = result["info"].get("agent_outputs", {})
    agent6 = outputs.get("agent6", {})
    if agent6.get("final_decision") != "REJECTED":
        return

    issues = agent6.get("details", {}).get("reason_summary", [])
    if not issues:
        issues = ["Cheque failed safety thresholds — specific agent details unavailable."]

    items_html = "".join(f'<div class="rejection-item"><span>⛔</span><span>{iss}</span></div>' for iss in issues)
    st.markdown(f"""
    <div class="rejection-box">
        <div class="rejection-title">📋 Why was this cheque rejected?</div>
        {items_html}
    </div>
    """, unsafe_allow_html=True)


def render_cheque_preview(result: Dict[str, Any]) -> None:
    st.markdown('<div class="section-title">Uploaded Cheque</div>', unsafe_allow_html=True)
    img_path = result.get("image_path", "")
    if img_path and Path(img_path).exists():
        st.markdown('<div class="cheque-frame">', unsafe_allow_html=True)
        st.image(img_path, use_container_width=True, caption="Submitted Cheque Image")
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.warning("Cheque image not found on disk.")


def render_agent_detail_cards(result: Dict[str, Any]) -> None:
    outputs = result["info"].get("agent_outputs", {})
    st.markdown('<div class="section-title">Agent-by-Agent Breakdown</div>', unsafe_allow_html=True)

    agent_meta = [
        ("Agent 1 — OCR Extraction", "agent1", "📑"),
        ("Agent 2 — Signature Verification", "agent2", "✍️"),
        ("Agent 3 — Account Verification", "agent3", "🏦"),
        ("Agent 4 — Balance & Behaviour", "agent4", "💰"),
        ("Agent 5 — Interbank Transfer", "agent5", "🔄"),
        ("Agent 6 — Decision Orchestrator", "agent6", "🧠"),
    ]

    for title, key, icon in agent_meta:
        data = outputs.get(key, {})
        if key == "agent6":
            raw_status = "PASS" if data.get("final_decision") == "APPROVED" else "WARN" if data.get("final_decision") == "REVIEW" else "FAIL"
        else:
            raw_status = data.get("status", "FAIL")
        tone = tone_for_status(raw_status)
        conf = data.get("confidence", None)
        conf_str = f"{conf:.0%}" if conf is not None else "N/A"

        with st.expander(f"{icon} {title}  —  Status: **{raw_status}**"):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(badge(raw_status, tone), unsafe_allow_html=True)
                st.caption(f"Confidence: {conf_str}")
            with c2:
                if key == "agent1":
                    extracted = data.get("extracted", {})
                    if extracted:
                        st.write(f"**Payee:** {extracted.get('payee_name', '-') or '-'}")
                        st.write(f"**Amount:** Rs. {float(extracted.get('amount_digits', 0) or 0):,.2f}")
                        st.write(f"**Date:** {extracted.get('date', '-') or '-'}")
                        st.write(f"**OCR Confidence:** {float(data.get('ocr_confidence', 0.0)):.0%}")
                        missing_fields = extracted.get("missing_fields", [])
                        st.write(f"**Missing Fields:** {', '.join(missing_fields) if missing_fields else 'None'}")
                        preview = data.get("ocr_text_preview", "").strip()
                        if preview:
                            st.markdown("**Extracted Text Preview:**")
                            st.code(preview, language="text")
                elif key == "agent2":
                    st.write(f"**Match Score:** {data.get('best_match_score', 0):.3f}")
                    st.write(f"**Matched File:** {data.get('matched_signature', 'None')}")
                elif key == "agent3":
                    st.write(f"**Match Type:** {data.get('match_type', '-')}")
                    st.write(f"**Account Valid:** {data.get('account_valid', False)}")
                    matched_record = data.get("matched_record")
                    if matched_record:
                        st.markdown("**Matched Record:**")
                        st.json(matched_record)
                elif key == "agent4":
                    st.write(f"**Balance OK:** {data.get('balance_ok', False)}")
                elif key == "agent5":
                    st.write(f"**Transfer Ready:** {data.get('transfer_possible', False)}")
                    st.write(f"**Transfer Type:** {data.get('transfer_type', '-')}")
                elif key == "agent6":
                    st.write(f"**Decision:** {data.get('final_decision', '-')}")
                    st.write(f"**Weighted Score:** {data.get('details', {}).get('weighted_score', '-')}")

            issues = data.get("issues", []) or data.get("details", {}).get("reason_summary", [])
            if issues:
                st.markdown("**Issues:**")
                for iss in issues:
                    st.markdown(f"- {iss}")


def render_history_chart() -> None:
    if not st.session_state.history:
        return
    st.markdown('<div class="section-title">Session Performance History</div>', unsafe_allow_html=True)
    history_df = pd.DataFrame(st.session_state.history)
    st.line_chart(history_df.set_index("Cheque")[["Reward", "Confidence"]], height=180)


def render_empty_state() -> None:
    st.markdown("""
    <div class="empty-state">
        <div class="empty-icon">🏦</div>
        <div class="empty-title">No cheque analyzed yet</div>
        <div class="empty-desc">Upload a cheque image or pick a demo from the sidebar, then click <strong>Analyze Cheque</strong>.</div>
    </div>
    """, unsafe_allow_html=True)


def main() -> None:
    configure_page()
    inject_styles()
    initialize_state()

    result = st.session_state.analysis_result
    render_header(result)
    render_sidebar()

    top_l, top_r = st.columns([0.72, 0.28])
    with top_l:
        st.markdown('<div style="color:rgba(255,255,255,0.55);font-size:0.88rem;">Single-upload pipeline — cheque image only. Agents 3, 4, and 5 validate against the bank Excel dataset automatically.</div>', unsafe_allow_html=True)
    with top_r:
        if st.button("🔍 Analyze Cheque", use_container_width=True, type="primary"):
            run_analysis()
            st.rerun()

    if result is None:
        render_empty_state()
        return

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    render_pipeline(result)
    st.markdown("</div>", unsafe_allow_html=True)

    render_rejection_reason(result)

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    render_signature_comparison(result)
    st.markdown("</div>", unsafe_allow_html=True)

    left, right = st.columns([1, 1])
    with left:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        render_cheque_preview(result)
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        render_agent_detail_cards(result)

    render_history_chart()


if __name__ == "__main__":
    main()
