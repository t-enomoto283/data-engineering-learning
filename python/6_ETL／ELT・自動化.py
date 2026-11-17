
### STEP 6-1｜増分処理
# STEP 6では、これまで実装してきたデータ取得・加工・保存の処理を、継続的に運用できるデータパイプラインへ発展させます。
#
# 今回使うPython・pandasの知識
# ① pd.to_datetime()
# pd.to_datetime() は、文字列などの日付データを、pandasで日付・時刻として扱える型に変換する関数です。
# 今回のSTEP 6-1では、前回処理した日付とBigQueryから取得した売上データの日付を比較し、増分データを抽出するために使用します。
# 例えば、次のような文字列があるとします。
import pandas as pd
date = "2026-11-03"
converted_date = pd.to_datetime(date)
print(converted_date)        # 2026-11-03 00:00:00
print(type(converted_date))  # <class 'pandas.Timestamp'>
# 文字列だった "2026-11-03" が、pandasの Timestamp 型に変換されます。
# Timestamp 型になることで、日付同士の大小比較や日付計算が可能になります。
# pd.to_datetime() は、単一の値だけでなく、DataFrameの列全体にも使用できます。
df = pd.DataFrame(
    {"order_date": ["2026-11-01", "2026-11-03", "2026-11-05"],
    "sales": [100, 200, 300]}
)
df["order_date"] = pd.to_datetime(df["order_date"])
#
# ② 日付を文字列に戻す
# Timestamp 型を文字列に変換する場合は、strftime() を使用できます。
latest_date = pd.to_datetime("2026-11-05")
formatted_date = latest_date.strftime("%Y-%m-%d")
print(formatted_date)        # 2026-11-05
print(type(formatted_date))  # <class 'str'>
#
# ③ 増分処理（Incremental Processing）
# これまでの演習では、取得したデータ全体を毎回加工していました。
# 例えば、売上データが100万行ある場合、毎回100万行を取得して処理する方法を全件処理（Full Processing）と呼びます。
# 一方、増分処理では、前回の実行以降に追加されたデータだけを対象にします。
# 増分処理のメリットは、データ量が増えても、毎回すべてのデータを処理する必要がないことです。
# これにより、処理時間やBigQueryのクエリ処理量を削減できる場合があります。
#
# ④ ウォーターマーク（Watermark）
# ウォーターマークとは、どこまでのデータを処理したかを記録する基準値です。
# 例えば、前回の処理で2026年11月3日までの売上データを処理した場合、
last_processed_date = "2026-11-03"
# という値を保持します。
# 次回の処理では、この日付より新しいデータを抽出します。
df["order_date"] > pd.to_datetime(last_processed_date)
# これにより、11月4日以降のデータだけを処理できます。
# ただし今回のように日付を基準とする方式では、過去の日付で遅れて追加されたデータや既存レコードの更新を取得できない場合があります。
# 実務では更新日時やIDなども考慮して設計しますが、今回は日付を基準とした単純な増分処理を学習します。
#
# ⑤ DataFrame.max() の応用
# max() は列の最大値を取得するメソッドです。
# 数値だけでなく、日付型の列にも使用できます。
latest_date = df["order_date"].max()
# 例えば、order_date に11月1日、11月2日、11月3日が格納されていれば、最大値は11月3日です。
# 今回の演習では、処理したデータの最新日付を取得し、次回の増分処理に使用するウォーターマークとして返します。

# 目的
# BigQueryから取得した売上データについて、前回処理済みの日付より新しいデータだけをpandasで抽出・集計する関数を実装してください。
# 今回は増分処理の仕組みを理解することが目的のため、ウォーターマークは引数で受け取り、更新後の値を戻り値で返す方式とします。
# ウォーターマークの永続化や定期実行は今回の対象外です。

# 使用するデータ
# 次のSQLを使用してください。
sql1 = """
SELECT DATE '2026-11-01' AS order_date, 'A' AS product_id, 100 AS sales
UNION ALL
SELECT DATE '2026-11-02', 'A', 200
UNION ALL
SELECT DATE '2026-11-03', 'B', 300
UNION ALL
SELECT DATE '2026-11-04', 'B', 150
UNION ALL
SELECT DATE '2026-11-05', 'C', 400
UNION ALL
SELECT DATE '2026-11-05', 'A', 250
"""

