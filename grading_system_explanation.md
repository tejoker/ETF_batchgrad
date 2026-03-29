# EuroTech Applicant Grading System

## Overview
The grading system is an automated, AI-augmented pipeline designed to ingest, verify, and evaluate applicants for deeptech and elite programs. Given a CSV file (`input.csv`) containing applicant responses, resumes, and URLs, the system aggregates external footprints and evaluates candidates across five distinct criteria. The final output provides component-level grades (0-100) and plots a visual pentagram radar chart for comparative analysis.

## Core Architecture

### 1. Data Ingestion & Scraping Engine
The engine goes beyond self-reported form data by proactively reaching out and gathering a more complete digital twin of each candidate.
*   **Resume Parsing**: Extracts skills, education, and experience from uploaded PDFs (`verifier/parser.py`).
*   **GitHub Scraper**: Fetches user profiles and highest-performing repositories, running local LLM reviews on `README.md` files to evaluate code quality, purpose, and capability.
*   **LinkedIn/Web Scraper**: Leverages Selenium to fetch real-world professional experience and scrapes personal/startup websites for ground-truth claims about products or funding.

### 2. Discrepancy & Cross-Verification
To ensure candidate integrity, the system uses a `CrossVerifier`. It compares the applicant's self-reported "form data" against their scraped digital footprint (LinkedIn, Resume). It yields a "trust score", flagging exaggerated or contradictory roles, startups, or education entries.

### 3. Evaluation Dimensions (The 5 Pillars)
The Grader (`grader.py`) structures its evaluation around five key criteria:

1.  **Education (Deterministic Evaluation)**:
    Scores range from 0 to 100 based on exact or fuzzy-matched institutional rankings dynamically correlated against datasets like *France DAUR* and *World University Rankings*. Highly-ranked schools (e.g. Top 10 World, or DAUR 'AAA' like Polytechnique/ENS Ulm) receive high 95-100 scores, with a mathematical decay applied to lower ranks.
2.  **Community (AI Graded)**:
    Evaluates applicant leadership and involvement based on their stated program experiences, associations, and contributions.
3.  **Hack/Personal Project (AI Graded)**:
    Analyzes hackathon victories, open-source involvement, and deeptech portfolio projects. Takes the LLM-summarized GitHub repository reviews into heavy consideration.
4.  **Research (AI Graded)**:
    Looks for verifiable deeptech academic research, Arxiv papers, publications, and specific research ambition (filtering out shallow tech projects).
5.  **Startup (AI Graded)**:
    Focuses on entrepreneurial success. Weighs heavily on funds raised, venture capital backing, and validated product websites. Includes a hard override rule: applicants raising $1M+ automatically score 100.

### 4. LLM Ensembling (Variance Reduction)
For AI-graded dimensions (Community, Hack/Project, Research, Startup), the system utilizes a local Llama model (`llama3.2:3b` via Ollama) acting as a venture capital evaluator. To prevent LLM grading hallucination and assure consistency, the system uses an ensemble approach: It generates the grade **5 separate times**, discards the lowest scores, and averages the **top 3 results**.

## Execution Protocol
**1. Single-Applicant Mode**: Processes a defined row index, printing scores to the console and saving an isolated graph representation.
```bash
python3 main_grader.py 0
```
**2. Batch Mode**: Seamlessly evaluates all non-processed applicants within `input.csv`, generates `.png` pentagram charts in the output directory, and logs errors continuously.
```bash
python3 main_grader.py --batch
```
