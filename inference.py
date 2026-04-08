#!/usr/bin/env python3
"""
Inference script for Bank Cheque Clearing Environment.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)

# ============================================
# CORRECT IMPORTS for your file structure
# ============================================
from env import BankChequeClearingEnv      # ← From env.py in same directory
from models import Action, Observation     # ← From models.py in same directory
from reward import calculate_reward, derive_expected_action  # ← Optional, if needed

# Configuration from environment variables
API_BASE_URL = os.environ.get("API_BASE_URL", "")
MODEL_NAME = os.environ.get("MODEL_NAME", "gpt-3.5-turbo")
HF_TOKEN = os.environ.get("HF_TOKEN", "")


class ChequeInferenceAgent:
    """Agent that uses rule-based or LLM decisions."""
    
    def __init__(self):
        self.client = None
        if API_BASE_URL and HF_TOKEN:
            try:
                from openai import OpenAI
                self.client = OpenAI(
                    base_url=API_BASE_URL,
                    api_key=HF_TOKEN,
                )
                logger.info("[STEP] LLM client initialized")
            except Exception as e:
                logger.warning(f"[STEP] Could not initialize OpenAI client: {e}")
    
    def llm_decision(self, observation: Dict[str, Any]) -> str:
        """Use LLM to make decision based on observation."""
        if self.client:
            try:
                prompt = f"""You are a bank cheque fraud detection agent. Based on the following observation, decide to APPROVE, REJECT, or FLAG the cheque.

Observation:
- Cheque Amount: {observation.get('cheque_amount', 0)}
- Account Balance: {observation.get('account_balance', 0)}
- Data Valid: {observation.get('data_valid', True)}
- Signature Valid: {observation.get('signature_valid', True)}
- Account Valid: {observation.get('account_valid', True)}
- Fraud Score: {observation.get('fraud_score', 0)}
- Transfer Status: {observation.get('transfer_status', 'PENDING')}

Rules:
- REJECT if: account invalid, transfer failed, fraud score > 0.75, or insufficient balance
- FLAG if: signature invalid OR fraud score between 0.45-0.75
- APPROVE only if: all checks pass AND fraud score < 0.45

Respond with exactly one word: APPROVE, REJECT, or FLAG"""

                response = self.client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0,
                    max_tokens=10,
                )
                decision = response.choices[0].message.content.strip().upper()
                if decision in ["APPROVE", "REJECT", "FLAG"]:
                    return decision
            except Exception as e:
                logger.warning(f"[STEP] LLM call failed: {e}")
        
        # Fallback to rule-based decision
        return self.rule_based_decision(observation)
    
    def rule_based_decision(self, observation: Dict[str, Any]) -> str:
        """Fallback rule-based decision."""
        if not observation.get("account_valid", True):
            return "REJECT"
        if observation.get("transfer_status") == "FAILED":
            return "REJECT"
        if observation.get("fraud_score", 0) > 0.75:
            return "REJECT"
        if observation.get("account_balance", 0) < observation.get("cheque_amount", 0):
            return "REJECT"
        if not observation.get("signature_valid", True):
            return "FLAG"
        if observation.get("fraud_score", 0) >= 0.45:
            return "FLAG"
        return "APPROVE"
    
    def act(self, observation: Dict[str, Any]) -> Action:
        """Convert observation to action."""
        decision = self.llm_decision(observation)
        logger.info(f"[STEP] Agent decision: {decision}")
        
        # Convert string decision to Action enum
        if decision == "APPROVE":
            return Action.APPROVE
        elif decision == "REJECT":
            return Action.REJECT
        else:
            return Action.FLAG


def run_episode(env: BankChequeClearingEnv, agent: ChequeInferenceAgent, 
                difficulty: str, image_path: Optional[str] = None, 
                signature_path: Optional[str] = None) -> Dict[str, Any]:
    """Run a single episode."""
    logger.info("[STEP] Resetting environment...")
    
    # Reset environment with parameters
    if image_path:
        observation = env.reset(
            difficulty=difficulty, 
            image_path=image_path,
            signature_path=signature_path
        )
    else:
        observation = env.reset(difficulty=difficulty)
    
    logger.info(f"[STEP] Observation received: cheque_amount={observation.get('cheque_amount')}, "
                f"fraud_score={observation.get('fraud_score')}, "
                f"signature_valid={observation.get('signature_valid')}, "
                f"account_valid={observation.get('account_valid')}")
    
    action = agent.act(observation)
    logger.info(f"[STEP] Taking action: {action.value}")
    
    next_obs, reward, done, info = env.step(action)
    logger.info(f"[STEP] Episode complete - Reward: {reward}, Done: {done}")
    
    return {
        "observation": observation,
        "action": action.value,
        "reward": reward,
        "done": done,
        "info": info,
    }


def main():
    """Main inference loop."""
    logger.info("[START] Bank Cheque Clearing Inference")
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Bank Cheque Clearing Inference")
    parser.add_argument("--difficulty", default="medium", choices=["easy", "medium", "hard"])
    parser.add_argument("--episodes", type=int, default=5)
    parser.add_argument("--image", type=str, help="Path to cheque image", default=None)
    parser.add_argument("--signature", type=str, help="Path to signature image", default=None)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    
    logger.info(f"[STEP] Running with difficulty={args.difficulty}, episodes={args.episodes}, seed={args.seed}")
    if args.image:
        logger.info(f"[STEP] Using cheque image: {args.image}")
    if args.signature:
        logger.info(f"[STEP] Using signature image: {args.signature}")
    
    # Initialize environment and agent
    env = BankChequeClearingEnv(seed=args.seed)
    agent = ChequeInferenceAgent()
    
    rewards = []
    decisions = []
    
    for episode in range(args.episodes):
        logger.info(f"[STEP] Starting episode {episode + 1}/{args.episodes}")
        
        # Use image/signature only for first episode if provided
        image_path = args.image if episode == 0 else None
        signature_path = args.signature if episode == 0 else None
        
        result = run_episode(env, agent, args.difficulty, image_path, signature_path)
        rewards.append(result["reward"])
        decisions.append(result["action"])
        
        logger.info(f"[STEP] Episode {episode + 1} completed - Action: {result['action']}, Reward: {result['reward']:.3f}")
    
    # Calculate statistics
    avg_reward = sum(rewards) / len(rewards) if rewards else 0
    
    logger.info(f"[STEP] Inference Summary:")
    logger.info(f"[STEP]   - Total Episodes: {args.episodes}")
    logger.info(f"[STEP]   - Average Reward: {avg_reward:.3f}")
    logger.info(f"[STEP]   - Max Reward: {max(rewards):.3f}")
    logger.info(f"[STEP]   - Min Reward: {min(rewards):.3f}")
    logger.info(f"[STEP]   - Decisions: {decisions}")
    
    logger.info("[END] Inference finished successfully")
    
    # Output final results in JSON format
    print(json.dumps({
        "status": "success",
        "avg_reward": avg_reward,
        "rewards": rewards,
        "decisions": decisions,
        "episodes": args.episodes,
        "difficulty": args.difficulty,
    }))


if __name__ == "__main__":
    main()