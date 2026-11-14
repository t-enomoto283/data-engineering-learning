
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
    # ここに処理を実装
    pass

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
































































