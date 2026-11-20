
### STEP 6-1｜増分処理
# STEP 6では、これまで実装してきたデータ取得・加工・保存の処理を、継続的に運用できるデータパイプラインへ発展させます。
#
# 今回使うPython・pandasの知識
# ① pd.to_datetime()
# pd.to_datetime() は、文字列などの日付データを、pandasで日付・時刻として扱える型に変換する関数です。
# 今回のSTEP 6-1では、前回処理した日付とBigQueryから取得した売上データの日付を比較し、増分データを抽出するために使用します。
# 例えば、次のような文字列があるとします。
import pandas as pd
from pandas.io.formats.format import return_docstring

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
# STEP 6-3では、次のような例外処理を実装しました。
try:
    # BigQuery接続・SQL実行・データ加工
    pass
except Exception as e:
    logging.exception("処理失敗")
# 今回は、実際に例外が発生したときに、この処理が期待どおり動作するかを確認します。
# logging.exception() は、例外メッセージだけでなく、どこでエラーが発生したかを示すトレースバックも記録します。
# 例えば、SQL実行中に例外が発生した場合、エラーを記録したうえで、呼び出し元に status="ERROR" を返せるかを検証します。
#
# ② raise
# raise は、Pythonで意図的に例外を発生させる構文です。
# 例えば、
def check_value(value):
    if value < 0:
        raise ValueError("負の値は指定できません")
    return value
# この関数に -1 を渡すと、ValueError が発生します。
# 一方、10 を渡せば正常に値が返ります。
# 今回の演習では、異常系テストのために意図的にエラーを発生させる用途で使用します。
#
# ③ RuntimeError
# RuntimeError は、プログラムの実行中に発生した問題を表す例外クラスです。
# これを try / except で捕捉すると、
try:
    raise RuntimeError("データ取得に失敗しました")
except Exception as e:
    print(str(e))  # データ取得に失敗しました
# 今回のテストでは、BigQueryからのデータ取得が失敗した状況を再現するために使用します。
#
# ④ unittest.mock.patch()
# ここが今回の重要な新規知識です。
# 実際のBigQueryで障害を発生させなくても、Python側で特定の処理だけをテスト用の動作に差し替えられます。
# これを「モック」と呼びます。
# 例えば、次の関数があるとします。
def get_data():
    return "取得成功"
# 通常は、
print(get_data())
# とすると、取得成功 が表示されます。
# しかし、patch() を使用すると、テスト中だけ別の動作にできます。
from unittest.mock import patch
with patch("__main__.get_data", return_value="テスト用データ"):
    print(get_data())
# 出力：テスト用データ
# with ブロックを抜けると、元の関数の動作に戻ります。
# ここでの "__main__.get_data" は、get_data が現在の実行スクリプトに定義されている場合の指定です。
# 別のPythonファイルから読み込んでいる場合は、参照先に応じて指定が変わります。
#
# ⑤ Mock()
# Mock() は、テスト用のオブジェクトを作成するための機能です。
from unittest.mock import Mock
mock_client = Mock()
# 例えば、メソッドの戻り値を設定できます。
mock_client.get_data.return_value = "テストデータ"
print(mock_client.get_data())
# 出力：テストデータ
# これにより、実際の外部サービスに接続せず、戻り値や例外を自由に設定できます。
#
# ⑥ side_effect
# side_effect を使用すると、モックのメソッドが呼び出された際に例外を発生させられます。
mock_client = Mock()
mock_client.get_data.side_effect = RuntimeError(
    "データ取得に失敗しました"
)
# この状態で、mock_client.get_data() を呼び出すと、指定した RuntimeError が発生します。
# 通常の return_value との違いは次のとおりです。
#   設定	                             動作
#   return_value	                 指定した値を返す
#   side_effect = RuntimeError(...)	 指定した例外を発生させる
# 今回のテストでは、これを利用してBigQueryのデータ取得失敗を再現します。
#
# ⑦ assert の応用
# assert は、条件が正しいことを検証する構文です。
result = {"status": "ERROR", "error": "SQL実行失敗"}
assert result["status"] == "ERROR"
assert result["error"] == "SQL実行失敗"
# 条件がすべて成立すれば、そのまま処理が進みます。
# 条件が成立しなければ、AssertionError が発生します。
# 今回は、単にエラーが発生したかを見るだけでなく、関数が期待した形式でエラー情報を返しているかを検証します。

# 演習の目的
# STEP 6-3で作成した関数を対象に、以下の2つの異常系を検証します。
#   テストケース①：SQL実行エラー
#   テストケース②：BigQueryからのデータ取得失敗
# 今回は異常系テストが目的なので、ウォーターマークの保存・更新や商品別売上の集計処理を新たに実装する必要はありません。
# また、BigQuery Sandboxで利用できないDMLやストリーミング挿入は使用しません。

# 実装する関数
# 今回は、STEP 6-3で作成した以下の関数をそのまま利用します。
#   process_sales_with_persistent_watermark(project_id, sql, watermark_table, pipeline_name)
# 関数の正常系の処理は変更しません。
# テスト用コードを別途作成し、異常時の動作を確認してください。

# テストケース
# テストケース①：SQL実行エラー
# 目的：
#   SQLの構文エラーが発生した場合、関数が例外を捕捉して ERROR を返せるか確認する。
# 今回は、実際のBigQueryに対して意図的に不正なSQLを実行します。
# テスト用SQL：
invalid_sql = """
SELECT
    FROM
"""

# 期待する戻り値：
# {
#     "status": "ERROR",
#     "project_id": "resonant-tract-508812-p9",
#     "pipeline_name": "sales_pipeline",
#     "row_count": 0,
#     "previous_watermark": None,
#     "processed_until": None,
#     "columns": [],
#     "rows": [],
#     "error": "BigQueryから返されたエラーメッセージ"
# }
# error の具体的な文字列はBigQuery側の応答によって変わるため、完全一致は要求しません。
# ただし、error が None ではなく、SQL実行失敗を示す文字列になっていることを確認してください。
# また、logging.exception() によってトレースバックが出力されることも確認します。

case1 = process_sales_with_persistent_watermark(
    "resonant-tract-508812-p9",
    invalid_sql,
    "resonant-tract-508812-p9.sql_training.pipeline_watermarks",
    "sales_pipeline"
)
print(case1)

# テストケース②：データ取得失敗
# 目的：
#   SQL実行後のDataFrame取得が失敗した場合、例外を捕捉できるか確認する。
# 今回は、実際のBigQueryで障害を起こすのではなく、unittest.mock を使用します。
# STEP 6-3の関数では、データ取得時に次の処理を行っています。
increment_df = increment_query_job.result().to_dataframe(
    create_bqstorage_client=False
)
# この to_dataframe() が失敗する状況を再現します。
# そのために、patch()、Mock()、side_effect を使用してください。
# 今回はテスト用モックを構築する部分が新規学習内容なので、必要な構成を示します。
from unittest.mock import patch, Mock
mock_job = Mock()
mock_job.result.return_value.to_dataframe.side_effect = RuntimeError(
    "データ取得に失敗しました"
)
# このコードでは、mock_job.result().to_dataframe() が呼び出されると RuntimeError が発生します。
# ただし、STEP 6-3の関数は、ウォーターマーク取得時にも to_dataframe() を使用しています。
# そのため、ウォーターマーク取得は正常に動作させ、増分データ取得の部分だけを失敗させる必要があります。
# 具体的には、client.query() の呼び出しが2回あることを考慮し、
# 1回目には正常なウォーターマーク取得結果、2回目にはエラーを発生させるモックを返すように設定してください。
# 今回のテストで使用する正常なウォーターマークDataFrameは、次のものです。
watermark_test_df = pd.DataFrame(
    [
        {"pipeline_name": "sales_pipeline",
        "last_processed_date": pd.to_datetime("2026-11-05")}
        ]
)
# テスト対象関数内の bigquery.Client() を patch() で差し替えることで、実際のBigQueryへの接続なしに検証できます。
# 期待する戻り値：
# {
#     "status": "ERROR",
#     "project_id": "resonant-tract-508812-p9",
#     "pipeline_name": "sales_pipeline",
#     "row_count": 0,
#     "previous_watermark": None,
#     "processed_until": None,
#     "columns": [],
#     "rows": [],
#     "error": "データ取得に失敗しました"
# }
# こちらは、RuntimeError のメッセージを自分で設定しているため、error の文字列も完全一致で確認できます。
# テストケース②は、Mock() と patch() を使用して、SQL実行後の to_dataframe() だけを意図的に失敗させるテストです。
# テストケース①と異なり、実際のBigQueryには接続しません。

