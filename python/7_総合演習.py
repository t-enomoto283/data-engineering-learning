
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
            raise ValueError(me)

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
























































































