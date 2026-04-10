from __future__ import annotations

import argparse
import sys
from pathlib import Path
from statistics import mean

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from server.environment import BankChequeClearingEnv
from tasks.easy import get_cases as get_easy_cases
from tasks.hard import get_cases as get_hard_cases
from tasks.medium import get_cases as get_medium_cases


def get_cases(difficulty: str) -> list[dict]:
    return {
        "easy": get_easy_cases(),
        "medium": get_medium_cases(),
        "hard": get_hard_cases(),
    }[difficulty]


def main() -> None:
    parser = argparse.ArgumentParser(description="Baseline inference runner for the multi-agent cheque environment.")
    parser.add_argument("--difficulty", choices=["easy", "medium", "hard"], default="easy")
    parser.add_argument("--episodes", type=int, default=5)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--signature-pdf",
        default="",
        help="Optional path to a PDF containing signature images. If omitted, backend stored signatures are used.",
    )
    args = parser.parse_args()

    env = BankChequeClearingEnv(seed=args.seed)
    cases = get_cases(args.difficulty)
    rewards: list[float] = []

    for episode in range(args.episodes):
        env.reset(seed=args.seed + episode)
        case = cases[episode % len(cases)]
        action = {
            "cheque_image_path": case["cheque_image_path"],
            "difficulty": args.difficulty,
        }
        if args.signature_pdf:
            action["signature_pdf_path"] = args.signature_pdf
        state, reward, done, info = env.step(action)
        rewards.append(reward)
        print(
            f"Episode {episode + 1:02d} | cheque_id={state['cheque_id']} | "
            f"decision={state['final_decision']:<8} | confidence={state['confidence']:.2f} | reward={reward:.2f}"
        )
        print(f"  extracted_signatures={len(info['extracted_signature_paths'])} | issues={len(info['issues'])}")
        assert done

    print("\nSummary")
    print(f"Mean reward: {mean(rewards):.3f}")
    print(f"Max reward:  {max(rewards):.3f}")
    print(f"Min reward:  {min(rewards):.3f}")


if __name__ == "__main__":
    main()
