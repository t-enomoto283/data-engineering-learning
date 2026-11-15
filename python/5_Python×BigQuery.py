
### STEP 5-1｜BigQueryへの接続
# STEP 5では、これまで学習してきたPython・pandasの知識を、BigQueryを利用した実際のデータ取得・加工・保存処理へ発展させます。
#
# 今回使うPython・BigQueryの知識
# ① PythonからBigQueryを操作する仕組み
# 今回の環境構築で登場した各要素の関係を整理します。
#   PyCharm / Python：Pythonコードを実行する環境
#     ↓
#   google-cloud-bigquery：BigQueryを操作するPythonライブラリ
#     ↓
#   ADC（認証情報）：Google Cloudにアクセスするための認証
#     ↓
#   BigQuery API：Google Cloud上のBigQueryと通信
# Google Cloud CLIは、この図のADC認証情報を設定するために使用しました。
# Pythonプログラムの実行時に、毎回 gcloud コマンドを呼び出すわけではありません。
#
# ② bigquery.Client() と認証
from google.cloud import bigquery
client = bigquery.Client(
    project="resonant-tract-508812-p9"
)
print(client.project)  # resonant-tract-508812-p9
# このコードは、BigQueryを操作するためのクライアントを生成します。
#   bigquery.Client()：BigQueryクライアントの生成
#   project：操作対象のGoogle CloudプロジェクトID
#   ADC：認証情報が自動的に読み込まれる
# 今回、ここまでは実際に成功しています。
# ただし、client.project を表示できても、BigQuery APIにアクセスできたことにはなりません。
#
# ③ BigQuery APIへのアクセス確認
# 当初は get_service_account_email() を使う予定でした。
# このメソッドもBigQuery APIを呼び出しますが、取得するのはプロジェクトのBigQueryサービスアカウントのメールアドレスです。
# 今回の目的は接続確認なので、client.list_datasets() を使用する方法に変更します。
datasets = list(client.list_datasets())
print(datasets)
# list_datasets() は、指定プロジェクトで参照できるデータセットの一覧を取得するメソッドです。
# list() によってイテレータを実際に評価することでAPIへのリクエストが実行されます。Google公式のPythonサンプルでもこの方法が使われています。
# ただし、データセット一覧の取得成功は、SQL実行やテーブルへの書き込み権限まで保証するものではありません。
#
# ④ データセット名を表示してみましょう。
# 試しに、次のコードを実行してみてください。
for dataset in datasets:
    print(dataset.dataset_id)
# dataset.dataset_id は、DatasetListItem オブジェクトが持っているデータセットIDを取得する属性です。

# ⑤ try / except による例外処理
try:
    value = int("123")
except Exception as e:
    print(str(e))
else:
    print("処理成功")
# 今回は認証エラー、権限エラー、通信エラーなど、さまざまな例外が考えられるため、演習では Exception を使用します
#
# ⑥ logging による実行記録
import logging
logging.info("処理成功")
logging.exception("処理失敗")
# logging.exception() は例外処理中に使用すると、エラーメッセージに加えてトレースバックも記録できます。
#
# ⑦ 今回のイレギュラー対応で学んだこと
#   項目                 今回の学習内容
#   仮想環境 .venv        プロジェクトごとにPythonパッケージを管理する
#   Google Cloud CLI     Google Cloudの認証や設定を操作する
#   ADC                  Pythonプログラムが利用する認証情報
#   IAM権限               認証できても、すべての操作が許可されるわけではない
#   Smart App Control    Windowsがネイティブモジュールの読み込みを制限する場合がある
#   grpcio               今回は読み込みがブロックされた。問題は未解決だが、基本的なBigQuery操作とは切り分ける
# この内容は、追加の演習にはせず、STEP 5全体で必要に応じて扱います。

# 演習問題：BigQueryへの接続とAPIアクセス確認
# PythonからBigQueryクライアントを生成し、BigQuery APIへ実際にアクセスできるかを確認する関数を作成してください。
# 作成する関数
def check_bigquery_connection(project_id):
    from google.cloud import bigquery
    import logging
    try:
        client = bigquery.Client(
            project=project_id
        )
        list(client.list_datasets())
    except Exception as e:
        print(str(e))
        logging.exception("処理失敗")
        return {
            "status": "ERROR",
            "project_id": project_id,
            "error": str(e)
        }
    else:
        logging.info("処理成功")
        return {
            "status": "OK",
            "project_id": project_id,
            "error": None
        }

