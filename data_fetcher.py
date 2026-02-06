import pandas_datareader.data as web
import pandas as pd
import datetime

# --- 炭鉱のカナリア 12指標リスト（日本語名マッピング） ---
INDICATORS = {
    "T10Y2Y": "10Y-2Y長短金利差",
    "HTRUCKSSAAR": "重量トラック販売台数",
    "HOUST": "住宅着工件数",
    "PERMIT": "住宅許認可件数",
    "BAMLH0A0HYM2": "HYスプレッド",
    "TEMPHELPS": "暫定雇用サービス",
    "ICSA": "新規失業保険申請",
    "UMCSENT": "消費者態度指数",
    "WALCL": "FRB総資産",
    "RRPONTSYD": "リバースレポ",
    "M2SL": "M2マネーストック",
    "MANEMP": "ISM製造業雇用指数"
}

def fetch_data():
    start = datetime.datetime(2015, 1, 1)
    end = datetime.date.today()
    
    # 全データを一括取得
    df = web.DataReader(list(INDICATORS.keys()), 'fred', start, end)
    
    # 欠損値を補完（日次/月次が混ざるため）
    df = df.ffill()
    
    # 保存
    df.to_csv('canary_data.csv')
    print("✅ 12指標のデータを正常に更新しました (canary_data.csv)")

if __name__ == "__main__":
    fetch_data()
    
def fetch_data():
    try:
        start = datetime.datetime(2015, 1, 1)
        end = datetime.date.today()
        df = web.DataReader(list(INDICATORS.keys()), 'fred', start, end)
        df = df.ffill()
        df.to_csv('canary_data.csv')
        print("✅ 12指標のデータを正常に更新しました (canary_data.csv)")
    except Exception as e:
        print(f"❌ データ取得中にエラーが発生しました: {e}")
