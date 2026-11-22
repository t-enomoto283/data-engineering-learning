
### STEP 7-1｜総合演習① データパイプラインの設計と実装
# テーマは、複数のCSVファイルを読み込み、データ品質を検証し、加工・集計した結果をCSVに保存するETLパイプラインです。
# 今回は新しいライブラリや文法を増やすことよりも、既習の知識を組み合わせて一連の処理を設計することを重視します。
# 完成する処理の流れは次のとおりです。
#   sales.csv 売上明細     products.csv 商品マスタ
#                └─────┬─────┘
#   Extract：データ取得 CSVをDataFrameとして読み込む
#                      ↓
#     Validate：品質検証 必須列・欠損・重複・結合関係
#                      ↓
#   Transform：データ加工 結合・売上金額計算・商品別集計
#                      ↓
#        Load：結果保存 商品別売上CSVを出力

# 今回使うPython・pandas
#   pd.read_csv()            CSVデータの取得
#   DataFrame.columns        必須列の確認
#   isna()                   欠損値の検証
#   duplicated()             重複データの検証
#   pd.merge()               売上明細と商品マスタの結合
#   validate="many_to_one"   結合関係の保証
#   groupby() / agg()        商品別売上集計
#   to_csv()                 集計結果の保存
#   try / except             異常系の処理
#   logging                  実行状況の記録
#   関数化・戻り値              パイプライン全体の管理

# 演習で使用するデータ
# 今回は2つのCSVファイルを使用します。
# 以下のデータをそれぞれ sales.csv、products.csv として保存してください。
#   sales.csv：売上明細
#   products.csv：商品マスタ
# 今回のデータには、欠損値や重複などの品質問題は含めていません。まず正常系のパイプラインを完成させ、その後に異常系を確認します。
import pandas as pd
sales_df = pd.DataFrame(
    {
        "sale_id": [1, 2, 3, 4, 5, 6],
        "sale_date": ["2026-11-01", "2026-11-01", "2026-11-02", "2026-11-02", "2026-11-03", "2026-11-03"],
        "product_id": ["P001", "P002", "P001", "P003", "P002", "P003"],
        "quantity": [2, 1, 3, 2, 2, 4],
        "unit_price": [1200, 2500, 1200, 800, 2500, 800]
    }
)
sales_df.to_csv("sales.csv", index=False)
read_sales = pd.read_csv("sales.csv")
print(read_sales)

product_df = pd.DataFrame(
    {
        "product_id": ["P001", "P002", "P003"],
        "product_name": ["ノート", "バッグ", "ペン"],
        "category": ["文房具", "雑貨", "文房具"]
    }
)
product_df.to_csv("products.csv", index=False)
read_products = pd.read_csv("products.csv")
print(read_products)

# データ品質の要件
# パイプラインでは、加工前に次の品質検証を行ってください。
#   検証対象	    条件	                          異常時の動作
#   sales	    必須列5項目が存在する             ValueError
#   products	必須列3項目が存在する             ValueError
#   sales	    sale_id が重複していない         ValueError
#   products	product_id が重複していない      ValueError
#   sales	    必須列に欠損がない	              ValueError
#   products	必須列に欠損がない	              ValueError
#   結合	        product_id が多対1で結合できる	  ValueError
#   結合	        salesの全行が商品マスタに対応する	  ValueError
#
# 最後の2つは似ていますが、意味が異なります。
# validate="many_to_one" は、右表の結合キーが一意であることを検証します。しかし、左表のキーがすべて右表に存在することまでは保証しません。
# そのため、商品マスタに存在しない product_id が売上明細に含まれていないかも確認する必要があります。
# 例えば、merge(..., how="left", indicator=True) を使用すれば、_merge 列の left_only から未対応の行を検出できます。

# 課題①：ETLパイプライン本体
# 次の関数を作成してください。
import pandas as pd
import logging
from pandas.errors import MergeError

def run_sales_etl(sales_csv, products_csv, output_csv):
    try:
        # csvからdataframe読み
        sales = pd.read_csv(sales_csv)
        products = pd.read_csv(products_csv)
        sales_row_count = sales.shape[0]
        products_row_count = products.shape[0]
        logging.info(f"{sales_csv} 読み込み完了: {sales_row_count}行")
        logging.info(f"{products_csv} 読み込み完了: {products_row_count}行")

        # 必須列確認
        required_sales_columns = ["sale_id", "sale_date", "product_id", "quantity", "unit_price"]
        required_products_columns = ["product_id", "product_name", "category"]
        shortage_sales_column = [rs_col for rs_col in required_sales_columns if rs_col not in sales.columns]
        shortage_products_column = [rp_col for rp_col in required_products_columns if rp_col not in products.columns]
        if shortage_sales_column:
            raise ValueError(f"{sales_csv} の必須列不足: {shortage_sales_column}")
        elif shortage_products_column:
            raise ValueError(f"{products_csv} の必須列不足: {shortage_products_column}")

        # 必須列の欠損確認（新しい判定ブロックとして if で開始）
        if sales[required_sales_columns].isna().any().any():  # 全体で「1つでもTrueがあるか」を判定（最終的に1つの True/False）
            raise ValueError(f"{sales_csv} の必須列に欠損")
        elif products[required_products_columns].isna().any().any():
            raise ValueError(f"{products_csv} の必須列に欠損")

        # キーの重複確認
        duplicate_sal_id = sales.duplicated(
            subset=["sale_id"],
            keep=False
        ).any()
        duplicate_product_id = products.duplicated(
            subset=["product_id"],
            keep=False
        ).any()
        if duplicate_sal_id:
            raise ValueError("sale_id重複")
        elif duplicate_product_id:
            raise ValueError("product_id重複")

        # 結合キーのvalidate確認
        try:
            join_table = sales.merge(
                products,
                on="product_id",
                how="left",
                validate="many_to_one",
                indicator=True
            )
        except MergeError as me:
            raise ValueError(me) from me

        # 商品マスタに存在しない product_id が売上明細に含まれていないか確認
        not_match_row = join_table[
            join_table["_merge"] == "left_only"
        ]
        not_match_count = not_match_row.shape[0]
        if not_match_count > 0:
            raise ValueError(f"商品マスタに存在しない product_id が売上明細にあります: {not_match_row}")

        # 計算したsales_amount列を追加
        join_table["sales_amount"] = join_table["quantity"] * join_table["unit_price"]

        # product_id、product_name、category ごとに集計
        agg_sales = join_table.groupby(
            ["product_id", "product_name", "category"],
            as_index=False  # as_index=False を追加してグループ化列が消えるのを防止
        ).agg(
            total_quantity=("quantity", "sum"),
            total_sales=("sales_amount", "sum")
        )
        agg_sales = agg_sales.sort_values(
            "product_id",
            ascending=True
        )
        agg_sales = agg_sales.reset_index(drop=True)

        # output_csv にCSV形式で保存
        agg_sales.to_csv(output_csv, index=False)

        # 正常終了時の戻り値
        return {
            "status": "SUCCESS",
            "input_rows": sales_row_count,
            "output_rows": agg_sales.shape[0],
            "total_sales": agg_sales["total_sales"].sum().item()
        }

    except Exception as e:
        logging.error(e)
        raise