# 演習要件
#   google.cloud.bigquery と logging をインポートする。
#   引数 project_id を指定して bigquery.Client() を生成する。
#   client.list_datasets() を呼び出し、list() で評価してAPIへのアクセスを確認する。
#   try / except を使用し、処理中の例外を捕捉する。
#   成功時と失敗時で、以下の形式の辞書を返す。
#   成功時は logging.info()、失敗時は logging.exception() を使用する。
#
# 戻り値の仕様
# 成功時
# {
#     "status": "OK",
#     "project_id": "指定したプロジェクトID",
#     "error": None
# }
# 失敗時
# {
#     "status": "ERROR",
#     "project_id": "指定したプロジェクトID",
#     "error": "発生した例外メッセージ"
# }
# error には、例外オブジェクトを str() で文字列に変換したものを格納してください。
# 今回は、取得したデータセット一覧を返したり、表示したりする必要はありません。

# テストケース
# テストケース①：正常なプロジェクトID
result1 = check_bigquery_connection("resonant-tract-508812-p9")
print(result1)
# 期待する結果：
# {
#     "status": "OK",
#     "project_id": "resonant-tract-508812-p9",
#     "error": None
# }
# これは、現在設定済みのADC認証とBigQuery APIへのアクセス権限が有効である場合の期待結果です。

# テストケース②：存在しないプロジェクトID
result2 = check_bigquery_connection("nonexistent-project-123456789")
print(result2)
# 期待する結果：
# {
#     "status": "ERROR",
#     "project_id": "nonexistent-project-123456789",
#     "error": "実際に発生した例外メッセージ"
# }
# 存在しないプロジェクトを指定した場合、APIからエラーが返されることを想定しています。エラー文言は環境によって異なるため完全一致は求めません。
# ただし、APIがエラーを返さず空の一覧を返す場合もあり得ます。
# その場合は実行結果を確認し、演習のテスト設計側の問題として扱います。無理にコードを変更してエラーにする必要はありません。


### STEP 5-2｜PythonからBigQueryのSQLを実行
# STEP 5-1では、PythonからBigQuery APIにアクセスし、正常系・異常系を処理する関数を実装しました。
# 今回は、PythonからSQLを送信し、BigQuery上でクエリを実行します。
#
# 今回学習する知識
# ① client.query()：SQLを実行するジョブを作成
from google.cloud import bigquery
client = bigquery.Client(
    project="resonant-tract-508812-p9"
)
sql = "SELECT 1 AS test_value"
query_job = client.query(sql)
# client.query(sql) は、BigQueryにSQLを送信し、クエリジョブを開始するメソッドです。
# ここで重要なのは、SQLを送信した時点で、必ずしもクエリの実行が完了しているわけではないという点です。
# query_job は、クエリの実行状態や結果を管理するオブジェクトです。
#
# ② query_job.result()：クエリの完了を待つ
rows = query_job.result()
# result() はクエリの完了を待ち、成功した場合に結果の行を取得するためのオブジェクトを返します。
# SQLの実行中にエラーが発生した場合は、ここで例外が発生することもあります。
# そのため、STEP 5-1と同様に try / except を使用します。
#
# ③ クエリ結果の取得
for row in rows:
    print(row.test_value)
# 今回のSQLは SELECT 1 AS test_value であるため、結果は 1 になります。
# row.test_value は、SQLの AS test_value で指定した列名を使って値を取り出しています。
#
# ④ RowIterator と list()
# BigQueryのクエリ結果は、行を順番に取り出せる RowIterator というオブジェクトで扱われます。
rows = query_job.result()
records = list(rows)
# list() を使用すると、結果をPythonのリストとして保持できます。
# ただし、実務で大量のデータを取得する際には、すべてをリストに変換するとメモリを消費するため注意が必要です。
# 今回は少量のデータだけを扱いますが、今後は取得するデータ量に応じて必要な行だけ取り出す方法や、pandasのDataFrameとして扱う方法を学習します。
#
# ⑤ クエリ実行と料金の関係
# 今回使用するSQLは次のようなものです。
#   SELECT 1 AS test_value
# テーブルを参照しないため、BigQueryのテーブルデータをスキャンしません。
# STEP 5-2では、このようなテーブルを参照しない小規模なSELECT文だけを使用します。
# データの更新・削除・書き込みは行いません。

