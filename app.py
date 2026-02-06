import streamlit as st
import pandas as pd
import plotly.express as px

# --- ページ基本設定 ---
st.set_page_config(page_title="Macro NOTE (KURURUGI)", layout="wide")

# --- データの読み込み ---
try:
    # 先ほど python data_fetcher.py で取得した最新データを読み込む
    df = pd.read_csv('canary_data.csv', index_col=0, parse_dates=True)
    
    # リスクスコア自動算出ロジック (0-100)
    def calc_score(code, inv=False):
        s = df[code].dropna()
        if s.empty: return 50
        cur = s.iloc[-1]
        score = ((cur - s.min()) / (s.max() - s.min())) * 100
        return (100 - score) if inv else score

    # カテゴリー別リスク（12指標から算出）
    r_housing = (calc_score('HOUST', True) + calc_score('PERMIT', True)) / 2
    r_labor = (calc_score('ICSA', False) + calc_score('TEMPHELPS', True)) / 2
    r_market = (calc_score('BAMLH0A0HYM2', False) + calc_score('T10Y2Y', True)) / 2
    r_physical = calc_score('HTRUCKSSAAR', True)

    # --- ヘッダー（日本語） ---
    st.title("🐤 経済 Macro NOTE (KURURUGI)")
    st.caption(f"最終更新（日本時間）: {df.index[-1].strftime('%Y年%m月%d日')}")

    # --- Section 1: メインチャート & リスクレーダー ---
    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader("📉 主要指標：10Y-2Y 長短金利差")
        fig_m = px.line(df, y='T10Y2Y', color_discrete_sequence=['#F43F5E'])
        fig_m.update_layout(template='plotly_dark', height=400, margin=dict(l=0,r=0,t=20,b=0))
        st.plotly_chart(fig_m, width="stretch") # 修正済みの設定

    with c2:
        st.subheader("🕸️ リスクレーダー（自動計算）")
        radar_df = pd.DataFrame({
            '項目': ['市場', '実体経済', '住宅', '労働', 'AI'],
            'リスク': [r_market, r_physical, r_housing, r_labor, 75]
        })
        fig_radar = px.line_polar(radar_df, r='リスク', theta='項目', line_close=True)
        fig_radar.update_traces(fill='toself', line_color='#C5A059')
        fig_radar.update_layout(template='plotly_dark', polar=dict(radialaxis=dict(visible=True, range=[0, 100])))
        st.plotly_chart(fig_radar, width="stretch")

    # --- Section 2: 12指標・カテゴリー別タブ ---
    st.divider()
    tabs = st.tabs(["🏠 住宅・物流", "👥 労働・景況", "💸 金融・流動性"])
    sections = [
        {"HTRUCKSSAAR": "重量トラック販売", "HOUST": "住宅着工件数", "PERMIT": "住宅許認可"},
        {"TEMPHELPS": "暫定雇用サービス", "ICSA": "失業保険申請", "MANEMP": "ISM製造業雇用"},
        {"WALCL": "FRB総資産", "RRPONTSYD": "リバースレポ", "M2SL": "M2マネーストック"}
    ]
    for i, sect in enumerate(sections):
        with tabs[i]:
            cols = st.columns(2)
            for j, (code, name) in enumerate(sect.items()):
                if code in df.columns:
                    f = px.line(df, y=code, title=f"【{name}】")
                    f.update_layout(template='plotly_dark', height=300)
                    cols[j % 2].plotly_chart(f, width="stretch")

except Exception as e:
    st.error(f"データの読み込み中... GitHub Actions（Daily Macro Data Update）の完了をお待ちください。")
