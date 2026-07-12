"""
cli.py

Usage:
    python cli.py --skill sentinel --input skills/sentinel/sample_data/sample_logs.csv
    python cli.py --skill finsight --input skills/finsight/sample_data/sample_transactions.csv
    python cli.py --list
"""

import argparse
import pandas as pd

from core.skill_loader import load_skill, list_available_skills
from core.pipeline import run_pipeline
from core.llm_client import LocalLLM


def main():
    parser = argparse.ArgumentParser(description="CoreMind - local-first anomaly intelligence engine")
    parser.add_argument("--skill", help="Skill pack to run (e.g. sentinel, finsight)")
    parser.add_argument("--input", help="Path to input CSV file")
    parser.add_argument("--top", type=int, default=3, help="Number of top anomalies to explain")
    parser.add_argument("--model", default="phi3:mini", help="Ollama model name to use")
    parser.add_argument("--list", action="store_true", help="List available skill packs")
    args = parser.parse_args()

    if args.list:
        skills = list_available_skills()
        print("Available skill packs:")
        for s in skills:
            print(f"  - {s}")
        return

    if not args.skill or not args.input:
        parser.print_help()
        return

    print(f"Loading skill pack: {args.skill}")
    skill = load_skill(args.skill)
    print(f"  {skill.description.strip()}\n")

    raw_df = pd.read_csv(args.input)
    llm = LocalLLM(model=args.model)

    if not llm.is_available():
        print("NOTE: Ollama not detected on localhost:11434 -- using stub LLM responses.")
        print("      Run `ollama serve` (and `ollama pull phi3:mini`) for real explanations.\n")

    results = run_pipeline(skill, raw_df, top_n=args.top, llm=llm)

    print(f"Top {len(results)} anomalies detected:\n" + "=" * 50)
    for i, r in enumerate(results, 1):
        print(f"\n[{i}] Anomaly score: {r['row'].get('anomaly_score'):.3f}")
        print(f"    Raw data: {r['row']}")
        print(f"    Explanation:\n    {r['explanation']}")
        print("-" * 50)


if __name__ == "__main__":
    main()
