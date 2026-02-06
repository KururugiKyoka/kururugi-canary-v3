import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- 設定 ---
st.set_page_config(page_title="Macro NOTE (KURURUGI)", layout="wide")

# --- データ読み込み ---
try:
    df = pd.read_csv('canary_data.csv', index_col=0, parse_dates=True)
    
    # --- リスクスコア自動判定ロジック ---
    def calc_score(code, inverse=False):
        series = df[code].dropna()
        if series.empty: return 50
        current = series.iloc[-1]
        s_min, s_max = series.min(), series.max()
        score = ((current - s_min) / (s_max - s_min)) * 100
        return (100 - score) if inverse else score

    # カテゴリー別リスク算出
    risk_housing = (calc_score('HOUST', True) + calc_score('PERMIT', True)) / 2
    risk_labor = (calc_score('ICSA', False) + calc_score('TEMPHELPS', True)) / 2
    risk_market = (calc_score('BAMLH0A0HYM2', False) + calc_score('T10Y2Y', True)) / 2
    risk_physical = calc_score('HTRUCKSSAAR', True)
    
    # ヘッダー
    st.title("🐤 経済 Macro NOTE ダッシュボード (KURURUGI)")
    st.caption(f"最終更新: {df.index[-1].strftime('%Y年%m月%d日')}")

    # --- Section 1: メインチャート & リスクレーダー ---
    c_left, c_right = st.columns([2, 1])
    
    with c_left:
        st.subheader("📉 【先行指標】10Y-2Y 長短金利差")
        fig_main = px.line(df, y='T10Y2Y', color_discrete_sequence=['#F43F5E'])
        fig_main.update_layout(template='plotly_dark', height=400, margin=dict(l=0,r=0,t=20,b=0))
        st.plotly_chart(fig_main, width="stretch") # 最新の設定

    with c_right:
        st.subheader("🕸️ リスク集中度 (自動分析)")
        radar_df = pd.DataFrame({
            '項目': ['市場', '実体経済', '住宅', '労働', 'AI'],
            'リスク': [risk_market, risk_physical, risk_housing, risk_labor, 75]
        })
        fig_radar = px.line_polar(radar_df, r='リスク', theta='項目', line_close=True)
        fig_radar.update_traces(fill='toself', line_color='#C5A059')
        fig_radar.update_layout(template='plotly_dark', polar=dict(radialaxis=dict(visible=True, range=[0, 100])))
        st.plotly_chart(fig_radar, width="stretch")

    # --- Section 2: 12指標カテゴリー別タブ ---
    st.divider()
    cats = {
        "🏠 住宅・物流": {"HTRUCKSSAAR": "重量トラック販売", "HOUST": "住宅着工件数", "PERMIT": "住宅許認可"},
        "👥 労働市場": {"TEMPHELPS": "暫定雇用サービス", "ICSA": "失業保険申請", "MANEMP": "ISM製造業雇用"},
        "💸 金融・流動性": {"WALCL": "FRB総資産", "RRPONTSYD": "リバースレポ", "M2SL": "M2マネーストック"}
    }
    
    tabs = st.tabs(list(cats.keys()))
    for i, (name, indicators) in enumerate(cats.items()):
        with tabs[i]:
            cols = st.columns(2)
            for j, (code, label) in enumerate(indicators.items()):
                if code in df.columns:
                    fig_sub = px.line(df, y=code, title=f"【{label}】")
                    fig_sub.update_layout(template='plotly_dark', height=300)
                    cols[j % 2].plotly_chart(fig_sub, width="stretch")

except Exception as e:
    st.error(f"データの読み込みに失敗しました: {e}")