# 実装要件1
# A. データ取得
#   sales_csv と products_csv を読み込み、DataFrameに格納する。
#   読み込んだ行数をログに出力する。
# B. データ品質検証
#   両DataFrameの必須列を確認する。
#   必須列の欠損を確認する。
#   sale_id と商品マスタの product_id の重複を確認する。
#   不正なデータが存在する場合は ValueError を発生させる。
# C. データ加工
#   product_id をキーに売上明細と商品マスタを左結合する。
#   validate="many_to_one" を指定する。
#   商品マスタに対応しない売上明細があれば ValueError を発生させる。
#   sales_amount = quantity * unit_price を計算する。
#   product_id、product_name、category ごとに集計する。
# 集計結果には、次の列を含めてください。
#   列	            内容
#   product_id	    商品ID
#   product_name	商品名
#   category	    カテゴリ
#   total_quantity	販売数量の合計
#   total_sales	    売上金額の合計
# D. データ保存
#   商品IDの昇順で並べ替える。
#   output_csv にCSV形式で保存する。
#   保存時にDataFrameのインデックスは含めない。
# E. 実行結果管理
#   正常終了した場合は、次の辞書を返す。
# {
#     "status": "SUCCESS",
#     "input_rows": 6,
#     "output_rows": 3,
#     "total_sales": 18300
# }
# エラーが発生した場合は、エラー内容をログに出力し、例外を呼び出し元へ再送出する。
# total_sales は、集計結果の total_sales 列の合計です。

# 期待する集計結果
#   商品別売上集計
#   商品ID	商品名	カテゴリ	数量	売上
#   P001	ノート	文房具	5	6,000
#   P002	バッグ	雑貨	3	7,500
#   P003	ペン	文房具	6	4,800
# テストケース①：正常系
result = run_sales_etl(
    "sales.csv",
    "products.csv",
    "sales_summary.csv"
)
print(result)
print(pd.read_csv("sales_summary.csv"))
# 期待する戻り値：
# {
#     "status": "SUCCESS",
#     "input_rows": 6,
#     "output_rows": 3,
#     "total_sales": 18300
# }

# テストケース②：異常系
# 商品マスタの P003 を P999 に変更した別ファイル products_invalid.csv を用意してください。
# そのファイルを指定してパイプラインを実行します。
products_invalid = product_df.copy()
products_invalid.loc[
    products_invalid["product_id"] == "P003", "product_id"
] = "P999"
products_invalid.to_csv("products_invalid.csv", index=False)

run_sales_etl(
    "sales.csv",
    "products_invalid.csv",
    "sales_summary_invalid.csv"
)
# 期待する動作は、商品マスタに存在しない商品IDを検出して ValueError を発生させ、異常系の出力CSVを作成しないことです。
# 例外メッセージの文言は自由です。


### STEP 7-2｜BigQueryと連携したELTパイプライン
# 今回は、STEP 7-1で作成した売上データを使い、PythonからBigQueryへデータをロードし、BigQuery上のSQLで加工/集計するELTパイプラインです。
# STEP 7-1では、Python・pandasで加工した後にCSVへ保存しました。今回は、加工処理をBigQuery側に移すことが大きな違いです。
#
# 今回の目標は、次の3つです。既習の知識を統合する総合演習です。基本的に新しいPython文法は導入しません。
#   1. PythonからBigQueryへ複数のCSVデータをロードする。
#   2. BigQuery上のSQLで結合・加工・集計を行う。
#   3. 集計結果をBigQueryのテーブルとして保存し、Pythonから検証する。
#
# ETLとELTの違い
#       STEP 7-1：ETL               STEP 7-2：ELT
#     Extract CSV読み込み          Extract CSV読み込み
#            ↓                           ↓
#   Transform pandasで加工・集計    Load BigQueryへロード
#            ↓                           ↓
#      Load CSVへ保存          Transform BigQueryで加工・集計

# 今回使うPython・pandas・BigQueryの知識
#   知識                          使用目的
#   pd.read_csv()                 CSVデータの取得
#   bigquery.Client()             BigQueryへの接続
#   load_table_from_dataframe()	  DataFrameをBigQueryへロード
#   LoadJobConfig                 ロード方法の指定
#   WRITE_TRUNCATE                テーブル内容の置き換え
#   client.query()                BigQueryでSQLを実行
#   CREATE OR REPLACE TABLE       SQL集計結果をテーブルに保存
#   JOIN / GROUP BY               BigQuery上での結合・集計
#   to_dataframe()                BigQueryの結果を取得
#   try / except                  エラー処理
#   logging                       処理状況の記録
# 今回は、これまで使用してきたBigQuery Sandbox環境を前提にします。
# SandboxではDMLの INSERT・UPDATE・MERGE・DELETE を使わずに実装します。
# 代わりに、DataFrameのバッチロードと CREATE OR REPLACE TABLE ... AS SELECT を使用します。

# 今回のデータとテーブル構成
# STEP 7-1で使用した2つのCSVを、そのまま使用します。
#   CSV	            BigQueryテーブル	      内容
#   sales.csv	    sales_raw_step7	      売上明細6行
#   products.csv	products_raw_step7	  商品マスタ3行
#       —           sales_summary_step7	  商品別売上集計3行
#
# BigQueryの保存先は、これまでの学習環境に合わせて次のようにします。
project_id = "resonant-tract-508812-p9"
dataset_id = "sql_training"
# 最終的には、次の3テーブルが作成される構成です。
#   sales_raw_step7 売上明細   products_raw_step7 商品マスタ
#              └─────────┬─────────┘
#        BigQuery SQL JOIN・売上金額計算・GROUP BY
#                        ↓
#            sales_summary_step7 商品別売上集計

# 今回の新しい設計：SQLの集計結果をテーブルに保存する
# STEP 5では、PythonからBigQueryにSQLを送信して結果を取得する処理をしました。
# 今回は、そのSQLの結果をBigQueryのテーブルとして保存します。
# 使用するのは CREATE OR REPLACE TABLE です。
# 例えば、次のSQLを考えます。
"""
CREATE OR REPLACE TABLE `project.dataset.output_table` AS
SELECT
  category,
  COUNT(*) AS row_count
FROM `project.dataset.input_table`
GROUP BY category
"""
# このSQLでは、次の処理が行われます。
#   input_table からデータを取得する。
#   category ごとに集計する。
#   集計結果を output_table に保存する。
# output_table がすでに存在する場合は、テーブルを置き換えます。
# 今回の演習では、同じ入力データで再実行しても、集計結果が重複して増えない構成を目指します。
# ただし、テーブルを置き換えることだけで、パイプライン全体の冪等性や障害時の安全性が保証されるわけではありません。

