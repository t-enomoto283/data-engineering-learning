
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











































































































