# 演習問題：PythonからBigQueryのSQLを実行する
# SQL文を引数として受け取り、BigQuery上で実行した結果をPythonの辞書として返す関数を作成してください。
# 作成する関数
from google.cloud import bigquery
import logging
def execute_bigquery_query(project_id, sql):
    try:
        client = bigquery.Client(
            project=project_id
        )
        query_job = client.query(sql)
        rows = query_job.result()
        records = list(rows)  # SQLが大量行を返す場合 list(rows) 実行は大量のデータをPythonのメモリに消費してしまう
        # 原則は後述のSTEPにおける「データ量に応じて必要な行だけ取り出す方法」や「pandasのDataFrameとして扱う方法」で実行
    except Exception as e:
        logging.exception("処理失敗")
        return {
            "status": "ERROR",
            "project_id": project_id,
            "row_count": 0,
            "rows": [],
            "error": str(e)
        }
    else:
        logging.info("処理成功")
        return {
            "status": "OK",
            "project_id": project_id,
            "row_count": len(records),
            "rows": [dict(row.items()) for row in records],
            "error": None
        }

# 要件
#   from google.cloud import bigquery と import logging を使用する。
#   引数 project_id でBigQueryクライアントを生成する。
#   client.query(sql) でSQLを実行する。
#   query_job.result() でクエリの完了を待つ。
#   クエリ結果を list() でリストに変換する。
#   try / except で例外を捕捉する。
#   成功時は logging.info()、失敗時は logging.exception() を使用する。
#   以下の形式の辞書を返す。
# 戻り値の仕様
# 成功時：
# {
#     "status": "OK",
#     "project_id": "指定したプロジェクトID",
#     "row_count": 1,
#     "rows": [{"test_value": 1}],
#     "error": None
# }
# rows には、BigQueryの各行をPythonの辞書に変換して格納してください。BigQueryの Row オブジェクトは次のように変換できます。
# dict(row.items())
#
# 失敗時：
# {
#     "status": "ERROR",
#     "project_id": "指定したプロジェクトID",
#     "row_count": 0,
#     "rows": [],
#     "error": "実際に発生した例外メッセージ"
# }

# テストケース
# テスト①：正常なSQL
result1 = execute_bigquery_query(
    "resonant-tract-508812-p9",
    "SELECT 1 AS test_value"
)
print(result1)
# 期待する結果：
# {
#     "status": "OK",
#     "project_id": "resonant-tract-508812-p9",
#     "row_count": 1,
#     "rows": [{"test_value": 1}],
#     "error": None
# }

# テスト②：構文エラーのあるSQL
result2 = execute_bigquery_query(
    "resonant-tract-508812-p9",
    "SELEC 1 AS test_value"
)
print(result2)
# 期待する結果：
# {
#     "status": "ERROR",
#     "project_id": "resonant-tract-508812-p9",
#     "row_count": 0,
#     "rows": [],
#     "error": "実際に発生した例外メッセージ"
# }


### STEP 5-3｜BigQueryから取得したデータをpandasのDataFrameとして扱う
# STEP 5-2では、PythonからBigQueryにSQLを送信し、取得した行を辞書のリストに変換するところまで実装しました。
# 今回は、BigQueryでSQLを実行し、その結果をpandasのDataFrameとして取得する処理です。
#
# 今回学習する知識
# ① BigQueryからpandasへのデータ取得
# STEP 5-2では、次のように取得していました。
query_job = client.query(sql)
rows = query_job.result()
records = list(rows)
# 今回は、取得したデータをDataFrameに変換します。
df = query_job.result().to_dataframe()
# to_dataframe() は、BigQueryのクエリ結果をpandasのDataFrameとして取得するメソッドです。
#
# ② 必要なライブラリ
# 今回使用するライブラリは以下のとおりです。
import pandas as pd
from google.cloud import bigquery
import logging
# BigQueryの to_dataframe() は、内部で pandas に加えて db-dtypes などのパッケージを必要とします。
# まだ導入されていない場合、PyCharmのターミナルで次を実行してください。すでに導入済みであれば、再インストールは不要です。
python -m pip install pandas db-dtypes
# また、google-cloud-bigquery-storage は今回の必須要件ではありません。BigQuery Storage APIを使用しない取得方法もあります。
# 以前、WindowsのSmart App Controlによって grpcio がブロックされていたため、今回は BigQuery Storage APIを使わない方法を指定します。
df = query_job.result().to_dataframe(
    create_bqstorage_client=False
)
# これにより、BigQuery Storage API用のクライアントを自動生成しないようにします。
#
# ③ DataFrameの行数と列数
# pandasでは、df.shape でDataFrameの行数と列数を取得できます。
row_count = df.shape[0]
column_count = df.shape[1]
# 例えば、次のDataFrameなら、row_count は 3、column_count は 2 になります。
#   product_id	sales
#   A	        100
#   B	        200
#   C	        300
# df.shape を実行すると、内部的には (行数, 列数) のタプルが返ってきます。
# インデックスに従って、このタプルから値を取り出しています。上記DataFrame例であれば df.shape は (3=行数, 2=列数) のタプルです。
#
# ④ DataFrameの列名を取得する
columns = df.columns.tolist()
# df.columns はDataFrameの列名を保持するIndexオブジェクトです。
# .tolist() を使うことで、通常のPythonリストに変換できます。例えば、次の結果になります。
["product_id", "sales"]
#
# ⑤ DataFrameを辞書のリストに変換する
# STEP 5-2では、BigQueryの Row オブジェクトを辞書に変換しました。
# 今回はpandasのDataFrameから変換します。
records = df.to_dict(orient="records")
# 例えば、次のような形式になります。
[
    {"product_id": "A", "sales": 100},
    {"product_id": "B", "sales": 200}
]
# orient="records" は、DataFrameの各行を1つの辞書として扱う指定です。
#
# ⑥ 今回のSQL
# 今回も、実際のテーブルを参照しないSQLを使用します。
# SELECT
#   'A' AS product_id,
#   100 AS sales
# UNION ALL
# SELECT
#   'B',
#   200
# UNION ALL
# SELECT
#   'C',
#   300
#
# このSQLは3行2列の結果を返します。
# BigQueryの既存テーブルをスキャンしないため、今回の演習ではデータ処理量に応じたクエリ料金を心配する必要はありません。
# ただし、Google Cloudの利用状況による一般的な課金条件は別途適用されます

