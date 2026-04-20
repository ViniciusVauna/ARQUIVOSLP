import streamlit as st
from google.cloud import bigquery
import pandas as pd
import json
import plotly.graph_objects as go

st.set_page_config(page_title="FBM Lost — BRSP06", layout="wide", page_icon="🔵")

@st.cache_resource
def get_client():
    try:
        creds_dict = json.loads(st.secrets["gcp_service_account"])
        from google.oauth2 import service_account
        creds = service_account.Credentials.from_service_account_info(
            creds_dict, scopes=["https://www.googleapis.com/auth/bigquery"])
        return bigquery.Client(project="meli-bi-data", credentials=creds)
    except Exception:
        return bigquery.Client(project="meli-bi-data")

QUERY = """
SELECT
    a.FBM_ISSUE_ID,
    IFNULL(
        CONCAT('W', LPAD(CAST(1 + DIV(DATE_DIFF(DATE(b.FBM_ISSUE_DUE_DATE),
            DATE(EXTRACT(YEAR FROM b.FBM_ISSUE_DUE_DATE), 1, 1), DAY), 7) AS STRING), 2, '0'),
            '-', FORMAT_DATE('%Y', DATE(b.FBM_ISSUE_DUE_DATE))),
        'Sem previsão'
    ) AS WEEK_DUE_DATE,
    a.PENDING_USD,
    a.STATUS_BUSCA_ORIGEN,
    a.STATUS_REVISAO_ORIGEN,
    a.FBM_PROCCESS_NAME
FROM `meli-bi-data.WHOWNER.DM_LP_FBM_CAZA_LOST_TABL` a
LEFT JOIN `meli-bi-data.WHOWNER.DM_LP_FBM_PENDINGS_LOST` b
    ON a.FBM_ISSUE_ID = b.FBM_ISSUE_ID
WHERE a.WAREHOUSE_ID = 'BRSP06'
  AND a.PENDING_USD > 15
  AND LOWER(a.FBM_PROCCESS_NAME) <> 'inbound'
"""

@st.cache_data(ttl=600, show_spinner=False)
def load_data():
    client = get_client()
    df = client.query(QUERY).to_dataframe()
    df['PENDING_USD']           = pd.to_numeric(df['PENDING_USD'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
    df['STATUS_BUSCA_ORIGEN']   = df['STATUS_BUSCA_ORIGEN'].fillna('').astype(str).str.strip()
    df['STATUS_REVISAO_ORIGEN'] = df['STATUS_REVISAO_ORIGEN'].fillna('').astype(str).str.strip()
    df['WEEK_DUE_DATE']         = df['WEEK_DUE_DATE'].fillna('').astype(str).str.strip()
    return df

def pct_color(p):
    if p >= 80: return 'normal'
    if p >= 40: return 'off'
    return 'inverse'

col_logo, col_title, col_status = st.columns([1, 6, 2])
with col_logo:
    st.image("https://http2.mlstatic.com/frontend-assets/ui-navigation/5.21.3/mercadolibre/logo__large_plus.png", width=120)
with col_title:
    st.markdown("### CORE | FBM LOST — BRSP06")
with col_status:
    st.success("🟢 Live · BigQuery")

st.divider()

with st.spinner("Conectando ao BigQuery..."):
    try:
        df = load_data()
    except Exception as e:
        st.error(f"Erro ao conectar: {e}")
        st.stop()

valid_weeks = sorted([w for w in df['WEEK_DUE_DATE'].unique()
                      if w and w != 'Sem previsão' and '-' in w])
NEXT_4 = valid_weeks[:4]
CUR    = valid_weeks[0] if valid_weeks else ''

st.caption("SEMANA ATUAL + PRÓXIMAS 3 · PROGRESSO DE BUSCA & REVISÃO")
st.divider()

cols = st.columns(len(NEXT_4))

for i, week in enumerate(NEXT_4):
    df_w  = df[df['WEEK_DUE_DATE'] == week]
    total = len(df_w)
    if total == 0:
        continue

    usd   = df_w['PENDING_USD'].sum()
    pb    = int((df_w['STATUS_BUSCA_ORIGEN'] == '').sum())
    pr    = int((df_w['STATUS_REVISAO_ORIGEN'] == '').sum())
    pct_b = round((total - pb) / total * 100, 1)
    pct_r = round((total - pr) / total * 100, 1)

    with cols[i]:
        if week == CUR:
            st.info(f"**{week}** · semana atual")
        else:
            st.markdown(f"**{week}**")

        m1, m2 = st.columns(2)
        m1.metric("Total issues", f"{total:,}")
        m2.metric("USD", f"${usd:,.0f}")

        st.divider()

        st.caption("BUSCA")
        st.metric("Concluídas", f"{pct_b}%",
                  delta=f"{total-pb:,} ok · {pb:,} faltam",
                  delta_color=pct_color(pct_b))
        st.progress(pct_b / 100)

        st.divider()

        st.caption("REVISÃO")
        st.metric("Concluídas", f"{pct_r}%",
                  delta=f"{total-pr:,} ok · {pr:,} faltam",
                  delta_color=pct_color(pct_r))
        st.progress(pct_r / 100)