from unittest.mock import Mock, patch
# ① テスト用のウォーターマークDataFrame
watermark_test_df = pd.DataFrame(
    [
        {"pipeline_name": "sales_pipeline",
        "last_processed_date": pd.to_datetime("2026-11-05")}
    ]
)
# ② 1回目のクエリ：ウォーターマーク取得成功
mock_watermark_job = Mock()
mock_watermark_job.result.return_value.to_dataframe.return_value = watermark_test_df
# ③ 2回目のクエリ：データ取得失敗
mock_increment_job = Mock()
mock_increment_job.result.return_value.to_dataframe.side_effect = RuntimeError(
    "データ取得に失敗しました"
)
# ④ BigQueryクライアントをテスト用に差し替える
with patch.object(bigquery, "Client") as mock_client_class:
    # 偽物のクライアントを取得
    mock_client = mock_client_class.return_value
    # 状態管理テーブルは存在することにする
    mock_client.get_table.return_value = Mock()
    # query()の1回目・2回目の戻り値を設定
    mock_client.query.side_effect = [
        mock_watermark_job,
        mock_increment_job
    ]
    # ⑤ STEP 6-3の関数を実行
    case2 = process_sales_with_persistent_watermark(
        "resonant-tract-508812-p9",
        sql1,
        "resonant-tract-508812-p9.sql_training.pipeline_watermarks",
        "sales_pipeline"
    )
print(case2)


### STEP 6-4.5｜モック基礎
## モックとは何か・なぜ必要なのか
#
# 例えば、次のような処理があるとします。
# あるECサイトで、商品の単価と数量から購入金額を計算するプログラムです。
def get_price():
    return 1000
def calculate_total(quantity):
    price = get_price()
    return price * quantity
result = calculate_total(3)
print(result)  # 3000
# このコードには、2つの関数があります。
#   get_price() 商品の単価を取得する関数です。今回は単純に 1000 を返します。
#   calculate_total(quantity)  商品の単価を取得し、数量を掛けて合計金額を返す関数です。
# ここまでは通常のPythonの処理です。では、なぜモックが必要なのでしょうか？
# 実務では、get_price() が必ずしも単純な関数とは限りません。
#
# 例えば、BigQueryから商品の価格を取得する関数だったとします。
def get_price():
    # BigQueryに接続して商品の単価を取得する処理
    pass
# この場合、calculate_total() をテストするたびに、BigQueryへ接続することになります。
# しかし、確認したいのは「取得した単価に数量を掛ける計算が正しいか」という部分だけかもしれません。
# それなのに、BigQueryへの接続が失敗すると合計金額の計算が正しいかどうかを確認できなくなります。
# そこで、次のように考えます。
#
# 「BigQueryから単価を取得する部分は、テスト中だけ偽物に置き換えて、必ず1000を返すようにできないだろうか？」
# このような場面で使用するのが、モック（Mock）です。
# 先ほどの処理を、通常時とテスト時で比較します。
#   通常の処理 calculate_total()            モックを使うテスト calculate_total()
#     ↓                                     ↓
#   本物の get_price() BigQueryへ接続        偽物の get_price() BigQueryには接続しない
#     ↓                                     ↓
#   取得した単価を返す                        1000 を返す
#
# 重要なのは、calculate_total() 自体の計算処理は変更しないという点です。
# 変更するのは、calculate_total() が呼び出す get_price() の動作だけです。
# テスト中は、あらかじめ決めた値を返すようにすることで、外部サービスの状態に左右されず計算処理を確認できます。
# なお、Pythonでは unittest.mock を使ってこのような差し替えを実現でき、具体的な構文は後の段階で学びます。
#
# 「テスト対象」と「依存先」の違い
# モックを理解するうえで、この2つの言葉は重要です。
#   用語	        今回の例	            意味
#   テスト対象	calculate_total()	正しく動くか確認したい処理
#   依存先	    get_price()	        テスト対象が利用する別の処理
# 目的は、calculate_total() の計算が正しいか確認することです。
# そのため、get_price() をモックに置き換えることを考えます。
# 一方、get_price() が本当にBigQueryから正しい価格を取得できるかはこのテストでは確認できないので、そこは別のテストで確認する必要があります。
# モックを使うことで、すべての処理が正しいと証明できるわけではない、という点も覚えておいてください。
#
# 演習：モックを使わず、仕組みを理解する
# まだ Mock() や patch() は使用しません。
# 次のコードを確認してください。
def get_price():
    return 500
def calculate_total(quantity):
    price = get_price()
    return price * quantity
print(calculate_total(4))
# 問題① このコードを実行すると、何が出力されますか？
#   2000
# 問題② calculate_total() のコードを変更せず、get_price() の戻り値だけを 800 に変更した場合、calculate_total(4) の結果は？
#   3200
# 問題③ 仮に get_price() がBigQueryへ接続する関数だった場合、
# calculate_total() の計算処理だけをテストするために、なぜ get_price() を偽物に置き換えることが有効なのでしょうか？
#   BigQueryへの接続が失敗すると合計金額の計算が正しいかどうかを確認できなくなるため。

## Mock() の基本操作
#
# Pythonには、テスト用の偽物のオブジェクトを作る Mock というクラスが用意されています。
from unittest.mock import Mock
fake_function = Mock()
# このコードを分解します。
#   ① from unittest.mock import Mock
#     Python標準ライブラリの unittest.mock から、Mock クラスを読み込んでいます。
#     追加インストールは不要です。
#   ② fake_function = Mock()
#     Mock クラスから、テスト用のオブジェクトを作成しています。
#     fake_function という変数に格納されたものは、通常のPython関数ではなく、関数のように呼び出せるモックオブジェクトです。
# 例えば、次のように呼び出せます。
fake_function()
# ただし、この段階では特定の処理や戻り値を設定していません。
#
# モックが呼び出されたか確認する
# 次のコードを見てください。
from unittest.mock import Mock
fake_function = Mock()
print(fake_function.called)  # False
fake_function()
print(fake_function.called)  # True
# called は、モックが一度でも呼び出されたかを表す属性です。
#   False：まだ一度も呼び出されていない
#   True：一度以上呼び出されている
# 注意したいのは、次の違いです。
fake_function.called
# これは属性の値を参照しています。
# 一方、
fake_function()
# こちらはモック自体を呼び出しています。
# called に () は付けません。
#
# モックの呼び出し回数を確認する
# 次に、call_count を使います。
from unittest.mock import Mock
fake_function = Mock()
print(fake_function.call_count)  # 0
fake_function()
fake_function()
print(fake_function.call_count)  # 2
# call_count は、そのモックが呼び出された回数を保持しています。
#   状態	        called	call_count
#   呼び出し前	False	0
#   1回呼び出し	True	1
#   2回呼び出し	True	2
# ここで重要なのは、モックは呼び出しの記録を自動的に保持してくれるということです。
# 例えば、実際のプログラムで「データ保存処理が1回だけ呼ばれたか」を確認したい場合にも、この仕組みを利用できます。
# ただし、今回の段階ではまだ本物の関数を差し替えていません。単独のモックを作成し、その動作を確認しているだけです。
#
# 演習：Mockの基本操作
# 今回は、自分で短いコードを書いてください。
# 要件
#   unittest.mock から Mock をインポートする。
#   mock_task という変数にモックを作成する。
#   呼び出し前の called と call_count を表示する。
#   mock_task を3回呼び出す。
#   呼び出し後の called と call_count を表示する。
from unittest.mock import Mock
mock_task = Mock()
print(mock_task.called)
print(mock_task.call_count)
mock_task()
mock_task()
mock_task()
print(mock_task.called)
print(mock_task.call_count)

## return_value による戻り値の設定
#
# ここからは、モックの「戻り値」を設定する方法を学びます。
# 今回は return_value だけを新しく扱います。
#
# return_value とは何か？
# 通常のPython関数では、return を使って戻り値を指定します。
def get_price():
    return 1000
