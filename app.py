import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="FBM Lost — BRSP06", layout="wide", page_icon="🔵")

CSV_URL = "https://raw.githubusercontent.com/ViniciusVauna/ARQUIVOSLP/main/data.csv"

@st.cache_data(ttl=600, show_spinner=False)
def load_data():
    df = pd.read_csv(CSV_URL)
    df['PENDING_USD'] = pd.to_numeric(df['PENDING_USD'].astype(str).str.replace(',','.'), errors='coerce').fillna(0)
    df['AGING'] = pd.to_numeric(df['AGING'], errors='coerce').fillna(0).astype(int)
    for col in ['STATUS_BUSCA_ORIGEN','STATUS_REVISAO_ORIGEN','WEEK_DUE_DATE',
                'WEEK_CREATED','STATUS_FINAL','VERTICAL','ZONA','FBM_PROCCESS_NAME']:
        if col in df.columns:
            df[col] = df[col].fillna('').astype(str).str.strip()
    return df

FOUND_SET = {'Found Inv.', 'Found LP', 'Found Inv', 'Found LP.'}

def is_finalizado(row):
    b, r = row['STATUS_BUSCA_ORIGEN'], row['STATUS_REVISAO_ORIGEN']
    if b == 'DFL' and r == 'DFL': return True
    if b in FOUND_SET: return True
    if b == 'DFL' and r in FOUND_SET: return True
    return False

def pct_color(p):
    if p >= 80: return '#16a34a'
    if p >= 40: return '#d97706'
    return '#dc2626'

def chart_style(fig, height=300):
    fig.update_layout(
        height=height, margin=dict(t=10,b=10,l=10,r=30),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#111827', size=11),
        legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(color='#111827')),
    )
    fig.update_xaxes(showgrid=False, color='#6b7280')
    fig.update_yaxes(gridcolor='#f3f4f6', color='#6b7280')
    return fig

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

[data-testid="stHeader"] { display: none !important; }
.block-container { padding: 1.5rem 2rem !important; max-width: 100% !important; }
html, body, .stApp, [data-testid="stAppViewContainer"] {
    background: #ffffff !important;
    font-family: 'Inter', sans-serif !important;
    color: #111827 !important;
}

