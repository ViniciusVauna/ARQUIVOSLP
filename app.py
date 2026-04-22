import streamlit as st
import pandas as pd
import json
import plotly.graph_objects as st_go

st.set_page_config(page_title="FBM Lost — BRSP06", layout="wide", page_icon="🔵")

# ── URL DO CSV NO GITHUB ───────────────────────────────────────────────────────
CSV_URL = "https://raw.githubusercontent.com/ViniciusVauna/ARQUIVOSLP/main/data.csv"

# ── LOAD ───────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=600, show_spinner=False)
def load_data():
    df = pd.read_csv(CSV_URL)
    df['PENDING_USD'] = pd.to_numeric(
        df['PENDING_USD'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
    df['AGING'] = pd.to_numeric(df['AGING'], errors='coerce').fillna(0).astype(int)
    for col in ['STATUS_BUSCA_ORIGEN','STATUS_REVISAO_ORIGEN','WEEK_DUE_DATE',
                'WEEK_CREATED','STATUS_FINAL','VERTICAL','ZONA','FBM_PROCCESS_NAME']:
        if col in df.columns:
            df[col] = df[col].fillna('').astype(str).str.strip()
    return df

# ── HELPERS ────────────────────────────────────────────────────────────────────
FOUND_SET = {'Found Inv.', 'Found LP', 'Found Inv', 'Found LP.'}

def is_finalizado(row):
    b, r = row['STATUS_BUSCA_ORIGEN'], row['STATUS_REVISAO_ORIGEN']
    if b == 'DFL' and r == 'DFL': return True
    if b in FOUND_SET: return True
    if b == 'DFL' and r in FOUND_SET: return True
    return False

def pct_color(p):
    if p >= 80: return '#00c853'
    if p >= 40: return '#ffd600'
    return '#ff1744'

def chart_style(fig, height=300):
    fig.update_layout(
        height=height, margin=dict(t=10, b=10, l=10, r=30),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#475569', size=11),
        legend=dict(bgcolor='rgba(0,0,0,0)'),
    )
    fig.update_xaxes(showgrid=False, color='#94a3b8')
    fig.update_yaxes(gridcolor='#f1f5f9', color='#94a3b8')
    return fig

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stHeader"] { display: none !important; }
.block-container { padding: 1.5rem 2rem !important; max-width: 100% !important; }
.stApp { background: #f4f6fb; }
[data-testid="stSidebar"] { background: #0a1628 !important; }
[data-testid="stSidebar"] div.stButton > button {
    background: transparent !important; color: #8fa9cc !important;
    border: none !important; border-radius: 8px !important;
    font-size: 13px !important; width: 100% !important; text-align: left !important;
    padding: 8px 12px !important;
}
[data-testid="stSidebar"] div.stButton > button:hover {
    background: rgba(255,255,255,0.08) !important; color: #fff !important;
}
[data-testid="stSidebar"] div.stButton > button[kind="primary"] {
    background: rgba(59,130,246,0.2) !important;
    color: #60a5fa !important;
    border-left: 3px solid #3b82f6 !important;
}
</style>
""", unsafe_allow_html=True)

# ── SESSION STATE ──────────────────────────────────────────────────────────────
if 'page' not in st.session_state:
    st.session_state.page = 'semana'

# ── SIDEBAR ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://http2.mlstatic.com/frontend-assets/ui-navigation/5.21.3/mercadolibre/logo__large_plus.png", width=130)
    st.markdown("---")
    st.markdown("<p style='color:#3d5a7a;font-size:10px;letter-spacing:2px;text-transform:uppercase;padding:0 4px'>FBM LOST</p>", unsafe_allow_html=True)

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
    st.caption("🟢 GitHub · Auto-atualização 8h e 14h")
    from datetime import datetime
    st.caption(f"BRSP06 · {datetime.now().strftime('%d/%m/%Y %H:%M')}")

# ── LOAD DATA ──────────────────────────────────────────────────────────────────
with st.spinner("Carregando dados..."):
    try:
        df = load_data()
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        st.stop()

valid_weeks = sorted([w for w in df['WEEK_DUE_DATE'].unique()
                      if w and w != 'Sem previsão' and '-' in w])
NEXT_4 = valid_weeks[:4]
CUR    = valid_weeks[0] if valid_weeks else ''

# ── HEADER ─────────────────────────────────────────────────────────────────────
c1, c2 = st.columns([6, 2])
with c1:
    st.markdown("### CORE | FBM LOST — BRSP06")
with c2:
    st.success("🟢 Live · GitHub")
st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: SEMANA ATUAL
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.page == 'semana':
    st.markdown(f"**Semana atual — {CUR}** · due date")
    st.divider()

    df_cur = df[df['WEEK_DUE_DATE'] == CUR].copy()
    df_cur['fin'] = df_cur.apply(is_finalizado, axis=1)
    df_cur['rec'] = df_cur.apply(lambda r: r['PENDING_USD'] if (
        r['STATUS_BUSCA_ORIGEN'] in FOUND_SET or
        r['STATUS_REVISAO_ORIGEN'] in FOUND_SET) else 0, axis=1)

    total     = len(df_cur)
    usd_total = df_cur['PENDING_USD'].sum()
    usd_rec   = df_cur['rec'].sum()
    usd_pend  = df_cur[~df_cur['fin']]['PENDING_USD'].sum()
    n_fin     = int(df_cur['fin'].sum())
    pct_fin   = round(n_fin / total * 100, 1) if total else 0
    n_pb      = int((df_cur['STATUS_BUSCA_ORIGEN'] == '').sum())
    n_pr      = int((df_cur['STATUS_REVISAO_ORIGEN'] == '').sum())
    pct_b     = round((total - n_pb) / total * 100, 1) if total else 0
    pct_r     = round((total - n_pr) / total * 100, 1) if total else 0

    # KPIs
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Total issues", f"{total:,}", "due esta semana")
    k2.metric("USD total", f"${usd_total:,.0f}")
    k3.metric("USD pendente", f"${usd_pend:,.0f}", f"{total-n_fin} em aberto", delta_color="inverse")
    k4.metric("USD recuperado", f"${usd_rec:,.0f}", "Found Inv./LP")
    k5.metric("% Conclusão", f"{pct_fin}%", f"{n_fin} de {total}")

    st.divider()

    # Progresso busca e revisão
    col_b, col_r = st.columns(2)
    with col_b:
        st.markdown("**Processo de Busca**")
        st.metric("Concluídas", f"{pct_b}%", f"{total-n_pb:,} ok · {n_pb:,} faltam",
                  delta_color="normal" if pct_b >= 80 else "inverse")
        st.progress(pct_b / 100)
        if n_pb > 0:
            st.caption("Pendentes por processo")
            df_pb = df_cur[df_cur['STATUS_BUSCA_ORIGEN'] == '']['FBM_PROCCESS_NAME'].value_counts().head(5).reset_index()
            df_pb.columns = ['Processo', 'Qtd']
            fig = st_go.Figure(st_go.Bar(x=df_pb['Qtd'], y=df_pb['Processo'],
                orientation='h', marker_color='#ef4444', text=df_pb['Qtd'], textposition='outside'))
            st.plotly_chart(chart_style(fig, 200), use_container_width=True)

    with col_r:
        st.markdown("**Processo de Revisão**")
        st.metric("Concluídas", f"{pct_r}%", f"{total-n_pr:,} ok · {n_pr:,} faltam",
                  delta_color="normal" if pct_r >= 80 else "inverse")
        st.progress(pct_r / 100)
        if n_pr > 0:
            st.caption("Pendentes por processo")
            df_pr = df_cur[df_cur['STATUS_REVISAO_ORIGEN'] == '']['FBM_PROCCESS_NAME'].value_counts().head(5).reset_index()
            df_pr.columns = ['Processo', 'Qtd']
            fig = st_go.Figure(st_go.Bar(x=df_pr['Qtd'], y=df_pr['Processo'],
                orientation='h', marker_color='#f59e0b', text=df_pr['Qtd'], textposition='outside'))
            st.plotly_chart(chart_style(fig, 200), use_container_width=True)

    st.divider()
    col_f, col_u = st.columns(2)
    with col_f:
        st.markdown("**Finalizados por critério**")
        dfl_dfl   = len(df_cur[(df_cur['STATUS_BUSCA_ORIGEN']=='DFL')&(df_cur['STATUS_REVISAO_ORIGEN']=='DFL')])
        found_b   = len(df_cur[df_cur['STATUS_BUSCA_ORIGEN'].isin(FOUND_SET)&~df_cur['STATUS_REVISAO_ORIGEN'].isin(FOUND_SET)])
        dfl_found = len(df_cur[(df_cur['STATUS_BUSCA_ORIGEN']=='DFL')&df_cur['STATUS_REVISAO_ORIGEN'].isin(FOUND_SET)])
        found_both= len(df_cur[df_cur['STATUS_BUSCA_ORIGEN'].isin(FOUND_SET)&df_cur['STATUS_REVISAO_ORIGEN'].isin(FOUND_SET)])
        fig = st_go.Figure(st_go.Bar(
            x=['DFL+DFL','Found busca','DFL+Found rev.','Found+Found'],
            y=[dfl_dfl, found_b, dfl_found, found_both],
            marker_color='#22c55e', text=[dfl_dfl,found_b,dfl_found,found_both], textposition='outside'))
        st.plotly_chart(chart_style(fig, 260), use_container_width=True)

    with col_u:
        st.markdown("**USD — Total · Pendente · Recuperado**")
        fig = st_go.Figure(st_go.Bar(
            x=['Total','Pendente','Finalizado','Recuperado'],
            y=[usd_total, usd_pend, usd_total-usd_pend, usd_rec],
            marker_color=['#3b82f6','#ef4444','#94a3b8','#22c55e'],
            text=[f'${v:,.0f}' for v in [usd_total,usd_pend,usd_total-usd_pend,usd_rec]],
            textposition='outside'))
        st.plotly_chart(chart_style(fig, 260), use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: PRÓXIMAS SEMANAS
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == 'proximas':
    st.markdown("**Semana atual + próximas 3** · progresso de busca & revisão")
    st.divider()

    df_4  = df[df['WEEK_DUE_DATE'].isin(NEXT_4)]
    tot4  = len(df_4)
    usd4  = df_4['PENDING_USD'].sum()
    pb4   = (df_4['STATUS_BUSCA_ORIGEN'] == '').sum()
    rec4  = df_4[df_4['STATUS_BUSCA_ORIGEN'].isin(FOUND_SET)|df_4['STATUS_REVISAO_ORIGEN'].isin(FOUND_SET)]['PENDING_USD'].sum()

    k1,k2,k3,k4 = st.columns(4)
    k1.metric("Total 4 semanas", f"{tot4:,}")
    k2.metric("USD total", f"${usd4:,.0f}")
    k3.metric("Pend. busca", f"{pb4:,}", f"{round(pb4/tot4*100) if tot4 else 0}% sem busca", delta_color="inverse")
    k4.metric("USD recuperado", f"${rec4:,.0f}")

    st.divider()
    cols = st.columns(len(NEXT_4))
    for i, week in enumerate(NEXT_4):
        df_w  = df[df['WEEK_DUE_DATE'] == week]
        total = len(df_w)
        if total == 0: continue
        usd   = df_w['PENDING_USD'].sum()
        pb    = int((df_w['STATUS_BUSCA_ORIGEN'] == '').sum())
        pr    = int((df_w['STATUS_REVISAO_ORIGEN'] == '').sum())
        avg_a = df_w['AGING'].mean()
        rec   = df_w[df_w['STATUS_BUSCA_ORIGEN'].isin(FOUND_SET)|df_w['STATUS_REVISAO_ORIGEN'].isin(FOUND_SET)]['PENDING_USD'].sum()
        pct_b = round((total-pb)/total*100,1)
        pct_r = round((total-pr)/total*100,1)

        with cols[i]:
            if week == CUR:
                st.info(f"**{week}** · atual")
            else:
                st.markdown(f"**{week}**")
            st.metric("Issues", f"{total:,}")
            st.metric("USD", f"${usd:,.0f}")
            st.caption(f"Aging médio: {avg_a:.1f}d")
            st.divider()
            st.caption("BUSCA")
            st.metric("Concluída", f"{pct_b}%", f"{total-pb:,} ok · {pb:,} faltam",
                      delta_color="normal" if pct_b>=80 else "inverse")
            st.progress(pct_b/100)
            st.caption("REVISÃO")
            st.metric("Concluída", f"{pct_r}%", f"{total-pr:,} ok · {pr:,} faltam",
                      delta_color="normal" if pct_r>=80 else "inverse")
            st.progress(pct_r/100)
            if rec > 0:
                st.success(f"💰 ${rec:,.0f} recuperado")

    st.divider()
    st.markdown("**Pendente Busca & Revisão por semana**")
    df_bar = pd.DataFrame([{
        'Semana': w.replace('-2026',''),
        'Pendente Busca': int((df[df['WEEK_DUE_DATE']==w]['STATUS_BUSCA_ORIGEN']=='').sum()),
        'Pendente Revisão': int((df[df['WEEK_DUE_DATE']==w]['STATUS_REVISAO_ORIGEN']=='').sum()),
    } for w in NEXT_4])
    fig = st_go.Figure()
    fig.add_trace(st_go.Bar(name='Pendente Busca', y=df_bar['Semana'],
        x=df_bar['Pendente Busca'], orientation='h', marker_color='#1e293b',
        text=df_bar['Pendente Busca'], textposition='outside'))
    fig.add_trace(st_go.Bar(name='Pendente Revisão', y=df_bar['Semana'],
        x=df_bar['Pendente Revisão'], orientation='h', marker_color='#f59e0b',
        text=df_bar['Pendente Revisão'], textposition='outside'))
    fig.update_layout(barmode='group', legend=dict(orientation='h', y=1.1))
    st.plotly_chart(chart_style(fig, 280), use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: EVOLUÇÃO SEMANAL
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == 'evolucao':
    st.markdown("**Evolução semanal** · por semana de criação")
    st.divider()

    evo_weeks = sorted([w for w in df['WEEK_CREATED'].unique() if w and '-' in w])
    evo_data  = []
    for w in evo_weeks:
        dfw = df[df['WEEK_CREATED'] == w]
        evo_data.append({
            'Semana': w.replace('-2026','').replace('-2025',''),
            'SemFull': w, 'Total': len(dfw),
            'Pend. Busca': int((dfw['STATUS_BUSCA_ORIGEN']=='').sum()),
            'Pend. Revisão': int((dfw['STATUS_REVISAO_ORIGEN']=='').sum()),
            'USD': dfw['PENDING_USD'].sum()
        })
    df_evo = pd.DataFrame(evo_data)
    pico   = df_evo.loc[df_evo['Total'].idxmax()] if not df_evo.empty else None

    k1,k2,k3,k4 = st.columns(4)
    k1.metric("Total issues", f"{len(df):,}", "período completo")
    k2.metric("Pico semanal", f"{int(pico['Total']):,}" if pico is not None else '—',
              pico['SemFull'] if pico is not None else '')
    k3.metric("Sem status", f"{(df['STATUS_FINAL']=='Sem Status').sum():,}", "aguardam busca")
    k4.metric("USD total", f"${df['PENDING_USD'].sum():,.0f}")

    st.divider()
    st.markdown("**Pendente Busca & Revisão por semana de criação**")
    fig = st_go.Figure()
    fig.add_trace(st_go.Scatter(name='Pend. Busca', x=df_evo['Semana'], y=df_evo['Pend. Busca'],
        fill='tozeroy', line=dict(color='#ef4444', width=2), fillcolor='rgba(239,68,68,0.08)'))
    fig.add_trace(st_go.Scatter(name='Pend. Revisão', x=df_evo['Semana'], y=df_evo['Pend. Revisão'],
        fill='tozeroy', line=dict(color='#f59e0b', width=2, dash='dot'), fillcolor='rgba(245,158,11,0.06)'))
    fig.update_layout(legend=dict(orientation='h', y=1.1))
    st.plotly_chart(chart_style(fig, 280), use_container_width=True)

    st.markdown("**Volume total por semana**")
    last_w = df_evo['Semana'].iloc[-1] if not df_evo.empty else ''
    colors = ['#3b82f6' if w == last_w else '#bfdbfe' for w in df_evo['Semana']]
    fig2 = st_go.Figure(st_go.Bar(x=df_evo['Semana'], y=df_evo['Total'],
        marker_color=colors, text=df_evo['Total'], textposition='outside'))
    st.plotly_chart(chart_style(fig2, 240), use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: DETALHAMENTO
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == 'detalhe':
    st.markdown("**Detalhamento** · filtros combinados")
    st.divider()

    f1,f2,f3,f4 = st.columns(4)
    with f1: sel_st = st.multiselect("Status", sorted(df['STATUS_FINAL'].unique()))
    with f2: sel_vt = st.multiselect("Vertical", sorted(df['VERTICAL'].unique()))
    with f3: sel_wk = st.multiselect("Semana due", sorted([w for w in df['WEEK_DUE_DATE'].unique() if w != 'Sem previsão']))
    with f4: sel_pr = st.multiselect("Processo", sorted(df['FBM_PROCCESS_NAME'].unique()))

    df_f = df.copy()
    if sel_st: df_f = df_f[df_f['STATUS_FINAL'].isin(sel_st)]
    if sel_vt: df_f = df_f[df_f['VERTICAL'].isin(sel_vt)]
    if sel_wk: df_f = df_f[df_f['WEEK_DUE_DATE'].isin(sel_wk)]
    if sel_pr: df_f = df_f[df_f['FBM_PROCCESS_NAME'].isin(sel_pr)]

    st.caption(f"{len(df_f):,} issues encontradas")
    cols_show = [c for c in ['FBM_ISSUE_ID','FBM_ISSUE_DATE_CREATED','WEEK_CREATED',
                 'WEEK_DUE_DATE','STATUS_FINAL','VERTICAL','ZONA','FBM_PROCCESS_NAME',
                 'AGING','PENDING_USD','STATUS_BUSCA_ORIGEN','STATUS_REVISAO_ORIGEN',
                 'ITEM_TITLE'] if c in df_f.columns]
    st.dataframe(
        df_f[cols_show].sort_values('PENDING_USD', ascending=False).reset_index(drop=True),
        use_container_width=True, hide_index=True,
        column_config={
            'PENDING_USD': st.column_config.NumberColumn("USD", format="$%.2f"),
            'AGING': st.column_config.NumberColumn("Aging (d)"),
        }
    )
    st.download_button("⬇️ Exportar CSV",
        df_f[cols_show].to_csv(index=False).encode('utf-8'),
        "fbm_lost_brsp06.csv", "text/csv")
