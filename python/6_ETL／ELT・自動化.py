
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
# STEP 6-1では、BigQueryから全件取得した後、pandasで増分データを抽出しました。
df = query_job.result().to_dataframe(
    create_bqstorage_client=False
)
watermark = pd.to_datetime(last_processed_date)
increment_df = df[
    df["order_date"] > watermark
]
# この方法では、処理済みのデータもPython側に転送されます。
# 今回は、BigQueryのSQLで増分データを抽出してから、pandasに取り込みます。
# SQLで日付を比較する場合は、次のように書きます。
"""
SELECT
  order_date,
  product_id,
  sales
FROM `project.dataset.orders`
WHERE order_date > DATE '2026-11-03'
"""
# これにより、11月4日以降のデータだけを取得できますが、WHERE 句によって必ずBigQueryのスキャン量や料金が減るわけではありません。
# 例えば、日付列でパーティション分割されたテーブルであれば、条件によって読み取り対象のパーティションを削減できる場合があります。
#
# ② クエリパラメータ
# ウォーターマークを毎回SQLに直接書き込むのは不便です。
# 例えば、次のSQLでは日付が固定されています。
"WHERE order_date > DATE '2026-11-03'"
# Pythonから実行する場合、ウォーターマークの値を変数として渡したいところです。
# そこで使用するのが、クエリパラメータです。
# BigQueryでは、名前付きパラメータを @パラメータ名 と記述します。
"""
SELECT
  order_date,
  product_id,
  sales
FROM `project.dataset.orders`
WHERE order_date > @watermark
"""
# @watermark の値は、Python側から指定できます。
# クエリパラメータを使用すると、SQL文字列に値を直接埋め込む必要がなくなり、値の型も明確に指定できます。
# なお、クエリパラメータは日付や数値などの値を渡す仕組みです。テーブル名や列名を置き換える用途には使用できません。
#
# ③ bigquery.ScalarQueryParameter()
# BigQueryに単一の値を渡す場合に使用するクラスです。
# 基本構文：
bigquery.ScalarQueryParameter(
    name,
    type_,
    value
)
#   引数	    内容	                指定例
#   name	パラメータ名	        "watermark"
#   type_	BigQueryのデータ型	"DATE"
#   value	渡す値	            "2026-11-03"
# 使用例：
parameter = bigquery.ScalarQueryParameter(
    "watermark",
    "DATE",
    "2026-11-03"
)
# この場合、SQL内の @watermark に日付 2026-11-03 が渡されます。
# 主な型には次のものがあります。
#   BigQueryの型	 用途
#   STRING	     文字列
#   INT64	     整数
#   FLOAT64	     浮動小数点数
#   DATE	     日付
#   TIMESTAMP	 タイムスタンプ
#   BOOL	     真偽値
#
# ④ bigquery.QueryJobConfig()
# bigquery.QueryJobConfig は、SQLクエリを実行するジョブの設定を指定するクラスです。
# STEP 5-5では、DataFrameをBigQueryへ書き込むために bigquery.LoadJobConfig を使用しました。
# 今回はSQLを実行するため、QueryJobConfig を使用します。
job_config = bigquery.QueryJobConfig(
    query_parameters=[
        bigquery.ScalarQueryParameter(
            "watermark",
            "DATE",
            "2026-11-03"
        )
    ]
)
# query_parameters は、SQLに渡すパラメータのリストです。
# 設定した job_config は、次のように client.query() に渡します。
query_job = client.query(
    sql,
    job_config=job_config
)
# これにより、SQL内の @watermark に指定した日付が適用されます。
#   LoadJobConfig と QueryJobConfig の違い
#   クラス	        用途
#   LoadJobConfig	データをBigQueryにロードする際の設定
#   QueryJobConfig	BigQueryでSQLを実行する際の設定
#
# ⑤ pd.to_datetime() の応用
# 今回のウォーターマークは、Pythonの引数として文字列で受け取ります。
last_processed_date = "2026-11-03"
# BigQueryへ DATE パラメータとして渡す際には、pd.to_datetime() で Timestamp 型に変換後、Python標準の date 型にする方法があります。
watermark = pd.to_datetime(last_processed_date).date()
# pd.to_datetime() は Timestamp 型を返しますが、.date() によって日付部分だけを取り出せます。
print(type(watermark))  # <class 'datetime.date'>
# この値は、BigQueryの DATE パラメータとして使用できます。
# 応用ポイントは、pandasで扱う日時データと、BigQueryに渡す日付データの型を意識することです。
#
# ⑥ DataFrame.max() の応用
# STEP 6-1では、増分抽出後のDataFrameから最新日付を取得しました。
latest_date = increment_df["order_date"].max()
# STEP 6-2では、BigQuery側ですでに増分抽出が完了します。
# そのため、Python側で取得したDataFrameから直接、最新日付を取得できます。
latest_date = df["order_date"].max()
# ただし、BigQueryの DATE 列は、取得方法によってPythonの datetime.date オブジェクトとして扱われることがあります。
# そのため、日付型を統一してから最大値を取得する方法もあります。
df["order_date"] = pd.to_datetime(df["order_date"])
latest_date = df["order_date"].max()
# 今回はデータが0件の場合、STEP 6-1と同様に df.empty で分岐してください。