print(get_price())  # 1000
# 一方、モックでは return_value を使って戻り値を設定できます。
from unittest.mock import Mock
mock_price = Mock()
mock_price.return_value = 1000
print(mock_price())  # 1000
# この2つは、呼び出したときに 1000 が返るという点では同じですが、仕組みは異なります。
#   通常の関数	            モック
#   return 1000	            return_value = 1000
#   関数内部に戻り値を記述	    モックの属性に戻り値を設定
#   get_price() で呼び出す	mock_price() で呼び出す
#
# コードを分解してみます
mock_price = Mock()             # これは、モックオブジェクトを作成しています。
mock_price.return_value = 1000  # これは、mock_price() が呼び出されたときに返す値を 1000 に設定しています。
print(mock_price())             # ここで初めてモックを呼び出し、設定した値を取得しています。
# 重要なのは、次の違いです。
mock_price.return_value
# これは設定されている戻り値を参照します。モックを実際に呼び出し、戻り値を取得します。同時に call_count も増加します。
#
# 戻り値は変更できる
# 例えば、次のコードを考えます。
from unittest.mock import Mock
mock_price = Mock()
mock_price.return_value = 500
print(mock_price())            # 500
mock_price.return_value = 800
print(mock_price())            # 800
print(mock_price.call_count)   # 2
# 最初は 500 を返し、途中で設定を変更すると 800 を返すようになります。
# return_value を変更しても、モックの呼び出し履歴はリセットされません。
#
# 演習：戻り値を設定する
# 今回も、短いコードを自分で作成してください。
# 要件
#   Mock をインポートする。
#   mock_price というモックを作成する。
#   return_value に 1200 を設定する。
#   mock_price() を呼び出し、結果を price1 に代入する。
#   return_value を 1800 に変更する。
#   mock_price() を再度呼び出し、結果を price2 に代入する。
#   price1、price2、mock_price.call_count を順番に表示する。
from unittest.mock import Mock
mock_price = Mock()
mock_price.return_value = 1200
price1 = mock_price()
mock_price.return_value = 1800
price2 = mock_price()
print(price1)
print(price2)
print(mock_price.call_count)

## side_effect による例外の再現
#
# ここからは、モックを使って意図的にエラーを発生させる方法を学びます。
# 前回のSTEP 6-4では、次のコードが登場しました。
mock_increment_job.result.return_value.to_dataframe.side_effect = RuntimeError(
    "データ取得に失敗しました"
)
# 今回はこの長いコードを扱いません。まず、side_effect が何をするものなのか、単純なモックを使って理解します。
#
# return_value と side_effect の違い
# まず、return_value を振り返ります。
from unittest.mock import Mock
mock_task = Mock()
mock_task.return_value = "成功"
print(mock_task())  # 成功
# これは、モックが呼び出されたときに "成功" を返す処理です。
# では、テストで「この処理が失敗した場合」を確認したいときは、どうすればよいでしょうか？
# そこで使用できるのが side_effect です。
from unittest.mock import Mock
mock_task = Mock()
mock_task.side_effect = RuntimeError("処理に失敗しました")
mock_task()
# 実行すると、RuntimeError: 処理に失敗しました の例外が発生します。
# ここで重要なのは、mock_task() を呼び出したタイミングでエラーが発生するという点です。
#   mock_task = Mock() モックを作成
#     ↓
#   mock_task.side_effect = RuntimeError(...) 呼び出し時に発生させる例外を設定
#     ↓
#   mock_task() ここで例外が発生する
#
# RuntimeError とは何か？
# RuntimeError は、Pythonに標準で用意されている例外クラスの一つです。
# 例えば、次のコードでも使用できます。
try:
    pass
except Exception as e:
    raise RuntimeError("処理に失敗しました")
# raise は、例外を発生させるための構文です。
# side_effect に例外オブジェクトを設定すると、モックを呼び出したときに、その例外が発生します。
# つまり、今回の2つは、例外を発生させるという点では似た働きをします。
# ただし、前者はその場所で直接例外を発生させます。後者はモックの呼び出し時に例外が発生します。
#
# try / except で例外を捕捉する
# 次のコードを見てください。
from unittest.mock import Mock
mock_task = Mock()
mock_task.side_effect = RuntimeError("データ取得に失敗しました")
try:
    mock_task()
except RuntimeError as e:
    print("エラーを捕捉しました")
    print(str(e))
# 実行結果：
#   エラーを捕捉しました
#   データ取得に失敗しました
# 処理は次の順番で進みます。
#   Mock() でモックを作成する。
#   side_effect に = RuntimeError(...) を設定する。
#   try の中で mock_task() を呼び出すと、設定した RuntimeError が発生する。
#   except RuntimeError as e で例外を捕捉して、str(e) で例外メッセージを取得する。
# これが、前回のSTEP 6-4で使用した異常系テストの基本的な仕組みです。
# ただし、現段階では、実際のBigQuery処理をモックに差し替える方法までは学んでいません。それは後の patch() で扱います。
#
# 演習：side_effect による例外の再現
# 今回は、side_effect を使用してエラーを発生させ、そのエラーを捕捉するコードを作成してください。
# 要件
#   Mock をインポートする。
#   mock_fetch というモックを作成する。
#   side_effect に RuntimeError("取得処理に失敗しました") を設定する。
#   try ブロック内で mock_fetch() を呼び出す。
# 5. except RuntimeError as e で例外を捕捉する。
# 6. 捕捉した例外メッセージを print(str(e)) で表示する。
# 7. 最後に mock_fetch.call_count を表示する。
from unittest.mock import Mock
mock_fetch = Mock()
mock_fetch.side_effect = RuntimeError("取得処理に失敗しました")
try:
    mock_fetch()
except RuntimeError as e:
    print(str(e))
print(mock_fetch.call_count)

## side_effect で呼び出しごとの戻り値を変更する
#
# 先ほどは side_effect を使って例外を発生させました。
# しかし、side_effect にはもう一つ重要な使い方があり、モックを呼び出すたびに、異なる戻り値を返せます。
# これは、STEP 6-4で使用した次のコードを理解するために必要な知識です。
mock_client.query.side_effect = [
    mock_watermark_job,
    mock_increment_job
]
# 今回は、まだこの複雑なコードを扱いません。まず単純な例から確認します。
#
# return_value との違い
# まず、これまで学習した return_value です。
from unittest.mock import Mock
mock_task = Mock()
mock_task.return_value = 100
print(mock_task())  # 100
print(mock_task())  # 100
print(mock_task())  # 100
# return_value に 100 を設定しているため、何度呼び出しても同じ値が返ります。
# 一方、side_effect にリストを設定すると、次のようになります。
from unittest.mock import Mock
mock_task = Mock()
mock_task.side_effect = [100, 200, 300]
print(mock_task())  # 100
print(mock_task())  # 200
print(mock_task())  # 300
# これは、モックが呼び出されるたびに、リストの値を先頭から順番に返しているためです。
# リストの値を使い切った場合、StopIteration の例外が発生します。
# StopIteration は、イテレーターから次の値を取得しようとしたときに、もう値が残っていないことを示す例外です。
# 設定した値の数より多くモックを呼び出すと、StopIteration が発生すると理解できれば十分です。
#
# 例外と戻り値を組み合わせることもできる
# 例えば、次のコードです。
from unittest.mock import Mock
mock_task = Mock()
mock_task.side_effect = [
    100,
    RuntimeError("2回目の処理に失敗しました"),
    300
]
try:
    print(mock_task())
    print(mock_task())
except RuntimeError as e:
    print(str(e))
print(mock_task())
# 実行結果：
#   100
#   2回目の処理に失敗しました
#   300
# ここでは、1回目は正常に値を返し、2回目だけ例外を発生させ、3回目は再び値を返しています。
# なお、2回目に例外が発生すると、その時点で try ブロック内の残りの処理は実行されず、except に移ります。
# この例では、3回目の mock_task() は try / except の外側にあるため実行されています。
#
# 演習：呼び出しごとに異なる値を返す
# 今回は、side_effect にリストを設定する演習です。
# 要件
#   Mock をインポートする。
#   mock_fetch というモックを作成する。
#   side_effect に [500, 800, 1200] を設定する。
#   mock_fetch() を3回呼び出し、それぞれの戻り値を result1、result2、result3 に代入する。
#   それぞれの戻り値を順番に表示する。
#   最後に mock_fetch.call_count を表示する。
from unittest.mock import Mock
mock_fetch = Mock()
mock_fetch.side_effect = [
    500,
    800,
    1200
]
result1 = mock_fetch()
result2 = mock_fetch()
result3 = mock_fetch()
print(result1)
print(result2)
print(result3)
print(mock_fetch.call_count)

