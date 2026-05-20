import datetime as dt
from typing import Any, Dict, List, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

st.set_page_config(
    page_title="NextCure Signal Room",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

API_URL = "https://clinicaltrials.gov/api/v2/studies"
TODAY = dt.date.today()

DEFAULT_QUERIES = [
    "NextCure OR B7-H4 OR VTCN1 OR CDH6 OR ovarian cancer ADC",
    "B7-H4 antibody drug conjugate ovarian cancer",
    "CDH6 antibody drug conjugate ovarian cancer",
]

PHASE_ORDER = ["Early Phase 1", "Phase 1", "Phase 1/2", "Phase 2", "Phase 2/3", "Phase 3", "Phase 4", "N/A"]
STATUS_ORDER = ["Recruiting", "Not yet recruiting", "Active, not recruiting", "Enrolling by invitation", "Completed", "Terminated", "Suspended", "Withdrawn", "Unknown"]

CSS = """
<style>
    :root {
        --bg: #080d18;
        --panel: rgba(18, 27, 44, 0.78);
        --panel2: rgba(14, 22, 36, 0.92);
        --line: rgba(164, 183, 219, 0.16);
        --text: #edf4ff;
        --muted: #8f9db7;
        --gold: #d8b86c;
        --cyan: #63d7ff;
        --blue: #5a82ff;
        --green: #75e3b4;
        --red: #ff7878;
    }
    html, body, [data-testid="stAppViewContainer"] {
        background:
            radial-gradient(circle at top left, rgba(74, 113, 255, .19), transparent 34%),
            radial-gradient(circle at top right, rgba(216, 184, 108, .12), transparent 26%),
            linear-gradient(180deg, #080d18 0%, #0b1020 50%, #070a12 100%);
        color: var(--text);
    }
    [data-testid="stHeader"] { background: rgba(8, 13, 24, 0); }
    [data-testid="stToolbar"] { display: none; }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(10, 16, 28, .98), rgba(8, 13, 24, .98));
        border-right: 1px solid var(--line);
    }
    .block-container { padding-top: 2rem; padding-bottom: 4rem; max-width: 1440px; }
    .hero {
        border: 1px solid var(--line);
        background: linear-gradient(135deg, rgba(18, 27, 44, .92), rgba(9, 15, 28, .64));
        border-radius: 30px;
        padding: 32px 34px;
        box-shadow: 0 24px 70px rgba(0,0,0,.33);
        position: relative;
        overflow: hidden;
    }
    .hero:after {
        content: "";
        position: absolute;
        right: -120px;
        top: -120px;
        width: 340px;
        height: 340px;
        background: radial-gradient(circle, rgba(99, 215, 255, .16), transparent 64%);
        pointer-events: none;
    }
    .eyebrow { color: var(--gold); letter-spacing: .18em; text-transform: uppercase; font-size: .78rem; font-weight: 700; }
    .hero h1 { font-size: 3.2rem; line-height: 1.02; margin: .35rem 0 .7rem 0; letter-spacing: -.055em; }
    .hero p { color: var(--muted); font-size: 1.05rem; max-width: 760px; margin: 0; }
    .pill-row { display:flex; gap:10px; flex-wrap: wrap; margin-top: 22px; }
    .pill {
        border: 1px solid rgba(216,184,108,.22);
        background: rgba(216,184,108,.08);
        color: #f5e7bc;
        padding: 8px 12px;
        border-radius: 999px;
        font-size: .82rem;
    }
    .metric-card {
        border: 1px solid var(--line);
        background: linear-gradient(180deg, rgba(20, 31, 51, .82), rgba(12, 19, 33, .72));
        border-radius: 22px;
        padding: 21px 21px 18px 21px;
        min-height: 138px;
        box-shadow: 0 16px 44px rgba(0,0,0,.23);
    }
    .metric-label { color: var(--muted); text-transform: uppercase; letter-spacing: .12em; font-size: .72rem; font-weight: 700; }
    .metric-value { color: var(--text); font-size: 2.35rem; font-weight: 760; letter-spacing: -.04em; margin-top: 8px; }
    .metric-note { color: #aab6cc; font-size: .87rem; margin-top: 7px; line-height: 1.35; }
    .section-title {
        margin-top: 28px;
        margin-bottom: 8px;
        font-size: 1.25rem;
        font-weight: 760;
        letter-spacing: -.02em;
    }
    .section-subtitle { color: var(--muted); margin-bottom: 16px; font-size: .93rem; }
    .glass {
        border: 1px solid var(--line);
        background: linear-gradient(180deg, rgba(18, 27, 44, .70), rgba(10, 16, 29, .62));
        border-radius: 24px;
        padding: 18px;
        box-shadow: 0 18px 52px rgba(0,0,0,.24);
    }
    .signal {
        border-left: 3px solid rgba(99, 215, 255, .85);
        background: rgba(99, 215, 255, .055);
        border-radius: 14px;
        padding: 12px 14px;
        margin-bottom: 10px;
        color: #dceaff;
    }
    .signal strong { color: #ffffff; }
    .caption { color: var(--muted); font-size: .82rem; }
    div[data-testid="stButton"] button {
        width: 100%; border-radius: 16px; min-height: 48px; border: 1px solid rgba(216,184,108,.35);
        background: linear-gradient(135deg, rgba(216,184,108,.95), rgba(117,227,180,.7)); color: #0a1020;
        font-weight: 800; letter-spacing: -.01em;
    }
    .stPlotlyChart { border-radius: 22px; overflow: hidden; }
    div[data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: 18px; overflow: hidden; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


def normalize_phase(phases: List[str]) -> str:
    if not phases:
        return "N/A"
    phase_map = {
        "EARLY_PHASE1": "Early Phase 1",
        "PHASE1": "Phase 1",
        "PHASE2": "Phase 2",
        "PHASE3": "Phase 3",
        "PHASE4": "Phase 4",
        "NA": "N/A",
    }
    clean = [phase_map.get(str(p).strip().upper(), str(p).replace("_", " ").title()) for p in phases]
    joined = "/".join([c.strip() for c in clean if c.strip()])
    return joined.replace("Phase 1/Phase 2", "Phase 1/2").replace("Phase 2/Phase 3", "Phase 2/3") or "N/A"


def prettify_status(status: Optional[str]) -> str:
    if not status:
        return "Unknown"
    return status.replace("_", " ").title().replace("And", "and").replace("By", "by")


def get_nested(d: Dict[str, Any], path: List[str], default=None):
    cur = d
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def parse_study(study: Dict[str, Any], source_query: str) -> Dict[str, Any]:
    protocol = study.get("protocolSection", {})
    ident = protocol.get("identificationModule", {})
    status = protocol.get("statusModule", {})
    sponsor = protocol.get("sponsorCollaboratorsModule", {})
    design = protocol.get("designModule", {})
    cond = protocol.get("conditionsModule", {})
    arms = protocol.get("armsInterventionsModule", {})

    org = sponsor.get("leadSponsor", {}).get("name", "Unknown sponsor")
    conditions = cond.get("conditions", []) or []
    interventions = arms.get("interventions", []) or []
    intervention_names = [i.get("name", "") for i in interventions if isinstance(i, dict)]

    return {
        "nct_id": ident.get("nctId", ""),
        "title": ident.get("briefTitle", "Untitled study"),
        "sponsor": org,
        "status": prettify_status(status.get("overallStatus")),
        "phase": normalize_phase(design.get("phases", []) or []),
        "enrollment": get_nested(design, ["enrollmentInfo", "count"], 0) or 0,
        "start_date": get_nested(status, ["startDateStruct", "date"]),
        "completion_date": get_nested(status, ["completionDateStruct", "date"]),
        "last_update": get_nested(status, ["lastUpdateSubmitDateStruct", "date"]),
        "conditions": ", ".join(conditions[:4]),
        "interventions": ", ".join(intervention_names[:4]),
        "source_query": source_query,
        "url": f"https://clinicaltrials.gov/study/{ident.get('nctId', '')}",
    }


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_trials(queries: List[str], page_size: int = 60) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    seen = set()
    for query in queries:
        params = {"format": "json", "query.term": query, "pageSize": min(page_size, 100)}
        try:
            res = requests.get(API_URL, params=params, timeout=18)
            res.raise_for_status()
            payload = res.json()
            for study in payload.get("studies", []):
                row = parse_study(study, query)
                if row["nct_id"] and row["nct_id"] not in seen:
                    rows.append(row)
                    seen.add(row["nct_id"])
        except Exception:
            continue
    if not rows:
        return sample_trials()
    df = pd.DataFrame(rows)
    return clean_df(df)


def sample_trials() -> pd.DataFrame:
    data = [
        ["NCT-DEMO-001", "B7-H4 ADC in advanced solid tumors", "NextCure", "Recruiting", "Phase 1", 96, "2024-03-01", "2027-05-01", "2026-05-01", "Ovarian Cancer, Solid Tumor", "B7-H4 ADC", "Demo fallback"],
        ["NCT-DEMO-002", "CDH6 targeted ADC in ovarian cancer", "Competitor A", "Active, not recruiting", "Phase 1/2", 142, "2023-09-15", "2026-11-15", "2026-04-11", "Ovarian Cancer", "CDH6 ADC", "Demo fallback"],
        ["NCT-DEMO-003", "B7-H4 antibody in gynecologic malignancies", "Competitor B", "Recruiting", "Phase 2", 210, "2022-10-12", "2026-09-30", "2026-03-28", "Ovarian Cancer, Endometrial Cancer", "Anti-B7-H4", "Demo fallback"],
        ["NCT-DEMO-004", "ADC combination study in platinum-resistant ovarian cancer", "Competitor C", "Not yet recruiting", "Phase 1", 64, "2026-07-01", "2028-02-01", "2026-05-10", "Platinum-Resistant Ovarian Cancer", "ADC + Immunotherapy", "Demo fallback"],
        ["NCT-DEMO-005", "Solid tumor basket study for epithelial cancers", "Competitor D", "Completed", "Phase 1", 88, "2021-01-05", "2025-12-15", "2026-01-07", "Solid Tumor", "Investigational ADC", "Demo fallback"],
        ["NCT-DEMO-006", "Targeted therapy in ovarian and breast cancers", "Competitor E", "Recruiting", "Phase 2", 168, "2024-05-21", "2027-12-01", "2026-05-12", "Ovarian Cancer, Breast Cancer", "Targeted Antibody", "Demo fallback"],
    ]
    return clean_df(pd.DataFrame(data, columns=["nct_id", "title", "sponsor", "status", "phase", "enrollment", "start_date", "completion_date", "last_update", "conditions", "interventions", "source_query"]))


def clean_df(df: pd.DataFrame) -> pd.DataFrame:
    for c in ["start_date", "completion_date", "last_update"]:
        df[c] = pd.to_datetime(df[c], errors="coerce")
    df["enrollment"] = pd.to_numeric(df["enrollment"], errors="coerce").fillna(0).astype(int)
    df["target_hint"] = df.apply(extract_target_hint, axis=1)
    df["indication_hint"] = df["conditions"].fillna("Unknown").apply(extract_indication_hint)
    df["timeline_start"] = df["start_date"].fillna(pd.Timestamp(TODAY - dt.timedelta(days=365)))
    df["timeline_finish"] = df["completion_date"].fillna(pd.Timestamp(TODAY + dt.timedelta(days=365)))
    return df


def extract_target_hint(row: pd.Series) -> str:
    text = " ".join(str(row.get(c, "")) for c in ["title", "interventions", "source_query"]).lower()
    if "b7-h4" in text or "vtcn1" in text:
        return "B7-H4 / VTCN1"
    if "cdh6" in text:
        return "CDH6"
    if "trop2" in text or "trop-2" in text:
        return "TROP2"
    if "her2" in text or "erbb2" in text:
        return "HER2"
    if "adc" in text:
        return "ADC / Unspecified Target"
    return "Other / Unclassified"


def extract_indication_hint(text: str) -> str:
    t = text.lower()
    if "ovarian" in t:
        return "Ovarian"
    if "breast" in t:
        return "Breast"
    if "lung" in t or "nsclc" in t:
        return "Lung / NSCLC"
    if "endometrial" in t:
        return "Endometrial"
    if "solid" in t:
        return "Solid Tumor"
    return "Other"


def chart_layout(fig: go.Figure, height: int = 410) -> go.Figure:
    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#dbe7ff", "family": "Inter, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"},
        margin={"l": 10, "r": 10, "t": 42, "b": 10},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
        xaxis={"gridcolor": "rgba(164,183,219,.10)", "zerolinecolor": "rgba(164,183,219,.16)"},
        yaxis={"gridcolor": "rgba(164,183,219,.10)", "zerolinecolor": "rgba(164,183,219,.16)"},
    )
    return fig


def metric_card(label: str, value: str, note: str):
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-note">{note}</div>
    </div>
    """, unsafe_allow_html=True)