/* SIDEBAR */
[data-testid="stSidebar"] { background: #111827 !important; }
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] caption { color: #9ca3af !important; }
[data-testid="stSidebar"] div.stButton > button {
    background: transparent !important;
    color: #9ca3af !important;
    border: none !important;
    border-radius: 8px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    width: 100% !important;
    text-align: left !important;
    padding: 9px 14px !important;
    transition: all 0.15s !important;
}
[data-testid="stSidebar"] div.stButton > button:hover {
    background: rgba(255,255,255,0.06) !important;
    color: #ffffff !important;
}
[data-testid="stSidebar"] div.stButton > button[kind="primary"] {
    background: #ffe600 !important;
    color: #111827 !important;
    font-weight: 700 !important;
}

/* MÉTRICAS */
[data-testid="stMetric"] {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 16px 18px !important;
    border-top: 3px solid #ffe600;
}
[data-testid="stMetricLabel"] { color: #6b7280 !important; font-size: 11px !important; font-weight: 600 !important; text-transform: uppercase; letter-spacing: 0.5px; }
[data-testid="stMetricValue"] { color: #111827 !important; font-size: 24px !important; font-weight: 700 !important; }
[data-testid="stMetricDelta"] { font-size: 11px !important; }

/* PROGRESS */
[data-testid="stProgress"] > div > div {
    background: #ffe600 !important;
    border-radius: 4px !important;
}
[data-testid="stProgress"] > div {
    background: #f3f4f6 !important;
    border-radius: 4px !important;
    height: 8px !important;
}

/* DIVIDER */
hr { border-color: #f3f4f6 !important; }

/* CAPTION */
.stCaption { color: #6b7280 !important; font-size: 11px !important; text-transform: uppercase; letter-spacing: 0.8px; }

/* SUCCESS / INFO */
[data-testid="stAlert"] { border-radius: 8px !important; }

/* DATAFRAME */
[data-testid="stDataFrame"] { border: 1px solid #e5e7eb; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# ── SESSION STATE ──────────────────────────────────────────────────────────────
if 'page' not in st.session_state:
    st.session_state.page = 'semana'

# ── SIDEBAR ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://http2.mlstatic.com/frontend-assets/ui-navigation/5.21.3/mercadolibre/logo__large_plus.png", width=130)
    st.markdown("---")
    st.markdown("<p style='color:#4b5563;font-size:10px;letter-spacing:2px;text-transform:uppercase;padding:0 4px;margin-bottom:6px'>FBM LOST</p>", unsafe_allow_html=True)

    pages = [
        ('semana',   '📅', 'Semana atual'),
        ('proximas', '📊', 'Próximas semanas'),
        ('evolucao', '📈', 'Evolução semanal'),
        ('detalhe',  '🗂️', 'Detalhamento'),
    ]
    for key, icon, label in pages:
        t = "primary" if st.session_state.page == key else "secondary"
        if st.button(f"{icon}  {label}", key=f"nav_{key}", use_container_width=True, type=t):
            st.session_state.page = key
            st.rerun()

    st.markdown("---")
    st.caption(f"🟡 Auto-atualização 8h e 14h")
    st.caption(f"BRSP06 · {datetime.now().strftime('%d/%m/%Y %H:%M')}")

# ── LOAD ───────────────────────────────────────────────────────────────────────
with st.spinner("Carregando dados..."):
    try:
        df = load_data()
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        st.stop()

valid_weeks = sorted([w for w in df["WEEK_DUE_DATE"].unique()
                      if w and w != "Sem previsão" and "-" in w])

# Semana atual baseada no calendário real de hoje
def get_current_week_label():
    today = datetime.now()
    week_num = today.isocalendar()[1]
    year = today.year
    return f"W{str(week_num).zfill(2)}-{year}"

today_week = get_current_week_label()

# Pega semanas a partir da semana atual
future_weeks = [w for w in valid_weeks if w >= today_week]
if not future_weeks:
    future_weeks = valid_weeks

NEXT_4 = future_weeks[:4]
CUR    = future_weeks[0] if future_weeks else (valid_weeks[0] if valid_weeks else "")

# ── HEADER ─────────────────────────────────────────────────────────────────────
c1, c2 = st.columns([7, 2])
with c1:
    st.markdown("<h2 style='color:#111827;margin:0;font-weight:700'>CORE <span style='color:#ffe600'>|</span> FBM LOST — BRSP06</h2>", unsafe_allow_html=True)
with c2:
    st.markdown(f"<div style='background:#ffe600;color:#111827;font-weight:700;font-size:12px;padding:8px 16px;border-radius:8px;text-align:center;margin-top:4px'>🟢 Live · GitHub</div>", unsafe_allow_html=True)
st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: SEMANA ATUAL
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.page == 'semana':
    st.markdown(f"<p style='color:#6b7280;font-size:12px;text-transform:uppercase;letter-spacing:1px;font-weight:600'>Semana atual — {CUR} · due date</p>", unsafe_allow_html=True)

    df_cur = df[df['WEEK_DUE_DATE'] == CUR].copy()
    df_cur['fin'] = df_cur.apply(is_finalizado, axis=1)
    df_cur['rec'] = df_cur.apply(lambda r: r['PENDING_USD'] if (
        r['STATUS_BUSCA_ORIGEN'] in FOUND_SET or r['STATUS_REVISAO_ORIGEN'] in FOUND_SET) else 0, axis=1)

    total     = len(df_cur)
    usd_total = df_cur['PENDING_USD'].sum()
    usd_rec   = df_cur['rec'].sum()
    usd_pend  = df_cur[~df_cur['fin']]['PENDING_USD'].sum()
    n_fin     = int(df_cur['fin'].sum())
    pct_fin   = round(n_fin/total*100,1) if total else 0
    n_pb      = int((df_cur['STATUS_BUSCA_ORIGEN']=='').sum())
    n_pr      = int((df_cur['STATUS_REVISAO_ORIGEN']=='').sum())
    pct_b     = round((total-n_pb)/total*100,1) if total else 0
    pct_r     = round((total-n_pr)/total*100,1) if total else 0

    k1,k2,k3,k4,k5 = st.columns(5)
    k1.metric("Total issues", f"{total:,}", "due esta semana")
    k2.metric("USD total", f"${usd_total:,.0f}")
    k3.metric("USD pendente", f"${usd_pend:,.0f}", f"{total-n_fin} em aberto", delta_color="inverse")
    k4.metric("USD recuperado", f"${usd_rec:,.0f}", "Found Inv./LP")
    k5.metric("% Conclusão", f"{pct_fin}%", f"{n_fin} de {total}")

    st.divider()

    col_b, col_r = st.columns(2)
    with col_b:
        st.markdown("<p style='font-weight:600;color:#111827;font-size:14px;margin-bottom:8px'>Processo de Busca</p>", unsafe_allow_html=True)
        cb = pct_color(pct_b)
        st.markdown(f"<p style='font-size:32px;font-weight:700;color:{cb};margin:0'>{pct_b}%</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size:12px;color:#6b7280;margin:4px 0 8px'>{total-n_pb:,} concluídas · <span style='color:#dc2626;font-weight:600'>{n_pb:,} faltam</span></p>", unsafe_allow_html=True)
        st.progress(pct_b/100)
        if n_pb > 0:
            st.markdown("<p style='color:#6b7280;font-size:11px;text-transform:uppercase;letter-spacing:0.8px;margin:14px 0 6px'>Pendentes por processo</p>", unsafe_allow_html=True)
            df_pb = df_cur[df_cur['STATUS_BUSCA_ORIGEN']=='']['FBM_PROCCESS_NAME'].value_counts().head(5).reset_index()
            df_pb.columns = ['Processo','Qtd']
            fig = go.Figure(go.Bar(x=df_pb['Qtd'], y=df_pb['Processo'], orientation='h',
                marker_color='#1d4ed8', text=df_pb['Qtd'], textposition='outside',
                textfont=dict(color='#111827')))
            st.plotly_chart(chart_style(fig, 200), use_container_width=True)

    with col_r:
        st.markdown("<p style='font-weight:600;color:#111827;font-size:14px;margin-bottom:8px'>Processo de Revisão</p>", unsafe_allow_html=True)
        cr = pct_color(pct_r)
        st.markdown(f"<p style='font-size:32px;font-weight:700;color:{cr};margin:0'>{pct_r}%</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size:12px;color:#6b7280;margin:4px 0 8px'>{total-n_pr:,} concluídas · <span style='color:#dc2626;font-weight:600'>{n_pr:,} faltam</span></p>", unsafe_allow_html=True)
        st.progress(pct_r/100)
        if n_pr > 0:
            st.markdown("<p style='color:#6b7280;font-size:11px;text-transform:uppercase;letter-spacing:0.8px;margin:14px 0 6px'>Pendentes por processo</p>", unsafe_allow_html=True)
            df_pr = df_cur[df_cur['STATUS_REVISAO_ORIGEN']=='']['FBM_PROCCESS_NAME'].value_counts().head(5).reset_index()
            df_pr.columns = ['Processo','Qtd']
            fig = go.Figure(go.Bar(x=df_pr['Qtd'], y=df_pr['Processo'], orientation='h',
                marker_color='#2563eb', text=df_pr['Qtd'], textposition='outside',
                textfont=dict(color='#111827')))
            st.plotly_chart(chart_style(fig, 200), use_container_width=True)

    st.divider()
    col_f, col_u = st.columns(2)
    with col_f:
        st.markdown("<p style='font-weight:600;color:#111827;font-size:14px;margin-bottom:4px'>Finalizados por critério</p>", unsafe_allow_html=True)
        dfl_dfl   = len(df_cur[(df_cur['STATUS_BUSCA_ORIGEN']=='DFL')&(df_cur['STATUS_REVISAO_ORIGEN']=='DFL')])
        found_b   = len(df_cur[df_cur['STATUS_BUSCA_ORIGEN'].isin(FOUND_SET)&~df_cur['STATUS_REVISAO_ORIGEN'].isin(FOUND_SET)])
        dfl_found = len(df_cur[(df_cur['STATUS_BUSCA_ORIGEN']=='DFL')&df_cur['STATUS_REVISAO_ORIGEN'].isin(FOUND_SET)])
        found_both= len(df_cur[df_cur['STATUS_BUSCA_ORIGEN'].isin(FOUND_SET)&df_cur['STATUS_REVISAO_ORIGEM'].isin(FOUND_SET)] if 'STATUS_REVISAO_ORIGEN' in df_cur.columns else [])
        fig = go.Figure(go.Bar(
            x=['DFL+DFL','Found busca','DFL+Found rev.','Found+Found'],
            y=[dfl_dfl,found_b,dfl_found,found_both],
            marker_color=['#ffe600','#fbbf24','#f59e0b','#d97706'],
            text=[dfl_dfl,found_b,dfl_found,found_both], textposition='outside',
            textfont=dict(color='#111827')))
        st.plotly_chart(chart_style(fig,260), use_container_width=True)

    with col_u:
        st.markdown("<p style='font-weight:600;color:#111827;font-size:14px;margin-bottom:4px'>USD — Total · Pendente · Recuperado</p>", unsafe_allow_html=True)
        fig = go.Figure(go.Bar(
            x=['Total','Pendente','Finalizado','Recuperado'],
            y=[usd_total,usd_pend,usd_total-usd_pend,usd_rec],
            marker_color=['#1d4ed8','#dc2626','#93c5fd','#16a34a'],
            text=[f'${v:,.0f}' for v in [usd_total,usd_pend,usd_total-usd_pend,usd_rec]],
            textposition='outside', textfont=dict(color='#111827')))
        st.plotly_chart(chart_style(fig,260), use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: PRÓXIMAS SEMANAS
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == 'proximas':
    st.markdown("<p style='color:#6b7280;font-size:12px;text-transform:uppercase;letter-spacing:1px;font-weight:600'>Semana atual + próximas 3 · progresso de busca & revisão</p>", unsafe_allow_html=True)

    df_4  = df[df['WEEK_DUE_DATE'].isin(NEXT_4)]
    tot4  = len(df_4)
    usd4  = df_4['PENDING_USD'].sum()
    pb4   = (df_4['STATUS_BUSCA_ORIGEN']=='').sum()
    rec4  = df_4[df_4['STATUS_BUSCA_ORIGEN'].isin(FOUND_SET)|df_4['STATUS_REVISAO_ORIGEN'].isin(FOUND_SET)]['PENDING_USD'].sum()

    k1,k2,k3,k4 = st.columns(4)
    k1.metric("Total 4 semanas", f"{tot4:,}")
    k2.metric("USD total", f"${usd4:,.0f}")
    k3.metric("Pend. busca", f"{pb4:,}", f"{round(pb4/tot4*100) if tot4 else 0}% sem busca", delta_color="inverse")
    k4.metric("USD recuperado", f"${rec4:,.0f}")

    st.divider()
    cols = st.columns(len(NEXT_4))
    for i, week in enumerate(NEXT_4):
        df_w  = df[df['WEEK_DUE_DATE']==week]
        total = len(df_w)
        if total == 0: continue
        usd   = df_w['PENDING_USD'].sum()
        pb    = int((df_w['STATUS_BUSCA_ORIGEN']=='').sum())
        pr    = int((df_w['STATUS_REVISAO_ORIGEN']=='').sum())
        avg_a = df_w['AGING'].mean()
        rec   = df_w[df_w['STATUS_BUSCA_ORIGEN'].isin(FOUND_SET)|df_w['STATUS_REVISAO_ORIGEN'].isin(FOUND_SET)]['PENDING_USD'].sum()
        pct_b = round((total-pb)/total*100,1)
        pct_r = round((total-pr)/total*100,1)
        cb, cr = pct_color(pct_b), pct_color(pct_r)
        border = "border:2px solid #ffe600;background:#fffbeb;" if week==CUR else "border:1px solid #e5e7eb;background:#ffffff;"

        with cols[i]:
            badge = "<span style='background:#ffe600;color:#111827;font-size:9px;font-weight:700;padding:2px 8px;border-radius:20px;margin-left:6px'>ATUAL</span>" if week==CUR else ""
            st.markdown(f"""
            <div style='{border}border-radius:14px;padding:18px;margin-bottom:8px'>
                <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:12px'>
                    <span style='font-family:monospace;font-size:13px;font-weight:700;color:#111827'>{week}</span>{badge}
                </div>
                <div style='font-size:26px;font-weight:800;color:#111827'>{total:,}</div>
                <div style='font-size:11px;color:#6b7280;font-family:monospace'>${usd:,.0f} · {avg_a:.1f}d aging</div>
                <hr style='border-color:#f3f4f6;margin:12px 0'>
                <div style='font-size:10px;text-transform:uppercase;letter-spacing:1px;color:#9ca3af;margin-bottom:6px'>Busca</div>
                <div style='display:flex;justify-content:space-between;margin-bottom:4px'>
                    <span style='font-size:18px;font-weight:700;color:{cb}'>{pct_b}%</span>
                    <span style='font-size:11px;color:#dc2626;font-weight:600'>{pb} faltam</span>
                </div>
                <div style='height:6px;background:#f3f4f6;border-radius:3px;overflow:hidden;margin-bottom:12px'>
                    <div style='height:100%;width:{pct_b}%;background:{cb};border-radius:3px'></div>
                </div>
                <div style='font-size:10px;text-transform:uppercase;letter-spacing:1px;color:#9ca3af;margin-bottom:6px'>Revisão</div>
                <div style='display:flex;justify-content:space-between;margin-bottom:4px'>
                    <span style='font-size:18px;font-weight:700;color:{cr}'>{pct_r}%</span>
                    <span style='font-size:11px;color:#dc2626;font-weight:600'>{pr} faltam</span>
                </div>
                <div style='height:6px;background:#f3f4f6;border-radius:3px;overflow:hidden;margin-bottom:10px'>
                    <div style='height:100%;width:{pct_r}%;background:{cr};border-radius:3px'></div>
                </div>
                {"<div style='font-size:11px;color:#16a34a;font-weight:600'>💰 $"+f"{rec:,.0f} recuperado</div>" if rec>0 else ""}
            </div>""", unsafe_allow_html=True)

    st.divider()
    st.markdown("<p style='font-weight:600;color:#111827;font-size:14px'>Pendente Busca & Revisão por semana</p>", unsafe_allow_html=True)
    df_bar = pd.DataFrame([{
        'Semana': w.replace('-2026',''),
        'Pendente Busca': int((df[df['WEEK_DUE_DATE']==w]['STATUS_BUSCA_ORIGEN']=='').sum()),
        'Pendente Revisão': int((df[df['WEEK_DUE_DATE']==w]['STATUS_REVISAO_ORIGEN']=='').sum()),
    } for w in NEXT_4])
    fig = go.Figure()
    fig.add_trace(go.Bar(name='Pendente Busca', y=df_bar['Semana'], x=df_bar['Pendente Busca'],
        orientation='h', marker_color='#111827', text=df_bar['Pendente Busca'],
        textposition='outside', textfont=dict(color='#111827')))
    fig.add_trace(go.Bar(name='Pendente Revisão', y=df_bar['Semana'], x=df_bar['Pendente Revisão'],
        orientation='h', marker_color='#ffe600', text=df_bar['Pendente Revisão'],
        textposition='outside', textfont=dict(color='#111827')))
    fig.update_layout(barmode='group', legend=dict(orientation='h', y=1.1, font=dict(color='#111827')))
    st.plotly_chart(chart_style(fig,280), use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: EVOLUÇÃO SEMANAL
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == 'evolucao':
    st.markdown("<p style='color:#6b7280;font-size:12px;text-transform:uppercase;letter-spacing:1px;font-weight:600'>Evolução semanal · por semana de criação</p>", unsafe_allow_html=True)

    evo_weeks = sorted([w for w in df['WEEK_CREATED'].unique() if w and '-' in w])
    evo_data  = []
    for w in evo_weeks:
        dfw = df[df['WEEK_CREATED']==w]
        evo_data.append({'Semana': w.replace('-2026','').replace('-2025',''),
                         'SemFull':w, 'Total':len(dfw),
                         'Pend. Busca': int((dfw['STATUS_BUSCA_ORIGEN']=='').sum()),
                         'Pend. Revisão': int((dfw['STATUS_REVISAO_ORIGEN']=='').sum()),
                         'USD': dfw['PENDING_USD'].sum()})
    df_evo = pd.DataFrame(evo_data)
    pico   = df_evo.loc[df_evo['Total'].idxmax()] if not df_evo.empty else None

    k1,k2,k3,k4 = st.columns(4)
    k1.metric("Total issues", f"{len(df):,}")
    k2.metric("Pico semanal", f"{int(pico['Total']):,}" if pico is not None else '—',
              pico['SemFull'] if pico is not None else '')
    k3.metric("Sem status", f"{(df['STATUS_FINAL']=='Sem Status').sum():,}")
    k4.metric("USD total", f"${df['PENDING_USD'].sum():,.0f}")

    st.divider()
    st.markdown("<p style='font-weight:600;color:#111827;font-size:14px'>Pendente Busca & Revisão por semana de criação</p>", unsafe_allow_html=True)
    fig = go.Figure()
    fig.add_trace(go.Scatter(name='Pend. Busca', x=df_evo['Semana'], y=df_evo['Pend. Busca'],
        fill='tozeroy', line=dict(color='#1d4ed8',width=2), fillcolor='rgba(29,78,216,0.08)'))
    fig.add_trace(go.Scatter(name='Pend. Revisão', x=df_evo['Semana'], y=df_evo['Pend. Revisão'],
        fill='tozeroy', line=dict(color='#ffe600',width=2,dash='dot'), fillcolor='rgba(255,230,0,0.1)'))
    fig.update_layout(legend=dict(orientation='h',y=1.1,font=dict(color='#111827')))
    st.plotly_chart(chart_style(fig,280), use_container_width=True)

    st.markdown("<p style='font-weight:600;color:#111827;font-size:14px'>Volume total por semana</p>", unsafe_allow_html=True)
    last_w = df_evo['Semana'].iloc[-1] if not df_evo.empty else ''
    colors = ['#ffe600' if w==last_w else '#bfdbfe' for w in df_evo['Semana']]
    fig2 = go.Figure(go.Bar(x=df_evo['Semana'], y=df_evo['Total'], marker_color=colors,
        text=df_evo['Total'], textposition='outside', textfont=dict(color='#111827')))
    st.plotly_chart(chart_style(fig2,240), use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: DETALHAMENTO
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == 'detalhe':
    st.markdown("<p style='color:#6b7280;font-size:12px;text-transform:uppercase;letter-spacing:1px;font-weight:600'>Detalhamento · filtros combinados</p>", unsafe_allow_html=True)

    f1,f2,f3,f4 = st.columns(4)
    with f1: sel_st = st.multiselect("Status", sorted(df['STATUS_FINAL'].unique()))
    with f2: sel_vt = st.multiselect("Vertical", sorted(df['VERTICAL'].unique()))
    with f3: sel_wk = st.multiselect("Semana due", sorted([w for w in df['WEEK_DUE_DATE'].unique() if w!='Sem previsão']))
    with f4: sel_pr = st.multiselect("Processo", sorted(df['FBM_PROCCESS_NAME'].unique()))

    df_f = df.copy()
    if sel_st: df_f = df_f[df_f['STATUS_FINAL'].isin(sel_st)]
    if sel_vt: df_f = df_f[df_f['VERTICAL'].isin(sel_vt)]
    if sel_wk: df_f = df_f[df_f['WEEK_DUE_DATE'].isin(sel_wk)]
    if sel_pr: df_f = df_f[df_f['FBM_PROCCESS_NAME'].isin(sel_pr)]

    st.caption(f"{len(df_f):,} issues encontradas")
    cols_show = [c for c in ['FBM_ISSUE_ID','FBM_ISSUE_DATE_CREATED','WEEK_CREATED','WEEK_DUE_DATE',
                 'STATUS_FINAL','VERTICAL','ZONA','FBM_PROCCESS_NAME','AGING','PENDING_USD',
                 'STATUS_BUSCA_ORIGEN','STATUS_REVISAO_ORIGEN','ITEM_TITLE'] if c in df_f.columns]
    st.dataframe(df_f[cols_show].sort_values('PENDING_USD',ascending=False).reset_index(drop=True),
        use_container_width=True, hide_index=True,
        column_config={
            'PENDING_USD': st.column_config.NumberColumn("USD", format="$%.2f"),
            'AGING': st.column_config.NumberColumn("Aging (d)"),
        })
    st.download_button("⬇️ Exportar CSV",
        df_f[cols_show].to_csv(index=False).encode('utf-8'),
        "fbm_lost_brsp06.csv","text/csv")
