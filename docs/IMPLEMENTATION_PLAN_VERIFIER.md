# Resume Verifier Enhancement Plan

## Goal
Automatically extract GitHub and LinkedIn profile URLs from the resume PDF so the user doesn't need to manually provide the username.

## Proposed Changes

### [MODIFY] `verifier/parser.py`
- Add `extract_links()` method to `ResumeParser`.
- Use Regex to find:
  - GitHub: `github.com/([a-zA-Z0-9-]+)`
  - LinkedIn: `linkedin.com/in/([a-zA-Z0-9-]+)`
- Store found links in `self.sections`.

### [MODIFY] `resume_verifier.py`
- Update `argparse`: Make `--github` argument **optional**.
- Logic flow:
  1. Parse PDF first.
  2. If `--github` is provided -> Use it.
  3. If not provided -> Check parsed GitHub links.
     - If found -> Use the first one.
     - If not found -> specific error message.
  4. Print found LinkedIn URL (informational only).

## Verification Plan
1. **Regenerate dummy resume** with a GitHub link included.
2. **Run without `--github` arg**:
   ```bash
   python3 resume_verifier.py --resume example_resume.pdf
   ```
3. **Expectation**: Tool finds `octocat` from the link and verifies successfully.
