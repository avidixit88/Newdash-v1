# NextCure Signal Room v1

A preliminary Built By BuildWell-style Streamlit rebuild focused only on clinicaltrials.gov intelligence visualization.

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Cloud
Push these files to a GitHub repo, then create a Streamlit Cloud app pointing to `app.py`.

## Notes
- Uses ClinicalTrials.gov API v2 `/api/v2/studies` endpoint.
- Includes a premium fallback sample dataset if the API is unavailable or returns no rows.
- This v1 intentionally avoids AI summaries, market data, PubMed, patents, and crawling.
