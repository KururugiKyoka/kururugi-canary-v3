import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import datetime

# 1. ページ基本設定（note/スマホ対応）
st.set_page_config(
    page_title="経済 Macro NOTE (KURURUGI) | 景気分析",
    page_icon="🐤",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# noteのクローラー対策
st.markdown('<head><title>経済 Macro NOTE (KURURUGI) | 景気分析</title></head>', unsafe_allow_html=True)

# --- 2. データの読み込み（キャッシュを強力に） ---
@st.cache_data(ttl=3600)
def load_data():
    try:
        df = pd.read_csv('canary_data.csv', index_col=0, parse_dates=True)
        return df
    except Exception as e:
        st.error(f"データの読み込みに失敗しました: {e}")
        return None

# --- 3. スコア計算 ---
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

# ========= メイン表示処理 =========
df = load_data()

if df is not None:
    try:
        latest_date = df.index[-1]
        
        # 期間設定
        period_map = {"1ヶ月前": 30, "6ヶ月前": 180, "1年前": 365}
        selected_period = st.sidebar.selectbox("比較対象を選択", list(period_map.keys()))
        
        target_past_date = latest_date - datetime.timedelta(days=period_map[selected_period])
        idx = df.index.get_indexer([target_past_date], method='nearest')[0]
        past_date = df.index[idx]

        current_scores = get_cached_scores(df, df.loc[latest_date].to_dict())
        past_scores = get_cached_scores(df, df.loc[past_date].to_dict())

        st.title("🐤 Macro NOTE")
        st.caption(f"最終更新: {latest_date.strftime('%Y-%m-%d')} / 比較: {selected_period}")

        st.divider()

        # --- チャート表示（スマホ優先: 縦積みレイアウト） ---
        # カラムを使わず、あえて縦に並べることでスマホでの「消える」「ズレる」を完全に防ぎます
        
        st.subheader("🕸️ リスク・モメンタム")
        items = list(current_scores.keys()); items_c = items + [items[0]]
        fig_r = go.Figure()
        fig_r.add_trace(go.Scatterpolar(r=[25]*6, theta=items_c, fill='toself', fillcolor='rgba(0, 255, 255, 0.1)', line=dict(color='rgba(0, 255, 255, 0.2)', width=1), name='安全圏'))
        fig_r.add_trace(go.Scatterpolar(r=[past_scores[i] for i in items]+[past_scores[items[0]]], theta=items_c, mode='lines+markers', line=dict(color='#00FFFF', width=2, dash='dot'), name=selected_period))
        fig_r.add_trace(go.Scatterpolar(r=[current_scores[i] for i in items]+[current_scores[items[0]]], theta=items_c, fill='toself', fillcolor='rgba(220, 20, 60, 0.8)', line=dict(color='#FF0000', width=5), name='現在'))
        fig_r.update_layout(template='plotly_dark', polar=dict(radialaxis=dict(visible=True, range=[0, 100])), legend=dict(orientation="h", y=1.2), height=400, margin=dict(l=40, r=40, t=40, b=40))
        st.plotly_chart(fig_r, use_container_width=True, config={'displayModeBar': False})

        st.divider()

        st.subheader("📉 長短金利差 (10Y-2Y)")
        fig_m = px.line(df, y='T10Y2Y', color_discrete_sequence=['#F43F5E'])
        fig_m.update_layout(template='plotly_dark', height=300, margin=dict(l=0, r=0, t=20, b=0), xaxis_title=None, yaxis_title=None)
        st.plotly_chart(fig_m, use_container_width=True, config={'displayModeBar': False})

        st.divider()

        # --- セクター別詳細タブ ---
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
                        st.plotly_chart(f, use_container_width=True, config={'displayModeBar': False})

    except Exception as e:
        st.error(f"表示処理中にエラーが発生しました: {e}")
else:
    st.warning("データファイル(canary_data.csv)が見つかりません。")
