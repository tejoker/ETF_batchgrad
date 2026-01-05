
import matplotlib.pyplot as plt
import numpy as np

def plot_pentagram(grades, filename="pentagram_grade.png"):
    """
    Plot a radar chart for the given grades.
    grades: dict of {criteria: score}
    Overlay reference quantiles (Top 1%, 5%, 10%, 15%, 20%).
    """
    # Categories (5 criteria)
    categories = ['Education', 'Community', 'Hack/Project', 'Research', 'Startup']
    values = [grades.get(c, 0) for c in categories]
    
    # Close the loop
    values += values[:1]
    
    # Angles
    N = len(categories)
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]
    
    # Initialise the spider plot
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))
    
    # Draw one axe per variable + add labels
    plt.xticks(angles[:-1], categories)
    
    # Draw ylabels
    ax.set_rlabel_position(0)
    plt.yticks([20,40,60,80,100], ["20","40","60","80","100"], color="grey", size=7)
    plt.ylim(0,100)
    
    # Reference Quantiles (Approximations/Targets)
    # Top 1% = 98, Top 5% = 90, Top 10% = 85, Top 15% = 80, Top 20% = 75
    quantiles = [
        (98, '1%', 'red'),
        (90, '5%', 'orange'),
        (85, '10%', 'yellow'),
        (80, '15%', 'lightgreen'),
        (75, '20%', 'green')
    ]
    
    for score, label, color in quantiles:
        # Plot circle/polygon for this quantile
        q_values = [score] * N
        q_values += q_values[:1]
        ax.plot(angles, q_values, linewidth=1, linestyle='dashed', color=color, label=f"Top {label}")
        # ax.fill(angles, q_values, color=color, alpha=0.1)

    # Plot data
    ax.plot(angles, values, linewidth=2, linestyle='solid', label='Candidate')
    ax.fill(angles, values, 'b', alpha=0.2)
    
    # Add legend
    plt.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))
    
    plt.title("Candidate Evaluation Pentagram")
    plt.savefig(filename)
    plt.close()
    print(f"Graph saved to {filename}")

if __name__ == "__main__":
    # Test
    test_grades = {
        'Education': 95,
        'Community': 80,
        'Hack/Project': 60,
        'Research': 40,
        'Startup': 70
    }
    plot_pentagram(test_grades)
