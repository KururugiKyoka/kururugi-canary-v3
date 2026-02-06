import pandas_datareader.data as web
import pandas as pd
import datetime

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
    try:
        start = datetime.datetime(2015, 1, 1)
        end = datetime.date.today()
        df = web.DataReader(list(INDICATORS.keys()), 'fred', start, end)
        df = df.ffill()
        df.to_csv('canary_data.csv')
        print("✅ Success")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    fetch_data()

