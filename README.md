# EcoSort | Smart Waste Operations

A Python and Streamlit dashboard for monitoring public waste bins, prioritizing collections, planning short pickup routes, and checking how common items should be sorted. The bundled bin network is clearly labeled sample data; reports and simulated collections persist for the current browser session.

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

Open the local URL printed by Streamlit. To run the core logic tests:

```powershell
python -m unittest
```

Collection priorities combine bin fill (75% of the score) and days since pickup (25%, capped at seven days). Suggested routes use a nearest-neighbor distance heuristic and are not a substitute for live traffic or vehicle-capacity planning.
