from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from pypdf import PdfReader

from src.nlp_pipeline import analyze, keywords, load_documents, similar_documents

st.set_page_config(page_title="ChipIntel NLP", page_icon="◈", layout="wide")
DATA_PATH = Path(__file__).parent / "data" / "sample_documents.csv"

@st.cache_data
def get_sample_data():
    return analyze(load_documents(DATA_PATH))

def parse_upload(uploaded_file):
    suffix = Path(uploaded_file.name).suffix.lower()
    if suffix == ".csv":
        return analyze(pd.read_csv(uploaded_file))
    if suffix == ".pdf":
        text = "\n".join(page.extract_text() or "" for page in PdfReader(uploaded_file).pages)
    else:
        text = uploaded_file.getvalue().decode("utf-8", errors="ignore")
    return analyze(pd.DataFrame([{"company": "Uploaded", "document_type": suffix[1:] or "text", "period": "Custom", "text": text}]))

st.title("◈ ChipIntel NLP")
st.caption("NVIDIA · AMD · Broadcom · TSMC · Micron · ASML — earnings call & annual report intelligence")

with st.sidebar:
    st.header("Controls")
    uploaded = st.file_uploader("Upload CSV, PDF, or TXT", type=["csv", "pdf", "txt"])
    data = parse_upload(uploaded) if uploaded else get_sample_data()
    companies = st.multiselect("Companies", sorted(data.company.unique()), default=sorted(data.company.unique()))
    doc_types = st.multiselect("Document type", sorted(data.document_type.unique()), default=sorted(data.document_type.unique()))
    filtered = data[data.company.isin(companies) & data.document_type.isin(doc_types)]

if filtered.empty:
    st.warning("Select at least one company and document type.")
    st.stop()

tab1, tab2, tab3 = st.tabs(["Overview", "Company comparison", "Document search"])

with tab1:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Documents", len(filtered))
    c2.metric("Companies", filtered.company.nunique())
    c3.metric("Avg. sentiment", f"{filtered.sentiment_score.mean():+.2f}")
    c4.metric("Topics detected", filtered.topic.nunique())
    left, right = st.columns(2)
    with left:
        st.subheader("Topic distribution")
        topic_counts = filtered.topic.value_counts().rename_axis("topic").reset_index(name="documents")
        st.plotly_chart(px.bar(topic_counts, x="documents", y="topic", orientation="h", color="documents"), use_container_width=True)
    with right:
        st.subheader("Sentiment by company")
        sent = filtered.groupby(["company", "sentiment"], as_index=False).size()
        st.plotly_chart(px.bar(sent, x="company", y="size", color="sentiment", barmode="group"), use_container_width=True)
    st.subheader("Most important terms")
    st.dataframe(pd.DataFrame(keywords(filtered.text.tolist()), columns=["term", "tfidf_score"]), use_container_width=True, hide_index=True)

with tab2:
    st.subheader("Company-level comparison")
    summary = filtered.groupby("company").agg(documents=("text", "size"), avg_sentiment=("sentiment_score", "mean"), dominant_topic=("topic", lambda x: x.mode().iat[0])).reset_index()
    summary["avg_sentiment"] = summary["avg_sentiment"].round(3)
    st.dataframe(summary, use_container_width=True, hide_index=True)
    pivot = filtered.pivot_table(index="company", columns="topic", values="text", aggfunc="count", fill_value=0)
    st.plotly_chart(px.imshow(pivot, text_auto=True, aspect="auto", color_continuous_scale="Blues", title="Topic footprint by company"), use_container_width=True)
    st.download_button("Download analyzed data", filtered.to_csv(index=False), "chipintel_analysis.csv", "text/csv")

with tab3:
    st.subheader("Semantic document search")
    query = st.text_input("Search for a theme", "AI data center supply chain risk")
    for _, row in similar_documents(filtered, query).iterrows():
        with st.expander(f"{row.company} · {row.document_type} · {row.period} · similarity {row.similarity:.2f}"):
            st.write(row.text)
            st.caption(f"Topic: {row.topic}  |  Sentiment: {row.sentiment} ({row.sentiment_score:+.2f})")

st.divider()
st.caption("Demo corpus is illustrative. Replace it with licensed or publicly available documents for research use.")

