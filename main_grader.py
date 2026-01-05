
import pandas as pd
from grader import Grader
from visualizer import plot_pentagram
import sys
import os

def main():
    print("Loading data...")
    try:
        df = pd.read_csv('input.csv')
    except FileNotFoundError:
        print("Error: input.csv not found.")
        return

    print(f"Loaded {len(df)} applicants.")
    
    # Pick sample
    # Defaulting to first row (index 0) or user argument
    index = 0
    if len(sys.argv) > 1:
        try:
            index = int(sys.argv[1])
        except ValueError:
            pass
            
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
    # Ensure it goes to artifacts if possible, or local dir
    # For now local dir
    print(f"\nGenerating graph: {output_filename}")
    plot_pentagram(grades, output_filename)
    
    # Also save to artifacts dir if it exists
    artifact_dir = "/home/nicolasbigeard/.gemini/antigravity/brain/f862a5da-a79c-4afc-9238-02bd682db0f3"
    artifact_path = os.path.join(artifact_dir, output_filename)
    plot_pentagram(grades, artifact_path)
    print(f"Graph also saved to {artifact_path}")

if __name__ == "__main__":
    main()