# 演習
# BigQuery側でウォーターマークによる増分抽出を実行し、取得したデータをpandasで集計する関数を実装してください。
# 増分抽出をPython側ではなくSQL側で行います。今回はBigQueryへの書き込みは行いません。
# 使用するデータ
# 今回は実テーブルを作成せず、次のCTEを使ったSQLによる仮想の売上データを使用してください。
sql1 = """
WITH orders AS (
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
)
SELECT
  order_date,
  product_id,
  sales
FROM orders
WHERE order_date > @watermark
"""
# このSQLの @watermark に、Python側からクエリパラメータを渡します。

# 実装要件
# 関数名：
#   process_incremental_sales_sql
# 引数：
#   引数                  内容
#   project_id           BigQueryのプロジェクトID
#   sql                  増分抽出用SQL
#   last_processed_date  前回処理済みの最新日付（文字列）
# 処理内容：
#   bigquery.Client() でBigQueryに接続する。
#   last_processed_date を日付型に変換する。
#   ScalarQueryParameter で watermark パラメータを作成する。
#   QueryJobConfig にパラメータを設定する。
#   client.query() でSQLを実行する。
#   クエリ結果をDataFrameとして取得する。
#   order_date 列を日付型に変換する。
#   増分データが0件かどうかを判定する。
#   データがある場合、product_id ごとに売上を合計し、total_sales の降順に並べ替える。
#   処理対象データの最新日付を取得する。
#   処理結果を辞書で返し、ログを記録する。
# 戻り値の形式：
# {
#     "status": "OK" または "ERROR",
#     "project_id": プロジェクトID,
#     "row_count": 増分抽出した明細の行数,
#     "processed_until": 処理済みの最新日付,
#     "columns": ["product_id", "total_sales"],
#     "rows": [
#         {"product_id": 商品ID, "total_sales": 売上合計},
#         ...
#     ],
#     "error": None または エラーメッセージ
# }
# 増分データが0件の場合は、status="OK"、row_count=0、rows=[]、processed_until は元の日付を維持してください。
# エラー時は、status="ERROR"、row_count=0、columnsとrows=[]、processed_until は元の日付を維持、error に例外メッセージを格納。

