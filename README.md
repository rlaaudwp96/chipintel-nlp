# ChipIntel NLP

An end-to-end Python NLP dashboard comparing semiconductor companies' earnings-call and annual-report language.

Companies covered in the demo corpus: NVIDIA, AMD, Broadcom, TSMC, Micron, and ASML.

## Features

- Topic detection for AI/data center, memory/packaging, manufacturing/equipment, supply chain, competition/demand, and geopolitics/regulation
- Explainable lexicon sentiment scoring
- TF-IDF keyword extraction
- Semantic search over uploaded documents
- Company comparison charts and CSV export
- Upload `.csv`, `.pdf`, or `.txt` documents through the UI

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

For CSV uploads, use these columns:

```text
company,document_type,period,text
NVIDIA,earnings_call,2025-Q4,"Your document text..."
```

## Project structure

```text
app.py                         Streamlit frontend
src/nlp_pipeline.py            Reusable NLP analysis functions
data/sample_documents.csv      Demo corpus
```

## Notes

The included corpus is synthetic and intended for a reproducible demo. For a research version, add properly sourced annual reports and transcripts, preserve document dates, and cite the original investor-relations or regulatory filing URLs.