# 課題①：BigQuery ELTパイプラインの作成
# 次の関数を作成してください。
# A. Extract：CSVの読み込み
#   sales_csv と products_csv をpandasで読み込む。
#   それぞれの行数を取得する。
#   読み込み行数を logging.info() で記録する。
# B. Load：BigQueryへのロード
#   bigquery.Client(project=project_id) でクライアントを作成する。
#   以下の2つのテーブルIDを作成する。
#     {project_id}.{dataset_id}.sales_raw_step7
#     {project_id}.{dataset_id}.products_raw_step7
#   load_table_from_dataframe() を使って、それぞれのDataFrameをBigQueryへロードする。
#   ロード時は WRITE_TRUNCATE を指定する。
#   それぞれのロードジョブについて .result() を呼び出し、完了を待つ。
# C. Transform：BigQueryでのSQL加工
#   BigQueryで次の処理を行うSQLを作成する。
#     sales_raw_step7 と products_raw_step7 を product_id で結合する。
#     quantity * unit_price で売上金額を計算する。
#     product_id、product_name、category ごとに集計する。
#     total_quantity と total_sales を求める。
#     CREATE OR REPLACE TABLE を使い、集計結果を sales_summary_step7 に保存する。
#   client.query() でSQLを実行し、.result() で完了を待つ。
#   今回は、STEP 7-1と同じく、商品マスタの対応があるデータを使用するため結合には INNER JOIN を使用。
#   今回は正常データを前提とするため、未対応キーの検証はSTEP 7-2の必須要件には含めません。
# D. 検証：集計結果の取得
#   sales_summary_step7 から全行を取得するSQLを実行する。
#   to_dataframe(create_bqstorage_client=False) でpandasのDataFrameに変換する。
#   商品IDの昇順に並んだ結果を確認する。
#   次の条件を検証する。
#     出力行数が3行である。
#     total_sales の合計が18,300である。
#   検証条件を満たさない場合は ValueError を発生させる。
# E. 実行結果管理
#   正常終了時には、次の辞書を返す。
# {
#     "status": "SUCCESS",
#     "input_rows": {
#         "sales": 6,
#         "products": 3
#     },
#     "output_rows": 3,
#     "total_sales": 18300
# }
# 今回はBigQueryへ2つの入力テーブルをロードするため、input_rows をファイル別に記録する仕様にしています。
# これはSTEP 7-2の新しい仕様であり、STEP 7-1の戻り値の仕様を変更するものではありません。
# 例外発生時は logging.error() で記録し、raise で呼び出し元に再送出する。

import pandas as pd
from google.cloud import bigquery
import logging

def run_sales_elt(project_id, dataset_id, sales_csv, products_csv):
    try:
        # CSV読み
        sales_df = pd.read_csv(sales_csv)
        products_df = pd.read_csv(products_csv)
        sales_row_count = sales_df.shape[0]
        products_row_count = products_df.shape[0]
        # 発ログ
        logging.info(f"{sales_csv} 読み込み完了: {sales_row_count}行")
        logging.info(f"{products_csv} 読み込み完了: {products_row_count}行")

        # BigQuery接続
        client = bigquery.Client(
            project=project_id,
        )
        # BigQueryテーブルID作成
        sales_table_id = f"{project_id}.{dataset_id}.sales_raw_step7"
        products_table_id = f"{project_id}.{dataset_id}.products_raw_step7"
        # Loadのジョブ設定・それぞれのジョブ実行・完了待ち
        load_job_config = bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE  # destinationで指定したテーブルが既にある場合は置換）
        )
        sales_table_load_job = client.load_table_from_dataframe(
            dataframe=sales_df,
            destination=sales_table_id,
            job_config=load_job_config,
        )
        sales_table_load_job.result()
        products_table_load_job = client.load_table_from_dataframe(
            dataframe=products_df,
            destination=products_table_id,
            job_config=load_job_config,
        )
        products_table_load_job.result()

        # BigQuery上での結合・集計用SQL（CTASで指定したテーブルが既にある場合はテーブルを置き換えます）
        ctas_join_agg_sql = f"""
        CREATE OR REPLACE TABLE `{project_id}.{dataset_id}.sales_summary_step7` AS
        SELECT
          s.product_id,
          p.product_name,
          p.category,
        SUM(s.quantity) AS total_quantity,
        SUM(s.quantity * s.unit_price) AS total_sales
        FROM `{sales_table_id}` AS s
        INNER JOIN `{products_table_id}` AS p
          ON s.product_id = p.product_id
        GROUP BY s.product_id, p.product_name, p.category;
        """
        # 結合・集計SQLのジョブ実行・完了待ち
        ctas_join_agg_job = client.query(ctas_join_agg_sql)
        ctas_join_agg_job.result()

        # BigQuery上にCTASしたテーブルの全行読み・PythonのDataFrame変換
        fetch_all_rows_sql = f"""
        SELECT
          *
        FROM `{project_id}.{dataset_id}.sales_summary_step7`
        ORDER BY product_id ASC;
        """
        fetch_all_rows_job = client.query(fetch_all_rows_sql)
        sales_summary_step7_df = fetch_all_rows_job.result().to_dataframe(
            create_bqstorage_client=False
        )

        # 検証（演習のため固定値）
        if sales_summary_step7_df.shape[0] != 3:
            raise ValueError("sales_summary_step7_dfの行数が異なります")
        if sales_summary_step7_df["total_sales"].sum().item() != 18300:
            raise ValueError("sales_summary_step7_dfの合計額が異なります")

        return {
            "status": "SUCCESS",
            "input_rows": {
                "sales": sales_row_count,
                "products": products_row_count,
            },
            "output_rows": sales_summary_step7_df.shape[0],
            "total_sales": sales_summary_step7_df["total_sales"].sum().item()
        }
    except Exception as e:
        logging.error(e)
        raise

# 実装時の注意点
# ① BigQuery Sandboxの制約
# 今回の演習では、DMLを使用しません。
# DataFrameのロードには、次の構成を使用できます。
job_config = bigquery.LoadJobConfig(
    write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE
)
# SQLで集計結果を保存する場合は、CREATE OR REPLACE TABLE ... AS SELECT を使用します。
#
# ② テーブルIDとSQLの組み立て
# PythonからテーブルIDをSQLに埋め込む場合は、BigQueryのテーブル識別子をバッククォートで囲みます。
table_id = f"{project_id}.{dataset_id}.sales_raw_step7"
sql = f"""
SELECT *
FROM `{table_id}`
"""
# 今回のテーブルIDは、演習で指定した固定のプロジェクト・データセットを使用してください。
#
# ③ 検証する数値について
# 今回は固定の演習データを使用するため、出力行数3行、売上合計18,300を期待値として検証します。
# 実務のパイプラインでは、毎回処理件数や売上合計が変わることが一般的です。
# その場合、固定値ではなく、入力データとの整合性や品質ルールに基づいて検証します。

# テストケース
# テスト①：正常系
result = run_sales_elt(
    "resonant-tract-508812-p9",
    "sql_training",
    "sales.csv",
    "products.csv"
)
print(result)
# 期待する戻り値：
# {
#     "status": "SUCCESS",
#     "input_rows": {
#         "sales": 6,
#         "products": 3
#     },
#     "output_rows": 3,
#     "total_sales": 18300
# }
# BigQueryの sales_summary_step7 には、次の結果が保存されます。
# product_id	product_name	category	total_quantity	total_sales
# P001	ノート	文房具	5	6,000
# P002	バッグ	雑貨	3	7,500
# P003	ペン	文房具	6	4,800

# テスト②：再実行テスト
# 同じ関数を、同じ引数でもう一度実行してください。
# 期待する結果は、1回目と同じ3行・売上合計18,300 です。
# 今回は、WRITE_TRUNCATE と CREATE OR REPLACE TABLE により、同じ入力データを再実行しても行数や売上金額が増加しないことを確認します。


