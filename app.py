import streamlit as st
import pandas as pd
import plotly.express as px

# ページ設定
st.set_page_config(page_title="Macro NOTE (KURURUGI)", layout="wide")

# --- 1. 高速化のためのキャッシュ機能 ---
@st.cache_data(ttl=3600)  # 1時間は計算結果を保持
def load_and_process_data():
    df = pd.read_csv('canary_data.csv', index_col=0, parse_dates=True)
    
    # リスクスコア計算ロジック（一括計算用）
    def get_score(code, inv=False):
        s = df[code].dropna()
        if s.empty: return 50
        cur = s.iloc[-1]
        score = ((cur - s.min()) / (s.max() - s.min())) * 100
        return (100 - score) if inv else score

    # 事前に全カテゴリのスコアを計算しておく
    scores = {
        'housing': (get_score('HOUST', True) + get_score('PERMIT', True)) / 2,
        'labor': (get_score('ICSA', False) + get_score('TEMPHELPS', True)) / 2,
        'market': (get_score('BAMLH0A0HYM2', False) + get_score('T10Y2Y', True)) / 2,
        'physical': get_score('HTRUCKSSAAR', True)
    }
    return df, scores

# --- 2. データの取得（キャッシュから呼び出し） ---
try:
    df, risk_scores = load_and_process_data()

    # ヘッダー
    st.title("🐤 経済 Macro NOTE (KURURUGI)")
    st.caption(f"最終更新: {df.index[-1].strftime('%Y年%m月%d日')}")

    # 上段：メイン & レーダー
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("📉 主要指標：10Y-2Y 長短金利差")
        fig_m = px.line(df, y='T10Y2Y', color_discrete_sequence=['#F43F5E'])
        fig_m.update_layout(template='plotly_dark', height=400, margin=dict(l=0,r=0,t=20,b=0))
        # 安定表示のための設定
        st.plotly_chart(fig_m, use_container_width=True, theme=None)

    with col2:
        st.subheader("🕸️ リスクレーダー")
        radar_df = pd.DataFrame({
            '項目': ['市場', '実体', '住宅', '労働', 'AI'],
            'リスク': [risk_scores['market'], risk_scores['physical'], risk_scores['housing'], risk_scores['labor'], 75]
        })
        fig_r = px.line_polar(radar_df, r='リスク', theta='項目', line_close=True)
        fig_r.update_traces(fill='toself', line_color='#C5A059')
        fig_r.update_layout(template='plotly_dark', polar=dict(radialaxis=dict(visible=True, range=[0, 100])))
        st.plotly_chart(fig_r, use_container_width=True, theme=None)

    # 下段：タブ分け（ここも表示負荷を分散させる効果があります）
    st.divider()
    tabs = st.tabs(["🏠 住宅・物流", "👥 労働・景況", "💸 金融・流動性"])
    
    sections = [
        {"HTRUCKSSAAR": "重量トラック販売", "HOUST": "住宅着工", "PERMIT": "住宅許認可"},
        {"TEMPHELPS": "暫定雇用", "ICSA": "失業申請", "MANEMP": "ISM雇用"},
        {"WALCL": "FRB総資産", "RRPONTSYD": "リバースレポ", "M2SL": "M2マネーストック"}
    ]

    for i, sect in enumerate(sections):
        with tabs[i]:
            cols = st.columns(2)
            for j, (code, name) in enumerate(sect.items()):
                if code in df.columns:
                    f = px.line(df, y=code, title=f"【{name}】")
                    f.update_layout(template='plotly_dark', height=300)
                    # use_container_width=True を指定してレイアウトを固定
                    cols[j % 2].plotly_chart(f, use_container_width=True, theme=None)

except Exception as e:
    st.error(f"読み込み中... 少し待ってから再読み込みしてください: {e}")
