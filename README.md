# Bank Cheque Clearing RL Environment

This project provides a simple OpenEnv-style reinforcement learning environment for bank cheque clearing. Each episode creates one cheque case, and the agent must decide whether to `APPROVE`, `REJECT`, or `FLAG` it.

The upgraded version also accepts cheque image paths, extracts demo cheque data, verifies signatures against a simulated bank dataset, and converts that output into the RL observation used by the agent.
It now also supports the real cheque JPGs in `e:\cheque` and includes a browser dashboard for testing whether the agent actually processed a cheque.

## Folder Structure

```text
bank_env/
├── agent/
│   └── baseline_agent.py
├── data/
│   ├── cheques/
│   └── signatures/
├── tasks/
│   ├── easy.py
│   ├── hard.py
│   └── medium.py
├── vision/
│   ├── cheque_processor.py
│   └── signature_verifier.py
├── Dockerfile
├── README.md
├── app.py
├── frontend/
│   └── index.html
├── env.py
├── models.py
├── openenv.yaml
├── reward.py
└── run.py
```

## Observation Space

Each state contains:

- `cheque_amount`: cheque value
- `account_balance`: available account balance
- `signature_valid`: signature verification result
- `account_valid`: account status
- `fraud_score`: fraud risk from `0.0` to `1.0`

## Action Space

- `APPROVE`
- `REJECT`
- `FLAG`

## Reward Logic

- Correct approval: `+1`
- Fraud or bad cheque approved: `-2`
- Correct rejection: `+2`
- Wrong rejection: `-0.5`
- Correct flag on uncertain cases: `+0.5`
- Flag on non-uncertain cases: small positive or negative reward depending on risk

## Difficulty Levels

- `easy`: very clear legitimate or fraudulent cheques
- `medium`: mixed signals such as signature issues or borderline fraud
- `hard`: conflicting signals such as valid documents with high fraud or invalid accounts with low fraud

## Environment API

### `reset()`

Generates a new cheque case and returns the observation.

```python
env.reset()
env.reset(image_path="bank_env/data/cheques/cheque1.png")
```

### `step(action)`

Processes one action and returns:

```python
observation, reward, done, info
```

### `state()`

Returns the current internal state, including the recommended banking action used for reward calculation.

## Baseline Agent

The baseline agent is rule-based. It follows simple banking heuristics:

- reject invalid accounts
- reject insufficient funds
- reject very high fraud risk
- flag ambiguous cases
- approve clean cases

## Run Locally

```bash
python -m bank_env.run --difficulty hard --episodes 20
```

Image mode:

```bash
python -m bank_env.run --image bank_env/data/cheques/cheque1.png
python -m bank_env.run --image bank_env/data/cheques/cheque1.png --image bank_env/data/cheques/cheque2.png --episodes 2
python -m bank_env.run --image e:/cheque/cheque1.jpg --episodes 1
```

## Sample Test Cases

```bash
python -m bank_env.run --image bank_env/data/cheques/cheque1.png --episodes 1
python -m bank_env.run --image bank_env/data/cheques/cheque2.png --episodes 1
python -m bank_env.run --image bank_env/data/cheques/cheque3.png --episodes 1
```

Expected behavior:

- `cheque1.png`: valid signature, enough balance, low fraud, likely `APPROVE`
- `cheque2.png`: invalid signature and insufficient balance, likely `REJECT`
- `cheque3.png`: invalid signature with elevated fraud, likely `REJECT`
- `cheque1.jpg`: valid reference signature, enough balance, likely `APPROVE`
- `cheque2.jpg`: signature mismatch, likely `REJECT`
- `cheque3.jpg`: very large amount plus signature mismatch, likely `REJECT`

## Frontend Dashboard

Run:

```bash
uvicorn bank_env.app:app --host 0.0.0.0 --port 7860
```

Open `http://localhost:7860` to:

- run one-click analysis on the provided cheque JPG samples
- enter a cheque path and optional signature path
- upload cheque and signature files directly
- inspect extracted data, signature score, fraud score, and the final agent decision

## Image Pipeline

The image pipeline is intentionally hackathon-ready:

- cheque metadata extraction uses a hardcoded demo mapping keyed by image filename
- signature verification compares a cheque signature image and a stored reference image
- OpenCV handles loading, grayscale conversion, and resizing
- SSIM is used for similarity scoring, with a compatibility fallback if `scikit-image` is not installed locally

The simulated bank dataset lives in `vision/cheque_processor.py`.

## Hugging Face Spaces Notes

This project is lightweight and Docker-ready, and includes a small FastAPI app in `app.py`. That makes it easy to run in a Docker-based Hugging Face Space.

Example API commands:

```bash
uvicorn bank_env.app:app --host 0.0.0.0 --port 7860
```

Endpoints:

- `GET /`
- `POST /reset` with JSON body like `{"difficulty":"easy","image_path":"bank_env/data/cheques/cheque1.png"}`
- `POST /step` with JSON body like `{"action":"FLAG"}`

## Example Usage

```python
from bank_env.env import BankChequeClearingEnv
from bank_env.models import Action

env = BankChequeClearingEnv(difficulty="medium", seed=42)
obs = env.reset()
print(obs)

next_obs, reward, done, info = env.step(Action.FLAG)
print(reward, done, info)
```