### STEP 7-3｜増分処理・再実行制御・ログ・監視の統合
# STEP 7-2では、CSVをBigQueryにロードし、SQLで集計して結果を保存するELTパイプラインを実装しました。
# 今回は、処理済みデータを管理し、新しいデータだけを安全に処理するパイプラインの実装です。
# これまで学習したウォーターマーク、増分処理、冪等性、実行ログ、エラー処理を組み合わせます。
#
# 今回は次の4点を目標にします。
#   BigQuery上のウォーターマークを参照し、未処理データだけを抽出する。
#   処理対象がない場合でも、正常に終了できるようにする。
#   処理が成功した場合だけ、ウォーターマークを更新する。
#   実行結果を構造化ログに記録し、処理状況を確認できるようにする。
#
# STEP 7-2との違い
#   観点	         STEP 7-2	 STEP 7-3
#   処理対象	     CSV全件	     未処理データのみ
#   処理済みデータ	 毎回置き換え	 保持する
#   再実行	     全件再ロード	 同じデータを二重処理しない
#   処理状態	     戻り値で確認	 BigQueryのウォーターマークで管理
#   ログ	         通常のログ	 JSONL形式の構造化ログ
#   主な目的	     ELTの実装	 増分パイプラインの運用

# 使用する知識
#   pd.read_csv()	              入力データの読み込み
#   DataFrameの条件抽出	          未処理データの抽出
#   pd.to_datetime()	          日付の比較
#   bigquery.Client()	          BigQuery接続
#   client.query()		          ウォーターマークの取得
#   load_table_from_dataframe()	  増分データの保存
#   WRITE_APPEND	              既存データへの追記
#   WRITE_TRUNCATE	              状態テーブルの置き換え
#   max()	                      ウォーターマークの更新
#   datetime	                  実行日時の記録
#   json	            	      JSONLログの出力
#   try / except	              エラー処理
# 今回も、これまでのBigQuery Sandbox環境を使用します。

# 今回のパイプライン構成
# 今回の演習では、次の3つを使用します。
#   データ	    保存先	                    役割
#   入力CSV	    sales_incremental.csv	    増分処理の元データ
#   売上テーブル	sales_incremental_step7	    処理済み売上データ
#   状態テーブル	pipeline_watermarks_step7	パイプラインごとのウォーターマーク
# 実行ログはローカルの sales_incremental_log.jsonl に保存します。
#
#   sales_incremental.csv 売上明細データ
#     ↓
#   Python：増分判定 BigQueryからウォーターマーク取得・sale_date がウォーターマークより新しい行を抽出
#     ↓
#   BigQuery：sales_incremental_step7 WRITE_APPENDで増分データを保存
#     ↓
#   BigQuery：pipeline_watermarks_step7 成功後にウォーターマーク更新
#     ↓
#   JSONL：実行ログ 実行結果・処理件数・エラー情報

## ウォーターマークの管理方法
# 今回は、1つのBigQueryテーブルで複数のパイプラインのウォーターマークを管理できる構成にします。
# WRITE_TRUNCATE は、対象テーブルの既存データをすべて置き換えます。
# 仮に sales_incremental の1行だけを書き戻した場合、inventory_incremental は消えてしまいます。
# 今回は、それを防ぐために「状態テーブル全体を読み込み、対象行だけ更新して、全行を書き戻す」という設計にします。
#
# 具体例
# 更新前のBigQuery状態テーブル：
#   pipeline_name	        watermark
#   sales_incremental	    2026-11-01
#   inventory_incremental	2026-11-05
#
# 問題のある方法：
# sales_incremental の行だけ取得し、更新して WRITE_TRUNCATE する場合です。
watermark_df = pd.DataFrame(
    {"pipeline_name": ["sales_incremental"],
    "watermark": ["2026-11-03"]}
)
# このDataFrameを WRITE_TRUNCATE すると、BigQueryの状態テーブルは次のようになり inventory_incremental は消えてしまいます。
#   pipeline_name	    watermark
#   sales_incremental	2026-11-03
#
# 今回想定している方法：
# まず、状態テーブルの全行をDataFrameとして取得します。
watermark_df
#   pipeline_name	        watermark
#   sales_incremental	    2026-11-01
#   inventory_incremental	2026-11-05
# 次に、sales_incremental に該当する行だけを「更新」します。
watermark_df.loc[
    watermark_df["pipeline_name"] == "sales_incremental", "watermark"
] = "2026-11-03"
# 更新後のDataFrameは次のようになります。
#   pipeline_name	        watermark
#   sales_incremental	    2026-11-03
#   inventory_incremental	2026-11-05
# このように「更新後の全行を保持したDataFrame全体を WRITE_TRUNCATE でBigQueryの状態テーブルへ書き戻す」という設計です。
# これなら、対象パイプラインのウォーターマークを更新しつつ、他のパイプラインの状態も保持されます。
#
# 状態テーブルの構造は次のとおりです。
#   pipeline_watermarks_step7
#   pipeline_name	        watermark
#   sales_incremental	    2026-11-01
#   inventory_incremental	2026-11-05
# pipeline_name で対象パイプラインを識別します。
# 今回処理するのは sales_incremental だけです。inventory_incremental は、別のパイプラインの状態を保持する例として使用します。
#
# 今回の更新方式
# BigQuery SandboxではDMLを使用できないため、次の方法で状態を管理します。
#   1. BigQueryから状態テーブルを読み込む。
#   2. 今回のパイプラインのウォーターマークを取得する。
#   3. 新しいウォーターマークを計算する。
#   4. 状態テーブルのDataFrameで対象を更新する。
#   5. WRITE_TRUNCATE で状態テーブル全体を書き戻す。
# なお、テーブル全体の置き換えは、他のパイプラインが同時に更新すると競合する可能性があります。
# 今回は単独実行を前提とし、同時更新への対応は演習の対象外とします。

# 演習用データ：
#   sales_incremental.csv
# 今回は、日付による増分処理を確認します。
sales_incremental_df = pd.DataFrame(
    {
        "sale_id": [1, 2, 3, 4, 5, 6],
        "sale_date": ["2026-11-01", "2026-11-01", "2026-11-02", "2026-11-02", "2026-11-03", "2026-11-03"],
        "product_id": ["P001", "P002", "P001", "P003", "P002", "P003"],
        "quantity": [2, 1, 3, 2, 2, 4],
        "unit_price": [1200, 2500, 1200, 800, 2500, 800]
    }
)
sales_incremental_df.to_csv("sales_incremental.csv", index=False)
#
# 今回は、状態テーブルに次の初期データがある状態から開始します。
#   pipeline_name	        watermark
#   sales_incremental	    2026-11-01
#   inventory_incremental	2026-11-05
# 売上テーブルには、すでに11月1日の2行が保存されているものとします。
# したがって、今回の増分処理対象は11月2日・3日の4行です。