## patch() による処理の差し替え
#
# 今回は、これまで作成してきたモックを、実際の関数の代わりに使用する方法を学びます。
# ここは前回のSTEP 6-4で特に説明が不足していた部分なので、まずは単純なPythonの関数だけを使用します。
def get_price():
    return 1000
def calculate_total(quantity):
    price = get_price()
    return price * quantity
print(calculate_total(3))  # 3000
# calculate_total() は、内部で get_price() を呼び出しています。ここで、次のようなテストを考えます。
# get_price() のコードを変更せずに、テスト中だけ戻り値を 500 にしたい。つまり、テスト時だけ以下の動作にしたいわけです。
def get_price():
    return 500
# しかし、本物の関数を書き換える必要はありません。そこで使用するのが patch() です。
#
# patch() の基本構文
# まず、完成したコードを示します。
from unittest.mock import patch
def get_price():
    return 1000
def calculate_total(quantity):
    price = get_price()
    return price * quantity
print(calculate_total(3))

with patch("__main__.get_price") as mock_price:
    mock_price.return_value = 500
    print(calculate_total(3))

print(calculate_total(3))
# 通常の .py ファイルを直接実行する場合、上記一連の結果は、次のとおりです。
#   3000
#   1500
#   3000
# __main__ は、今回のように直接実行しているPythonファイルを指します。別のモジュールから関数を読み込む場合などは指定する場所が変わります。
#
with patch("__main__.get_price")
# この部分では、get_price という名前が参照する本物の関数を、with ブロックの間だけモックに差し替えています。
# patch() は、指定された場所に存在する名前を一時的に差し替える仕組みです。今回差し替え対象は __main__ で実行された get_price です。
                                 as mock_price:
# patch() が作成したモックを、mock_price という変数で受け取っています。
# つまり、mock_price はモックオブジェクトです。これまで学習した Mock() と同じように、return_value を設定できます。
    mock_price.return_value = 500
# ここで、差し替えたモックの戻り値を 500 に設定しています。
# そのため、with ブロック内で calculate_total(3) を実行すると、500 × 3 = 1500 となります。
#
# with ブロックの外では元に戻る
print(calculate_total(3))
# with ブロックを抜けると、patch() による差し替えは解除されます。
# そのため、再び本物の get_price() が呼び出され、1000 × 3 = 3000 になります。
#
# 演習：patch() を使った関数の差し替え
# 今回は、patch() を使って本物の関数を一時的に差し替える演習です。
# 使用するコード
def get_tax_rate():
    return 0.1
def calculate_tax(price):
    tax_rate = get_tax_rate()
    return price * tax_rate
# 要件
#   unittest.mock から patch をインポートする。
#   上記2つの関数を定義する。
#   差し替え前に calculate_tax(1000) を実行して表示する。
#   with patch("__main__.get_tax_rate") as mock_tax_rate: を使用して、get_tax_rate() をモックに差し替える。
#   モックの return_value を 0.08 に設定する。
#   with ブロック内で calculate_tax(1000) を実行して表示する。
#   with ブロックを抜けた後、再び calculate_tax(1000) を実行して表示する。
from unittest.mock import patch

def get_tax_rate():
    return 0.1
def calculate_tax(price):
    tax_rate = get_tax_rate()
    return price * tax_rate
print(calculate_tax(1000))

with patch("__main__.get_tax_rate") as mock_tax_rate:
    mock_tax_rate.return_value = 0.08
    print(calculate_tax(1000))

print(calculate_tax(1000))

## メソッドの連鎖とモック
#
# ここからは、STEP 6-4で登場した次のコードを理解するための学習です。
mock_increment_job.result.return_value.to_dataframe.side_effect = RuntimeError(
    "データ取得に失敗しました"
)
# このコードが難しかった理由の一つは、メソッドの呼び出しが連続していることです。
# 今回は、いきなりBigQueryを使わず、まず通常のPythonクラスで仕組みを確認します。
#
# まず通常のPythonコードで考える
# 次の2つのクラスを見てください。
class Result:
    def get_value(self):
        return 100

class Job:
    def result(self):
        return Result()
# このコードでは、Job クラスの result() メソッドが、Result クラスのオブジェクトを返します。
# 実際に使うと、次のようになります。
job = Job()
result_obj = job.result()
value = result_obj.get_value()
print(value)  # 100
# 処理を順番に整理すると次の流れです。
#   job.result() を呼び出す。
#   Result オブジェクト（クラス）が返る。
#   返されたオブジェクトの get_value() を呼び出す。
#   100 が返る。
#
# メソッドを連続して呼び出す
# 先ほどのコードは、次のように短く書くこともできます。
job = Job()
print(job.result().get_value())  # 100
# つまり、
# job.result().get_value() は、result() の戻り値に対して get_value() を呼び出しているということです。
# ここまでが、通常のPythonでのメソッドの連続呼び出しです。
#
# 同じ構造をモックで作る
# では、この処理をモックで再現してみます。
from unittest.mock import Mock
mock_job = Mock()
mock_job.result.return_value.get_value.return_value = 100
print(mock_job.result().get_value())  # 100
# 重要なのは、次の1行です。
mock_job.result.return_value.get_value.return_value = 100
# これを分解します。
#   部分	                  意味
#   mock_job	          最初のモックオブジェクト
#   .result	              result という名前のモック
#   .return_value	      result() を呼び出したときに返るオブジェクト
#   .get_value	          そのオブジェクトの get_value という名前のモック
#   .return_value = 100	  get_value() の戻り値を100に設定
# ここで、Mock の便利な特徴があります。
# 存在する属性を事前に定義していなくても、Mock はアクセスされた属性に対応する子モックを自動的に作成できます。
# そのため、mock_job.result や mock_job.result.return_value.get_value を個別に Mock() で作成する必要がありません。
# これは通常のPythonオブジェクトとは異なる、Mock 特有の動作です。
#
# STEP 6-4のコードとの対応
# ここで、以前のコードに戻ります。
mock_increment_job.result.return_value.to_dataframe.side_effect = RuntimeError(
    "データ取得に失敗しました"
)
# このコードは、次の呼び出しを想定しています。
mock_increment_job.result().to_dataframe()
# 対応関係は次のとおりです。
#   モックの設定	                        実際の呼び出し
#   result.return_value	                result() が返すオブジェクト
#   result.return_value.to_dataframe	戻り値の to_dataframe メソッド
#   .side_effect = RuntimeError(...)	to_dataframe() を呼び出したときに例外を発生させる
# つまり、result() は成功するが、その後の to_dataframe() で失敗する状況を作っています。
# これが、STEP 6-4で行ったデータ取得失敗テストの仕組みです。
#
# 演習：メソッドの連続呼び出しをモックで再現する
# 今回は、まだBigQueryを使用しません。
# 要件
#   Mock をインポートする。
#   mock_job というモックを作成する。
#   mock_job.result().get_value() の戻り値が 500 になるよう、return_value を設定する。
#   mock_job.result().get_value() を実行して結果を表示する。
#   mock_job.result.call_count を表示する。
#   mock_job.result.return_value.get_value.call_count を表示する。
from unittest.mock import Mock
mock_job = Mock()
mock_job.result.return_value.get_value.return_value = 500
print(
    mock_job.result().get_value()
)
print(mock_job.result.call_count)
print(mock_job.result.return_value.get_value.call_count)

## BigQueryの異常系テストを再構築する
#
# ここまで学習した内容を使い、STEP 6-4で登場したBigQueryの異常系テストを理解していきます。
# ただし、最初から以前の長いテストコードを再現することはしません。
# まずは、BigQueryの処理を模した小さな関数を用意し、データ取得時のエラーをモックで再現するところから始めます。
# 今回テストする関数
# 次のコードを見てください。
def fetch_data(client):
    try:
        job = client.query("SELECT * FROM sales")
        result = job.result()
        df = result.to_dataframe()
        return {
            "status": "OK",
            "data": df
        }
    except RuntimeError as e:
        return {
            "status": "ERROR",
            "message": str(e)
        }
