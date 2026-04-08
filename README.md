# Automated-Cheque-Clearance

### *Multi-Agent Intelligence for Bank Cheque Fraud Detection*

---

## 📌 Overview

**Automated-Cheque-Clearance** is an end-to-end AI-powered platform that automates bank cheque verification and fraud detection. The system uses a **multi-agent architecture** to perform OCR extraction, signature verification, account validation, balance checking, and final decision orchestration — all in real-time.

> 🎯 **Built for:** Hackathons, Banking AI Demos, RL Research, Production Pilot Deployments

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🧠 **Multi-Agent Pipeline** | 6 specialized agents working in concert |
| 📄 **OCR Extraction** | Automatically extracts payee, amount, date from cheques |
| ✍️ **Signature Verification** | SSIM-based matching against stored signatures |
| 🏦 **Account Validation** | Cross-checks with bank dataset (Excel/CSV) |
| 💰 **Balance & Fraud Scoring** | Real-time risk assessment |
| 🔄 **Interbank Transfer Simulation** | End-to-end clearing simulation |
| 🎨 **Streamlit Dashboard** | Beautiful, dark-themed UI with real-time analytics |
| 🤖 **RL-Ready Environment** | OpenEnv compliant for reinforcement learning |
| 🚀 **Docker Support** | One-click deployment on Hugging Face Spaces |

---

## 🏗️ Architecture
┌─────────────────────────────────────────────────────────────────┐
│ CHEQUE AI COMMAND CENTER │
├─────────────────────────────────────────────────────────────────┤
│ │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│ │ Agent 1 │ → │ Agent 2 │ → │ Agent 3 │ │
│ │ OCR │ │ Signature│ │ Account │ │
│ │ Extract │ │ Verify │ │ Validate │ │
│ └──────────┘ └──────────┘ └──────────┘ │
│ ↓ ↓ ↓ │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│ │ Agent 4 │ → │ Agent 5 │ → │ Agent 6 │ │
│ │ Balance │ │ Transfer │ │ Decision │ │
│ │ & Fraud │ │ Simulate │ │ Make │ │
│ └──────────┘ └──────────┘ └──────────┘ │
│ │
│ 🎯 Final Output: APPROVED / REJECTED / FLAGGED │
└─────────────────────────────────────────────────────────────────┘

text

---

## 📁 Project Structure
PROJECT/
├── 🧠 agent/ # RL agents (baseline + custom)
├── 🧩 agents/ # Multi-agent pipeline components
├── 📊 data/ # Cheque images & signatures
├── 🎨 frontend/ # HTML frontend assets
├── 🔧 server/ # API server & environment
├── 📋 tasks/ # Easy/Medium/Hard test cases
├── 🛠️ utils/ # Helper utilities
├── 👁️ vision/ # OCR & signature verification
│
├── 🐳 Dockerfile # Container configuration
├── 📄 README.md # This file
├── 🚀 app.py # Streamlit dashboard
├── 💻 client.py # Client interface
├── 🌍 env.py # OpenEnv RL environment
├── 🧠 inference.py # LLM-powered inference script
├── 📦 models.py # Data models (Action, Observation)
├── 📋 openenv.yaml # OpenEnv specification
├── 📚 requirements.txt # Python dependencies
└── 🎁 reward.py # Reward calculation logic

text

---

## 🚀 Quick Start

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/yourusername/cheque-ai-command-center.git
cd cheque-ai-command-center
2️⃣ Install Dependencies
bash
pip install -r requirements.txt
3️⃣ Run the Streamlit Dashboard
bash
streamlit run app.py
Then open http://localhost:8501 in your browser.

4️⃣ Run Inference (CLI)
bash
# Basic run
python inference.py --difficulty medium --episodes 5

# With custom cheque image
python inference.py --difficulty hard --episodes 1 --image "e:/cheque/cheque3.jpg"

# With signature verification
python inference.py --difficulty easy --episodes 1 --image "cheque.jpg" --signature "signature.jpg"
5️⃣ Run with Docker
bash
# Build the image
docker build -t cheque-ai .

# Run the container
docker run -p 8501:8501 -p 7860:7860 cheque-ai
🎮 Demo Cases
Case	Difficulty	Expected Outcome
✅ Valid Cheque	Easy	APPROVE
⚠️ Signature Mismatch	Medium	FLAG / REJECT
🚨 High-Value Fraud	Hard	REJECT
🤖 RL Environment API
The project provides an OpenEnv-compliant reinforcement learning environment.

Reset Environment
python
from env import BankChequeClearingEnv

env = BankChequeClearingEnv(seed=42)
observation = env.reset(difficulty="medium")
Take an Action
python
from models import Action

observation, reward, done, info = env.step(Action.APPROVE)
Observation Space
Field	Type	Description
cheque_amount	float	Amount on cheque
account_balance	float	Available balance
data_valid	bool	OCR data validity
signature_valid	bool	Signature match status
account_valid	bool	Account exists in dataset
fraud_score	float	0.0 (safe) to 1.0 (fraud)
transfer_status	str	SUCCESS / FAILED
Action Space
Action	Description
APPROVE	Clear the cheque
REJECT	Decline the cheque
FLAG	Mark for manual review
Reward Function
Scenario	Reward
Correct APPROVE	+1.0
Correct REJECT	+2.0
Correct FLAG	+0.5
Wrong APPROVE (fraud)	-2.0
Wrong REJECT	-0.5
🖥️ Streamlit Dashboard Features
🔥 Dark theme with gradient effects

📊 Real-time agent pipeline visualization

✍️ Side-by-side signature comparison with SSIM scoring

📈 Session performance history charts

🎯 Difficulty selector (Easy/Medium/Hard)

📤 File upload for custom cheques

🚀 One-click demo cases

🧪 Run Tests
bash
# Test all difficulty levels
python inference.py --difficulty easy --episodes 3
python inference.py --difficulty medium --episodes 3
python inference.py --difficulty hard --episodes 3

# Test with specific images
python inference.py --episodes 1 --image "data/cheques/cheque1.jpg"
🐳 Deployment on Hugging Face Spaces
Create a new Space on Hugging Face

Choose Docker as Space SDK

Connect your GitHub repository

Add secrets (if using LLM):

HF_TOKEN: Your API token

API_BASE_URL: LLM endpoint

MODEL_NAME: Model identifier

📊 Environment Variables
Variable	Required	Description
API_BASE_URL	No	LLM API endpoint
MODEL_NAME	No	Model name for inference
HF_TOKEN	No	Hugging Face / API key
🛠️ Built With
Technology	Purpose
Python 3.10+	Core language
Streamlit	Interactive dashboard
OpenCV	Image processing
scikit-image	SSIM signature matching
PyTesseract	OCR extraction
Docker	Containerization
OpenAI	LLM-powered decisions (optional)
📈 Performance Metrics
Metric	Value
Inference Time	< 2 sec per cheque
Signature Accuracy	85%+ (SSIM threshold)
Fraud Detection Rate	90%+ on hard cases
Docker Image Size	~800 MB
🤝 Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

Fork the repository

Create your feature branch (git checkout -b feature/amazing-feature)

Commit your changes (git commit -m 'Add amazing feature')

Push to the branch (git push origin feature/amazing-feature)

Open a Pull Request

📝 License
This project is licensed under the MIT License - see the LICENSE file for details.

👥 Authors
Manish Kumar , Gursimar Singh , Harmanpreet singh Birdi