# 実装上の重要な注意点
# ① BigQueryの初期テーブルについて
#   今回の課題では、既存の売上テーブルと状態テーブルを前提にしています。
#   そのため、実行前に初期状態を作成する必要があります。
#   ただし、初期状態の作成処理と増分パイプライン本体は分離してください。毎回の関数実行で初期状態を作り直すと、増分処理の意味がなくなるためです。
# ② 初期登録されていないパイプラインについて
#   今回は状態テーブルに sales_incremental が存在する前提です。
#   新しい pipeline_name が状態テーブルに存在しない場合の初期登録処理は、今回の必須要件には含めません。
#   複数パイプラインの初期登録を含むウォーターマーク管理は、別途扱う発展課題として残します。
# ③ 失敗時の状態管理
#   今回の実装では、データのロードが成功してからウォーターマークを更新します。
#   ただし、ロード成功後にウォーターマーク更新だけが失敗すると、再実行時に同じデータを追記してしまう可能性があります。
#   今回確認する冪等性は、正常終了後の再実行についてです。障害途中からの完全な復旧保証までは求めません。
#   この制約は、実務で増分パイプラインを設計する際の重要な検討事項です。

# 課題①：増分パイプラインの作成
# 次の関数を実装してください。
# A. Extract：入力データとウォーターマークの取得
#   input_csv をpandasで読み込む。
#   sale_date を日付型に変換する。
#   BigQueryに接続する。
#   pipeline_watermarks_step7 から、pipeline_name に対応するウォーターマークを取得する。
#   sale_date > watermark を満たす行だけを抽出する。
#   今回の演習では、sale_date が日付として解釈できるデータを使用します。
# B. Load：増分データの保存
#   増分データが存在する場合、sales_incremental_step7 に WRITE_APPEND でロードする。
#   .result() でロードジョブの完了を待つ。
#   増分データが0行の場合、ロードを実行しない。
# C. ウォーターマークの更新
#   ロードが成功した場合、増分データの sale_date の最大値を取得する。
#   新しいウォーターマークを max(旧ウォーターマーク, 増分データの最大日付) で決定する。
#   状態テーブルの対象パイプラインのウォーターマークを更新する。
#   他のパイプラインのウォーターマークは変更しない。
#   状態テーブルを WRITE_TRUNCATE で書き戻す。
#   増分データが0行の場合、ウォーターマークは更新しません。
# D. JSONL形式のログ
#   実行結果をJSONL形式で log_file に追記する。
#   次の情報を記録する
# {
#   "pipeline_name": "sales_incremental",
#   "status": "SUCCESS",
#   "input_rows": 6,
#   "processed_rows": 4,
#   "old_watermark": "2026-11-01",
#   "new_watermark": "2026-11-03",
#   "executed_at": "実行日時"
# }
#   増分データが0行の場合は、status を "SKIPPED" としてください。
#   エラー発生時は status を "FAILED" とし、error キーにエラー内容を記録してください。
# E. 戻り値・例外処理
#   正常終了時は、ログと同じ主要情報を辞書で返す。
#   増分データが0行の場合は、SKIPPED の辞書を返す。
#   エラー発生時はJSONLログに記録し、例外を再送出する。

import pandas as pd
from google.cloud import bigquery
import logging
import json
from datetime import datetime

