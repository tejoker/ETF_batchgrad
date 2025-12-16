# 🕵️‍♂️ Resume HR Verifier

A tool to cross-reference a candidate's PDF resume with their public GitHub profile.

## 🚀 Features
- **Identity Verification**: Matches name on resume vs GitHub.
- **Company Check**: Verifies if the candidate's current employer matches their GitHub organization.
- **Skill Validation**: Cross-references "Skills" section in resume with actual languages used in GitHub repositories.
- **Trust Score**: Generates a 0-100 confidence score based on the data match.

## 🛠️ Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *(Requires `pypdf`, `fuzzywuzzy`, `python-Levenshtein`, `reportlab`)*

2. **Verify Installation**:
   ```bash
   python3 resume_verifier.py --help
   ```

## 📖 Usage

Run the verifier by providing a PDF resume. The tool will automatically find GitHub and LinkedIn links in the PDF.

```bash
python3 resume_verifier.py --resume <path_to_resume.pdf>
```

*(You can still manually provide a username with `--github` if needed)*

### Example
To test with the provided dummy resume:

```bash
# 1. Generate the example resume (if not already present)
python3 create_dummy_resume.py

# 2. Run verification (it will auto-detect 'octocat' from the link in the PDF)
python3 resume_verifier.py --resume example_resume.pdf
```

## 📊 Output
The tool prints a summary to the console and saves a detailed JSON report to `verification_report.json`.

**Console Output Example:**
```text
============================================================
RESUME VERIFICATION REPORT: octocat
============================================================
TRUST SCORE: 87/100
SUMMARY: High Trust: Resume aligns well with public GitHub profile.
------------------------------------------------------------
✅ [Identity] Name Match
   Resume: The Octocat
   GitHub: The Octocat
   Score:  100%

✅ [Professional] Company Match
...
```

## 🧩 Architecture
- **`resume_verifier.py`**: CLI entry point.
- **`verifier/parser.py`**: Extracts text and sections (Skills, Experience) from PDFs using `pypdf`.
- **`verifier/engine.py`**: Logic using `fuzzywuzzy` to compare claims.
- **`GitHubScraper.py`**: Reused from the main project to fetch live data.