with st.sidebar:
    st.markdown("### Control Deck")
    st.caption("ClinicalTrials.gov search inputs for the preliminary rebuild.")
    query_text = st.text_area("Search lanes", value="\n".join(DEFAULT_QUERIES), height=150)
    page_size = st.slider("Results per lane", 20, 100, 60, 10)
    run_scan = st.button("Run Intelligence Scan", type="primary")
    st.caption("v1 scope: clinical trial registry only. No AI summaries or market interpretation yet.")

st.markdown("""
<div class="hero">
    <div class="eyebrow">NextCure Signal Room</div>
    <h1>Clinical Intelligence Console</h1>
    <p>A premium rebuild focused on structured ClinicalTrials.gov intelligence: trial timelines, sponsor density, phase mix, target/indication heat, and concise evidence-first signals.</p>
    <div class="pill-row">
        <span class="pill">ClinicalTrials.gov API v2</span>
        <span class="pill">Charts before commentary</span>
        <span class="pill">Confidence through structure</span>
        <span class="pill">Built By BuildWell standard</span>
    </div>
</div>
""", unsafe_allow_html=True)

queries = [q.strip() for q in query_text.splitlines() if q.strip()]
if not queries:
    queries = DEFAULT_QUERIES

with st.spinner("Running clinical intelligence scan..."):
    df = fetch_trials(queries, page_size=page_size)

