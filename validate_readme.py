#!/usr/bin/env python3
"""
Validate README.md references after package restructuring
"""

import re
import sys
from pathlib import Path

def check_readme_references():
    """Check README.md for outdated references"""
    readme_path = Path("README.md")
    
    if not readme_path.exists():
        print("❌ README.md not found")
        return False
    
    content = readme_path.read_text(encoding='utf-8')
    
    issues = []
    
    # Check for old import patterns
    old_imports = [
        r'from data_pipeline import',
        r'from crl_agent import', 
        r'from baselines import',
        r'from causal_graph import',
        r'from metrics import',
        r'import data_pipeline',
        r'import crl_agent',
        r'import baselines',
        r'import causal_graph',
        r'import metrics'
    ]
    
    for pattern in old_imports:
        # Find lines with the pattern that are not comments
        lines = content.split('\n')
        real_matches = []
        for line in lines:
            if re.search(pattern, line, re.IGNORECASE) and not line.strip().startswith('#'):
                real_matches.append(line.strip())
        if real_matches:
            issues.append(f"Found old import pattern: {pattern} ({len(real_matches)} non-comment occurrences)")
    
    # Check for old directory references
    old_paths = [
        r'DATA_SPLITS/',  # Should be data/DATA_SPLITS/
        r'config/',       # Should be configs/
        r'\.py\b(?!\s*(#|$))',  # Check for loose .py references
    ]
    
    for pattern in old_paths:
        if pattern == r'DATA_SPLITS/':
            # Find standalone DATA_SPLITS/ references (not preceded by data/)
            lines = content.split('\n')
            problematic_lines = []
            for line in lines:
                if 'DATA_SPLITS/' in line and 'data/DATA_SPLITS/' not in line and '├── 📂 DATA_SPLITS/' not in line:
                    problematic_lines.append(line.strip())
            if problematic_lines:
                issues.append(f"Found old DATA_SPLITS/ path (should be data/DATA_SPLITS/): {len(problematic_lines)} occurrences")
        elif pattern == r'config/':
            matches = re.findall(r'\bconfig/', content)
            # Filter out configs/ occurrences
            matches = [m for m in matches if 'configs/' not in content[content.find(m)-10:content.find(m)+10]]
            if matches:
                issues.append(f"Found old config/ path (should be configs/): {len(matches)} occurrences")
    
    # Check for proper new imports
    new_imports = [
        r'from healthcare_crl\.',
        r'healthcare_crl\.agents\.',
        r'healthcare_crl\.data\.',
        r'healthcare_crl\.models\.',
        r'healthcare_crl\.baselines\.',
        r'healthcare_crl\.utils\.'
    ]
    
    new_import_found = False
    for pattern in new_imports:
        if re.search(pattern, content):
            new_import_found = True
            break
    
    if not new_import_found:
        issues.append("No new healthcare_crl import patterns found")
    
    # Check for references to new structure
    structure_refs = [
        r'src/healthcare_crl',
        r'pyproject\.toml',
        r'test_package_structure\.py',
        r'PACKAGE_STRUCTURE\.md'
    ]
    
    structure_found = 0
    for pattern in structure_refs:
        if re.search(pattern, content):
            structure_found += 1
    
    if structure_found < 2:
        issues.append("Missing references to new package structure")
    
    # Report results
    print("🔍 README.md Validation Report")
    print("=" * 40)
    
    if issues:
        print("❌ Issues found:")
        for issue in issues:
            print(f"  • {issue}")
        return False
    else:
        print("✅ No issues found!")
        print("✅ README.md properly updated for new package structure")
        return True

def check_new_structure_documentation():
    """Check if new structure is properly documented"""
    readme_path = Path("README.md")
    content = readme_path.read_text(encoding='utf-8')
    
    required_sections = [
        "Package Structure & Imports",
        "src/healthcare_crl", 
        "pip install -e",
        "configs/",
        "tests/",
        "scripts/"
    ]
    
    missing_sections = []
    for section in required_sections:
        if section not in content:
            missing_sections.append(section)
    
    if missing_sections:
        print("\n❌ Missing documentation sections:")
        for section in missing_sections:
            print(f"  • {section}")
        return False
    else:
        print("\n✅ All required documentation sections present")
        return True

if __name__ == "__main__":
    print("📝 Validating README.md after package restructuring...")
    
    refs_ok = check_readme_references()
    docs_ok = check_new_structure_documentation()
    
    if refs_ok and docs_ok:
        print("\n🎉 README.md validation passed!")
        print("All references updated for new package structure.")
    else:
        print("\n❌ README.md validation failed.")
        print("Some references may need updating.")
        sys.exit(1)