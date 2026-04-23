import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Loss Prevention — BRSP06", layout="wide", page_icon="🔵")

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

CSV_PI2_URL       = "https://raw.githubusercontent.com/ViniciusVauna/ARQUIVOSLP/main/data_pi2.csv"
CSV_REPRESADO_URL      = "https://raw.githubusercontent.com/ViniciusVauna/ARQUIVOSLP/main/data_found_represado.csv"
CSV_REPRESADO_HIST_URL = "https://raw.githubusercontent.com/ViniciusVauna/ARQUIVOSLP/main/data_found_represado_hist.csv"
CSV_PI2_HIST_URL = "https://raw.githubusercontent.com/ViniciusVauna/ARQUIVOSLP/main/data_pi2_historico.csv"

@st.cache_data(ttl=600, show_spinner=False)
def load_pi2_hist():
    df = pd.read_csv(CSV_PI2_HIST_URL)
    for col in ['Status','Range','Issue','Usuario','Week','Week_pagamento']:
        if col in df.columns:
            df[col] = df[col].fillna('').astype(str).str.strip()
    for col in ['Valor Recuperado','Valor Unitario','Total Issue']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',','.'), errors='coerce').fillna(0)
    df['recuperado'] = df['Status'].str.lower().isin(['conciliado','issue a conciliar'])
    return df

import re as _re

def _parse_semana(val):
    try:
        m = _re.search(r'(\w{3} \w{3} \d{2} \d{4})', str(val))
        if m:
            dt = pd.to_datetime(m.group(1), format='%a %b %d %Y')
            return f"W{dt.isocalendar()[1]:02d}-{dt.year}"
    except: pass
    return ''

@st.cache_data(ttl=600, show_spinner=False)
def load_represado():
    df = pd.read_csv(CSV_REPRESADO_URL)
    df['INSURANCE_COST'] = pd.to_numeric(df['INSURANCE_COST'].astype(str).str.replace(',','.'), errors='coerce').fillna(0)
    df['AGING'] = pd.to_numeric(df['AGING'], errors='coerce').fillna(0).astype(int)
    for col in ['SEMANA_REPRESADO','PROCCESS','RANGE_STATUS','FBM_ISSUE_ID','ADDRESS_ID_FROM','MELI']:
        if col in df.columns:
            df[col] = df[col].fillna('').astype(str).str.strip()
    # Chave para cruzar com histórico: Endereço|FBM_ISSUE_ID|MELI
    df['CHAVE_CALC'] = df['ADDRESS_ID_FROM'] + '|' + df['FBM_ISSUE_ID'] + '|' + df['MELI']
    # Semana de pagamento a partir de DATA_PAGAMENTO
    df['semana_pag'] = df['DATA_PAGAMENTO'].apply(_parse_semana)
    return df

@st.cache_data(ttl=600, show_spinner=False)
def load_represado_hist():
    df = pd.read_csv(CSV_REPRESADO_HIST_URL)
    df['VALOR_CONCILIADO'] = pd.to_numeric(df['VALOR_CONCILIADO'], errors='coerce').fillna(0)
    df['INSURANCE_COST']   = pd.to_numeric(df['INSURANCE_COST'], errors='coerce').fillna(0)
    for col in ['STATUS','PROCCESS','FBM_ISSUE_ID','USUARIO','CHAVE_UNICA']:
        if col in df.columns:
            df[col] = df[col].fillna('').astype(str).str.strip()
    df['conciliado'] = df['STATUS'] == 'Conciliado'
    df['semana_pag'] = df['DATA_PAGAMENTO'].apply(_parse_semana)
    return df