def process_incremental_sales_sql(project_id, sql, last_processed_date):
    try:
    # 関数が受け取った第三引数を BigQueryへ DATEパラメータとして渡すための変換
        prm_date = pd.to_datetime(last_processed_date).date()
    # BigQuery接続
        client = bigquery.Client(
            project=project_id
        )
    # SQLクエリ実行ジョブ設定
        query_job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter(
                    "watermark",
                    "DATE",
                    prm_date
                )
            ]
        )
    # SQL実行
        query_job = client.query(
            sql,
            job_config=query_job_config
        )
    # ジョブ完了待ち・結果のDataFrame変換
        df = query_job.result().to_dataframe(
            create_bqstorage_client=False
        )
    # 増分データが0件かどうか判定・0件ならば早期return
        if df.empty:
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
    # 増分データがある場合の処理
        else:
            df["order_date"] = pd.to_datetime(df["order_date"])
            processed_until = df["order_date"].max()
            summary = df.groupby(
                "product_id",
                as_index=False
            ).agg(
                total_sales=("sales", "sum")
            )
            summary = summary.sort_values(
                "total_sales",
                ascending=False
            )
            summary = summary.reset_index(drop=True)
            logging.info("処理成功")
            return {
                "status": "OK",
                "project_id": project_id,
                "row_count": df.shape[0],
                "processed_until": processed_until.strftime("%Y-%m-%d"),
                "columns": summary.columns.to_list(),
                "rows": summary.to_dict(orient="records"),
                "error": None
            }
    # エラー処理
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
# 引数：
last_processed_date = "2026-11-03"
# 期待される戻り値：
# {
#     "status": "OK",
#     "project_id": "resonant-tract-508812-p9",
#     "row_count": 3,
#     "processed_until": "2026-11-05",
#     "columns": ["product_id", "total_sales"],
#     "rows": [
#         {"product_id": "C", "total_sales": 400},
#         {"product_id": "A", "total_sales": 250},
#         {"product_id": "B", "total_sales": 150}
#     ],
#     "error": None
# }

case1 = process_incremental_sales_sql("resonant-tract-508812-p9",
                                      sql1,
                                      last_processed_date)
print(case1)

# テストケース②：増分データが存在しない場合
# 引数：
last_processed_date = "2026-11-05"
# 期待される戻り値：
# {
#     "status": "OK",
#     "project_id": "resonant-tract-508812-p9",
#     "row_count": 0,
#     "processed_until": "2026-11-05",
#     "columns": ["product_id", "total_sales"],
#     "rows": [],
#     "error": None
# }

case2 = process_incremental_sales_sql("resonant-tract-508812-p9",
                                      sql1,
                                      last_processed_date)
print(case2)


### STEP 6-3｜ウォーターマークの永続化
#
# 今回使うPython・pandasの知識
# ① ウォーターマークの永続化
# STEP 6-1とSTEP 6-2では、前回処理済みの日付を次のような引数で指定していました。
last_processed_date = "2026-11-03"
# しかし、実務で毎日パイプラインを動かす場合、実行するたびに人が日付を指定するのは現実的ではありません。
# そこで、前回処理した日付をBigQueryなどに保存し、次回実行時に自動的に読み込む仕組みを作ります。
#   BigQuery状態管理テーブル 保存済み：2026-11-03
#     ↓
#   Pythonでウォーターマークを読み込む 2026-11-03より新しいデータを取得
#     ↓
#   増分データを処理 最新日付：2026-11-05
#     ↓
#   BigQuery状態管理テーブルを更新 2026-11-05を保存
# これにより、次回実行時には自動的に11月5日以降のデータを対象にできます。
#
# ② BigQueryの状態管理テーブル
# ウォーターマークを保存する専用テーブルを作成します。
# 今回のテーブル名：
#   resonant-tract-508812-p9.sql_training.pipeline_watermarks
# テーブル構造：
#   pipeline_name	last_processed_date
#   sales_pipeline	2026-11-03
# pipeline_name は、どのパイプラインの状態かを識別するための文字列です。
# last_processed_date は、そのパイプラインが処理済みの最新日付です。
# 複数のパイプラインを管理する場合は、次のように行を増やせます。
#   pipeline_name	    last_processed_date
#   sales_pipeline	    2026-11-03
#   customer_pipeline	2026-11-01
# 今回は sales_pipeline の1行だけを扱います。
#
# ③ client.get_table()
# BigQueryにテーブルが存在するかを確認するために使用できます。
table = client.get_table(
    "resonant-tract-508812-p9.sql_training.pipeline_watermarks"
)
# テーブルが存在すれば、テーブル情報が返されます。
# 存在しなければ google.api_core.exceptions.NotFound が発生します。
# そのため、次のような分岐が可能です。
from google.api_core.exceptions import NotFound
try:
    table = client.get_table(table_id)
except NotFound:
    print("テーブルが存在しません")