# 実装要件
# 関数名：
#   process_incremental_sales
# 引数：
#   引数	                 内容
#   project_id	         BigQueryのプロジェクトID
#   sql	                 売上データ取得用SQL
#   last_processed_date	 前回処理済みの最新日付（YYYY-MM-DD 形式の文字列）
# 処理内容：
#   bigquery.Client() でBigQueryに接続する。
#   引数 sql を実行し、DataFrameとして取得する。
#   order_date 列を pd.to_datetime() で日付型に変換する。
#   last_processed_date も日付型に変換する。
#   order_date が last_processed_date より新しい行だけを抽出する。
#   抽出したデータを product_id ごとに集計し、total_sales 列を作成する。
#   total_sales の降順に並べ替える。
#   抽出したデータの最新 order_date を取得し、YYYY-MM-DD 形式の文字列にする。
#   対象データが0件の場合は、集計結果を空にし、ウォーターマークは変更しない。
#   正常系・異常系の結果を辞書として返し、logging で記録する。
# 戻り値の形式：
# {
#     "status": "OK" または "ERROR",
#     "project_id": プロジェクトID,
#     "row_count": 増分抽出した明細の行数,
#     "processed_until": 処理済みの最新日付,
#     "columns": ["product_id", "total_sales"],
#     "rows": 集計結果の辞書リスト,
#     "error": None または エラーメッセージ
# }
# 補足：
#   row_count は集計後の商品数ではなく、増分抽出された明細の行数です。
#   processed_until は、処理対象データがある場合はその最大日付、0件の場合は元の last_processed_date とします。
#   異常系では row_count=0、processed_until=last_processed_date、columns=[]、rows=[] としてください。
#   集計はSQL側ではなく、pandas側で実行してください。

from google.cloud import bigquery
import logging

def process_incremental_sales(project_id, sql, last_processed_date):
    try:
        client = bigquery.Client(
            project=project_id,
        )
        query_job = client.query(sql)
        df = query_job.result().to_dataframe(
            create_bqstorage_client=False
        )
        df["order_date"] = pd.to_datetime(df["order_date"])
        watermark = pd.to_datetime(last_processed_date)
        increment_df = df[df["order_date"] > watermark]
        if increment_df.empty:
            logging.info("増分なし")
            return {
                "status": "OK",
                "project_id": project_id,
                "row_count": 0,
                "processed_until": last_processed_date,
                "columns": ["product_id", "total_sales"],
                "rows": [],
                "error": None
            }
        else:
            summary = increment_df.groupby(
                "product_id",
                as_index=False
            ).agg(
                total_sales=("sales", "sum")
            )
            summary = summary.sort_values(
                by="total_sales",
                ascending=False
            )
            summary = summary.reset_index(drop=True)
            latest_date = increment_df["order_date"].max()
            logging.info("処理成功")
            return {
                "status": "OK",
                "project_id": project_id,
                "row_count": len(increment_df),
                "processed_until": latest_date.strftime("%Y-%m-%d"),
                "columns": summary.columns.to_list(),
                "rows": summary.to_dict(orient="records"),
                "error": None
            }
    except Exception as e:
        logging.exception("処理失敗")
        return {
            "status": "ERROR",
            "project_id": project_id,
            "row_count": 0,
            "processed_until": last_processed_date,
            "columns": [],
            "rows": [],
            "error": str(e)
        }

# テストケース
# テストケース①：増分データが存在する場合
# last_processed_date に以下を指定してください。
last_processed_date = "2026-11-03"
# 期待される抽出データ：
#   order_date	product_id	sales
#   2026-11-04	B	150
#   2026-11-05	C	400
#   2026-11-05	A	250
# 期待される集計結果：
#   product_id	total_sales
#   C	400
#   A	250
#   B	150
# 期待される戻り値の主な項目：
#   項目	期待値
#   status	"OK"
#   row_count	3
#   processed_until	"2026-11-05"
#   columns	["product_id", "total_sales"]
#   error	None

case1 = process_incremental_sales(
    "resonant-tract-508812-p9",
    sql1,
    last_processed_date
)
print(case1)

# テストケース②：増分データが存在しない場合
# last_processed_date に以下を指定してください。
last_processed_date = "2026-11-05"
# 期待される結果：
#   項目	期待値
#   status	"OK"
#   row_count	0
#   processed_until	"2026-11-05"
#   columns	["product_id", "total_sales"]
#   rows	[]
#   error	None
# 今回は、データが0件の場合も正常終了として扱います。

case2 = process_incremental_sales(
    "resonant-tract-508812-p9",
    sql1,
    last_processed_date
)
print(case2)


### STEP 6-2｜SQL側での増分抽出
#
# 今回使うPython・pandasの知識
# ① SQL側での増分抽出




































