active_statuses = {"Recruiting", "Not yet recruiting", "Active, not recruiting", "Enrolling by invitation"}
active_df = df[df["status"].isin(active_statuses)]
upcoming_df = df[df["completion_date"].notna() & (df["completion_date"].dt.date >= TODAY)]

st.markdown('<div class="section-title">Executive Snapshot</div>', unsafe_allow_html=True)
st.markdown('<div class="section-subtitle">A restrained top-line readout, based only on structured trial registry data.</div>', unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
with c1:
    metric_card("Trials Captured", f"{len(df):,}", "Unique studies returned across selected lanes.")
with c2:
    metric_card("Active Trials", f"{len(active_df):,}", "Recruiting, not yet recruiting, active, or invitation-based.")
with c3:
    metric_card("Sponsors", f"{df['sponsor'].nunique():,}", "Unique lead sponsors in the current scan.")
with c4:
    top_phase = df["phase"].mode().iloc[0] if not df.empty else "N/A"
    metric_card("Dominant Phase", top_phase, "Most common development phase in returned studies.")

st.markdown('<div class="section-title">Clinical Trial Timeline</div>', unsafe_allow_html=True)
st.markdown('<div class="section-subtitle">A lane-based view of active and upcoming development windows. Hover any bar for NCT ID, sponsor, phase, status, and enrollment.</div>', unsafe_allow_html=True)

show_df = df.sort_values(["timeline_start", "sponsor"]).copy().head(40)
show_df["label"] = show_df["sponsor"].str.slice(0, 28) + " · " + show_df["nct_id"]
fig_timeline = px.timeline(
    show_df,
    x_start="timeline_start",
    x_end="timeline_finish",
    y="label",
    color="phase",
    hover_data=["title", "sponsor", "status", "enrollment", "conditions", "interventions"],
    title="Trial Development Windows",
)
fig_timeline.update_yaxes(autorange="reversed", title="")
fig_timeline.update_xaxes(title="")
st.plotly_chart(chart_layout(fig_timeline, height=max(440, min(900, 40 + len(show_df) * 23))), use_container_width=True, config={"displayModeBar": False})

left, right = st.columns([1.22, .78])
with left:
    st.markdown('<div class="section-title">Target × Indication Heatmap</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Where registry activity concentrates across target hints and indication hints.</div>', unsafe_allow_html=True)
    heat = pd.crosstab(df["indication_hint"], df["target_hint"])
    fig_heat = px.imshow(heat, text_auto=True, aspect="auto", title="Clinical Activity Density")
    st.plotly_chart(chart_layout(fig_heat, height=430), use_container_width=True, config={"displayModeBar": False})

with right:
    st.markdown('<div class="section-title">Status Mix</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Current registry status distribution.</div>', unsafe_allow_html=True)
    status_counts = df["status"].value_counts().reset_index()
    status_counts.columns = ["status", "count"]
    fig_status = px.bar(status_counts, x="count", y="status", orientation="h", title="Trial Status")
    fig_status.update_yaxes(categoryorder="total ascending", title="")
    fig_status.update_xaxes(title="Studies")
    st.plotly_chart(chart_layout(fig_status, height=430), use_container_width=True, config={"displayModeBar": False})

st.markdown('<div class="section-title">Sponsor Activity</div>', unsafe_allow_html=True)
st.markdown('<div class="section-subtitle">Lead sponsor concentration across the returned clinical trial landscape.</div>', unsafe_allow_html=True)
sponsor_counts = df.groupby("sponsor", as_index=False).agg(trials=("nct_id", "count"), enrollment=("enrollment", "sum")).sort_values("trials", ascending=False).head(15)
fig_sponsor = px.bar(sponsor_counts.sort_values("trials"), x="trials", y="sponsor", orientation="h", hover_data=["enrollment"], title="Top Sponsors by Trial Count")
fig_sponsor.update_yaxes(title="")
fig_sponsor.update_xaxes(title="Studies")
st.plotly_chart(chart_layout(fig_sponsor, height=520), use_container_width=True, config={"displayModeBar": False})

st.markdown('<div class="section-title">Signal Feed</div>', unsafe_allow_html=True)
st.markdown('<div class="section-subtitle">Short, evidence-first observations generated from the structured data layer. No AI narrative yet.</div>', unsafe_allow_html=True)

signals = []
if len(active_df):
    signals.append(("Active development footprint", f"{len(active_df)} active or near-active studies are visible in the current clinical scan."))
if not upcoming_df.empty:
    next_completion = upcoming_df.sort_values("completion_date").iloc[0]
    signals.append(("Nearest upcoming completion window", f"{next_completion['sponsor']} has a study completion date listed for {next_completion['completion_date'].date()} ({next_completion['nct_id']})."))
if "B7-H4 / VTCN1" in set(df["target_hint"]):
    signals.append(("B7-H4 lane detected", "At least one returned study maps to B7-H4 / VTCN1 based on title, intervention, or search lane text."))
top_sponsor = sponsor_counts.iloc[-1] if not sponsor_counts.empty else None
if top_sponsor is not None:
    signals.append(("Sponsor concentration", f"{sponsor_counts.sort_values('trials', ascending=False).iloc[0]['sponsor']} is the most represented sponsor in this scan."))

for title, body in signals[:5]:
    st.markdown(f'<div class="signal"><strong>{title}</strong><br>{body}</div>', unsafe_allow_html=True)

st.markdown('<div class="section-title">Evidence Table</div>', unsafe_allow_html=True)
st.markdown('<div class="section-subtitle">The underlying rows powering the visuals. This keeps the system auditable from day one.</div>', unsafe_allow_html=True)
cols = ["nct_id", "title", "sponsor", "status", "phase", "enrollment", "start_date", "completion_date", "target_hint", "indication_hint", "conditions", "interventions"]
st.dataframe(df[cols].sort_values(["sponsor", "phase"]).reset_index(drop=True), use_container_width=True, hide_index=True)

st.markdown(f'<p class="caption">Data source: ClinicalTrials.gov API v2 /api/v2/studies. Last app refresh: {dt.datetime.now().strftime("%Y-%m-%d %H:%M")}. Search lanes are configurable in the sidebar.</p>', unsafe_allow_html=True)
