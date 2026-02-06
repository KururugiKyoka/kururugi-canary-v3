import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import datetime

# 1. ページ基本設定
st.set_page_config(
    page_title="経済 Macro NOTE (KURURUGI) | 景気分析",
    page_icon="🐤",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# note用メタデータ
st.markdown('<head><title>経済 Macro NOTE (KURURUGI)</title></head>', unsafe_allow_html=True)

# --- 2. データの読み込み ---
@st.cache_data(ttl=3600)
def load_data():
    try:
        df = pd.read_csv('canary_data.csv', index_col=0, parse_dates=True)
        df.columns = df.columns.str.strip()
        return df
    except:
        return None

# --- 3. スコア計算 ---
@st.cache_data
def get_cached_scores(df_history, data_row_dict):
    data_row = pd.Series(data_row_dict)
    def get_score(code, inv=False):
        if code not in df_history.columns: return 50
        s_hist = df_history[code].dropna()
        if s_hist.empty or code not in data_row or pd.isna(data_row[code]): return 50
        score = ((data_row[code] - s_hist.min()) / (s_hist.max() - s_hist.min())) * 100
        return (100 - score) if inv else score
    
    return {
        '金融リスク': (get_score('BAMLH0A0HYM2', False) + get_score('T10Y2Y', True)) / 2,
        '物流・実需': get_score('HTRUCKSSAAR', True),
        '住宅市場': (get_score('HOUST', True) + get_score('PERMIT', True)) / 2,
        '雇用不安': (get_score('ICSA', False) + get_score('TEMPHELPS', True)) / 2,
        '投資過熱感': 75 
    }

# ========= メイン表示処理 =========
df = load_data()

# 指標設定（名称, 単位, 倍率）
conf = {
    "HTRUCKSSAAR": ["大型トラック販売台数", "万台", 100],
    "HOUST": ["住宅着工件数", "万戸", 0.1],
    "T10Y2Y": ["景気の体温計（長短金利差）", "%", 1],
    "ICSA": ["失業保険申請数", "万人", 0.0001],
    "WALCL": ["FRB総資産", "兆ドル", 0.000001],
    "BAMLH0A0HYM2": ["企業の資金繰りリスク", "%", 1],
    "PERMIT": ["住宅建設許可数", "万戸", 0.1],
    "TEMPHELPS": ["派遣・一時雇用者数", "万人", 0.1]
}

if df is not None:
    try:
        latest_date = df.index[-1]
        period_map = {"1ヶ月前": 30, "6ヶ月前": 180, "1年前": 365}
        selected_period = st.sidebar.selectbox("比較対象を選択", list(period_map.keys()), index=2)
        
        target_past_date = latest_date - datetime.timedelta(days=period_years_map := period_map[selected_period])
        idx = df.index.get_indexer([target_past_date], method='nearest')[0]
        past_date = df.index[idx]

        current_scores = get_cached_scores(df, df.loc[latest_date].to_dict())
        past_scores = get_cached_scores(df, df.loc[past_date].to_dict())

        st.title("🐤 Macro NOTE (KURURUGI)")
        st.caption(f"最終更新: {latest_date.strftime('%Y-%m-%d')} / 比較対象: {selected_period}")

        st.divider()

        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("🕸️ 景気後退リスク")
            items = list(current_scores.keys()); items_c = items + [items[0]]
            fig_r = go.Figure()
            
            fig_r.add_trace(go.Scatterpolar(
                r=[25]*6, 
                theta=items_c, 
                fill='toself', 
                fillcolor='rgba(0, 255, 255, 0.3)',
                line=dict(color='#00FFFF', width=3),
                name='安全圏'
            ))
            
            fig_r.add_trace(go.Scatterpolar(r=[past_scores[i] for i in items]+[past_scores[items[0]]], theta=items_c, mode='lines+markers', line=dict(color='rgba(255, 255, 255, 0.5)', width=2, dash='dot'), marker=dict(size=6), name=selected_period))
            
            fig_r.add_trace(go.Scatterpolar(r=[current_scores[i] for i in items]+[current_scores[items[0]]], theta=items_c, fill='toself', fillcolor='rgba(220, 20, 60, 0.8)', line=dict(color='#FF0000', width=5), name='現在'))
            
            fig_r.update_layout(template='plotly_dark', polar=dict(radialaxis=dict(visible=True, range=[0, 100], gridcolor='rgba(255,255,255,0.1)')), legend=dict(orientation="h", y=1.2), height=450, margin=dict(l=40, r=40, t=40, b=40))
            st.plotly_chart(fig_r, use_container_width=True)

        with col2:
            code = "T10Y2Y"
            if code in df.columns:
                st.subheader(f"📉 {conf[code][0]}")
                fig_m = go.Figure()
                fig_m.add_trace(go.Scatter(x=df.index, y=df[code], fill='tozeroy', fillcolor='rgba(244, 63, 94, 0.2)', line=dict(color='#F43F5E', width=3), name="金利差"))
                fig_m.add_hline(y=0.0, line_width=2, line_dash="dash", line_color="white")
                fig_m.add_annotation(x=df.index[-1], y=-0.5, text="逆イールド（異常）", showarrow=False, font=dict(color="#00FFFF"))
                fig_m.add_annotation(x=df.index[-1], y=0.5, text="スティープ化（警戒）", showarrow=False, font=dict(color="#F43F5E"))
                fig_m.update_layout(template='plotly_dark', height=400, margin=dict(l=0, r=0, t=20, b=0), xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)'))
                st.plotly_chart(fig_m, use_container_width=True)

        st.divider()

        tabs = st.tabs(["🏠 住宅・物流", "👥 労働・景況", "💸 金融・供給量"])
        sections = [["HTRUCKSSAAR", "HOUST"], ["ICSA", "TEMPHELPS"], ["WALCL", "BAMLH0A0HYM2"]]
        for i, codes in enumerate(sections):
            with tabs[i]:
                c1, c2 = st.columns(2)
                for j, code in enumerate(codes):
                    if code in df.columns:
                        display_df = df[[code]].copy()
                        display_df[code] = display_df[code] * conf[code][2]
                        f = px.line(display_df, y=code, title=f"【{conf[code][0]}】 ({conf[code][1]})")
                        f.update_layout(template='plotly_dark', height=280, margin=dict(t=50))
                        (c1 if j==0 else c2).plotly_chart(f, use_container_width=True)
    except Exception as e:
        st.error(f"表示エラー: {e}")
else:
    st.error("canary_data.csv が見つかりません。")
