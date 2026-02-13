# Quick Start - Egeria Advisor Phase 2

## Installation & Testing (5 minutes)

### 1. Navigate to Project
```bash
cd /home/dwolfson/localGit/egeria-v6/egeria-advisor
```

### 2. Create Virtual Environment
```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -e ".[dev]"
```

### 4. Create Environment File
```bash
cp .env.example .env
# The defaults should work, but verify ADVISOR_DATA_PATH points to egeria-python
```

### 5. Test Setup
```bash
python scripts/test_setup.py
```

Expected output:
```
================================================================================
Egeria Advisor Setup Test
================================================================================
Testing imports...
  ✓ pydantic
  ✓ loguru
  ✓ pyyaml
  ✓ advisor.config
  ✓ advisor.data_prep.CodeParser

✅ All imports successful!

Testing configuration...
  ✓ Settings loaded
    - Data path: /home/dwolfson/localGit/egeria-v6/egeria-python
    ...

🎉 All tests passed! Setup is complete.
```

### 6. Run the Pipeline
```bash
# Full pipeline (takes ~30-60 seconds)
python -m advisor.data_prep.pipeline

# Or test individual components first
python advisor/data_prep/code_parser.py
python advisor/data_prep/doc_parser.py
python advisor/data_prep/example_extractor.py
```

### 7. Check Results
```bash
ls -lh data/cache/
cat data/cache/pipeline_summary.json
```

---

## What You Should See

### Pipeline Output
```
================================================================================
Starting Data Preparation Pipeline
================================================================================

[1/4] Parsing Python code files...
Parsing /home/dwolfson/localGit/egeria-v6/egeria-python/pyegeria...
✓ Extracted 5000+ code elements

[2/4] Parsing documentation files...
✓ Extracted 200+ documentation sections

[3/4] Extracting code examples...
✓ Extracted 300+ code examples

[4/4] Extracting file metadata...
✓ Extracted metadata from 500+ files

Pipeline completed in 45.23 seconds

PIPELINE SUMMARY
================================================================================
📝 Code Elements: 5247
   - Functions: 2103
   - Classes: 521
   - Methods: 2623
   ...
```

### Cache Files Created
```
data/cache/
├── code_elements.json       # ~15 MB - All functions, classes, methods
├── doc_sections.json        # ~2 MB  - All documentation sections
├── examples.json            # ~5 MB  - All code examples
├── metadata.json            # ~1 MB  - File metadata
└── pipeline_summary.json    # ~5 KB  - Statistics
```

---

## Troubleshooting

### Import Errors
```bash
# Reinstall dependencies
pip install -e ".[dev]"
```

### Path Errors
```bash
# Verify egeria-python path
ls /home/dwolfson/localGit/egeria-v6/egeria-python/pyegeria

# Update .env if needed
nano .env
# Change ADVISOR_DATA_PATH to correct path
```

### Permission Errors
```bash
# Ensure cache directory is writable
mkdir -p data/cache
chmod 755 data/cache
```

---

## Next Steps

Once Phase 2 is working:

1. ✅ **Verify Output** - Check that JSON files look reasonable
2. ✅ **Review Statistics** - Ensure counts make sense
3. ➡️ **Proceed to Phase 3** - Vector store integration

---

## Quick Commands Reference

```bash
# Activate environment
source .venv/bin/activate

# Test setup
python scripts/test_setup.py

# Run full pipeline
python -m advisor.data_prep.pipeline

# Run with options
python -m advisor.data_prep.pipeline --no-examples --cache-dir ./custom/cache

# Test individual parsers
python advisor/data_prep/code_parser.py /path/to/egeria-python
python advisor/data_prep/doc_parser.py /path/to/egeria-python
python advisor/data_prep/example_extractor.py /path/to/egeria-python
python advisor/data_prep/metadata_extractor.py /path/to/egeria-python

# View results
cat data/cache/pipeline_summary.json | python -m json.tool
head -n 50 data/cache/code_elements.json
```

---

## Files Created

**Total**: 19 files, ~4,600 lines of code

### Core Implementation
- `advisor/config.py` - Configuration management
- `advisor/data_prep/code_parser.py` - Python code parsing
- `advisor/data_prep/doc_parser.py` - Documentation parsing
- `advisor/data_prep/example_extractor.py` - Example extraction
- `advisor/data_prep/metadata_extractor.py` - Metadata extraction
- `advisor/data_prep/pipeline.py` - Pipeline orchestration

### Configuration
- `pyproject.toml` - Project dependencies
- `.env.example` - Environment template
- `config/advisor.yaml` - Configuration file
- `.gitignore` - Git ignore rules

### Documentation
- `README.md` - Project overview
- `PHASE2_COMPLETE.md` - Phase 2 summary
- `QUICK_START.md` - This file

### Scripts
- `scripts/test_setup.py` - Setup verification

---

## Support

If you encounter issues:
1. Check the error message carefully
2. Verify paths in .env file
3. Ensure Python 3.12+ is being used
4. Check that all dependencies installed

Ready to help debug any issues!