@st.cache_data(ttl=600, show_spinner=False)
def load_pi2():
    df = pd.read_csv(CSV_PI2_URL)
    df['INSURANCE_COST'] = pd.to_numeric(df['INSURANCE_COST'].astype(str).str.replace(',','.'), errors='coerce').fillna(0)
    df['Aging'] = pd.to_numeric(df['Aging'], errors='coerce').fillna(0).astype(int)
    for col in ['Status_busca','Status_Conciliacao','PROCESSO_LOST','Range','Semana de Pagamento','ISSUE','ADDRESS_ID_TO']:
        if col in df.columns:
            df[col] = df[col].fillna('').astype(str).str.strip()
    df['pendente'] = df['Status_busca'] == 'Não localizado'
    df['tratado']  = df['Status_busca'] != 'Não localizado'
    df['semana_norm'] = df['Semana de Pagamento'].str.replace(' ', '', regex=False)
    return df

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
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&display=swap');
[data-testid="stHeader"] { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }
.block-container { padding: 1.5rem 2rem 2rem 2rem !important; max-width: 100% !important; }
.stApp { background: #f0f0f0 !important; }
body { font-family: 'DM Sans', sans-serif !important; color: #1a1a2e !important; }
[data-testid="stMetric"] { background: #ffffff; border-radius: 10px; padding: 16px 18px !important; border-top: 3px solid #ffe600; box-shadow: 0 2px 6px rgba(0,0,0,0.07); }
[data-testid="stMetricLabel"] { color: #888888 !important; font-size: 10px !important; font-weight: 700 !important; text-transform: uppercase; letter-spacing: 0.8px; }
[data-testid="stMetricValue"] { color: #1a1a2e !important; font-size: 26px !important; font-weight: 800 !important; }
[data-testid="stMetricDelta"] { font-size: 11px !important; }
[data-testid="stProgress"] > div > div { background: #ffe600 !important; border-radius: 4px !important; }
[data-testid="stProgress"] > div { background: #e0e0e0 !important; border-radius: 4px !important; height: 8px !important; }
hr { border-color: #e0e0e0 !important; margin: 1.5rem 0 !important; }
[data-testid="stDataFrame"] { border-radius: 10px !important; box-shadow: 0 2px 6px rgba(0,0,0,0.07) !important; background: #ffffff !important; }
.section-label { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; color: #888888; margin-bottom: 12px; border-left: 3px solid #ffe600; padding-left: 10px; }
.placeholder-box { background: #ffffff; border: 2px dashed #d0d0d0; border-radius: 12px; padding: 60px 40px; text-align: center; margin: 20px 0; }
[data-testid="stDownloadButton"] > button { background: #1a73e8 !important; color: #ffffff !important; border: none !important; font-weight: 600 !important; border-radius: 8px !important; }
[data-testid="stDownloadButton"] > button:hover { background: #1557b0 !important; }
</style>
""", unsafe_allow_html=True)

# ── SESSION STATE ──────────────────────────────────────────────────────────────
if 'page' not in st.session_state:
    st.session_state.page = 'caca_lost'

# ── SIDEBAR ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://http2.mlstatic.com/frontend-assets/ui-navigation/5.21.3/mercadolibre/logo__large_plus.png", width=130)
    st.markdown("---")
    st.markdown("<p style='color:#4b5563;font-size:10px;letter-spacing:2px;text-transform:uppercase;padding:0 4px;margin-bottom:6px'>LOSS PREVENTION</p>", unsafe_allow_html=True)

    pages = [
        ('caca_lost',       '🎯', 'Caça Lost'),
        ('pi2',             '📋', 'PI 2.0'),
        ('found_represado', '🔒', 'Found Represado'),
    ]
    for key, icon, label in pages:
        t = "primary" if st.session_state.page == key else "secondary"
        if st.button(f"{icon}  {label}", key=f"nav_{key}", use_container_width=True, type=t):
            st.session_state.page = key
            st.rerun()

    st.markdown("---")
    if st.button("🔄  Atualizar dados", key="refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.caption(f"🟡 Auto-atualização 8h e 14h")
    st.caption(f"BRSP06 · {datetime.now().strftime('%d/%m/%Y %H:%M')}")

# ── HEADER ─────────────────────────────────────────────────────────────────────
page_titles = {
    'caca_lost':       ('🎯 Evolução Caça Lost',       'Acompanhamento semanal de busca e revisão · BRSP06'),
    'pi2':             ('📋 Evolução PI 2.0',           'Em breve · aguardando dados'),
    'found_vendavel':  ('✅ Evolução Found Vendável',   'Em breve · aguardando dados'),
    'found_represado': ('🔒 Evolução Found Represado',  'Em breve · aguardando dados'),
}
title, subtitle = page_titles.get(st.session_state.page, ('—','—'))

# HEADER
st.markdown(f"""
<div style='background:#ffe600;padding:12px 20px;border-radius:10px;
    display:flex;justify-content:space-between;align-items:center;
    box-shadow:0 2px 6px rgba(0,0,0,0.1);margin-bottom:16px'>
    <div>
        <div style='font-size:18px;font-weight:800;color:#1a1a2e'>{title}</div>
        <div style='font-size:12px;color:#555555;margin-top:2px'>{subtitle}</div>
    </div>
    <div style='font-size:12px;font-weight:600;color:#1a1a2e;background:rgba(0,0,0,0.08);padding:6px 12px;border-radius:6px'>
        🟢 Live · GitHub · {datetime.now().strftime('%d/%m/%Y %H:%M')}
    </div>
</div>
""", unsafe_allow_html=True)
st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# EVOLUÇÃO CAÇA LOST
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.page == 'caca_lost':
    with st.spinner("Carregando dados..."):
        try:
            df = load_data()
        except Exception as e:
            st.error(f"Erro ao carregar dados: {e}")
            st.stop()

    today_week   = get_current_week()
    valid_weeks  = sorted([w for w in df['WEEK_DUE_DATE'].unique() if w and w != 'Sem previsão' and '-' in w])
    future_weeks = [w for w in valid_weeks if w >= today_week]
    if not future_weeks: future_weeks = valid_weeks
    NEXT_4 = future_weeks[:4]
    CUR    = future_weeks[0] if future_weeks else ''

    # ── SEMANA ATUAL ──────────────────────────────────────────────────────────
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

    k1,k2,k3,k4,k5 = st.columns(5)
    k1.metric("Total issues", f"{total:,}", "due esta semana")
    k2.metric("USD total", f"${usd_total:,.0f}")
    k3.metric("USD pendente", f"${usd_pend:,.0f}", f"{total-n_fin} em aberto", delta_color="inverse")
    k4.metric("USD recuperado", f"${usd_rec:,.0f}", "Found Inv./LP")
    k5.metric("% Conclusão", f"{pct_fin}%", f"{n_fin} de {total}")

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    col_b, col_r = st.columns(2)
    with col_b:
        cb = pct_color(pct_b)
        st.markdown(f"""
        <div style='background:#fff;border:1px solid #e5e7eb;border-radius:12px;padding:18px 20px;box-shadow:0 1px 3px rgba(0,0,0,0.04)'>
            <p style='font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:#6b7280;margin:0 0 8px'>Processo de Busca</p>
            <div style='display:flex;justify-content:space-between;align-items:baseline;margin-bottom:6px'>
                <span style='font-size:34px;font-weight:800;color:{cb}'>{pct_b}%</span>
                <div style='text-align:right'>
                    <div style='font-size:12px;color:#6b7280'>{total-n_pb:,} concluídas</div>
                    <div style='font-size:12px;color:#dc2626;font-weight:700'>{n_pb:,} faltam</div>
                </div>
            </div>
        </div>""", unsafe_allow_html=True)
        st.progress(pct_b/100)
        if n_pb > 0:
            st.caption("Pendentes por processo")
            df_pb = df_cur[df_cur['STATUS_BUSCA_ORIGEN']=='']['FBM_PROCCESS_NAME'].value_counts().head(5).reset_index()
            df_pb.columns = ['Processo','Qtd']
            fig = go.Figure(go.Bar(x=df_pb['Qtd'], y=df_pb['Processo'], orientation='h',
                marker_color='#1d4ed8', text=df_pb['Qtd'], textposition='outside', textfont=dict(color='#111827')))
            st.plotly_chart(chart_style(fig, 180), use_container_width=True)

    with col_r:
        cr = pct_color(pct_r)
        st.markdown(f"""
        <div style='background:#fff;border:1px solid #e5e7eb;border-radius:12px;padding:18px 20px;box-shadow:0 1px 3px rgba(0,0,0,0.04)'>
            <p style='font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:#6b7280;margin:0 0 8px'>Processo de Revisão</p>
            <div style='display:flex;justify-content:space-between;align-items:baseline;margin-bottom:6px'>
                <span style='font-size:34px;font-weight:800;color:{cr}'>{pct_r}%</span>
                <div style='text-align:right'>
                    <div style='font-size:12px;color:#6b7280'>{total-n_pr:,} concluídas</div>
                    <div style='font-size:12px;color:#dc2626;font-weight:700'>{n_pr:,} faltam</div>
                </div>
            </div>
        </div>""", unsafe_allow_html=True)
        st.progress(pct_r/100)
        if n_pr > 0:
            st.caption("Pendentes por processo")
            df_pr = df_cur[df_cur['STATUS_REVISAO_ORIGEN']=='']['FBM_PROCCESS_NAME'].value_counts().head(5).reset_index()
            df_pr.columns = ['Processo','Qtd']
            fig = go.Figure(go.Bar(x=df_pr['Qtd'], y=df_pr['Processo'], orientation='h',
                marker_color='#2563eb', text=df_pr['Qtd'], textposition='outside', textfont=dict(color='#111827')))
            st.plotly_chart(chart_style(fig, 180), use_container_width=True)

    st.divider()

    # ── 4 SEMANAS ─────────────────────────────────────────────────────────────
    st.markdown('<div class="section-label">Semana atual + próximas 3 · progresso de busca & revisão</div>', unsafe_allow_html=True)

    df_4 = df[df['WEEK_DUE_DATE'].isin(NEXT_4)]
    tot4 = len(df_4); usd4 = df_4['PENDING_USD'].sum()
    pb4  = int((df_4['STATUS_BUSCA_ORIGEN']=='').sum())
    rec4 = df_4[df_4['STATUS_BUSCA_ORIGEN'].isin(FOUND_SET)|df_4['STATUS_REVISAO_ORIGEN'].isin(FOUND_SET)]['PENDING_USD'].sum()

    k1,k2,k3,k4 = st.columns(4)
    k1.metric("Total 4 semanas", f"{tot4:,}")
    k2.metric("USD total", f"${usd4:,.0f}")
    k3.metric("Pend. busca", f"{pb4:,}", f"{round(pb4/tot4*100) if tot4 else 0}% sem busca", delta_color="inverse")
    k4.metric("USD recuperado", f"${rec4:,.0f}")

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    cols = st.columns(4)
    for i, week in enumerate(NEXT_4):
        df_w = df[df['WEEK_DUE_DATE']==week]
        tw = len(df_w)
        if tw == 0: continue
        uw   = df_w['PENDING_USD'].sum()
        pbw  = int((df_w['STATUS_BUSCA_ORIGEN']=='').sum())
        prw  = int((df_w['STATUS_REVISAO_ORIGEN']=='').sum())
        aaw  = df_w['AGING'].mean()
        recw = df_w[df_w['STATUS_BUSCA_ORIGEN'].isin(FOUND_SET)|df_w['STATUS_REVISAO_ORIGEN'].isin(FOUND_SET)]['PENDING_USD'].sum()
        pbp  = round((tw-pbw)/tw*100,1)
        prp  = round((tw-prw)/tw*100,1)
        cbw  = pct_color(pbp); crw = pct_color(prp)
        is_c = week == CUR
        bord = "border:2px solid #ffe600;background:#fffef0;" if is_c else "border:1px solid #e5e7eb;background:#ffffff;"
        bdg  = "<span style='background:#ffe600;color:#111827;font-size:9px;font-weight:800;padding:2px 8px;border-radius:20px'>ATUAL</span>" if is_c else f"<span style='font-size:10px;color:#9ca3af'>+{i}W</span>"
        with cols[i]:
            st.markdown(f"""
            <div style='{bord}border-radius:14px;padding:18px;box-shadow:0 1px 4px rgba(0,0,0,0.06)'>
                <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:10px'>
                    <span style='font-family:monospace;font-size:13px;font-weight:700;color:#111827'>{week}</span>{bdg}
                </div>
                <div style='font-size:28px;font-weight:800;color:#111827;line-height:1'>{tw:,}</div>
                <div style='font-size:11px;color:#6b7280;margin:3px 0 12px;font-family:monospace'>${uw:,.0f} · {aaw:.1f}d aging</div>
                <div style='height:1px;background:#f3f4f6;margin-bottom:12px'></div>
                <div style='font-size:10px;text-transform:uppercase;letter-spacing:1px;color:#9ca3af;margin-bottom:5px'>Busca</div>
                <div style='display:flex;justify-content:space-between;margin-bottom:4px'>
                    <span style='font-size:20px;font-weight:800;color:{cbw}'>{pbp}%</span>
                    <span style='font-size:11px;color:#dc2626;font-weight:700'>{pbw:,} faltam</span>
                </div>
                <div style='height:6px;background:#f3f4f6;border-radius:3px;overflow:hidden;margin-bottom:12px'>
                    <div style='height:100%;width:{pbp}%;background:{cbw};border-radius:3px'></div>
                </div>
                <div style='font-size:10px;text-transform:uppercase;letter-spacing:1px;color:#9ca3af;margin-bottom:5px'>Revisão</div>
                <div style='display:flex;justify-content:space-between;margin-bottom:4px'>
                    <span style='font-size:20px;font-weight:800;color:{crw}'>{prp}%</span>
                    <span style='font-size:11px;color:#dc2626;font-weight:700'>{prw:,} faltam</span>
                </div>
                <div style='height:6px;background:#f3f4f6;border-radius:3px;overflow:hidden;margin-bottom:10px'>
                    <div style='height:100%;width:{prp}%;background:{crw};border-radius:3px'></div>
                </div>
                {"<div style='font-size:11px;color:#16a34a;font-weight:700'>💰 $"+f"{recw:,.0f} recuperado</div>" if recw>0 else ""}
            </div>""", unsafe_allow_html=True)

    st.divider()

    # ── DETALHAMENTO ──────────────────────────────────────────────────────────
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

    cols_show = [c for c in ['FBM_ISSUE_ID','FBM_ISSUE_DATE_CREATED','WEEK_CREATED','WEEK_DUE_DATE',
                 'STATUS_FINAL','VERTICAL','ZONA','FBM_PROCCESS_NAME','AGING','PENDING_USD',
                 'STATUS_BUSCA_ORIGEN','STATUS_REVISAO_ORIGEN','ITEM_TITLE'] if c in df_f.columns]

    ci, cb2 = st.columns([4,1])
    ci.caption(f"{len(df_f):,} issues encontradas")
    with cb2:
        st.download_button("⬇️ Exportar CSV",
            df_f[cols_show].sort_values('PENDING_USD',ascending=False).to_csv(index=False).encode('utf-8'),
            "fbm_lost_brsp06.csv","text/csv", use_container_width=True)

    st.dataframe(df_f[cols_show].sort_values('PENDING_USD',ascending=False).reset_index(drop=True),
        use_container_width=True, hide_index=True,
        column_config={
            'PENDING_USD': st.column_config.NumberColumn("USD", format="$%.2f"),
            'AGING': st.column_config.NumberColumn("Aging (d)"),
            'FBM_ISSUE_DATE_CREATED': st.column_config.DatetimeColumn("Criado", format="DD/MM/YY"),
        })

# ══════════════════════════════════════════════════════════════════════════════
# PLACEHOLDERS — aguardando dados
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == 'pi2':
    with st.spinner("Carregando PI 2.0..."):
        try:
            df2 = load_pi2()
            try:
                df2h = load_pi2_hist()
                pi2_hist_ok = True
            except:
                pi2_hist_ok = False
                df2h = None
        except Exception as e:
            st.error(f"Erro ao carregar PI 2.0: {e}")
            st.stop()

    # Semanas disponíveis (Semana de Pagamento da base ativa)
    semanas_pi2 = sorted([s for s in df2['semana_norm'].unique() if s])

    # ── FILTRO DE PERÍODO ─────────────────────────────────────────────────────
    st.markdown('<div class="section-label">Período de análise · semana de pagamento</div>', unsafe_allow_html=True)
    sel_semanas = st.multiselect("Selecione as semanas", options=semanas_pi2, default=semanas_pi2, key='pi2_period')
    if not sel_semanas:
        st.warning("Selecione ao menos uma semana.")
        st.stop()

    df2f = df2[df2['semana_norm'].isin(sel_semanas)]

    # Histórico filtrado pela semana de pagamento
    if pi2_hist_ok and df2h is not None:
        semana_col_hist = 'Week_pagamento' if 'Week_pagamento' in df2h.columns else ('Week' if 'Week' in df2h.columns else None)
        if semana_col_hist:
            df2h_sel = df2h[df2h[semana_col_hist].isin(sel_semanas)]
        else:
            df2h_sel = df2h
        rec_issues    = df2h_sel['Issue'].nunique() if 'Issue' in df2h_sel.columns else 0
        brl_rec_pi2   = df2h_sel['Valor Recuperado'].sum() if 'Valor Recuperado' in df2h_sel.columns else 0
    else:
        df2h_sel = None; rec_issues = 0; brl_rec_pi2 = 0

    st.divider()

    # ── KPIs GERAIS ───────────────────────────────────────────────────────────
    st.markdown('<div class="section-label">KPIs · período selecionado</div>', unsafe_allow_html=True)

    total_end     = len(df2f)
    total_issues  = df2f['ISSUE'].nunique()
    pend_end      = int(df2f['pendente'].sum())
    trat_end      = int(df2f['tratado'].sum())
    pct_end       = round(trat_end/total_end*100,1) if total_end else 0
    brl_total     = df2f['INSURANCE_COST'].sum()
    brl_pend      = df2f[df2f['pendente']]['INSURANCE_COST'].sum()
    issue_status  = df2f.groupby('ISSUE')['pendente'].sum()
    issues_res    = int((issue_status == 0).sum())
    issues_pend   = int((issue_status > 0).sum())
    pct_issues    = round(issues_res/total_issues*100,1) if total_issues else 0

    k1,k2,k3,k4,k5,k6 = st.columns(6)
    k1.metric("Total endereços", f"{total_end:,}")
    k2.metric("Issues únicos", f"{total_issues:,}")
    k3.metric("Tratados", f"{trat_end:,}", f"{pct_end}%")
    k4.metric("Pendentes", f"{pend_end:,}", delta_color="inverse")
    k5.metric("Issues recuperados", f"{rec_issues:,}")
    k6.metric("R$ recuperado", f"R${brl_rec_pi2:,.0f}")

    st.divider()

    # ── BARRAS DE PROGRESSO ───────────────────────────────────────────────────
    st.markdown('<div class="section-label">Progresso de varredura e recuperação</div>', unsafe_allow_html=True)
    col_b2, col_r2 = st.columns(2)

    with col_b2:
        cb2 = pct_color(pct_end)
        st.markdown(f"<div style='background:#fff;border:1px solid #e5e7eb;border-radius:12px;padding:18px 20px'><p style='font-size:11px;font-weight:700;text-transform:uppercase;color:#888;margin:0 0 8px'>Endereços Tratados</p><div style='display:flex;justify-content:space-between;align-items:baseline;margin-bottom:6px'><span style='font-size:40px;font-weight:800;color:{cb2}'>{pct_end}%</span><div style='text-align:right'><div style='font-size:12px;color:#555'>{trat_end:,} tratados</div><div style='font-size:13px;color:#dc2626;font-weight:700'>{pend_end:,} faltam</div></div></div><div style='height:8px;background:#e0e0e0;border-radius:4px;overflow:hidden'><div style='height:100%;width:{pct_end}%;background:{cb2};border-radius:4px'></div></div></div>", unsafe_allow_html=True)
        st.caption("Pendentes por processo")
        df_pb2 = df2f[df2f['pendente']].groupby('PROCESSO_LOST').size().reset_index(name='Qtd').sort_values('Qtd')
        if not df_pb2.empty:
            fig = go.Figure(go.Bar(x=df_pb2['Qtd'], y=df_pb2['PROCESSO_LOST'], orientation='h',
                marker_color='#1a73e8', text=df_pb2['Qtd'], textposition='outside', textfont=dict(color='#1a1a2e')))
            fig.update_layout(height=180, margin=dict(t=5,b=5,l=5,r=40), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#1a1a2e',size=11))
            fig.update_xaxes(showgrid=False, showticklabels=False); fig.update_yaxes(showgrid=False, color='#1a1a2e')
            st.plotly_chart(fig, use_container_width=True)

    with col_r2:
        ci2 = pct_color(pct_issues)
        st.markdown(f"<div style='background:#fff;border:1px solid #e5e7eb;border-radius:12px;padding:18px 20px'><p style='font-size:11px;font-weight:700;text-transform:uppercase;color:#888;margin:0 0 8px'>Issues Únicos Resolvidos</p><div style='display:flex;justify-content:space-between;align-items:baseline;margin-bottom:6px'><span style='font-size:40px;font-weight:800;color:{ci2}'>{pct_issues}%</span><div style='text-align:right'><div style='font-size:12px;color:#555'>{issues_res:,} resolvidos</div><div style='font-size:13px;color:#dc2626;font-weight:700'>{issues_pend:,} faltam</div></div></div><div style='height:8px;background:#e0e0e0;border-radius:4px;overflow:hidden'><div style='height:100%;width:{pct_issues}%;background:{ci2};border-radius:4px'></div></div></div>", unsafe_allow_html=True)
        st.caption("Pendentes por Range")
        df_rng = df2f[df2f['pendente']].groupby('Range').size().reset_index(name='Qtd').sort_values('Qtd')
        if not df_rng.empty:
            fig2 = go.Figure(go.Bar(x=df_rng['Qtd'], y=df_rng['Range'], orientation='h',
                marker_color='#2563eb', text=df_rng['Qtd'], textposition='outside', textfont=dict(color='#1a1a2e')))
            fig2.update_layout(height=180, margin=dict(t=5,b=5,l=5,r=40), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#1a1a2e',size=11))
            fig2.update_xaxes(showgrid=False, showticklabels=False); fig2.update_yaxes(showgrid=False, color='#1a1a2e')
            st.plotly_chart(fig2, use_container_width=True)

    st.divider()

    # ── CARDS POR SEMANA ──────────────────────────────────────────────────────
    st.markdown('<div class="section-label">Evolução por semana de pagamento</div>', unsafe_allow_html=True)
    n_cols4 = min(len(sel_semanas), 4)
    cols4   = st.columns(n_cols4)
    for i, sem in enumerate(sorted(sel_semanas)):
        df_s   = df2f[df2f['semana_norm'] == sem]
        t_end  = len(df_s); p_end = int(df_s['pendente'].sum()); tr_end = int(df_s['tratado'].sum())
        pp     = round(tr_end/t_end*100,1) if t_end else 0; cp = pct_color(pp)
        brl_s  = df_s['INSURANCE_COST'].sum()
        iss_s  = df_s['ISSUE'].nunique()
        is_st  = df_s.groupby('ISSUE')['pendente'].sum()
        iss_r  = int((is_st == 0).sum()); iss_p = int((is_st > 0).sum())
        pp_i   = round(iss_r/iss_s*100,1) if iss_s else 0; ci3 = pct_color(pp_i)
        # Recuperados do histórico nessa semana
        if pi2_hist_ok and df2h is not None and semana_col_hist:
            rec_s   = int((df2h[semana_col_hist] == sem).sum())
            brl_r_s = df2h[df2h[semana_col_hist] == sem]['Valor Recuperado'].sum() if 'Valor Recuperado' in df2h.columns else 0
        else:
            rec_s = 0; brl_r_s = 0
        with cols4[i % n_cols4]:
            st.markdown(f"<div style='border:1px solid #e5e7eb;background:#fff;border-radius:14px;padding:16px;box-shadow:0 1px 4px rgba(0,0,0,0.06);margin-bottom:8px'><div style='font-family:monospace;font-size:13px;font-weight:700;color:#1a1a2e;margin-bottom:6px'>{sem}</div><div style='font-size:11px;color:#888;margin-bottom:10px'>R${brl_s:,.0f} · {t_end:,} end.</div><div style='height:1px;background:#f3f4f6;margin-bottom:10px'></div><div style='font-size:10px;text-transform:uppercase;letter-spacing:1px;color:#9ca3af;margin-bottom:4px'>A bater · Tratei · Faltam</div><div style='font-size:13px;font-weight:700;color:#1a1a2e;margin-bottom:4px'>{t_end:,} · <span style='color:#1a73e8'>{tr_end:,}</span> · <span style='color:#dc2626'>{p_end:,}</span></div><div style='height:6px;background:#f3f4f6;border-radius:3px;overflow:hidden;margin-bottom:10px'><div style='height:100%;width:{pp}%;background:{cp};border-radius:3px'></div></div><div style='font-size:10px;text-transform:uppercase;letter-spacing:1px;color:#9ca3af;margin-bottom:4px'>Issues únicos resolvidos</div><div style='display:flex;justify-content:space-between;margin-bottom:4px'><span style='font-size:16px;font-weight:800;color:{ci3}'>{pp_i}%</span><span style='font-size:11px;color:#dc2626;font-weight:700'>{iss_p:,} faltam</span></div><div style='height:6px;background:#f3f4f6;border-radius:3px;overflow:hidden;margin-bottom:10px'><div style='height:100%;width:{pp_i}%;background:{ci3};border-radius:3px'></div></div><div style='font-size:10px;text-transform:uppercase;letter-spacing:1px;color:#9ca3af;margin-bottom:4px'>Recuperados</div><div style='font-size:16px;font-weight:800;color:#16a34a'>{rec_s:,} <span style='font-size:11px;color:#555'>· R${brl_r_s:,.0f}</span></div></div>", unsafe_allow_html=True)

    st.divider()

    # ── DETALHAMENTO ──────────────────────────────────────────────────────────
    st.markdown('<div class="section-label">Detalhamento · filtros & exportação</div>', unsafe_allow_html=True)
    fa, fb = st.columns(2)
    with fa: sel_proc2  = st.multiselect("Processo", sorted(df2f['PROCESSO_LOST'].unique()))
    with fb:
        sel_sts2 = st.multiselect("Status", ["Pendente","Tratado"])
    df2d = df2f.copy()
    if sel_proc2: df2d = df2d[df2d['PROCESSO_LOST'].isin(sel_proc2)]
    if sel_sts2:
        if "Pendente" in sel_sts2 and "Tratado" not in sel_sts2:
            df2d = df2d[df2d['pendente']]
        elif "Tratado" in sel_sts2 and "Pendente" not in sel_sts2:
            df2d = df2d[df2d['tratado']]
    cols2_show = [c for c in ['ISSUE','ITEM_TITLE_LOST','ENDERECO_LOST','ADDRESS_ID_TO','PROCESSO_LOST','Range','Status_busca','Status_Conciliacao','INSURANCE_COST','Aging','Semana de Pagamento'] if c in df2d.columns]
    ci2b, cb2b = st.columns([4,1])
    ci2b.caption(f"{len(df2d):,} endereços · {df2d['ISSUE'].nunique():,} issues únicos")
    with cb2b:
        st.download_button("⬇️ Exportar CSV", df2d[cols2_show].to_csv(index=False).encode('utf-8'), "pi2_brsp06.csv", "text/csv", use_container_width=True)
    st.dataframe(df2d[cols2_show].reset_index(drop=True), use_container_width=True, hide_index=True,
        column_config={'INSURANCE_COST': st.column_config.NumberColumn("R$", format="R$%.2f"), 'Aging': st.column_config.NumberColumn("Aging (d)")})


elif st.session_state.page == 'found_represado':
    with st.spinner("Carregando Found Represado..."):
        try:
            dfr  = load_represado()
            dfrh = load_represado_hist()
        except Exception as e:
            st.error(f"Erro ao carregar Found Represado: {e}")
            st.stop()

    # Chaves do histórico para cruzamento
    chaves_hist     = set(dfrh['CHAVE_UNICA'].astype(str).str.strip())
    chaves_conc     = set(dfrh[dfrh['conciliado']]['CHAVE_UNICA'].astype(str).str.strip())
    dfr['ja_bati']  = dfr['CHAVE_CALC'].isin(chaves_hist)
    dfr['recuperado']= dfr['CHAVE_CALC'].isin(chaves_conc)
    dfr['pendente'] = ~dfr['ja_bati']

    # Semanas disponíveis (da base ativa, por DATA_PAGAMENTO)
    semanas_rep = sorted([s for s in dfr['semana_pag'].unique() if s])

    # ── FILTRO DE PERÍODO ─────────────────────────────────────────────────────
    st.markdown('<div class="section-label">Período de análise · semana de pagamento</div>', unsafe_allow_html=True)
    sel_semanas_r = st.multiselect("Selecione as semanas", options=semanas_rep, default=semanas_rep[:4] if len(semanas_rep)>4 else semanas_rep, key='rep_period')
    if not sel_semanas_r:
        st.warning("Selecione ao menos uma semana.")
        st.stop()

    dfrF = dfr[dfr['semana_pag'].isin(sel_semanas_r)]

    # Recuperados do histórico (semana de pagamento)
    dfrh_sel = dfrh[dfrh['semana_pag'].isin(sel_semanas_r)]
    conc_sel  = dfrh_sel[dfrh_sel['conciliado']]

    st.divider()

    # ── KPIs GERAIS ───────────────────────────────────────────────────────────
    st.markdown('<div class="section-label">KPIs · período selecionado</div>', unsafe_allow_html=True)

    total_bater  = len(dfrF)
    total_bati   = int(dfrF['ja_bati'].sum())
    total_pend   = int(dfrF['pendente'].sum())
    total_rec    = len(conc_sel)
    brl_bater    = dfrF['INSURANCE_COST'].sum()
    brl_pend     = dfrF[dfrF['pendente']]['INSURANCE_COST'].sum()
    brl_rec      = conc_sel['VALOR_CONCILIADO'].sum()
    pct_bati     = round(total_bati/total_bater*100,1) if total_bater else 0
    pct_rec      = round(brl_rec/(brl_bater+brl_rec)*100,1) if (brl_bater+brl_rec) else 0

    k1,k2,k3,k4,k5,k6 = st.columns(6)
    k1.metric("Total a bater", f"{total_bater:,}")
    k2.metric("Já bati", f"{total_bati:,}", f"{pct_bati}%")
    k3.metric("Pendentes", f"{total_pend:,}", delta_color="inverse")
    k4.metric("Recuperados", f"{total_rec:,}")
    k5.metric("R$ pendente", f"R${brl_pend:,.0f}", delta_color="inverse")
    k6.metric("R$ recuperado", f"R${brl_rec:,.0f}")

    st.divider()

    # ── BARRAS DE PROGRESSO ───────────────────────────────────────────────────
    st.markdown('<div class="section-label">Progresso de varredura e recuperação</div>', unsafe_allow_html=True)

    col_b, col_r = st.columns(2)
    with col_b:
        cb = pct_color(pct_bati)
        st.markdown(f"<div style='background:#fff;border:1px solid #e5e7eb;border-radius:12px;padding:18px 20px'><p style='font-size:11px;font-weight:700;text-transform:uppercase;color:#888;margin:0 0 8px'>Varredura (Já bati)</p><div style='display:flex;justify-content:space-between;align-items:baseline;margin-bottom:6px'><span style='font-size:40px;font-weight:800;color:{cb}'>{pct_bati}%</span><div style='text-align:right'><div style='font-size:12px;color:#555'>{total_bati:,} bati</div><div style='font-size:13px;color:#dc2626;font-weight:700'>{total_pend:,} faltam</div></div></div><div style='height:8px;background:#e0e0e0;border-radius:4px;overflow:hidden'><div style='height:100%;width:{pct_bati}%;background:{cb};border-radius:4px'></div></div></div>", unsafe_allow_html=True)
        st.caption("Pendentes por processo")
        df_proc_r = dfrF[dfrF['pendente']].groupby('PROCCESS').size().reset_index(name='Qtd').sort_values('Qtd')
        if not df_proc_r.empty:
            fig = go.Figure(go.Bar(x=df_proc_r['Qtd'], y=df_proc_r['PROCCESS'], orientation='h',
                marker_color='#1a73e8', text=df_proc_r['Qtd'], textposition='outside', textfont=dict(color='#1a1a2e')))
            fig.update_layout(height=200, margin=dict(t=5,b=5,l=5,r=40), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#1a1a2e',size=11))
            fig.update_xaxes(showgrid=False, showticklabels=False); fig.update_yaxes(showgrid=False, color='#1a1a2e')
            st.plotly_chart(fig, use_container_width=True)

    with col_r:
        cv = pct_color(pct_rec)
        st.markdown(f"<div style='background:#fff;border:1px solid #e5e7eb;border-radius:12px;padding:18px 20px'><p style='font-size:11px;font-weight:700;text-transform:uppercase;color:#888;margin:0 0 8px'>Recuperação (R$)</p><div style='display:flex;justify-content:space-between;align-items:baseline;margin-bottom:6px'><span style='font-size:40px;font-weight:800;color:{cv}'>{pct_rec}%</span><div style='text-align:right'><div style='font-size:12px;color:#555'>R${brl_rec:,.0f} rec.</div><div style='font-size:13px;color:#dc2626;font-weight:700'>R${brl_pend:,.0f} pend.</div></div></div><div style='height:8px;background:#e0e0e0;border-radius:4px;overflow:hidden'><div style='height:100%;width:{pct_rec}%;background:{cv};border-radius:4px'></div></div></div>", unsafe_allow_html=True)
        st.caption("Recuperados por semana")
        df_rec_sem = conc_sel.groupby('semana_pag').agg(end=('CHAVE_UNICA','count'), valor=('VALOR_CONCILIADO','sum')).reset_index().sort_values('semana_pag')
        if not df_rec_sem.empty:
            fig2 = go.Figure(go.Bar(x=df_rec_sem['semana_pag'], y=df_rec_sem['end'],
                marker_color='#16a34a', text=df_rec_sem['end'], textposition='outside', textfont=dict(color='#1a1a2e')))
            fig2.update_layout(height=200, margin=dict(t=5,b=5,l=5,r=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#1a1a2e',size=11))
            fig2.update_xaxes(showgrid=False, color='#888'); fig2.update_yaxes(showgrid=False, showticklabels=False)
            st.plotly_chart(fig2, use_container_width=True)

    st.divider()

    # ── CARDS POR SEMANA ──────────────────────────────────────────────────────
    st.markdown('<div class="section-label">Evolução por semana de pagamento</div>', unsafe_allow_html=True)
    n_cols_r = min(len(sel_semanas_r), 4)
    cols_r   = st.columns(n_cols_r)
    for i, sem in enumerate(sorted(sel_semanas_r)):
        df_s   = dfrF[dfrF['semana_pag'] == sem]
        tot_s  = len(df_s)
        bati_s = int(df_s['ja_bati'].sum())
        pend_s = int(df_s['pendente'].sum())
        pp_s   = round(bati_s/tot_s*100,1) if tot_s else 0
        cp_s   = pct_color(pp_s)
        brl_s  = df_s['INSURANCE_COST'].sum()
        # Recuperados do histórico para essa semana
        rec_s  = len(dfrh[(dfrh['semana_pag']==sem) & dfrh['conciliado']])
        brl_r_s= dfrh[(dfrh['semana_pag']==sem) & dfrh['conciliado']]['VALOR_CONCILIADO'].sum()
        with cols_r[i % n_cols_r]:
            st.markdown(f"<div style='border:1px solid #e5e7eb;background:#fff;border-radius:14px;padding:16px;box-shadow:0 1px 4px rgba(0,0,0,0.06);margin-bottom:8px'><div style='font-family:monospace;font-size:13px;font-weight:700;color:#1a1a2e;margin-bottom:6px'>{sem}</div><div style='font-size:11px;color:#888;margin-bottom:10px'>R${brl_s:,.0f} exposição</div><div style='height:1px;background:#f3f4f6;margin-bottom:10px'></div><div style='font-size:10px;text-transform:uppercase;letter-spacing:1px;color:#9ca3af;margin-bottom:4px'>A bater / Já bati / Pendente</div><div style='font-size:13px;font-weight:700;color:#1a1a2e;margin-bottom:4px'>{tot_s:,} · <span style='color:#1a73e8'>{bati_s:,}</span> · <span style='color:#dc2626'>{pend_s:,}</span></div><div style='height:6px;background:#f3f4f6;border-radius:3px;overflow:hidden;margin-bottom:10px'><div style='height:100%;width:{pp_s}%;background:{cp_s};border-radius:3px'></div></div><div style='font-size:10px;text-transform:uppercase;letter-spacing:1px;color:#9ca3af;margin-bottom:4px'>Recuperados</div><div style='font-size:20px;font-weight:800;color:#16a34a'>{rec_s:,} <span style='font-size:11px;color:#555'>· R${brl_r_s:,.0f}</span></div></div>", unsafe_allow_html=True)

    st.divider()

    # ── DETALHAMENTO ──────────────────────────────────────────────────────────
    st.markdown('<div class="section-label">Detalhamento · filtros & exportação</div>', unsafe_allow_html=True)
    fa, fb, fc = st.columns(3)
    with fa: sel_proc_r = st.multiselect("Processo", sorted(dfrF['PROCCESS'].unique()), key='rep_proc')
    with fb: sel_rng_r  = st.multiselect("Range", sorted(dfrF['RANGE_STATUS'].unique()), key='rep_rng')
    with fc: sel_sts_r  = st.multiselect("Status", ["Pendente","Já bati","Recuperado"], key='rep_sts')
    dfrD = dfrF.copy()
    if sel_proc_r: dfrD = dfrD[dfrD['PROCCESS'].isin(sel_proc_r)]
    if sel_rng_r:  dfrD = dfrD[dfrD['RANGE_STATUS'].isin(sel_rng_r)]
    if sel_sts_r:
        masks = []
        if "Pendente"   in sel_sts_r: masks.append(dfrD['pendente'])
        if "Já bati"    in sel_sts_r: masks.append(dfrD['ja_bati'] & ~dfrD['recuperado'])
        if "Recuperado" in sel_sts_r: masks.append(dfrD['recuperado'])
        if masks:
            import functools, operator
            dfrD = dfrD[functools.reduce(operator.or_, masks)]
    dfrD['STATUS_CALC'] = dfrD.apply(lambda r: 'Recuperado' if r['recuperado'] else ('Já bati' if r['ja_bati'] else 'Pendente'), axis=1)
    cols_show_r = [c for c in ['semana_pag','FBM_ISSUE_ID','TITULO','ADDRESS_ID_FROM','PROCCESS','RANGE_STATUS','STATUS_CALC','INSURANCE_COST','AGING'] if c in dfrD.columns]
    ci_r, cb_r = st.columns([4,1])
    ci_r.caption(f"{len(dfrD):,} endereços · {dfrD['pendente'].sum():,} pendentes · {dfrD['ja_bati'].sum():,} bati")
    with cb_r:
        st.download_button("⬇️ Exportar CSV", dfrD[cols_show_r].to_csv(index=False).encode('utf-8'), "represado_brsp06.csv", "text/csv", use_container_width=True)
    st.dataframe(dfrD[cols_show_r].reset_index(drop=True), use_container_width=True, hide_index=True,
        column_config={'INSURANCE_COST': st.column_config.NumberColumn("R$", format="R$%.2f"), 'AGING': st.column_config.NumberColumn("Aging (d)")})