# この関数は、BigQueryの処理を想定したものです。ただし、今回は本物のBigQueryには接続しません。
#   client.query("SELECT * FROM sales") クエリを実行し、ジョブを取得
#      ↓
#   job.result() クエリの実行結果を取得
#     ↓
#   result.to_dataframe() DataFrameとしてデータを取得
#     ↓
#   正常終了なら OK、RuntimeErrorが発生したら ERROR
# 今回は、最後の to_dataframe() でエラーが発生する状況をテストします。
#
# どこにモックを設定すればよいか？
# 今回の関数は、client を引数として受け取ります。
# そのため、本物のBigQueryクライアントではなく、モックを引数として渡すことができます。
mock_client = Mock()
# この場合、patch() は必要ありません。
# なぜなら、関数が外部から受け取った client をそのまま使用する構造になっているためです。
# これは、STEP 6-4の元の関数との重要な違いです。
# 元の関数は内部で bigquery.Client() を作成していたため、patch() による差し替えが必要でした。
# 一方、今回の関数は、引数でモックを直接渡せます。
#
# モックの構造を整理する
# 今回、失敗させたいのは次の処理です。
result.to_dataframe()
# しかし、その前には次の処理があります。
job = client.query("SELECT * FROM sales")
result = job.result()
# したがって、モックの呼び出し構造は次のようになります。
mock_client.query().result().to_dataframe()
# ここで、前回学習した return_value の考え方が使えます。
#   実際の呼び出し	            モック上の対応
#   client.query(...)	    mock_client.query.return_value
#   job.result()	        mock_client.query.return_value.result.return_value
#   result.to_dataframe()	mock_client.query.return_value.result.return_value.to_dataframe
# 最後の to_dataframe() でエラーを発生させたい場合は、そのモックの side_effect に例外を設定します。
#
# 演習：データ取得失敗のテスト
# 使用する関数
# 次の関数をそのまま使用してください。
def fetch_data(client):
    try:
        job = client.query("SELECT * FROM sales")
        result = job.result()
        df = result.to_dataframe()
        return {
            "status": "OK",
            "data": df
        }
    except RuntimeError as e:
        return {
            "status": "ERROR",
            "message": str(e)
        }
# 要件
#   Mock をインポートする。
#   上記の fetch_data() を定義する。
#   mock_client というモックを作成する。
#   mock_client.query().result().to_dataframe() が呼び出されたときに、
#   RuntimeError("データ取得に失敗しました") が発生するよう side_effect を設定する。
#   fetch_data(mock_client) を実行し、結果を result に代入する。
#   result["status"] と result["message"] を表示する。
#   mock_client.query.call_count を表示する。
from unittest.mock import Mock
mock_client = Mock()
mock_client.query.return_value.result.return_value.to_dataframe.side_effect = RuntimeError("データ取得に失敗しました")
result = fetch_data(mock_client)
print(result)
print(mock_client.query.call_count)

## patch.object() の仕組み
#
# ここからは、以前のSTEP 6-4で使用した、次のコードを理解していきます。
with patch.object(bigquery, "Client") as mock_client_class:
# これまで学習した patch() と何が違うのかを確認します。
#
# patch() と patch.object() の違い
# 先般の段階では、次のように記述しました。
with patch("__main__.get_tax_rate") as mock_tax_rate:
# これは、文字列で指定した get_tax_rate を一時的にモックへ差し替える方法でした。
# 一方、patch.object() は、オブジェクトと属性名を別々に指定する方法です。
# 例えば、次のようなコードがあるとします。
class Service:
    def get_price(self):
        return 1000
# この場合、次のように差し替えられます。
from unittest.mock import patch
with patch.object(Service, "get_price") as mock_get_price:
    mock_get_price.return_value = 500
    service = Service()
    print(service.get_price())  # 500
# ここでは、
#   Service：差し替え対象を持つオブジェクト（クラス）
#   "get_price"：差し替えたい属性（メソッド）の名前
#   mock_get_price：差し替えに使われるモック
# という対応になっています。
# with ブロックを抜けると、Service.get_price は元に戻ります。
#
# BigQueryの場合はどうなるか
# BigQueryでは、通常、次のようにクライアントを作成します。
from google.cloud import bigquery
client = bigquery.Client()
# この bigquery.Client を一時的にモックへ差し替えたい場合に、次のコードを使用できます。
with patch.object(bigquery, "Client") as mock_client_class:
# ここで注意したいのは、mock_client_class と mock_client_class() は異なるということです。
mock_client_class    # これは、bigquery.Client の代わりに置かれたモックそのものです。
mock_client_class()  # これは、そのモックを呼び出したときの戻り値です。
# つまり、実際のプログラムで、
client = bigquery.Client()
# が実行されると、差し替え中は、
client = mock_client_class()
# と同じ構造になります。
# そのため、クライアントの query() を設定する場合は、次のように return_value を経由します。
mock_client_class.return_value.query.return_value
# これは、先般の段階で直接 mock_client を作成した場合との違いです。
#
# 演習：クラスをモックに差し替える
# 今回はBigQueryへの接続は行わず、通常のPythonクラスで確認します。
# 使用するコード
class DataClient:
    def fetch(self):
        return "本物のデータ"

def get_data():
    client = DataClient()
    return client.fetch()
print(get_data())
# 要件
#   unittest.mock から patch をインポートする。
#   上の DataClient クラスと get_data() 関数を定義する。
#   差し替え前に get_data() を実行して表示する。
#   with patch("__main__.DataClient") as mock_client_class: を使用して、DataClient を一時的に差し替える。
#   mock_client_class.return_value.fetch.return_value に "モックのデータ" を設定する。
#   with ブロック内で get_data() を実行して表示する。
#   with ブロック終了後、再び get_data() を実行して表示する。
from unittest.mock import patch
with patch("__main__.DataClient") as mock_client_class:
    mock_client_class.return_value.fetch.return_value = "モックのデータ"
    print(get_data())
print(get_data())

## patch.object() と patch() の対応を確認する
#
# 前回の説明では patch.object() を紹介しましたが、演習では patch() を使いました。
# ここで、両者の違いを明確にしておきます。
# 今回のように、直接実行しているPythonファイルに DataClient が定義されている場合、次の2つは同じ対象を差し替えます。
# patch()
with patch("__main__.DataClient") as mock_client_class:
    pass
# patch.object()
import __main__
with patch.object(__main__, "DataClient") as mock_client_class:
    pass
# 違いは、差し替え対象の指定方法です。
#   方法	             指定方法
#   patch()          "__main__.DataClient" という文字列
#   patch.object()   __main__ というモジュールオブジェクトと "DataClient" という属性名
# どちらも、with ブロックの間だけ DataClient をモックに差し替えます。
#
# 演習：patch.object() を使う
# 今回は、先のコードを少し変更するだけです。
# 使用するコード
class DataClient:
    def fetch(self):
        return "本物のデータ"
def get_data():
    client = DataClient()
    return client.fetch()
# 要件
#   import __main__ と from unittest.mock import patch を記述する。
#   上記のクラスと関数を定義する。
#   with patch.object(__main__, "DataClient") as mock_client_class: を使用する。
#   fetch() の戻り値を "差し替え成功" に設定する。
#   with ブロックの前・中・後で get_data() を実行し、それぞれ表示する。
import __main__
from unittest.mock import patch
print(get_data())
with patch.object(__main__, "DataClient") as mock_client_class:
    mock_client_class.return_value.fetch.return_value = "差し替え成功"
    print(get_data())
print(get_data())

## BigQueryの異常系テストを組み立てる
#
# ここまで学習した内容を組み合わせて、STEP 6-4で使用したモックの構造を再現します。
# 今回は、BigQueryクライアントの生成からデータ取得失敗までを一つのテストで扱いますが、本物のBigQueryには接続しません。
# 新しいモック機能は登場しません。
# 今回テストする関数
# 次のコードを使用します。
class BigQueryClient:
    def query(self, sql):
        raise NotImplementedError("今回は本物のクエリを実行しません")

