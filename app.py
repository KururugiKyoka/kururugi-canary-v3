import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import datetime
import google.generativeai as genai

# 1. ページ基本設定
st.set_page_config(page_title="Macro NOTE (KURURUGI)", layout="wide")

# --- 2. データの読み込み ---
@st.cache_data(ttl=3600)
def load_data():
    return pd.read_csv('canary_data.csv', index_col=0, parse_dates=True)

# --- 3. 比較用データの抽出 ---
def get_historical_data(df_full, days_back):
    latest_date = df_full.index[-1]
    target_date = latest_date - datetime.timedelta(days=days_back)
    try:
        idx = df_full.index.get_indexer([target_date], method='nearest')[0]
        past_date = df_full.index[idx]
        return df_full.loc[latest_date], df_full.loc[past_date], latest_date, past_date
    except:
        return df_full.loc[latest_date], df_full.loc[latest_date], latest_date, latest_date

# --- 4. リスクスコア計算 ---
def calculate_scores(df_history, data_row):
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

# --- 5. Gemini API による分析関数（404エラー対策・強化版） ---
def get_ai_insight(current, past, period_name):
    if "GEMINI_API_KEY" not in st.secrets:
        return "⚠️ Secrets に GEMINI_API_KEY が設定されていません。"
    
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        # モデル名をより汎用的なものに変更
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        あなたはプロのマクロ経済アナリストです。
        現在と{period_name}のリスク変化を3行で鋭く解説してください。
        【現在のリスク】{current}
        【{period_name}のリスク】{past}
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"🤖 AI分析は現在準備中です。データの蓄積をお待ちください。\n(詳細: {e})"

# ========= メイン処理 =========
try:
    df = load_data()

    # サイドバー設定
    st.sidebar.header("⚙️ 表示設定")
    period_options = {"1ヶ月前": 30, "6ヶ月前": 180, "1年前": 365}
    selected_period = st.sidebar.selectbox("比較対象を選択", list(period_options.keys()))
    
    latest_row, past_row, latest_date, past_date = get_historical_data(df, period_options[selected_period])
    current_scores = calculate_scores(df, latest_row)
    past_scores = calculate_scores(df, past_row)

    st.title("🐤 経済 Macro NOTE (KURURUGI)")
    st.caption(f"最終更新: {latest_date.strftime('%Y-%m-%d')} / 比較対象: {past_date.strftime('%Y-%m-%d')} ({selected_period})")

    # AI 診断セクション
    st.divider()
    with st.expander("🤖 AI によるモメンタム診断", expanded=True):
        insight = get_ai_insight(current_scores, past_scores, selected_period)
        st.info(insight)
    st.divider()

    # グラフ表示（省略せずすべて含めています）
    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("🕸️ リスク・モメンタム")
        items = list(current_scores.keys())
        items_close = items + [items[0]]
        current_vals = [current_scores[i] for i in items] + [current_scores[items[0]]]
        past_vals = [past_scores[i] for i in items] + [past_scores[items[0]]]
        fig_r = go.Figure()
        fig_r.add_trace(go.Scatterpolar(r=[25]*6, theta=items_close, fill='toself', 
            fillcolor='rgba(0, 255, 255, 0.1)', line=dict(color='rgba(0, 255, 255, 0.2)', width=1), name='安全圏'))
        fig_r.add_trace(go.Scatterpolar(r=past_vals, theta=items_close, mode='lines+markers',
            line=dict(color='#00FFFF', width=2, dash='dot'), marker=dict(size=6), name=selected_period))
        fig_r.add_trace(go.Scatterpolar(r=current_vals, theta=items_close, fill='toself',
            fillcolor='rgba(220, 20, 60, 0.8)', line=dict(color='#FF0000', width=5), name='現在'))
        fig_r.update_layout(template='plotly_dark', polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                            legend=dict(orientation="h", y=1.1), margin=dict(l=40, r=40, t=20, b=20))
        st.plotly_chart(fig_r, use_container_width=True)

    with col2:
        st.subheader("📉 主要指標：10Y-2Y 長短金利差")
        fig_m = px.line(df, y='T10Y2Y', color_discrete_sequence=['#F43F5E'])
        fig_m.update_layout(template='plotly_dark', height=400, margin=dict(l=0,r=0,t=20,b=0))
        st.plotly_chart(fig_m, use_container_width=True, theme=None)

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