def run_incremental_sales_pipeline(project_id, dataset_id, input_csv, pipeline_name, log_file):
    start_time = datetime.now().isoformat()
    input_rows_count = 0
    processed_rows_count = 0
    error = None
    old_watermark_log = None
    new_watermark_log = None
    try:
        # input_csvをDataFrameに読み、sale_date を日付型に変換
        input_df = pd.read_csv(input_csv)
        input_rows_count += input_df.shape[0]
        input_df["sale_date"] = pd.to_datetime(input_df["sale_date"])

        # BigQuery接続
        client = bigquery.Client(
            project=project_id
        )
        # BigQueryテーブルID作成
        pipeline_watermarks_step7_id = f"{project_id}.{dataset_id}.pipeline_watermarks_step7"
        sales_incremental_step7_id = f"{project_id}.{dataset_id}.sales_incremental_step7"
        # BigQueryの状態テーブルからウォーターマークを取得してDataFrameに変換
        watermark_query_job = client.query(
            f"""
            SELECT
              pipeline_name,
              watermark
            FROM `{pipeline_watermarks_step7_id}`
            """
        )
        watermark_df = watermark_query_job.result().to_dataframe(
            create_bqstorage_client=False
        )
        watermark_df["watermark"] = pd.to_datetime(watermark_df["watermark"])
        pipeline_name_watermark = watermark_df[
            watermark_df["pipeline_name"] == pipeline_name
        ].iloc[0]

        # 後続 finally のログで使用の変数
        old_watermark_log = pipeline_name_watermark["watermark"].strftime("%Y-%m-%d")

        # sale_date > watermark を満たす行だけを抽出
        incremental_df = input_df[
            input_df["sale_date"] > pipeline_name_watermark["watermark"]
        ].copy()
        incremental_df["sale_date"] = pd.to_datetime(incremental_df["sale_date"]).dt.date

        # 増分データが存在する場合、sales_incremental_step7 に WRITE_APPEND でロード
        if not incremental_df.empty:
            load_append_job_config = bigquery.LoadJobConfig(
                schema=[
                    bigquery.SchemaField("sale_id", "INTEGER", mode="REQUIRED"),
                    bigquery.SchemaField("sale_date", "DATE", mode="REQUIRED"),
                    bigquery.SchemaField("product_id", "STRING", mode="REQUIRED"),
                    bigquery.SchemaField("quantity", "INTEGER", mode="REQUIRED"),
                    bigquery.SchemaField("unit_price", "INTEGER", mode="REQUIRED")
                ],
                write_disposition=bigquery.WriteDisposition.WRITE_APPEND
            )
            load_append_job = client.load_table_from_dataframe(
                incremental_df,
                sales_incremental_step7_id,
                job_config=load_append_job_config
            )
            load_append_job.result()
            processed_rows_count += incremental_df.shape[0]

            # ロードジョブの成功後に新しいウォーターマークを max(旧ウォーターマーク, 増分データの最大日付) で決定
            incremental_df["sale_date"] = pd.to_datetime(incremental_df["sale_date"])
            new_watermark = max(
                pipeline_name_watermark["watermark"],
                incremental_df["sale_date"].max()
            )

            watermark_df.loc[
                watermark_df["pipeline_name"] == pipeline_name, "watermark"
            ] = new_watermark
            watermark_df["watermark"] = pd.to_datetime(watermark_df["watermark"]).dt.date

            # 更新後の全行を保持したDataFrame全体を WRITE_TRUNCATE でBigQueryの状態テーブルへ書き戻す
            load_truncate_job_config = bigquery.LoadJobConfig(
                schema=[
                    bigquery.SchemaField("pipeline_name", "STRING", mode="REQUIRED"),
                    bigquery.SchemaField("watermark", "DATE", mode="REQUIRED"),
                ],
                write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE
            )
            load_truncate_job = client.load_table_from_dataframe(
                watermark_df,
                pipeline_watermarks_step7_id,
                job_config=load_truncate_job_config
            )
            load_truncate_job.result()

            # 後続 finally のログで使う status や new_watermark 用の変数に記録
            status = "SUCCESS"
            new_watermark_log = new_watermark.strftime("%Y-%m-%d")

        # 増分データが存在しない場合
        else:
            status = "SKIPPED"
            new_watermark_log = old_watermark_log

    except Exception as e:
        status = "FAILED"
        error = str(e)
        logging.error(e)
        raise

    finally:
        log = {
            "pipeline_name": pipeline_name,
            "status": status,
            "input_rows": input_rows_count,
            "processed_rows": processed_rows_count,
            "old_watermark": old_watermark_log,
            "new_watermark": new_watermark_log,
            "executed_at": start_time,
            "error": error
        }
        with open(f"{log_file}.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(log, ensure_ascii=False) + "\n")
    return log

# 初期テーブル準備用コード
# このコードは初期テーブルが存在しないことを前提にしています。途中で失敗して一部だけ作成された場合は再実行前に状態を確認する必要があります。
# 作成する初期状態は次のとおりです。
# ① sales_incremental_step7：売上2行
#   sale_id	sale_date	product_id	quantity	unit_price
#   1	2026-11-01	P001	2	1200
#   2	2026-11-01	P002	1	2500
# ② pipeline_watermarks_step7：状態2行
#   pipeline_name	watermark
#   sales_incremental	2026-11-01
#   inventory_incremental	2026-11-05
# 以下のコードでは、既存テーブルを誤って上書きしないよう、WRITE_EMPTY を使用します。
import pandas as pd
from datetime import date
from google.cloud import bigquery
from google.api_core.exceptions import NotFound
project_id = "resonant-tract-508812-p9"
dataset_id = "sql_training"
client = bigquery.Client(project=project_id)
sales_table_id = f"{project_id}.{dataset_id}.sales_incremental_step7"
watermark_table_id = f"{project_id}.{dataset_id}.pipeline_watermarks_step7"
# 既存テーブルがある場合は初期化を中止
for table_id in [sales_table_id, watermark_table_id]:
    try:
        client.get_table(table_id)
    except NotFound:
        pass
    else:
        raise ValueError(f"既存テーブルがあるため初期化を中止: {table_id}")
# 初期売上データ
sales_initial_df = pd.DataFrame(
    {"sale_id": [1, 2],
    "sale_date": [date(2026, 11, 1), date(2026, 11, 1)],
    "product_id": ["P001", "P002"],
    "quantity": [2, 1],
    "unit_price": [1200, 2500]}
)
sales_config = bigquery.LoadJobConfig(
    schema=[
        bigquery.SchemaField("sale_id", "INTEGER", mode="REQUIRED"),
        bigquery.SchemaField("sale_date", "DATE", mode="REQUIRED"),
        bigquery.SchemaField("product_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("quantity", "INTEGER", mode="REQUIRED"),
        bigquery.SchemaField("unit_price", "INTEGER", mode="REQUIRED")
    ],
    write_disposition=bigquery.WriteDisposition.WRITE_EMPTY
)
# 初期ウォーターマーク
watermark_initial_df = pd.DataFrame({
    "pipeline_name": [
        "sales_incremental",
        "inventory_incremental"
    ],
    "watermark": [
        date(2026, 11, 1),
        date(2026, 11, 5)
    ]
})
watermark_config = bigquery.LoadJobConfig(
    schema=[
        bigquery.SchemaField("pipeline_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("watermark", "DATE", mode="REQUIRED")
    ],
    write_disposition=bigquery.WriteDisposition.WRITE_EMPTY
)
# 初期テーブル作成
client.load_table_from_dataframe(
    sales_initial_df,
    sales_table_id,
    job_config=sales_config
).result()
client.load_table_from_dataframe(
    watermark_initial_df,
    watermark_table_id,
    job_config=watermark_config
).result()
print("初期テーブルの作成が完了しました。")
print(f"売上テーブル: {sales_table_id}")
print(f"状態テーブル: {watermark_table_id}")

# テストケース
# テスト①：初回増分処理
# 初期ウォーターマークが 2026-11-01 の状態で実行します。
result = run_incremental_sales_pipeline(
    project_id="resonant-tract-508812-p9",
    dataset_id="sql_training",
    input_csv="sales_incremental.csv",
    pipeline_name="sales_incremental",
    log_file="sales_incremental_log"
)
print(result)
# 期待する結果：
# {
#     "pipeline_name": "sales_incremental",
#     "status": "SUCCESS",
#     "input_rows": 6,
#     "processed_rows": 4,
#     "old_watermark": "2026-11-01",
#     "new_watermark": "2026-11-03",
#     "executed_at": 実行日時
# }
# executed_at は実行日時なので、値は固定しません。
# BigQuery側では、売上テーブルが6行、状態テーブルの sales_incremental のウォーターマークが 2026-11-03 になることを確認します。
# inventory_incremental のウォーターマークは 2026-11-05 のままです。

# テスト②：同じデータで再実行
# 同じ関数をもう一度実行します。
result = run_incremental_sales_pipeline(
    project_id="resonant-tract-508812-p9",
    dataset_id="sql_training",
    input_csv="sales_incremental.csv",
    pipeline_name="sales_incremental",
    log_file="sales_incremental_log"
)
print(result)
# 期待する結果：
# {
#     "pipeline_name": "sales_incremental",
#     "status": "SKIPPED",
#     "input_rows": 6,
#     "processed_rows": 0,
#     "old_watermark": "2026-11-03",
#     "new_watermark": "2026-11-03",
#     "executed_at": 実行日時
# }
# BigQuery側の売上テーブルは6行のままであり、ウォーターマークも変わらないことを確認します。

with open("sales_incremental_log.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        print(json.loads(line))


### STEP 7-4｜最終総合演習
# STEP 7-1〜7-3では、CSVによるETL、BigQueryを使ったELT、ウォーターマークによる増分処理を実装してきました。
# 今回は、それらの知識を統合して、データ品質検証からBigQueryへの保存、結果検証、ログ記録までを行う売上データパイプラインを実装します。
#
# 今回は、ECサイトの売上明細と商品マスタを扱います。
# 2つのCSVを読み込み、データ品質を検証し、売上を集計したうえでBigQueryへ保存します。
# さらに、BigQueryに保存されたデータを再取得して結果を検証し、処理結果をJSONL形式で記録します。
#
#         sales_final.csv 売上明細    products_final.csv 商品マスタ
#                       └─────────┬─────────┘
#     Python・pandas 必須列・欠損・重複・結合関係の検証、商品マスタ結合・売上集計
#                                 ↓
#              BigQuery：sales_summary_final_step7 集計結果を保存
#                                 ↓
#      結果検証・JSONLログ 保存後の行数・売上合計を確認 SUCCESS / FAILED を記録

# 使用する知識
#   関数定義・引数・戻り値            処理全体の関数化
#   pd.read_csv()                 CSV読み込み
#   DataFrame.columns             必須列の確認
#   isna() / duplicated()         欠損・重複検証
#   pd.to_datetime()              売上日付の変換
#   pd.merge()                    商品マスタとの結合
#   validate="many_to_one"        結合関係の検証
#   groupby() / agg()             商品別売上集計
#   bigquery.Client()             BigQuery接続
#   load_table_from_dataframe()   集計結果の保存
#   WRITE_TRUNCATE                再実行時の結果置き換え
#   client.query()                保存結果の検証
#   json.dumps()                  JSONLログ
#   try / except / finally        例外処理・ログ記録
#   データ品質と保存結果の一貫性        パイプライン全体の品質保証

# 重要な技術・設計ポイント
# ① データ品質検証はBigQueryへの保存前に実施する
#   今回の処理では、入力データに問題がある場合、BigQueryへの保存を実行しません。
#   例えば、商品マスタに存在しない product_id が売上明細に含まれていた場合、結合後に一部の売上が欠落する可能性があります。
#   そのため、次の順番を守ります。
#     必須列・欠損・重複の検証 → 商品マスタとの結合・未一致の検証 → 売上集計 → BigQueryへ保存
#   今回は、必須列の欠落、指定列の欠損、主キー重複、商品マスタ未一致を検証対象とします。
#
# ② many_to_one による結合関係の検証
#   売上明細と商品マスタの関係は次のとおりです。
#     売上明細では、同じ product_id が複数行に出現してよい。
#     商品マスタでは、product_id は一意でなければならない。
#   したがって、結合では次の設定を使用します。
validate="many_to_one"
# また、how="left" と indicator=True を使用して、商品マスタに一致しなかった売上明細がないことを確認してください。
#
# ③ BigQueryへの保存は WRITE_TRUNCATE
#   今回はSTEP 7-3のような増分処理ではありません。
#   入力CSV全体を毎回処理し、最新の集計結果でBigQueryテーブルを置き換える方式です。
#   したがって、WRITE_TRUNCATE を使用します。
#   これにより、同じ入力データで正常に再実行しても、集計結果が二重に追加されることはありません。
#   なお、保存対象は今回の演習用テーブル sales_summary_final_step7 のみとします。
#
# ④ 保存後にBigQueryから再取得して検証する
#   pandasで正しく集計できたとしても、それだけで処理を完了としません。
#   BigQueryへのロード完了後、保存したテーブルをSQLで取得し、以下を確認します。
#     保存された集計結果の行数
#     保存された売上合計金額
#   これにより、Python側で計算した結果と、BigQueryに保存された結果が一致することを確認します。

# 演習用データ
# 今回使用するCSVは2つです。以下の内容で作成してください。
#   sales_final.csv
#   products_final.csv
sales_final_df = pd.DataFrame({
    "sale_id": [1, 2, 3, 4, 5, 6, 7, 8],
    "sale_date": ["2026-11-01", "2026-11-01", "2026-11-02", "2026-11-02", "2026-11-03", "2026-11-03", "2026-11-04", "2026-11-04"],
    "product_id": ["P001", "P002", "P001", "P003", "P002", "P003", "P004", "P001"],
    "quantity": [2, 1, 3, 2, 2, 4, 3, 1],
    "unit_price": [1200, 2500, 1200, 800, 2500, 800, 1500, 1200]
})
sales_final_df.to_csv("sales_final.csv", index=False)

products_final_df = pd.DataFrame({
    "product_id": ["P001", "P002", "P003", "P004"],
    "product_name": ["ノート", "バッグ", "ペン", "ボトル"],
    "category": ["文房具", "雑貨", "文房具", "生活用品"]
})
products_final_df.to_csv("products_final.csv", index=False)

# 期待する商品別集計結果
#   product_id	product_name	category	total_quantity	total_sales
#   P001	    ノート	        文房具	    6	            7,200
#   P002	    バッグ	        雑貨	        3	            7,500
#   P003	    ペン	            文房具	    6	            4,800
#   P004	    ボトル	        生活用品	    3	            4,500
#   合計			                            18	            24,000
# この集計結果をBigQueryに保存します。

# 実装課題
# 次の関数を実装してください。以下が必須の処理フローです。
# A. Extract：入力データの取得
#   sales_csv と products_csv をそれぞれpandasで読み込む。
#   読み込んだ行数をそれぞれ取得する。
#   sale_date を pd.to_datetime() で日付型に変換する。
#   BigQuery接続に必要な project_id と dataset_id を使用する。
#   今回の正常系データでは、sale_date はすべて日付として解釈できるものとします。
# B. Validate：データ品質検証
#   売上明細の必須列を検証する。
#     sale_id, sale_date, product_id, quantity, unit_price
#   商品マスタの必須列を検証する。
#     product_id, product_name, category
#   売上明細の必須列に欠損値がないことを確認する。
#   商品マスタの必須列に欠損値がないことを確認する。
#   売上明細の sale_id に重複がないことを確認する。
#   商品マスタの product_id に重複がないことを確認する。
#   証に失敗した場合は ValueError を発生させ、以降の加工・保存処理を行わない。
#   補足： 必須列が存在しない場合は、欠損検証や日付変換より前に検出してください。
#   したがって、実装時はAのCSV読み込み後、Bの必須列検証を行ってから sale_date を変換する順序で構いません。
# C. Transform：結合・集計
#   売上明細を左表、商品マスタを右表として product_id で結合する。
#   how="left"、validate="many_to_one"、indicator=True を指定する。
#   商品マスタに一致しない売上明細がある場合は ValueError を発生させる。
#   各売上明細について、次の売上金額を計算する。
#     sales_amount = quantity * unit_price
#   product_id、product_name、category ごとに集計する。
#   quantity の合計を total_quantity、sales_amount の合計を total_sales とする。
#   集計結果を product_id の昇順に並べる。
#   BigQueryに保存するDataFrameの列を次の5列に揃える。
#     product_id, product_name, category, total_quantity, total_sales
# D. Load：BigQueryへの保存
#   bigquery.Client(project=project_id) で接続する。
#   次のテーブルIDを作成する。
#     f"{project_id}.{dataset_id}.sales_summary_final_step7"
#   集計結果を load_table_from_dataframe() で保存する。
#   書き込み方式には WRITE_TRUNCATE を使用する。
#   .result() でロードジョブの完了を待つ。
# E. Verify：保存結果の検証
#   BigQueryの保存先テーブルからSQLで全行を取得する。
#   to_dataframe(create_bqstorage_client=False) でpandasのDataFrameに変換する。
#   BigQueryから取得した行数が、Pythonで作成した集計結果の行数と一致することを検証する。
#   BigQueryから取得した total_sales の合計が、Pythonで計算した売上合計と一致することを検証する。
#   不一致があれば ValueError を発生させる。
#   関数内部の検証値を固定するのではなく、実際に処理したデータから計算した値との一致を検証する。
# F. Logging：JSONLログ
#   実行結果を log_file にJSONL形式で追記する。
#   ログには以下の情報を記録する。
#   {
#     "status": "SUCCESS",
#     "input_rows": {
#         "sales": 8,
#         "products": 4
#         },
#     "output_rows": 4,
#     "total_sales": 24000,
#     "executed_at": "実行日時",
#     "error": null
#   }
#   executed_at には実行開始日時をISO形式の文字列で記録する。
#   エラー発生時は status を "FAILED" とし、error にエラー内容を記録する。
#   正常時・異常時のいずれも、ログを1行追記する。
#   log_file は拡張子を含むファイルパスとして渡すものとします。関数内で .jsonl を追加する必要はありません。
# G. Return・Exception：戻り値と例外処理
#   正常終了時は、ログと同じ内容の辞書を返す。
#   エラー発生時はログを記録したうえで例外を再送出する。
#   FAILED 時は output_rows を 0、total_sales を 0 として記録する。
#   これは処理全体が成功しなかったことを表すログ上の値であり、BigQueryに一切書き込まれていないことを保証するものではありません。

from google.cloud import bigquery
import pandas as pd
from pandas.errors import MergeError
import logging
import json
from datetime import datetime

def run_final_sales_pipeline(project_id, dataset_id, sales_csv, products_csv, log_file):
    # ログ用初期値
    status = None
    input_rows_sales = 0
    input_rows_products = 0
    output_rows = 0
    total_sales = 0
    executed_at = datetime.now().isoformat()
    error = None

    try:
        # CSV読み
        sales_df = pd.read_csv(sales_csv)
        products_df = pd.read_csv(products_csv)
        input_rows_sales += sales_df.shape[0]
        input_rows_products += products_df.shape[0]

        # 売上明細・商品マスタの必須列検証
        required_sales_columns = ["sale_id", "sale_date", "product_id", "quantity", "unit_price"]
        required_products_columns = ["product_id", "product_name", "category"]
        shortage_sales_column = [rs_col for rs_col in required_sales_columns if rs_col not in sales_df.columns]
        shortage_products_column = [rp_col for rp_col in required_products_columns if rp_col not in products_df.columns]
        if shortage_sales_column:
            raise ValueError(f"{sales_csv} の必須列不足: {shortage_sales_column}")
        elif shortage_products_column:
            raise ValueError(f"{products_csv} の必須列不足: {shortage_products_column}")

        # 売上明細・商品マスタの必須列における欠損値検証
        if sales_df[required_sales_columns].isna().any().any():  # 全体で「1つでもTrueがあるか」判定（最終的に1つの True/False）
            raise ValueError(f"{sales_csv} の必須列に欠損値")
        elif products_df[required_products_columns].isna().any().any():
            raise ValueError(f"{products_csv} の必須列に欠損値")

        # 売上明細のsale_id・商品マスタのproduct_idにおける重複検証
        if sales_df.duplicated(subset=["sale_id"], keep=False).any():
            raise ValueError(f"sale_id 重複")
        elif products_df.duplicated(subset=["product_id"], keep=False).any():
            raise ValueError(f"product_id 重複")

        # sale_date を pd.to_datetime() で日付型に変換
        sales_df["sale_date"] = pd.to_datetime(sales_df["sale_date"])

        # 売上明細・商品マスタの結合
        try:
            join_table = sales_df.merge(
                products_df,
                on="product_id",
                how="left",
                validate="many_to_one",
                indicator=True,
            )
        except MergeError as me:
            raise ValueError(me) from me

        # 商品マスタに一致しない売上明細があるか検証
        not_match_row = join_table[
            join_table["_merge"] == "left_only"
            ]
        if not not_match_row.empty:
            raise ValueError(f"商品マスタに一致しない売上明細: {not_match_row}")

        # 売上金額計算
        join_table["sales_amount"] = join_table["quantity"] * join_table["unit_price"]

        # product_id、product_name、category ごとに集計・並び替え
        agg_sales = join_table.groupby(
            ["product_id", "product_name", "category"],
            as_index=False,
        ).agg(
            total_quantity=("quantity", "sum"),
            total_sales=("sales_amount", "sum")
        )
        agg_sales = agg_sales.sort_values("product_id", ascending=True)
        agg_sales = agg_sales.reset_index(drop=True)

        # BigQuery接続・集計結果の保存用BigQueryテーブルID作成
        client = bigquery.Client(project=project_id)
        sales_summary_final_step7_id = f"{project_id}.{dataset_id}.sales_summary_final_step7"

        # 集計結果を load_table_from_dataframe() でBigQueryのテーブルにWRITE_TRUNCATEで保存
        load_truncate_job_config = bigquery.LoadJobConfig(
            schema=[
                bigquery.SchemaField("product_id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("product_name", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("category", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("total_quantity", "INTEGER", mode="REQUIRED"),
                bigquery.SchemaField("total_sales", "INTEGER", mode="REQUIRED"),
            ],
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE
        )
        load_truncate_job = client.load_table_from_dataframe(
            agg_sales,
            sales_summary_final_step7_id,
            job_config=load_truncate_job_config
        )
        load_truncate_job.result()

        # BigQueryの保存先テーブルからSQLで全行取得・DataFrame変換
        verify_query_job = client.query(
            f"""
            SELECT
              *
            FROM `{sales_summary_final_step7_id}`;
            """
        )
        verify_df = verify_query_job.result().to_dataframe(
            create_bqstorage_client=False
        )

        # 保存結果の検証
        if verify_df.shape[0] != agg_sales.shape[0]:
            raise ValueError("保存結果の行数不一致")
        elif verify_df["total_sales"].sum().item() != agg_sales["total_sales"].sum().item():
            raise ValueError("保存結果の金額不一致")

        # 正常時ログ記載用
        status = "SUCCESS"
        output_rows += agg_sales.shape[0]
        total_sales += agg_sales["total_sales"].sum().item()

    except Exception as e:
        logging.error(e)
        status = "FAILED"
        error = str(e)
        raise

    finally:
        log = {
            "status": status,
            "input_rows": {
                "sales": input_rows_sales,
                "products": input_rows_products
            },
            "output_rows": output_rows,
            "total_sales": total_sales,
            "executed_at": executed_at,
            "error": error
        }
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log, ensure_ascii=False) + "\n")

    return log

# テストケース
# テスト①：正常系
# 指定した2つのCSVを使用して関数を実行します。
# 呼び出し例：
result = run_final_sales_pipeline(
    project_id="resonant-tract-508812-p9",
    dataset_id="sql_training",
    sales_csv="sales_final.csv",
    products_csv="products_final.csv",
    log_file="sales_final_log.jsonl"
)
print(result)
# 期待する戻り値：
# {
#     "status": "SUCCESS",
#     "input_rows": {
#         "sales": 8,
#         "products": 4
#     },
#     "output_rows": 4,
#     "total_sales": 24000,
#     "executed_at": "実行日時",
#     "error": None
# }
# BigQuery側では、sales_summary_final_step7 に4行が保存されていることを確認します。
# また、同じ正常系データで再実行した場合も、WRITE_TRUNCATE により結果が4行のままになる設計です。
# 再実行の実測は今回の必須テストには含めません。

# テスト②：異常系（商品マスタ未一致）
# テスト①の正常終了後、売上CSVの8行目にある P004 を P999 に変更した別のCSVを用意します。
# 変更後の該当行：
# 7, 2026-11-04, P999, 3, 1500
# それ以外の行は変更しません。
# このCSVを入力して関数を実行します。
# 期待する結果は次のとおりです。異常系で例外が発生すること自体が期待結果です。
#   商品マスタに存在しない P999 が検出される。
#   ValueError が発生する。
#   JSONLログに FAILED が追記される。
#   BigQueryへの保存処理は実行されない。
#   テスト①で保存された4行の集計結果が維持される。
sales_df = pd.read_csv("sales_final.csv")
sales_final_invalid = sales_df.copy()
sales_final_invalid.loc[
    sales_final_invalid["sale_id"] == 7, "product_id"
] = "P999"
sales_final_invalid.to_csv("sales_final_invalid.csv", index=False)

result = run_final_sales_pipeline(
    project_id="resonant-tract-508812-p9",
    dataset_id="sql_training",
    sales_csv="sales_final_invalid.csv",
    products_csv="products_final.csv",
    log_file="sales_final_log.jsonl"
)
print(result)

with open("sales_final_log.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        print(json.loads(line))