def fetch_sales():
    try:
        client = BigQueryClient()
        job = client.query("SELECT * FROM sales")
        result = job.result()
        df = result.to_dataframe()
        return {
            "status": "OK",
            "data": df
        }
    except RuntimeError as e:
        return {
            "status": "ERROR",
            "message": str(e)
        }
# BigQueryClient は、今回の演習用に作ったクラスです。Google Cloudの実際の bigquery.Client ではありません。
# query() には NotImplementedError を設定していますが、テストではクラスそのものをモックに差し替えるため、この処理は実行されません。
#
# 今回のテストで確認したいこと
# fetch_sales() の処理は、次の順番です。
#   BigQueryClient()
#     ↓
#   client.query(...)
#     ↓
#   job.result()
#     ↓
#   result.to_dataframe()
# このうち、to_dataframe() だけが RuntimeError を発生させる状況を作ります。
# その結果、fetch_sales() が例外を捕捉して、ERROR を返すことを確認します。
#
# モックを設定する対象
# 今回は fetch_sales() の内部で BigQueryClient() を作成しています。
# したがって引数でモックを渡すことはできないため、patch.object() を使用します。
import __main__
from unittest.mock import patch
with patch.object(__main__, "BigQueryClient") as mock_client_class:
    pass
# この mock_client_class は、BigQueryClient を差し替えたモックです。
# 実際のクライアントに相当するモックは、次のように取得できます。
mock_client = mock_client_class.return_value
# ここから先は、先般の学習した構造と同じです。
mock_client.query().result().to_dataframe()
# 今回は、この最後の呼び出しに例外を設定してください。
#
# 演習：クライアント生成からデータ取得失敗まで
# 要件
#   import __main__ と from unittest.mock import patch を記述する。
#   上記の BigQueryClient クラスと fetch_sales() 関数を定義する。
#   patch.object() で BigQueryClient をモックに差し替える。
#   mock_client_class.return_value を mock_client に代入する。
#   mock_client.query().result().to_dataframe() が呼び出されたとき、
#   RuntimeError("データ取得に失敗しました") が発生するように設定する。
#   with ブロック内で fetch_sales() を実行する。
#   戻り値の辞書と、mock_client.query.call_count を表示する。
import __main__
from unittest.mock import patch
with patch.object(__main__, "BigQueryClient") as mock_client_class:
    mock_client = mock_client_class.return_value
    mock_client.query.return_value.result.return_value.to_dataframe.side_effect = RuntimeError("データ取得に失敗しました")
    print(fetch_sales())
    print(mock_client.query.call_count)

## 2回の query() に異なる結果を返す
#
# 元のSTEP 6-4では、次のコードを使用していました。
mock_client.query.side_effect = [
    mock_watermark_job,
    mock_increment_job
]
# ここまでの学習内容を使えば、このコードの意味を理解できます。
#
# なぜ2つのジョブが必要だったのか？
# STEP 6-3で作成したウォーターマーク管理付きパイプラインでは、BigQueryへの問い合わせを複数回行っていました。
# 代表的には、次の2つです。
#   呼び出し	        目的
#   1回目の query()	前回処理したウォーターマークを取得する
#   2回目の query()	ウォーターマークより新しいデータを取得する
# 異常系テストでは、次の状況を再現したかったわけです。
# 「1回目のウォーターマーク取得は成功するが、2回目の増分データ取得で失敗する。」
# そのため、2種類のジョブモックを用意していました。
#
# side_effect のリストを復習する
# 先般で、次のコードを学習しました。
mock_task.side_effect = [100, 200]
print(mock_task())  # 100
print(mock_task())  # 200
# これと同じ仕組みです。
mock_client.query.side_effect = [
    mock_watermark_job,
    mock_increment_job
]
# この設定では、
#   1回目の query() は mock_watermark_job を返す。
#   2回目の query() は mock_increment_job を返す。
# という動作になります。
# さらに、それぞれのジョブに異なる動作を設定できます。
#
# 今回の演習で使用する関数
def fetch_incremental_data(client):
    try:
        watermark_job = client.query("SELECT MAX(last_date) FROM watermark")
        watermark_df = watermark_job.result().to_dataframe()

        increment_job = client.query("SELECT * FROM sales WHERE sale_date > last_date")
        increment_df = increment_job.result().to_dataframe()

        return {
            "status": "OK",
            "watermark": watermark_df,
            "data": increment_df
        }

    except RuntimeError as e:
        return {
            "status": "ERROR",
            "message": str(e)
        }
# この関数は、BigQueryの問い合わせを模した学習用コードです。SQLは実行せず、モックだけで動作を確認します。
# 今回は、1回目の to_dataframe() が "2026-11-18" を返し、2回目の to_dataframe() がエラーになるよう設定します。
#
# 演習：2回目のデータ取得だけを失敗させる
# 要件
#   Mock をインポートする。
#   上記の fetch_incremental_data() を定義する。
#   mock_client、mock_watermark_job、mock_increment_job の3つのモックを作成する。
#   mock_watermark_job.result().to_dataframe() が "2026-11-18" を返すよう設定する。
#   mock_increment_job.result().to_dataframe() が RuntimeError("増分データ取得に失敗しました") を発生させるよう設定する。
#   mock_client.query.side_effect に、2つのジョブモックを順番に設定する。
#   fetch_incremental_data(mock_client) を実行する。
#   戻り値の辞書と、mock_client.query.call_count を表示する。
from unittest.mock import Mock
mock_client = Mock()
mock_watermark_job = Mock()
mock_increment_job = Mock()

mock_watermark_job.result.return_value.to_dataframe.return_value = "2026-11-18"
mock_increment_job.result.return_value.to_dataframe.side_effect = RuntimeError("増分データ取得に失敗しました")
mock_client.query.side_effect = [
    mock_watermark_job,
    mock_increment_job
]
print(fetch_incremental_data(mock_client))
print(mock_client.query.call_count)


### STEP 6-5｜パイプラインのスケジュール実行
# 今回は、STEP 6-3で学習したウォーターマーク付き増分処理を、決められた時刻に自動実行する仕組みを学びます。
# これまでは、PyCharmから自分でPythonコードを実行していました。今回は、その実行をスケジュールに従って開始できるようにすることが目標です。
# 次の3点を理解・実装します。
#   スケジュール実行の仕組みを理解する。
#   Pythonで指定時刻に処理を実行する仕組みを作る。
#   パイプラインを定期実行する際の注意点を理解する。
# 今回は、外部ライブラリの schedule を使用します。
# 実務ではWindowsタスクスケジューラ、cron、Cloud Schedulerなどの方法もありますが、最初はPythonコード内で動作を確認できる方法から始めます。

# スケジュール実行とは何か？
# これまでの実行方法は、次のようなものでした。
#   手動実行 PyCharmで実行ボタンを押す → Pythonのパイプラインが実行される
# 一方、スケジュール実行では、次のようになります。
#   スケジュール実行 あらかじめ実行間隔や時刻を登録 → 指定時刻になったかを確認 → Pythonのパイプラインを自動実行
# 例えば、毎日午前9時にデータ取得処理を実行する、といった運用が考えられます。
# ただし、今回使用するライブラリの schedule は、Pythonプログラムが起動している間だけ動作する仕組みです。
# パソコンをシャットダウンした状態でも実行できるわけではありません。

# schedule ライブラリの基本
# ① インストール
# PyCharmのターミナルで、次のコマンドを実行してください。
pip install schedule
#
# ② 定期実行する関数を作成する
# まずは通常のPython関数です。
from datetime import datetime
def run_pipeline():
    print(f"パイプライン実行：{datetime.now()}")
# この関数は、呼び出された時刻を表示します。
#
# ③ 実行間隔を登録する
import schedule
schedule.every(5).seconds.do(run_pipeline)
# これは、run_pipeline() を5秒間隔で実行する予定として登録する処理です。
# ここで注意したいのは、この1行だけでは関数は実行されないということです。
# do() に渡しているのは run_pipeline であり、run_pipeline() ではありません。
# 前者は関数そのものを渡しています。後者はその場で関数を呼び出してしまいます。
#
# ④ 実行予定を確認する
schedule.run_pending()
# この処理は、登録されているジョブのうち、実行時刻に達したものを実行します。
# ただし、1回呼び出しただけでは、継続的に時刻を確認できません。
# そこで、while を使います。
#while True:
    schedule.run_pending()
    time.sleep(1)