# ここで重要なのは、テーブルが存在しないことと、BigQueryへの接続失敗などのエラーを区別することです。
#
# ④ bigquery.SchemaField() と client.create_table()
# BigQueryのテーブルをPythonから作成する場合は、まず列の構造を定義します。
schema = [
    bigquery.SchemaField("pipeline_name", "STRING"),
    bigquery.SchemaField("last_processed_date", "DATE")
]
# SchemaField() の基本構文は次のとおりです。
bigquery.SchemaField(
    name,
    field_type,
    mode="NULLABLE"
)
#   引数	        内容
#   name	    列名
#   field_type	BigQueryのデータ型
#   mode	    NULLを許可するかどうか
# mode は主に NULLABLE（NULL許可）、REQUIRED（NULL不可）、REPEATED（フィールドが配列となり同じデータ型の値を0個以上格納可能）があります。
# 今回の状態管理テーブルでは、2列とも REQUIRED にして構いません。
# テーブルを作成する場合は、bigquery.Table() と client.create_table() を組み合わせます。
table = bigquery.Table(
    table_id,
    schema=schema
)
client.create_table(table)
# これにより、指定したスキーマのテーブルがBigQueryに作成されます。
#
# ⑤ client.insert_rows_json()
# 作成したテーブルにデータを追加する方法の1つです。
errors = client.insert_rows_json(
    table_id,
    [
        {"pipeline_name": "sales_pipeline",
        "last_processed_date": "2026-11-03"}
    ]
)
# insert_rows_json() は、辞書形式のデータをBigQueryへ追加します。
# 戻り値の errors が空リスト [] であれば、行の挿入要求が受理されたことを意味します。非空の場合は、行ごとのエラー情報が格納されます。
# ただし、このメソッドは既存行を更新するものではありません。同じ pipeline_name の行を何度も挿入すると、重複する可能性があります。
# また、ストリーミング挿入した行は、直後にDMLで更新できない場合があります。
# そのため、今回このメソッドは知識として紹介し、実際のウォーターマーク更新には次の MERGE を使用します。
#
# ⑥ MERGE 文
# MERGE は、既存データの更新と新規データの追加を、条件に応じて実行するSQLです。
# 例えば、pipeline_name が一致する行が存在すれば更新し、存在しなければ追加します。
"""
MERGE `project.dataset.pipeline_watermarks` AS target
USING (
  SELECT
    @pipeline_name AS pipeline_name,
    @new_date AS last_processed_date
) AS source
ON target.pipeline_name = source.pipeline_name

WHEN MATCHED THEN
  UPDATE SET
    last_processed_date = source.last_processed_date

WHEN NOT MATCHED THEN
  INSERT (pipeline_name, last_processed_date)
  VALUES (source.pipeline_name, source.last_processed_date)
"""
# 今回は @pipeline_name と @new_date をクエリパラメータとして渡します。
# なお、MERGE はBigQueryのDML文であり、BigQuery SandboxではDMLが制限されるため、無料Sandbox環境では実行できない場合があります。
# その場合は、今回の学習で使用する保存方式を変更する必要があります。
#
# ⑦ pd.to_datetime() の応用
# BigQuery状態管理テーブルから読み込んだ日付は、Python側で型を確認して扱います。
watermark = pd.to_datetime(saved_date).date()
# これにより、文字列や datetime.date 型の値を、Pythonの date 型に統一できます。
# 今回は保存されたウォーターマークを、STEP 6-2で学習した ScalarQueryParameter に渡します。
#
# ⑧ DataFrame.max()
# 処理済みの最新日付を取得する際には、次のように使用します。
latest_date = df["order_date"].max()
# ただし、今回は取得した日付を単に戻り値に含めるだけではありません。
# 最新日付を状態管理テーブルに保存し、次回実行時のウォーターマークとして利用する点が応用部分です。
# データが0件の場合は、保存済みのウォーターマークを変更しません。

# 演習
# BigQueryに保存したウォーターマークを読み込み、その値を使用して増分抽出を実行し、処理後の最新日付を再びBigQueryに保存する仕組みを実装します。
# ただし、今回はBigQuery Sandboxの制約を考慮し、実装を2段階に分けます。
# まず、ウォーターマークの読み込みと増分処理を実装します。
# 更新処理については、使用中のBigQuery環境で MERGE が実行可能か確認してから進めます。

