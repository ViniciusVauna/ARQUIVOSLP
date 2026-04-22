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

def chart_style(fig, height=280):
    fig.update_layout(
        height=height, margin=dict(t=10,b=10,l=10,r=40),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#111827', size=11),
        legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(color='#111827')),
    )
    fig.update_xaxes(showgrid=False, color='#6b7280')
    fig.update_yaxes(gridcolor='#f3f4f6', color='#6b7280')
    return fig

def get_current_week():
    today = datetime.now()
    return f"W{str(today.isocalendar()[1]).zfill(2)}-{today.year}"

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
[data-testid="stHeader"] { display: none !important; }
[data-testid="stSidebar"] { display: none !important; }
.block-container { padding: 2rem 2.5rem !important; max-width: 100% !important; }
html, body, .stApp { background: #f8fafc !important; font-family: 'Inter', sans-serif !important; color: #111827 !important; }

[data-testid="stMetric"] {
    background: #ffffff; border: 1px solid #e5e7eb;
    border-radius: 12px; padding: 16px 18px !important;
    border-top: 3px solid #ffe600;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
[data-testid="stMetricLabel"] { color: #6b7280 !important; font-size: 10px !important; font-weight: 700 !important; text-transform: uppercase; letter-spacing: 0.8px; }
[data-testid="stMetricValue"] { color: #111827 !important; font-size: 26px !important; font-weight: 800 !important; }
[data-testid="stMetricDelta"] { font-size: 11px !important; }

[data-testid="stProgress"] > div > div { background: #ffe600 !important; border-radius: 4px !important; }
[data-testid="stProgress"] > div { background: #f3f4f6 !important; border-radius: 4px !important; height: 8px !important; }

hr { border-color: #e5e7eb !important; margin: 1.5rem 0 !important; }
.stCaption { color: #6b7280 !important; }
[data-testid="stDataFrame"] { border: 1px solid #e5e7eb; border-radius: 10px; }

.section-label {
    font-size: 11px; font-weight: 700; text-transform: uppercase;
    letter-spacing: 1px; color: #6b7280; margin-bottom: 12px;
    border-left: 3px solid #ffe600; padding-left: 10px;
}
</style>
""", unsafe_allow_html=True)

# ── LOAD ───────────────────────────────────────────────────────────────────────
with st.spinner("Carregando dados..."):
    try:
        df = load_data()
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        st.stop()

# Semana atual pelo calendário
today_week = get_current_week()
valid_weeks = sorted([w for w in df['WEEK_DUE_DATE'].unique()
                      if w and w != 'Sem previsão' and '-' in w])
future_weeks = [w for w in valid_weeks if w >= today_week]
if not future_weeks:
    future_weeks = valid_weeks

NEXT_4 = future_weeks[:4]
CUR    = future_weeks[0] if future_weeks else ''

# ── HEADER ─────────────────────────────────────────────────────────────────────
c1, c2, c3 = st.columns([5, 2, 2])
with c1:
    st.markdown("<h2 style='color:#111827;margin:0;font-weight:800;font-size:22px'>CORE <span style='color:#ffe600'>|</span> FBM LOST — BRSP06</h2>", unsafe_allow_html=True)
with c2:
    st.markdown(f"<div style='background:#111827;color:#ffe600;font-weight:700;font-size:12px;padding:9px 16px;border-radius:8px;text-align:center;margin-top:4px'>🟢 Live · GitHub</div>", unsafe_allow_html=True)
with c3:
    if st.button("🔄 Atualizar dados", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# SEÇÃO 1: SEMANA ATUAL
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(f'<div class="section-label">Semana atual — {CUR} · Due Date</div>', unsafe_allow_html=True)

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

# KPIs semana atual
k1,k2,k3,k4,k5 = st.columns(5)
k1.metric("Total issues", f"{total:,}", "due esta semana")
k2.metric("USD total", f"${usd_total:,.0f}")
k3.metric("USD pendente", f"${usd_pend:,.0f}", f"{total-n_fin} em aberto", delta_color="inverse")
k4.metric("USD recuperado", f"${usd_rec:,.0f}", "Found Inv./LP")
k5.metric("% Conclusão", f"{pct_fin}%", f"{n_fin} de {total}")

st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

# Progresso busca e revisão
col_b, col_r = st.columns(2)
with col_b:
    st.markdown("<div style='background:#fff;border:1px solid #e5e7eb;border-radius:12px;padding:18px 20px;box-shadow:0 1px 3px rgba(0,0,0,0.04)'>", unsafe_allow_html=True)
    cb = pct_color(pct_b)
    st.markdown(f"<p style='font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:#6b7280;margin:0 0 8px'>Processo de Busca</p>", unsafe_allow_html=True)
    st.markdown(f"<div style='display:flex;justify-content:space-between;align-items:baseline;margin-bottom:6px'><span style='font-size:34px;font-weight:800;color:{cb}'>{pct_b}%</span><div style='text-align:right'><div style='font-size:12px;color:#6b7280'>{total-n_pb:,} concluídas</div><div style='font-size:12px;color:#dc2626;font-weight:700'>{n_pb:,} faltam</div></div></div>", unsafe_allow_html=True)
    st.progress(pct_b/100)
    if n_pb > 0:
        st.markdown("<p style='font-size:10px;color:#9ca3af;text-transform:uppercase;letter-spacing:0.8px;margin:14px 0 6px'>Pendentes por processo</p>", unsafe_allow_html=True)
        df_pb = df_cur[df_cur['STATUS_BUSCA_ORIGEN']=='']['FBM_PROCCESS_NAME'].value_counts().head(5).reset_index()
        df_pb.columns = ['Processo','Qtd']
        fig = go.Figure(go.Bar(x=df_pb['Qtd'], y=df_pb['Processo'], orientation='h',
            marker_color='#1d4ed8', text=df_pb['Qtd'], textposition='outside', textfont=dict(color='#111827')))
        st.plotly_chart(chart_style(fig, 180), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col_r:
    st.markdown("<div style='background:#fff;border:1px solid #e5e7eb;border-radius:12px;padding:18px 20px;box-shadow:0 1px 3px rgba(0,0,0,0.04)'>", unsafe_allow_html=True)
    cr = pct_color(pct_r)
    st.markdown(f"<p style='font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:#6b7280;margin:0 0 8px'>Processo de Revisão</p>", unsafe_allow_html=True)
    st.markdown(f"<div style='display:flex;justify-content:space-between;align-items:baseline;margin-bottom:6px'><span style='font-size:34px;font-weight:800;color:{cr}'>{pct_r}%</span><div style='text-align:right'><div style='font-size:12px;color:#6b7280'>{total-n_pr:,} concluídas</div><div style='font-size:12px;color:#dc2626;font-weight:700'>{n_pr:,} faltam</div></div></div>", unsafe_allow_html=True)
    st.progress(pct_r/100)
    if n_pr > 0:
        st.markdown("<p style='font-size:10px;color:#9ca3af;text-transform:uppercase;letter-spacing:0.8px;margin:14px 0 6px'>Pendentes por processo</p>", unsafe_allow_html=True)
        df_pr = df_cur[df_cur['STATUS_REVISAO_ORIGEN']=='']['FBM_PROCCESS_NAME'].value_counts().head(5).reset_index()
        df_pr.columns = ['Processo','Qtd']
        fig = go.Figure(go.Bar(x=df_pr['Qtd'], y=df_pr['Processo'], orientation='h',
            marker_color='#2563eb', text=df_pr['Qtd'], textposition='outside', textfont=dict(color='#111827')))
        st.plotly_chart(chart_style(fig, 180), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# SEÇÃO 2: PRÓXIMAS 4 SEMANAS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-label">Semana atual + próximas 3 · progresso de busca & revisão</div>', unsafe_allow_html=True)

# KPIs agregados 4 semanas
df_4  = df[df['WEEK_DUE_DATE'].isin(NEXT_4)]
tot4  = len(df_4)
usd4  = df_4['PENDING_USD'].sum()
pb4   = int((df_4['STATUS_BUSCA_ORIGEN']=='').sum())
rec4  = df_4[df_4['STATUS_BUSCA_ORIGEN'].isin(FOUND_SET)|df_4['STATUS_REVISAO_ORIGEN'].isin(FOUND_SET)]['PENDING_USD'].sum()

k1,k2,k3,k4 = st.columns(4)
k1.metric("Total 4 semanas", f"{tot4:,}")
k2.metric("USD total", f"${usd4:,.0f}")
k3.metric("Pend. busca", f"{pb4:,}", f"{round(pb4/tot4*100) if tot4 else 0}% sem busca", delta_color="inverse")
k4.metric("USD recuperado", f"${rec4:,.0f}")

st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

# Cards das 4 semanas
cols = st.columns(4)
for i, week in enumerate(NEXT_4):
    df_w  = df[df['WEEK_DUE_DATE']==week]
    total_w = len(df_w)
    if total_w == 0: continue
    usd_w   = df_w['PENDING_USD'].sum()
    pb_w    = int((df_w['STATUS_BUSCA_ORIGEN']=='').sum())
    pr_w    = int((df_w['STATUS_REVISAO_ORIGEN']=='').sum())
    avg_a   = df_w['AGING'].mean()
    rec_w   = df_w[df_w['STATUS_BUSCA_ORIGEN'].isin(FOUND_SET)|df_w['STATUS_REVISAO_ORIGEN'].isin(FOUND_SET)]['PENDING_USD'].sum()
    pct_bw  = round((total_w-pb_w)/total_w*100,1)
    pct_rw  = round((total_w-pr_w)/total_w*100,1)
    cb_w    = pct_color(pct_bw)
    cr_w    = pct_color(pct_rw)
    is_cur  = week == CUR
    border  = "border:2px solid #ffe600;background:#fffef0;" if is_cur else "border:1px solid #e5e7eb;background:#ffffff;"
    badge   = "<span style='background:#ffe600;color:#111827;font-size:9px;font-weight:800;padding:2px 8px;border-radius:20px'>ATUAL</span>" if is_cur else f"<span style='font-size:10px;color:#9ca3af'>+{i}W</span>"

    with cols[i]:
        st.markdown(f"""
        <div style='{border}border-radius:14px;padding:18px;box-shadow:0 1px 4px rgba(0,0,0,0.06)'>
            <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:10px'>
                <span style='font-family:monospace;font-size:13px;font-weight:700;color:#111827'>{week}</span>
                {badge}
            </div>
            <div style='font-size:28px;font-weight:800;color:#111827;line-height:1'>{total_w:,}</div>
            <div style='font-size:11px;color:#6b7280;margin:3px 0 12px;font-family:monospace'>${usd_w:,.0f} · {avg_a:.1f}d aging</div>
            <div style='height:1px;background:#f3f4f6;margin-bottom:12px'></div>
            <div style='font-size:10px;text-transform:uppercase;letter-spacing:1px;color:#9ca3af;margin-bottom:5px'>Busca</div>
            <div style='display:flex;justify-content:space-between;margin-bottom:4px'>
                <span style='font-size:20px;font-weight:800;color:{cb_w}'>{pct_bw}%</span>
                <span style='font-size:11px;color:#dc2626;font-weight:700'>{pb_w:,} faltam</span>
            </div>
            <div style='height:6px;background:#f3f4f6;border-radius:3px;overflow:hidden;margin-bottom:12px'>
                <div style='height:100%;width:{pct_bw}%;background:{cb_w};border-radius:3px'></div>
            </div>
            <div style='font-size:10px;text-transform:uppercase;letter-spacing:1px;color:#9ca3af;margin-bottom:5px'>Revisão</div>
            <div style='display:flex;justify-content:space-between;margin-bottom:4px'>
                <span style='font-size:20px;font-weight:800;color:{cr_w}'>{pct_rw}%</span>
                <span style='font-size:11px;color:#dc2626;font-weight:700'>{pr_w:,} faltam</span>
            </div>
            <div style='height:6px;background:#f3f4f6;border-radius:3px;overflow:hidden;margin-bottom:10px'>
                <div style='height:100%;width:{pct_rw}%;background:{cr_w};border-radius:3px'></div>
            </div>
            {"<div style='font-size:11px;color:#16a34a;font-weight:700'>💰 $"+f"{rec_w:,.0f} recuperado</div>" if rec_w>0 else ""}
        </div>""", unsafe_allow_html=True)

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# SEÇÃO 3: DETALHAMENTO
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-label">Detalhamento · filtros & exportação</div>', unsafe_allow_html=True)

f1,f2,f3,f4,f5 = st.columns(5)
with f1: sel_wk = st.multiselect("Semana due", sorted([w for w in df['WEEK_DUE_DATE'].unique() if w!='Sem previsão']), default=NEXT_4)
with f2: sel_st = st.multiselect("Status", sorted(df['STATUS_FINAL'].unique()))
with f3: sel_vt = st.multiselect("Vertical", sorted(df['VERTICAL'].unique()))
with f4: sel_pr = st.multiselect("Processo", sorted(df['FBM_PROCCESS_NAME'].unique()))
with f5: sel_zo = st.multiselect("Zona", sorted([z for z in df['ZONA'].unique() if z]))

df_f = df.copy()
if sel_wk: df_f = df_f[df_f['WEEK_DUE_DATE'].isin(sel_wk)]
if sel_st: df_f = df_f[df_f['STATUS_FINAL'].isin(sel_st)]
if sel_vt: df_f = df_f[df_f['VERTICAL'].isin(sel_vt)]
if sel_pr: df_f = df_f[df_f['FBM_PROCCESS_NAME'].isin(sel_pr)]
if sel_zo: df_f = df_f[df_f['ZONA'].isin(sel_zo)]

col_info, col_btn = st.columns([4,1])
col_info.caption(f"{len(df_f):,} issues encontradas")
with col_btn:
    cols_show = [c for c in ['FBM_ISSUE_ID','FBM_ISSUE_DATE_CREATED','WEEK_CREATED','WEEK_DUE_DATE',
                 'STATUS_FINAL','VERTICAL','ZONA','FBM_PROCCESS_NAME','AGING','PENDING_USD',
                 'STATUS_BUSCA_ORIGEN','STATUS_REVISAO_ORIGEN','ITEM_TITLE'] if c in df_f.columns]
    st.download_button("⬇️ Exportar CSV",
        df_f[cols_show].sort_values('PENDING_USD', ascending=False).to_csv(index=False).encode('utf-8'),
        "fbm_lost_brsp06.csv", "text/csv", use_container_width=True)

st.dataframe(
    df_f[cols_show].sort_values('PENDING_USD', ascending=False).reset_index(drop=True),
    use_container_width=True, hide_index=True,
    column_config={
        'PENDING_USD': st.column_config.NumberColumn("USD", format="$%.2f"),
        'AGING': st.column_config.NumberColumn("Aging (d)"),
        'FBM_ISSUE_DATE_CREATED': st.column_config.DatetimeColumn("Criado", format="DD/MM/YY"),
        'WEEK_DUE_DATE': st.column_config.TextColumn("Semana Due"),
        'WEEK_CREATED': st.column_config.TextColumn("Semana Criação"),
        'STATUS_FINAL': st.column_config.TextColumn("Status"),
        'FBM_PROCCESS_NAME': st.column_config.TextColumn("Processo"),
        'STATUS_BUSCA_ORIGEN': st.column_config.TextColumn("Busca"),
        'STATUS_REVISAO_ORIGEN': st.column_config.TextColumn("Revisão"),
    }
)

# Footer
st.markdown(f"<div style='text-align:center;color:#9ca3af;font-size:11px;margin-top:20px'>BRSP06 · Loss Prevention · Atualizado {datetime.now().strftime('%d/%m/%Y %H:%M')} · Auto-atualização 8h e 14h</div>", unsafe_allow_html=True)
