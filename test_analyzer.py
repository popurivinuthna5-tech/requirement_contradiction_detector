import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.database import init_db
from app.services.document_parser import DocumentParser
from app.services.requirement_extractor import RequirementExtractor
from app.services.ai_providers.smart_local import SmartLocalProvider

def test_pipeline():
    init_db()
    srs_path = Path("sample_data/E-Commerce_Platform_SRS.txt")
    brd_path = Path("sample_data/E-Commerce_Business_Requirements_BRD.txt")
    
    srs_blocks = DocumentParser.parse_txt(srs_path)
    srs_reqs = RequirementExtractor.extract_from_blocks(srs_blocks, srs_path.name)
    
    brd_blocks = DocumentParser.parse_txt(brd_path)
    brd_reqs = RequirementExtractor.extract_from_blocks(brd_blocks, brd_path.name)
    
    print(f"Extracted {len(srs_reqs)} requirements from SRS")
    print(f"Extracted {len(brd_reqs)} requirements from BRD")
    
    provider = SmartLocalProvider()
    
    found_conflicts = []
    for r1 in srs_reqs:
        for r2 in brd_reqs:
            res = provider.analyze_requirement_pair(
                r1.requirement_text, r1.reference_code,
                r2.requirement_text, r2.reference_code
            )
            if res and res.is_conflict_or_overlap:
                found_conflicts.append((r1.reference_code, r2.reference_code, res.conflict_type, res.severity, res.conflicting_elements))
                
    print(f"\nTotal findings: {len(found_conflicts)}")
    for r1, r2, c_type, sev, elem in found_conflicts:
        print(f"[{sev.upper()}] {c_type}: {r1} vs {r2} -> {elem}")
        
    assert len(found_conflicts) > 0, "Should have detected conflicts!"
    print("\nTest passed successfully!")

if __name__ == "__main__":
    test_pipeline()