# 使用するデータ
# 次のCTEを使ったSQLによる仮想の売上データ（STEP 6-2と同様）を使用します。
sql1 = """
WITH orders AS (
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
)
SELECT
  order_date,
  product_id,
  sales
FROM orders
WHERE order_date > @watermark
"""

# 実装要件
# 関数名：
#   process_sales_with_persistent_watermark
# 引数：
#   project_id	     BigQueryのプロジェクトID
#   sql	             売上データの増分抽出SQL
#   watermark_table	 ウォーターマーク保存先テーブル
#   pipeline_name	 パイプライン識別名
# 処理内容：
#   BigQueryに接続する。
#   状態管理テーブルの存在を確認する。
#   テーブルが存在しなければ、指定したスキーマで作成する。
#   pipeline_name に対応するウォーターマークを取得する。
#   初回実行で保存済みのウォーターマークが存在しない場合は、2026-11-03 を初期値として使用する。
#   ウォーターマークをクエリパラメータに渡し、増分データを取得する。
#   増分データが存在する場合、商品別売上を集計する。
#   処理済みの最新日付を取得する。
#   増分データが0件の場合は、ウォーターマークを変更しない。
#   正常系・異常系の結果を辞書で返す。
# まずは状態管理テーブルの作成とウォーターマークの読み込み・処理部分を実装してください。MERGEによるウォーターマークの更新処理はその後に扱います。

def process_sales_with_persistent_watermark(project_id, sql, watermark_table, pipeline_name):
    try:
        client = bigquery.Client(
            project=project_id
        )
        try:
            client.get_table(watermark_table)
        except NotFound:
            schema = [
                bigquery.SchemaField("pipeline_name", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("last_processed_date", "DATE", mode="REQUIRED"),
            ]
            table = bigquery.Table(
                watermark_table,
                schema=schema
            )
            client.create_table(table)

            initial_df = pd.DataFrame(
                [
                    {"pipeline_name": pipeline_name,
                     "last_processed_date": pd.to_datetime("2026-11-03").date()}
                ]
            )
            load_job_config = bigquery.LoadJobConfig(
                schema=[
                    bigquery.SchemaField("pipeline_name", "STRING", mode="REQUIRED"),
                    bigquery.SchemaField("last_processed_date", "DATE", mode="REQUIRED")
                ],
                write_disposition=bigquery.WriteDisposition.WRITE_APPEND
            )
            load_job = client.load_table_from_dataframe(
                initial_df,
                watermark_table,
                job_config=load_job_config
                )
            load_job.result()

        watermark_query_job = client.query(
            f"""
            SELECT
                pipeline_name,
                last_processed_date
            FROM `{watermark_table}`
                WHERE pipeline_name = '{pipeline_name}'
            """
        )
        watermark_df = watermark_query_job.result().to_dataframe(
            create_bqstorage_client=False
        )
        watermark_df["last_processed_date"] = pd.to_datetime(watermark_df["last_processed_date"])
        latest_date = watermark_df["last_processed_date"].max()

        increment_query_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter(
                    "watermark",
                    "DATE",
                    latest_date.date()
                )
            ]
        )
        increment_query_job = client.query(
            sql,
            job_config=increment_query_config
        )
        increment_df = increment_query_job.result().to_dataframe(
            create_bqstorage_client=False
        )

        if increment_df.empty:
            logging.info("増分なし")
            return {
                "status": "OK",
                "project_id": project_id,
                "pipeline_name": pipeline_name,
                "row_count": 0,
                "previous_watermark": latest_date.strftime("%Y-%m-%d"),
                "processed_until": latest_date.strftime("%Y-%m-%d"),
                "columns": ["product_id", "total_sales"],
                "rows": [],
                "error": None
            }
        else:
            increment_df["order_date"] = pd.to_datetime(increment_df["order_date"])
            processed_until = increment_df["order_date"].max()

            summary = increment_df.groupby(
                "product_id",
                as_index=False
            ).agg(
                total_sales=("sales", "sum")
            )
            summary = summary.sort_values(
                "total_sales",
                ascending=False
            )
            summary = summary.reset_index(drop=True)

            increment_watermark_df = pd.DataFrame(
                [
                    {"pipeline_name": pipeline_name,
                     "last_processed_date": pd.to_datetime(processed_until).date()}
                ]
            )
            load_append_job_config = bigquery.LoadJobConfig(
                schema=[
                    bigquery.SchemaField("pipeline_name", "STRING", mode="REQUIRED"),
                    bigquery.SchemaField("last_processed_date", "DATE", mode="REQUIRED")
                ],
                write_disposition=bigquery.WriteDisposition.WRITE_APPEND
            )
            load_append_job = client.load_table_from_dataframe(
                increment_watermark_df,
                watermark_table,
                job_config=load_append_job_config
            )
            load_append_job.result()

            logging.info("処理成功")
            return {
                "status": "OK",
                "project_id": project_id,
                "pipeline_name": pipeline_name,
                "row_count": increment_df.shape[0],
                "previous_watermark": latest_date.strftime("%Y-%m-%d"),
                "processed_until": processed_until.strftime("%Y-%m-%d"),
                "columns": summary.columns.to_list(),
                "rows": summary.to_dict(orient="records"),
                "error": None
            }
    except Exception as e:
        logging.exception("処理失敗")
        return {
            "status": "ERROR",
            "project_id": project_id,
            "pipeline_name": pipeline_name,
            "row_count": 0,
            "previous_watermark": None,
            "processed_until": None,
            "columns": [],
            "rows": [],
            "error": str(e)
        }

