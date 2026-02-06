import streamlit as st
import pandas as pd
import plotly.express as px
import datetime

# ページ設定
st.set_page_config(page_title="Macro NOTE (KURURUGI)", layout="wide")

# --- データ処理関数 ---
@st.cache_data(ttl=3600)
def load_and_process_data_with_history():
    df_full = pd.read_csv('canary_data.csv', index_col=0, parse_dates=True)
    latest_date = df_full.index[-1]
    target_past_date = latest_date - datetime.timedelta(days=30)
    
    try:
        nearest_idx = df_full.index.get_indexer([target_past_date], method='nearest')[0]
        past_date = df_full.index[nearest_idx]
    except:
        past_date = latest_date

    latest_row = df_full.loc[latest_date]
    past_row = df_full.loc[past_date]
    return df_full, latest_row, past_row, latest_date, past_date

# --- スコア計算関数 ---
def calculate_scores_at_point(df_history, data_row):
    def get_score(code, inv=False):
        s_hist = df_history[code].dropna()
        if s_hist.empty or code not in data_row: return 50
        val_at_point = data_row[code]
        if pd.isna(val_at_point): return 50
        score = ((val_at_point - s_hist.min()) / (s_hist.max() - s_hist.min())) * 100
        return (100 - score) if inv else score

    # 直感的な項目名
    scores = {
        '金融・市場の歪み': (get_score('BAMLH0A0HYM2', False) + get_score('T10Y2Y', True)) / 2,
        '物流・実需の減退': get_score('HTRUCKSSAAR', True),
        '住宅・先行指標の冷え込み': (get_score('HOUST', True) + get_score('PERMIT', True)) / 2,
        '労働市場の脆弱化': (get_score('ICSA', False) + get_score('TEMPHELPS', True)) / 2,
        '投資・AIの過熱感': 75 # 固定値
    }
    return scores

# ========= メイン処理 =========
try:
    df, latest_row, past_row, latest_date, past_date = load_and_process_data_with_history()
    current_scores = calculate_scores_at_point(df, latest_row)
    past_scores = calculate_scores_at_point(df, past_row)

    st.title("🐤 経済 Macro NOTE (KURURUGI)")
    st.caption(f"最終更新: {latest_date.strftime('%Y年%m月%d日')} / 比較対象: {past_date.strftime('%Y年%m月%d日')} 時点")

    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📉 主要指標：10Y-2Y 長短金利差")
        fig_m = px.line(df, y='T10Y2Y', color_discrete_sequence=['#F43F5E'])
        fig_m.update_layout(template='plotly_dark', height=400, margin=dict(l=0,r=0,t=20,b=0))
        st.plotly_chart(fig_m, use_container_width=True, theme=None)

    with col2:
        st.subheader("🕸️ リスク・モメンタム (現在 vs 1ヶ月前)")
        
        radar_data = []
        items = ['金融・市場の歪み', '物流・実需の減退', '住宅・先行指標の冷え込み', '労働市場の脆弱化', '投資・AIの過熱感']
        
        for item in items:
            radar_data.append({'項目': item, 'リスク': current_scores[item], '時期': '現在', '透明度': 0.8})
        for item in items:
            radar_data.append({'項目': item, 'リスク': past_scores[item], '時期': '1ヶ月前', '透明度': 0.15})
            
        radar_df = pd.DataFrame(radar_data)

        # 【修正点】色を深みのあるクリムゾンレッド(#DC143C)に変更
        fig_r = px.line_polar(radar_df, r='リスク', theta='項目', color='時期', line_close=True,
                              color_discrete_map={'現在': '#DC143C', '1ヶ月前': '#00CED1'})
        
        # 【修正点】透明度を時期によって変えるための少し高度な設定
        # 過去は薄く(0.15)、現在は濃く(0.8)
        fig_r.for_each_trace(lambda t: t.update(fill='toself', opacity=0.8 if t.name == '現在' else 0.15, line=dict(width=5)))
        
        fig_r.update_layout(
            template='plotly_dark',
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 100], gridcolor='#444', tickfont=dict(size=10)),
                angularaxis=dict(gridcolor='#444', tickfont=dict(size=12, color='white'))
            ),
            legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1),
            margin=dict(l=50, r=50, t=30, b=30)
        )
        st.plotly_chart(fig_r, use_container_width=True, theme=None)

    # 下段タブ（変更なし）
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
                    cols[j % 2].plotly_chart(f, use_container_width=True, theme=None)

except Exception as e:
    st.error(f"エラーが発生しました: {e}")
