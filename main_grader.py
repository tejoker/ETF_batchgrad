
import pandas as pd
from grader import Grader
from visualizer import plot_pentagram
import sys
import os


def main(index: int = 0):
    print("Loading data...")
    try:
        df = pd.read_csv('input.csv')
    except FileNotFoundError:
        print("Error: input.csv not found.")
        return

    print(f"Loaded {len(df)} applicants.")

    if index >= len(df):
        print(f"Index {index} out of bounds.")
        return

    row = df.iloc[index]
    name = f"{row.get('firstName', 'Unknown')} {row.get('lastName', 'Unknown')}"
    print(f"Processing applicant: {name} (Index {index})")

    # Initialize grader
    grader = Grader()

    print("Grading...")
    grades = grader.grade_applicant(row)

    print("\nGrades:")
    for k, v in grades.items():
        print(f"{k}: {v}")

    # Plot
    output_filename = f"grade_{name.replace(' ', '_')}.png"
    print(f"\nGenerating graph: {output_filename}")
    plot_pentagram(grades, output_filename)

    # Also save to artifacts dir if it exists
    artifact_dir = "/home/nicolasbigeard/.gemini/antigravity/brain/f862a5da-a79c-4afc-9238-02bd682db0f3"
    artifact_path = os.path.join(artifact_dir, output_filename)
    plot_pentagram(grades, artifact_path)
    print(f"Graph also saved to {artifact_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ETF candidate grader")
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Run the batch pipeline (processes all pending rows in the CSV)"
    )
    parser.add_argument(
        "--csv",
        default="input.csv",
        help="Path to the input CSV file (default: input.csv)"
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Directory for charts and logs in batch mode (default: output)"
    )
    parser.add_argument(
        "index",
        nargs="?",
        type=int,
        default=0,
        help="Row index to process in single-candidate mode (default: 0)"
    )
    args = parser.parse_args()

    if args.batch:
        from pipeline import BatchPipeline
        BatchPipeline(csv_path=args.csv, output_dir=args.output_dir).run()
    else:
        main(args.index)