# while True により繰り返し処理を行い、time.sleep(1) で1秒待機します。
# このループは自動的には終了しないため、実際の演習では終了条件を設定します。

# 今回の演習で作る仕組み
# 今回は、5秒間隔で処理を実行し、3回実行したら自動終了するプログラムを作ります。
#   schedule.every(5).seconds.do(...) 5秒間隔で実行するジョブを登録
#     ↓
#   run_pending() で実行時刻を確認
#     ↓
#   実行回数をカウント
#     ↓
#   3回実行したら終了

# 演習：スケジュールによるパイプラインの自動実行
# 次の要件を満たすPythonコードを、自分で作成してください。
# 要件
#   schedule、time、datetime をインポートする。
#   実行回数を管理する変数 execution_count を 0 で初期化する。
#   run_pipeline() 関数を定義する。
#   run_pipeline() が呼び出されるたびに、execution_count を1増やす。
#   関数内で、実行回数と現在日時を表示する。
#   schedule を使用して、run_pipeline() を5秒間隔で実行するよう登録する。
#   while ループ内で schedule.run_pending() を呼び出す。
#   time.sleep(1) を使い、ループの各周回で1秒待機する。
#   execution_count が3になったらループを終了する。
#   最後に "スケジュール実行終了" と表示する。

import schedule
from datetime import datetime
import time

execution_count = 0
def run_pipeline():
    global execution_count
    execution_count += 1
    print(f"パイプライン実行 {execution_count}回目：{datetime.now()}")
    if execution_count == 3:
        print("スケジュール実行終了")

schedule.every(5).seconds.do(run_pipeline)
while execution_count < 3:
    schedule.run_pending()
    time.sleep(1)

# ヒント
# 関数の外側で定義した変数を、関数内で変更する場合は global を使用できます。
execution_count = 0
def run_pipeline():
    global execution_count
    execution_count += 1
# while の条件には、実行回数を使用できます。
#while execution_count < 3:
    # 実行予定の確認
    # 1秒待機

# 期待する実行結果
#   パイプライン実行 1回目：2026-11-19 10:00:05
#   パイプライン実行 2回目：2026-11-19 10:00:10
#   パイプライン実行 3回目：2026-11-19 10:00:15
#   スケジュール実行終了


### STEP 6-5.5｜増分パイプラインの定期実行設計 応用編
# ここからは、STEP 6-3で学習したウォーターマーク付き増分パイプラインとの接続を考えます。
# 今回は、スケジュール実行そのものよりも、定期実行するパイプラインを安全に運用するための設計に焦点を当てます。
#
# 実務で問題になりやすい3つの状況
# 例えば、毎日午前9時に増分処理を実行するパイプラインがあるとします。
#   状況	                    起こり得る問題	                対応の考え方
#   1.新しいデータがない	    毎回同じデータを処理する	        ウォーターマークで処理対象を限定
#   2.前回の処理が失敗した	    未処理データが残る	            成功時だけウォーターマークを更新
#   3.前回の処理がまだ実行中	同じデータを二重処理する可能性	同時実行を防止する
# このうち、最初の2つはSTEP 6-3で学習したウォーターマーク管理と関係しています。
# 3つ目の同時実行防止は、スケジュール実行で新たに意識したい問題です。

# schedule の動作について
# 今回使用した schedule は、基本的に run_pending() を呼び出したスレッド上で、登録したジョブを順番に実行します。
# 例えば、次のように登録したとします。
schedule.every(5).seconds.do(run_pipeline)
# 仮に run_pipeline() が10秒かかる場合でも、通常の同期実行では、同じスケジューラがその処理を並列に起動するわけではありません。
# また、schedule は、実行できなかった回数を後からすべて補填する仕組みでもありません。
# ただし、同じPythonプログラムを別プロセスで2つ起動した場合は、それぞれが独立して処理を実行するため、二重実行の可能性があります。
# そのため、本番運用ではスケジューラだけでなく、パイプライン側にも実行制御が必要になる場合があります。

# 応用演習：実行中の処理を重複起動させない
# 今回は、実際のBigQueryへの接続を行わず、実行状態を表す変数を使用して動作を確認します。
#
# 今回の設計
# is_running という変数を用意します。
#   False：パイプラインは実行されていない。
#   True：パイプラインが実行中。
# run_pipeline() が呼び出されたとき、is_running が True なら、新しい処理を開始せず終了します。
# ただし、この方法は同じPythonプロセス内の状態管理です。複数プロセス間の同時実行を防止する仕組みではありません。
# また、今回の同期スケジューラでは通常、ジョブが並列実行されないため、実行中フラグの確認は追加の安全策として扱います。
#
# 演習要件
#   time をインポートする。
#   is_running = False を定義する。
#   run_pipeline() 関数を定義する。
#   is_running が True の場合、"実行中のためスキップ" と表示して終了する。
#   False の場合、is_running = True に変更し、"パイプライン実行開始" と表示する。
#   try ブロック内で time.sleep(3) を実行する。
#   finally ブロックで is_running = False に戻し、"パイプライン実行終了" と表示する。
#   最初に is_running を表示する。
#   run_pipeline() を1回実行する。
#   実行後の is_running を表示する。
#   次に is_running = True を設定し、再度 run_pipeline() を呼び出して、スキップ処理を確認する。
#
# 期待する実行結果
#   False
#   パイプライン実行開始
#   パイプライン実行終了
#   False
#   実行中のためスキップ

import time

is_running = False
print(is_running)

def run_pipeline():
    global is_running
    if is_running:
        print("実行中のためスキップ")
        return
    else:
        is_running = True
        print("パイプライン実行開始")
    try:
        time.sleep(3)
    finally:
        is_running = False
        print("パイプライン実行終了")

run_pipeline()
print(is_running)
is_running = True
run_pipeline()

# ここで、STEP 6-3のウォーターマーク付き増分パイプラインとの関係を整理します。
# 既存パイプラインとスケジューラの接続
# STEP 6-3では、次の関数を作成していました。
process_sales_with_persistent_watermark(
    project_id,
    sql,
    watermark_table,
    pipeline_name
)

# この関数をスケジュール実行したい場合、基本的には、必要な引数を渡して呼び出す関数を用意し、それを schedule に登録する構成になります。
def scheduled_pipeline():
    result = process_sales_with_persistent_watermark(
        project_id,
        sql,
        watermark_table,
        pipeline_name
    )
    return result

schedule.every().day.at("09:00").do(scheduled_pipeline)

# これは接続方法を示す概念例です。実際に動かすには、STEP 6-3で使用した関数と引数を用意する必要があります。
# また、ウォーターマークがあることと、二重実行を完全に防止できることは別問題です。
# 例えば、2つのプロセスが同時に同じウォーターマークを読み取った場合、両方が同じ増分データを処理する可能性があります。
# 今回の is_running = True / False は、同一プロセス内での簡易的な状態管理であり、別プロセスや別サーバーからの重複起動までは防げません。
# 実務では、必要に応じて外部のロック機構やジョブ実行基盤による同時実行制御を検討します。


### STEP 6-6｜パイプラインの監視・実行結果管理
# これまでに学んだ増分処理、ウォーターマーク、例外処理、スケジュール実行を踏まえ、
# 今回はパイプラインがいつ実行され、成功したのか、失敗したのかを記録する仕組みを作ります。
#
# データエンジニアリングでは、パイプラインを自動実行できるだけでは不十分です。
# 例えば、毎朝9時に実行されるパイプラインがあったとしても、次のことが分からなければ運用に困ります。
#   今日の処理は成功したのか？
#   何件のデータを処理したのか？
#   失敗した場合、どんなエラーが発生したのか？
#   処理に何秒かかったのか？
#
# これらを確認できるようにするのが、今回学習する「実行結果管理（Execution Logging）」です。
# 監視（Monitoring）は、記録された実行結果を確認し、失敗や異常を検知することです。
# 今回はその基礎となる、実行ログの記録と簡単な異常判定を実装します。
# BigQueryへの接続はせず、まずローカルファイルで実行履歴を保存し、後から確認できる仕組みを作ります。

