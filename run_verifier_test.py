
import sys
import os

# Add parent directory to path to import verifier
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from verifier.cross_verifier import CrossVerifier

def test_cross_verifier():
    print("Testing CrossVerifier...")
    
    # Case 1: Perfect Match
    form_1 = {
        "education_school": "Stanford University",
        "current_role": "Founder",
        "startup_name": "TechStart",
        "projects": "Built a quantum computer"
    }
    linkedin_1 = {
        "education": [{"school": "Stanford University"}],
        "experience": [{"company": "TechStart", "title": "Founder"}],
        "projects": [{"name": "Quantum Computer"}]
    }
    resume_1 = {
        "raw_text": "Education: Stanford University. Experience: Founder at TechStart."
    }
    
    verifier = CrossVerifier(form_1, linkedin_1, resume_1)
    res = verifier.verify()
    print(f"Case 1 (Perfect): Score {res['trust_score']} (Expected ~100)")
    assert res['trust_score'] == 100, f"Expected 100, got {res['trust_score']}"

    # Case 2: Missing Education
    form_2 = {
        "education_school": "MIT",
        "current_role": "Engineer",
        "startup_name": "Google",
        "projects": "Search Engine"
    }
    linkedin_2 = {
        "education": [{"school": "Stanford"}], # Mismatch
        "experience": [{"company": "Google", "title": "Engineer"}]
    }
    resume_2 = {
        "raw_text": "Education: Stanford. Google Engineer."
    }
    
    verifier = CrossVerifier(form_2, linkedin_2, resume_2)
    res = verifier.verify()
    print(f"Case 2 (Missing Edu): Score {res['trust_score']} (Expected < 100)")
    assert res['trust_score'] < 100
    print("Discrepancies:", res['discrepancies'])

    print("✅ Logic Verified!")

if __name__ == "__main__":
    test_cross_verifier()
