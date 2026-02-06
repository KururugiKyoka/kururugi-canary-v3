import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import datetime
import google.generativeai as genai

# 1. ページ基本設定（note のタイトル表示 & スマホ最適化）
st.set_page_config(
    page_title="経済 Macro NOTE (KURURUGI) | 景気分析ダッシュボード",
    page_icon="🐤",
    layout="wide",
    initial_sidebar_state="collapsed" # スマホで画面を広く使うためサイドバーを閉じて開始
)

# --- 2. データの読み込み（キャッシュ） ---
@st.cache_data(ttl=3600)
def load_data():
    return pd.read_csv('canary_data.csv', index_col=0, parse_dates=True)

# --- 3. スコア計算（キャッシュ） ---
@st.cache_data
def get_cached_scores(df_history, data_row_dict):
    data_row = pd.Series(data_row_dict)
    def get_score(code, inv=False):
        s_hist = df_history[code].dropna()
        if s_hist.empty or code not in data_row or pd.isna(data_row[code]): return 50
        score = ((data_row[code] - s_hist.min()) / (s_hist.max() - s_hist.min())) * 100
        return (100 - score) if inv else score
    return {
        '金融・市場の歪み': (get_score('BAMLH0A0HYM2', False) + get_score('T10Y2Y', True)) / 2,
        '物流・実需の減退': get_score('HTRUCKSSAAR', True),
        '住宅・先行指標の冷え込み': (get_score('HOUST', True) + get_score('PERMIT', True)) / 2,
        '労働市場の脆弱化': (get_score('ICSA', False) + get_score('TEMPHELPS', True)) / 2,
        '投資・AIの過熱感': 75 
    }

# --- 4. Gemini API 分析（404エラー対策・安定版） ---
@st.cache_data(show_spinner=False)
def get_ai_insight(current, past, period_name):
    if "GEMINI_API_KEY" not in st.secrets: return "⚠️ APIキー未設定"
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        # 最新のモデル名を指定
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"マクロ経済分析: 現在{current}、{period_name}{past}の変化を3行で日本語解説して。"
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"🤖 分析準備中: {e}"

# ========= メイン表示処理 =========
try:
    df = load_data()
    latest_date = df.index[-1]
    
    # 比較設定
    period_map = {"1ヶ月前": 30, "6ヶ月前": 180, "1年前": 365}
    selected_period = st.sidebar.selectbox("比較対象を選択", list(period_map.keys()))
    
    target_past_date = latest_date - datetime.timedelta(days=period_map[selected_period])
    idx = df.index.get_indexer([target_past_date], method='nearest')[0]
    past_date = df.index[idx]

    current_scores = get_cached_scores(df, df.loc[latest_date].to_dict())
    past_scores = get_cached_scores(df, df.loc[past_date].to_dict())

    st.title("🐤 Macro NOTE")
    st.caption(f"最終更新: {latest_date.strftime('%Y-%m-%d')} / 比較: {selected_period}")

    # 結論（スマホで最初に見えるように配置）
    with st.container():
        insight = get_ai_insight(current_scores, past_scores, selected_period)
        st.info(f"**AIモメンタム診断:**\n\n{insight}")

    st.divider()

    # チャート（スマホ対応: 警告回避のため width='stretch' を使用）
    col1, col2 = st.columns([1, 1]) 
    with col1:
        st.subheader("🕸️ リスク・モメンタム")
        items = list(current_scores.keys()); items_c = items + [items[0]]
        fig_r = go.Figure()
        fig_r.add_trace(go.Scatterpolar(r=[25]*6, theta=items_c, fill='toself', fillcolor='rgba(0, 255, 255, 0.1)', line=dict(color='rgba(0, 255, 255, 0.2)', width=1), name='安全圏'))
        fig_r.add_trace(go.Scatterpolar(r=[past_scores[i] for i in items]+[past_scores[items[0]]], theta=items_c, mode='lines+markers', line=dict(color='#00FFFF', width=2, dash='dot'), name=selected_period))
        fig_r.add_trace(go.Scatterpolar(r=[current_scores[i] for i in items]+[current_scores[items[0]]], theta=items_c, fill='toself', fillcolor='rgba(220, 20, 60, 0.8)', line=dict(color='#FF0000', width=5), name='現在'))
        fig_r.update_layout(template='plotly_dark', polar=dict(radialaxis=dict(visible=True, range=[0, 100])), legend=dict(orientation="h", y=1.2), height=380, margin=dict(l=40, r=40, t=40, b=40))
        st.plotly_chart(fig_r, width='stretch', config={'displayModeBar': False})

    with col2:
        st.subheader("📉 長短金利差")
        fig_m = px.line(df, y='T10Y2Y', color_discrete_sequence=['#F43F5E'])
        fig_m.update_layout(template='plotly_dark', height=300, margin=dict(l=0, r=0, t=20, b=0))
        st.plotly_chart(fig_m, width='stretch', config={'displayModeBar': False})

    st.divider()
    tabs = st.tabs(["🏠 住宅・物流", "👥 労働・景況", "💸 金融"])
    sections = [
        {"HTRUCKSSAAR": "重量トラック", "HOUST": "住宅着工", "PERMIT": "住宅許認可"},
        {"TEMPHELPS": "暫定雇用", "ICSA": "失業申請", "MANEMP": "ISM雇用"},
        {"WALCL": "FRB資産", "RRPONTSYD": "リバースレポ", "M2SL": "M2マネーストック"}
    ]
    for i, sect in enumerate(sections):
        with tabs[i]:
            for code, name in sect.items():
                if code in df.columns:
                    f = px.line(df, y=code, title=f"【{name}】")
                    f.update_layout(template='plotly_dark', height=250, margin=dict(l=0, r=0, t=30, b=0))
                    st.plotly_chart(f, width='stretch', config={'displayModeBar': False})

except Exception as e:
    st.error(f"システムエラー: {e}")