# パイプラインの実行ログとは？
# 例えば、売上データを毎日取得するパイプラインを考えます。
#   スケジュール実行：毎日午前9時
#     ↓
#   売上データ処理：取得 -> 加工 -> 保存
#     ↓
#   実行ログを保存：日時・ステータス・処理件数・処理時間・エラー
#     ↓
#   pandasで実行履歴を確認：失敗した実行を抽出
#
# 保存するログの例です。
#   pipeline_name   status    processed_rows   duration_sec	 error_message
#   sales_daily	    SUCCESS	  120              2.4            null
#   sales_daily	    SUCCESS	  0                1.1            null
#   sales_daily	    ERROR     0                0.3            Connection failed
# ここで重要なのは、処理件数が0件でも、必ずしも失敗ではないということです。
# 増分処理では、新しいデータが存在しなければ0件で正常終了する場合があります。
# したがって、processed_rows == 0 だけでエラーと判定してはいけません。

# 新しい知識①：time.perf_counter()
# 処理時間を測定するために使用します。
import time
start = time.perf_counter()
time.sleep(2)
duration = time.perf_counter() - start
print(duration)  # 2.000696600007359
# datetime.now() は「何時に実行されたか」を記録するのに適しています。
# 一方、time.perf_counter() は、処理に何秒かかったかを測定するのに適しています。
# この2つは目的が異なります。
#
# 新しい知識②：JSON Lines形式でログを保存する
# 通常のJSONでは、辞書やリストを1つのJSONデータとして保存します。
# 今回使用する JSON Lines（.jsonl） は、1行に1つのJSONオブジェクトを保存する形式です。
# 例えば、次のようになります。
{"pipeline_name": "sales_daily", "status": "SUCCESS", "processed_rows": 120}
{"pipeline_name": "sales_daily", "status": "SUCCESS", "processed_rows": 0}
{"pipeline_name": "sales_daily", "status": "ERROR", "processed_rows": 0}
# 1回実行するたびに1行追加できるため、実行履歴の保存に向いています。
#
# 新しい知識③：json.dumps() とファイルへの追記
import json
log = {
    "pipeline_name": "sales_daily",
    "status": "SUCCESS",
    "processed_rows": 120
}
with open("pipeline_log.jsonl", "a", encoding="utf-8") as f:
    f.write(json.dumps(log, ensure_ascii=False) + "\n")
# ここでは3つのポイントがあります。
#   コード                意味
#   "a"                  ファイルの末尾に追記する。存在しなければ作成する
#   json.dumps()         Pythonの辞書をJSON形式の文字列に変換する
#   ensure_ascii=False   日本語をそのまま保存できるようにする
#   "\n"                 1回分のログごとに改行する
# 仮に "w" で開くと既存のファイル内容が上書きされるため、今回は "a" を使用します。
#
# 新しい知識④：保存したログをpandasで読み込む
import pandas as pd
df = pd.read_json("pipeline_log.jsonl", lines=True)
print(df)
# lines=True は、JSON Lines形式のファイルを読み込むための指定です。
# 通常のJSONファイルとは異なり、各行を独立したJSONデータとして扱います。
#
# 新しい知識⑤：成功・失敗をログに記録する
# パイプラインの実行結果を記録する場合、処理の成功と失敗を区別する必要があります。
# 基本的な構造は次のようになります。
try:
    # パイプライン本体を実行
    status = "SUCCESS"
except Exception as e:
    status = "ERROR"
    error_message = str(e)
finally:
    # 実行結果をログに保存
    pass
# ただし、実際には次の点にも注意します。
#   ① エラー発生前に変数を初期化する
#     例えば、error_message を正常終了時にもログに含めるなら、事前に None で初期化しておく必要があります。
#   ② finally は正常終了・異常終了の両方で実行される
#     そのため、ログの保存処理を配置する場所として利用できます。
#   ③ エラーを記録することと、エラーを握りつぶすことは別
#     実務では、エラーをログに記録したうえで、呼び出し元に例外を再送出する設計もあります。
#     今回はまず、実行結果を辞書として返す方法で実装します。

# 演習：パイプライン実行結果をJSON Linesに保存する
# 今回は、パイプライン本体とログ記録処理を分離して実装します。
#
# ① パイプライン本体を用意する
# 次の関数を使用してください。
def sample_pipeline(should_fail=False):
    if should_fail:
        raise RuntimeError("データ取得に失敗しました")
    return 5
# この関数は、通常は処理件数として 5 を返します。
# should_fail=True を渡すと、例外が発生します。
# この関数自体は変更する必要はありません。
#
# ② execute_pipeline() を作成する
# 次の引数を受け取る関数を作成してください。
import time
import json

def execute_pipeline(pipeline_name, should_fail=False):
    start_time = datetime.now().isoformat()
    start = time.perf_counter()

    status = "SUCCESS"
    processed_rows = 0
    error_message = None

    try:
        processed_rows = sample_pipeline(should_fail)
    except Exception as e:
        status = "ERROR"
        error_message = str(e)
    finally:
        end_time = datetime.now().isoformat()
        duration = time.perf_counter() - start
        log = {
            "pipeline_name": pipeline_name,
            "start_time": start_time,
            "end_time": end_time,
            "status": status,
            "processed_rows": processed_rows,
            "duration_sec": duration,
            "error_message": error_message
        }
        with open("pipeline_log.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(log, ensure_ascii=False) + "\n")
    return log

# 実装要件
#   関数開始時に、現在日時を start_time に記録する。
#   time.perf_counter() で処理時間の測定を開始する。
#   status = "SUCCESS"、processed_rows = 0、error_message = None を初期化する。
#   try 内で sample_pipeline(should_fail) を呼び出し、戻り値を processed_rows に格納する。
#   except Exception as e で例外を捕捉し、status を "ERROR"、error_message を例外メッセージに変更する。
#   finally 内で終了日時と処理時間を取得する。
#   次の項目を含む辞書 log を作成する。
#     キー              格納する内容
#     pipeline_name	    引数で受け取った名前
#     start_time	    開始日時（ISO形式の文字列）
#     end_time	        終了日時（ISO形式の文字列）
#     status	        "SUCCESS" または "ERROR"
#     processed_rows	処理件数
#     duration_sec	    処理時間（秒）
#     error_message	    エラー内容。正常時は None
#   log を pipeline_log.jsonl に1行追記する。
#   最後に log を戻り値として返す。

# 日時のISO形式への変換には、次のメソッドを使用できます。
datetime.now().isoformat()

# 正常系・異常系を実行する
# 次の2ケースを実行してください。
result1 = execute_pipeline("sales_daily", should_fail=False)
print(result1)

result2 = execute_pipeline("sales_daily", should_fail=True)
print(result2)

# 期待する実行結果
# 正常系
# {
#     "pipeline_name": "sales_daily",
#     "start_time": "2026-11-20T09:00:00",
#     "end_time": "2026-11-20T09:00:00",
#     "status": "SUCCESS",
#     "processed_rows": 5,
#     "duration_sec": 0.00001,
#     "error_message": None
# }
#
# 異常系
# {
#     "pipeline_name": "sales_daily",
#     "start_time": "2026-11-20T09:01:00",
#     "end_time": "2026-11-20T09:01:00",
#     "status": "ERROR",
#     "processed_rows": 0,
#     "duration_sec": 0.00001,
#     "error_message": "データ取得に失敗しました"
# }

# pandasで実行履歴を確認する
# 最後に、保存したログファイルをpandasで読み込んでください。
# そして、status が "ERROR" の行だけを抽出してください。
# 期待する結果は、今回の2ケースだけが保存されている場合、正常系1行、異常系1行、エラー抽出結果1行です。
# なお、過去の実行ログが残っている場合は、ファイルにその分の履歴も含まれます。

import pandas as pd
pipeline_log_df = pd.read_json("pipeline_log.jsonl", lines=True)
error_low = pipeline_log_df.loc[
    pipeline_log_df["status"] == "ERROR"
]
print(error_low)

# 実務上の補足
# 今回のコードに修正必須の箇所はありません。ただし、次の点は覚えておいてください。
# except Exception で例外を捕捉してログに記録すると、今回の関数は例外を呼び出し元に伝えず、ERROR を含む辞書を返して終了します。
# そのため、スケジューラや監視システム側が失敗を認識するには、戻り値の status を確認する必要があります。
# 実務では、ログ保存後に例外を再送出する設計もあります。


### STEP 6-6.5｜実行履歴から異常を検知する












































