# 演習：BigQueryのクエリ結果をpandasのDataFrameで取得する
# BigQueryにSQLを送信し、結果をpandasのDataFrameとして取得したうえで、行数・列数・列名・データ内容を辞書にまとめて返す関数を作成。
# 作成する関数
def fetch_bigquery_dataframe(project_id, sql):
    # ここに処理を実装
    pass

# 演習要件
#   pandas、bigquery、logging をインポートする。
#   引数 project_id でBigQueryクライアントを生成する。
#   client.query(sql) でSQLを実行する。
#   query_job.result() で実行完了を待つ。
#   to_dataframe(create_bqstorage_client=False) でDataFrameに変換する。
#   df.shape で行数・列数を取得する。
#   df.columns.tolist() で列名を取得する。
#   df.to_dict(orient="records") でデータ内容を辞書のリストに変換する。
#   try / except で例外を処理し、logging.info() と logging.exception() を使用する。
#   以下の形式の辞書を返す。
# 戻り値の仕様
# 成功時：
# {
#     "status": "OK",
#     "project_id": "指定したプロジェクトID",
#     "row_count": 3,
#     "column_count": 2,
#     "columns": ["product_id", "sales"],
#     "rows": [
#         {"product_id": "A", "sales": 100},
#         {"product_id": "B", "sales": 200},
#         {"product_id": "C", "sales": 300}
#     ],
#     "error": None
# }
#
# 失敗時：
# {
#     "status": "ERROR",
#     "project_id": "指定したプロジェクトID",
#     "row_count": 0,
#     "column_count": 0,
#     "columns": [],
#     "rows": [],
#     "error": "実際に発生した例外メッセージ"
# }

# テストケース
# テスト①：正常なSQL
sql1 = """
SELECT 'A' AS product_id, 100 AS sales
UNION ALL
SELECT 'B' AS product_id, 200 AS sales
UNION ALL
SELECT 'C' AS product_id, 300 AS sales
"""
result1 = fetch_bigquery_dataframe("resonant-tract-508812-p9", sql1)
print(result1)
# 今回のSQLのように複数行にわたって記述したい場合、"""（ダブルクォーテーション3つ）を使用します。
# """ を使用すると、改行を含む文字列をそのまま記述でき、SQLは長くなることが多いため、PythonからSQLを実行する際によく使われる書き方です。
# 期待する結果は、3行2列のデータを含む成功時の辞書です。
# なお、SQLに ORDER BY を指定していないため、行の順番は保証されません。A・B・Cの順序が異なってもデータ内容が一致していれば合格です。

# テスト②：構文エラーのあるSQL
sql2 = "SELEC 'A' AS product_id"
result2 = fetch_bigquery_dataframe("resonant-tract-508812-p9", sql2)
print(result2)
# 期待する結果は、status が "ERROR"、行数・列数が 0、columns と rows が空のリストで、
# error にBigQueryからのエラーメッセージが入った辞書です。


### STEP 5-4｜

