# テストケース
# テストケース①：初回実行
# 状態管理テーブルに sales_pipeline のウォーターマークが保存されていない状態で実行します。
# 期待値：
# {
#     "status": "OK",
#     "project_id": "resonant-tract-508812-p9",
#     "pipeline_name": "sales_pipeline",
#     "row_count": 3,
#     "previous_watermark": "2026-11-03",
#     "processed_until": "2026-11-05",
#     "columns": ["product_id", "total_sales"],
#     "rows": [
#         {"product_id": "C", "total_sales": 400},
#         {"product_id": "A", "total_sales": 250},
#         {"product_id": "B", "total_sales": 150}
#     ],
#     "error": None
# }

case1 = process_sales_with_persistent_watermark(
    "resonant-tract-508812-p9",
    sql1,
    "resonant-tract-508812-p9.sql_training.pipeline_watermarks",
    "sales_pipeline")
print(case1)

# テストケース②：保存済みウォーターマークが存在する場合
# 状態管理テーブルに以下が保存されている状態で実行します。
#   pipeline_name	last_processed_date
#   sales_pipeline	2026-11-05
# 期待値：
# {
#     "status": "OK",
#     "project_id": "resonant-tract-508812-p9",
#     "pipeline_name": "sales_pipeline",
#     "row_count": 0,
#     "previous_watermark": "2026-11-05",
#     "processed_until": "2026-11-05",
#     "columns": ["product_id", "total_sales"],
#     "rows": [],
#     "error": None
# }

case2 = process_sales_with_persistent_watermark(
    "resonant-tract-508812-p9",
    sql1,
    "resonant-tract-508812-p9.sql_training.pipeline_watermarks",
    "sales_pipeline"
)
print(case2)

# 対象テーブルだけを削除するコード
from google.cloud import bigquery
client = bigquery.Client(
    project="resonant-tract-508812-p9"
)
table_id = "resonant-tract-508812-p9.sql_training.pipeline_watermarks"
client.delete_table(
    table_id,
    not_found_ok=True
)
print("状態管理テーブルの削除完了")


### STEP 6-4｜ETLパイプラインの異常系テストとエラーハンドリング
# 今回は、これまで作成してきたBigQuery連携パイプラインについて、
# SQL実行時のエラーやデータ取得時の失敗を意図的に発生させ、Python側で適切に処理できるかを検証します。
# 新しいライブラリとして、Python標準ライブラリの unittest.mock を使用します（追加インストールは不要）。
#
# 今回使うPython・pandasの知識
# ① try / except と logging.exception() の応用
























































