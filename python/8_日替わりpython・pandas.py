from logging import exception

### 日替わりPython・pandas｜データ品質検証と検証結果の辞書化
# ETLパイプラインにおいて、取得したデータを後続処理に渡す前に、必須カラムの存在、主キーの欠損、主キーの重複を検証することがあります。
# 今回は、任意のDataFrameに対してこれらの検証を行い、検証結果を辞書形式で返す汎用的な関数を実装。
# BigQueryへの接続やCSVファイルの読み書きは不要。
#
#   関連技術          用途
#   df.columns	    カラムの存在確認
#   len()	        レコード件数の取得
#   isna()	        欠損値の検出
#   dropna()	    欠損値の除外
#   duplicated()	重複レコードの検出
#   sum()	        真偽値を利用した件数集計
#   辞書・条件分岐	    検証結果の管理

# 使用するデータ
# 以下のコードをテスト用のDataFrameとする。
import pandas as pd
df_ok = pd.DataFrame({
    "order_id": [101, 102, 103, 104],
    "customer_id": [1, 2, 1, 3],
    "amount": [3000, 5000, 2000, 4000]
})
df_error = pd.DataFrame({
    "order_id": [101, 102, 102, None],
    "customer_id": [1, 2, 2, 3]
})
# df_error には、必須カラムの不足・主キーの欠損・主キーの重複という3種類の品質上の問題が存在します。
#
# 実装要件
# A. 関数の定義
#   以下の関数を定義してください。
#   def validate_data(df, required_columns, key):
#   引数の仕様は以下のとおりです。
#     df                  検証対象のDataFrame
#     required_columns    必須カラム名のリスト
#     key	              主キーとして検証するカラム名（文字列）
# B. 検証結果を格納する辞書の初期化
#   関数内で、以下の辞書を初期化してください。
result = {
    "status": "OK",
    "row_count": 0,
    "missing_columns": [],
    "null_key_count": 0,
    "duplicate_key_count": 0
}
#   各項目には、後述する検証結果を格納します。
# C. レコード件数の取得
#   DataFrameの全レコード件数を取得し、row_count に格納してください。
# D. 必須カラムの存在検証
#   required_columns に指定されたカラムのうち、DataFrameに存在しないカラム名を取得してください。
#   存在しないカラム名は、missing_columns にリスト形式で格納します。
#   必須カラムが不足していても、主キーカラムが存在する場合は後続の検証を継続してください。
# E. 主キーの欠損・重複検証
#   key に指定されたカラムについて、以下の検証を行ってください。
#     検証項目                        格納先
#     主キーが欠損しているレコード件数     null_key_count
#     主キーが重複している余剰レコード件数	 duplicate_key_count
#   重複件数は、最初に出現したレコードを除いた余剰レコードの件数とします。
#   例えば、主キーが [101, 102, 102, 102] の場合、重複件数は 2 です。
#   なお、欠損値は重複検証の対象外としてください。
#   key に指定されたカラム自体が存在しない場合は、欠損・重複検証を行わず、両項目に None を格納してください。
# F. ステータスの判定と戻り値
#   以下のいずれかに該当する場合は、status を "ERROR" に変更してください。
#     必須カラムが不足している。
#     主キーカラムが存在しない。
#     主キーに欠損が存在する。
#     主キーに重複が存在する。
#   いずれにも該当しない場合は "OK" のままとします。
#   最後に、result を戻り値として返してください。

def validate_data(df, required_columns, key):
    result = {
        "status": "OK",
        "row_count": 0,
        "missing_columns": [],
        "null_key_count": 0,
        "duplicate_key_count": 0
    }
    try:
        # DataFrameの全レコード件数取得
        result["row_count"] = len(df)
        # 必須カラムの存在検証
        result["missing_columns"].extend([rc for rc in required_columns if rc not in df.columns])
        # 必須カラムが不足していても主キーカラムが存在する場合の後続検証
        if key in df.columns:
            # 主キーの欠損検証
            result["null_key_count"] = df[key].isna().sum().item()
            # 主キーの重複検証（欠損値を重複検証の対象外とした主キーの余剰レコード数）
            valid_key = df.dropna(subset=[key])
            result["duplicate_key_count"] = valid_key.duplicated(subset=[key], keep="first").sum().item()
        else:
            result["null_key_count"] = None
            result["duplicate_key_count"] = None

    except Exception as e:
        raise e

    finally:
        # ステータス判定
        error_judge = (
            len(result["missing_columns"]) != 0
            or result["null_key_count"] != 0
            or result["duplicate_key_count"] != 0
        )
        if error_judge:
            result["status"] = "ERROR"

    return result

# テスト実行
# テスト①：正常データ
print(validate_data(
    df=df_ok,
    required_columns=["order_id", "customer_id", "amount"],
    key="order_id"
))
# 期待される結果：
# {
#     "status": "OK",
#     "row_count": 4,
#     "missing_columns": [],
#     "null_key_count": 0,
#     "duplicate_key_count": 0
# }

# テスト②：異常データ
print(validate_data(
    df=df_error,
    required_columns=["order_id", "customer_id", "amount"],
    key="order_id"
))
# 期待される結果：
# {
#     "status": "ERROR",
#     "row_count": 4,
#     "missing_columns": ["amount"],
#     "null_key_count": 1,
#     "duplicate_key_count": 1
# }

# テスト③：異常データ（主キーの欠損）
df_error2 = pd.DataFrame({
    "order_id": [101, 102, 102, None, None],
    "customer_id": [1, 2, 2, 3, 4],
    "amount": [3000, 5000, 5000, 2000, 4000]
})
print(validate_data(
    df=df_error2,
    required_columns=["order_id", "customer_id", "amount"],
    key="order_id"
))


### 日替わりPython・pandas｜マスタデータとの結合と売上集計
# ECサイトの売上明細データと商品マスタを結合し、商品カテゴリ別の売上集計データを作成する関数を実装してください。
# 実務では、トランザクションデータにマスタ情報を付与したうえで、分析用データを作成する処理が頻繁に発生します。
# 今回は、結合時のレコード増加防止と、マスタに存在しないデータの取り扱いも考慮します。
#
#   関連技術          用途
#   merge()         DataFrameの結合
#   validate        結合関係の検証
#   fillna()        欠損値の補完
#   groupby()       カテゴリ単位のグループ化
#   agg()           複数の集計処理
#   nunique()       ユニーク件数の取得
#   sort_values()   複数カラムによる並び替え
#   reset_index()   インデックスの振り直し
#
# 使用するデータ
# 以下のコードを実行して、テストデータを準備してください。
import pandas as pd
df_sales = pd.DataFrame({
    "order_id": [101, 102, 103, 104, 105, 106],
    "product_id": [1, 2, 1, 3, 4, 5],
    "quantity": [2, 1, 3, 2, 1, 2],
    "unit_price": [1000, 3000, 1000, 2000, 5000, 1500]
})
df_products = pd.DataFrame({
    "product_id": [1, 2, 3, 4],
    "category": ["Food", "Electronics", "Food", "Clothing"]
})
# 売上明細には、商品マスタに登録されていない product_id = 5 が存在します。
#
# 実装要件
# A. 関数の定義
#   以下の関数を定義してください。
#     def summarize_sales(df_sales, df_products):
#     df_sales     売上明細のDataFrame
#     df_products	 商品マスタのDataFrame
#   戻り値は、カテゴリ別に集計されたDataFrameとします。
#   なお、引数として渡された元のDataFrameは変更しないでください。
# B. 売上明細と商品マスタの結合
#   product_id を結合キーとして、売上明細に商品カテゴリを付与してください。
#   結合条件は以下のとおりです。
#     売上明細の全レコードを保持する。
#     商品マスタ側の結合キーは一意であることを保証する。
#     商品マスタ側に結合キーの重複が存在する場合は、例外を発生させる。
#     結合関係の検証には、既習の merge() の validate 引数を使用してください。
# C. 欠損値の補完と売上金額の算出
#   結合後のDataFrameに対して、以下の加工を行ってください。
#     加工対象        処理内容
#     category      欠損値を "Unknown" に置換する
#     sales_amount  quantity * unit_price で算出し、新規カラムとして追加する
#   商品マスタに存在しない商品の売上も、集計対象から除外しないでください。
# D. カテゴリ別の集計
#   category ごとに、以下の項目を集計してください。
#     出力カラム        集計内容
#     category        商品カテゴリ
#     order_count     注文IDのユニーク件数
#     total_quantity  販売数量の合計
#     total_sales     売上金額の合計
#   order_count は単純なレコード件数ではなく、注文IDのユニーク件数とします。
# E. 並び替えと戻り値
#   集計後のDataFrameを以下の仕様に整えてください。
#     total_sales の降順で並び替える。
#     売上金額が同じ場合は category の昇順で並び替える。
#     インデックスを0から振り直す。
#     集計後のDataFrameを戻り値として返す

from pandas.errors import MergeError

def summarize_sales(df_sales, df_products):
    try:
        joined = pd.merge(
            df_sales,
            df_products,
            on="product_id",
            how="left",
            validate="many_to_one"
        )
    except MergeError as me:
        print(me)
        raise

    joined["category"] = joined["category"].fillna("Unknown")
    joined["sales_amount"] = joined["quantity"] * joined["unit_price"]

    agg_joined = joined.groupby(
        "category",
        as_index=False
    ).agg(
        order_count=("order_id", "nunique"),
        total_quantity=("quantity", "sum"),
        total_sales=("sales_amount", "sum")
    )
    agg_joined = agg_joined.sort_values(
        by=["total_sales", "category"],
        ascending=[False, True]
    )
    agg_joined = agg_joined.reset_index(drop=True)

    return agg_joined

# テスト実行
# テスト①：正常な商品マスタ
print(summarize_sales(
    df_sales=df_sales,
    df_products=df_products
))
# 期待される結果：
# index	category	order_count	total_quantity	total_sales
# 0	    Food	    3	        7	            9000
# 1	    Clothing	1	        1	            5000
# 2	    Electronics	1	        1	            3000
# 3	    Unknown	    1	        2	            3000
# 商品マスタに存在しない商品についても、Unknown として売上が集計されていることを確認してください。

# テスト②：結合キーが重複している商品マスタ
# 以下の異常データを準備してください。
df_products_error = pd.DataFrame({
    "product_id": [1, 2, 3, 4, 1],
    "category": ["Food", "Electronics", "Food", "Clothing", "Other"]
})
print(summarize_sales(
    df_sales=df_sales,
    df_products=df_products_error
))
# 期待される結果：
# pandas.errors.MergeError
# 商品マスタ側の結合キーが重複しているため、結合関係の検証によって例外が発生すれば正解です。
# 例外メッセージの全文は、pandasのバージョンによって異なっても構いません。


### 日替わりPython・pandas｜ウォーターマークによる差分データの抽出と更新候補の算出
# 売上データと前回処理時点のウォーターマークを受け取り、新たに処理すべき売上データを抽出する関数を実装してください。
# また、差分データから次回のウォーターマークとなる候補値を算出してください。
# 今回は、実際にBigQueryへ接続するのではなく、既存の差分処理パイプラインを構成する個別処理の復習とします。
#
#   関連技術	        用途
#   pd.Timestamp()	日時型の値の取り扱い
#   ブールインデックス	条件に合致するレコードの抽出
#   .copy()	        元データから独立したDataFrameの作成
#   .empty	        空のDataFrameの判定
#   .max()	        最大日時の取得
#   len()	        レコード件数の取得
#   辞書	            複数の処理結果の管理
#
# 使用するデータ
# 以下のコードをテストデータとしてください。
import pandas as pd
df_sales = pd.DataFrame({
    "order_id": [101, 102, 103, 104, 105, 106],
    "amount": [3000, 5000, 2000, 4000, 7000, 6000],
    "updated_at": pd.to_datetime([
        "2026-11-20 09:00:00",
        "2026-11-21 10:00:00",
        "2026-11-22 12:00:00",
        "2026-11-23 09:00:00",
        "2026-11-24 10:00:00",
        "2026-11-25 08:00:00"
    ])
})
watermark = pd.Timestamp("2026-11-22 12:00:00")

# 実装要件
# A. 関数の定義
#   以下の関数を定義してください。
#     def extract_increment(df_sales, watermark):
#     引数        内容
#     df_sales   売上データのDataFrame
#     watermark  現在のウォーターマーク（Timestamp型）
#   引数として渡された元のDataFrameは変更しないでください。
# B. 差分データの抽出
#   updated_at が現在のウォーターマークより新しいレコードのみを抽出してください。
#   抽出条件は以下のとおりです。
#     updated_at > watermark
#   ウォーターマークと同一日時のレコードは処理済みとみなし、抽出対象に含めないでください。
#   抽出したDataFrameは、updated_at の昇順に並び替え、インデックスを0から振り直してください。
# C. 次回のウォーターマーク候補の算出
#   差分データの有無によって、以下の処理を行ってください。
#     条件                 ウォーターマーク候補
#     差分データが存在する    差分データの updated_at の最大値
#     差分データが存在しない  引数で受け取った現在のウォーターマーク
#   ウォーターマーク候補はTimestamp型のままとしてください。
# D. 戻り値の作成
#   以下の構造を持つ辞書を戻り値としてください。
# {
#     "increment_data": ...,
#     "row_count": ...,
#     "next_watermark": ...
# }
#   キー	             格納する値	            型
#   increment_data	抽出した差分データ	        DataFrame
#   row_count       差分データの件数	        int
#   next_watermark	次回のウォーターマーク候補	Timestamp
#   差分データが存在しない場合も、increment_data には元のカラム構成を維持した空のDataFrameを格納してください。

def extract_increment(df_sales, watermark):
    incremental_df = df_sales[
        df_sales["updated_at"] > watermark
        ].copy()
    incremental_df = incremental_df.sort_values(by="updated_at", ascending=True)
    incremental_df = incremental_df.reset_index(drop=True)

    if not incremental_df.empty:
        new_watermark = incremental_df["updated_at"].max()
    else:
        new_watermark = watermark

    return {
        "increment_data": incremental_df,
        "row_count": len(incremental_df),
        "next_watermark": new_watermark
    }

# テスト実行
# テスト①：差分データが存在する場合
result = extract_increment(
    df_sales=df_sales,
    watermark=watermark
)
print(result["increment_data"])
print(result["row_count"])
print(result["next_watermark"])
# 期待される結果：
#   index	order_id	amount	updated_at
#   0	    104	        4000	2026-11-23 09:00:00
#   1	    105	        7000	2026-11-24 10:00:00
#   2	    106	        6000	2026-11-25 08:00:00
#
#   3
#   2026-11-25 08:00:00

# テスト②：差分データが存在しない場合
# テスト①で算出されたウォーターマーク候補を使用して、同じ売上データに対して再度関数を実行してください。
result2 = extract_increment(
    df_sales=df_sales,
    watermark=result["next_watermark"]
)
print(result2["increment_data"])
print(result2["row_count"])
print(result2["next_watermark"])
# 期待される結果：
#   Empty DataFrame
#   Columns: [order_id, amount, updated_at]
#   Index: []
#
#   0
#   2026-11-25 08:00:00
# 差分データが存在しない場合に、ウォーターマーク候補が None や NaT にならないことを確認してください。


### 日替わりPython・pandas｜増分データのBigQueryへの格納とウォーターマークの更新
# BigQuery上の状態管理テーブルからウォーターマークを取得し、売上データの増分抽出・格納・ウォーターマークの更新を行うパイプラインを実装。
# 今回はSTEP7で作成した既存のBigQueryテーブルを使用します。
#
# 使用データ
# 売上データ
import pandas as pd
df_sales = pd.DataFrame({
    "sale_id": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    "sale_date": pd.to_datetime([
        "2026-11-01",
        "2026-11-01",
        "2026-11-02",
        "2026-11-02",
        "2026-11-03",
        "2026-11-03",
        "2026-11-04",
        "2026-11-04",
        "2026-11-05",
        "2026-11-06"
    ]).date,
    "product_id": ["P001", "P002", "P001", "P003", "P002", "P003", "P001", "P002", "P003", "P001"],
    "quantity": [2, 1, 3, 2, 2, 4, 2, 3, 1, 5],
    "unit_price": [1200, 2500, 1200, 800, 2500, 800, 1200, 2500, 800, 1200]
})
# BigQuery：状態管理テーブル
state_table_id = "resonant-tract-508812-p9.sql_training.pipeline_watermarks_step7"
# 現在の状態：
#   pipeline_name	        watermark
#   inventory_incremental	2026-11-05
#   sales_incremental	    2026-11-03
# BigQuery：増分売上テーブル
sales_table_id = "resonant-tract-508812-p9.sql_training.sales_incremental_step7"
# 現在の状態：
#   sale_id	sale_date	product_id	quantity	unit_price
#   1	    2026-11-01	P001	    2	        1200
#   2	    2026-11-01	P002    	1	        2500
#   3	    2026-11-02	P001	    3	        1200
#   4	    2026-11-02	P003	    2	        800
#   5	    2026-11-03	P002	    2	        2500
#   6	    2026-11-03	P003	    4	        800

# 作成する関数
# def run_incremental_pipeline(df_sales, pipeline_name, state_table_id, sales_table_id):
#   df_sales	    処理対象の売上DataFrame
#   pipeline_name	対象パイプライン名
#   state_table_id	状態管理テーブルの完全修飾名
#   sales_table_id	増分売上テーブルの完全修飾名

# 実装仕様
# A. ウォーターマークの取得・増分データの抽出
#   BigQuery上の状態管理テーブルをDataFrameとして取得する。
#   pipeline_name に該当するウォーターマークを取得する。
#   対象のパイプラインが存在しない場合はエラーとする。
#   sale_date > watermark を満たすデータを抽出する。
#   sale_date の昇順に並べ替え、インデックスを振り直す。
#   増分データの件数を取得する。
#   増分データの sale_date の最大値を次回のウォーターマーク候補とする。
#   増分データが0件の場合は、仕様B・Cを実行せず、正常終了とする。
# B. 増分データの格納
#   仕様Aで抽出した増分データをBigQuery上の増分売上テーブルに格納する。
#   書き込み方式は WRITE_APPEND とする。
#   既存の売上データは保持する。
#   ロードジョブの正常完了を確認する。
#   格納処理でエラーが発生した場合は、仕様Cを実行せずに異常終了とする。
# C. ウォーターマークの更新
#   仕様Bが正常に完了した場合のみ実行する。
#   仕様Aで取得した状態管理DataFrameを使用する。
#   対象の pipeline_name に該当するウォーターマークのみを更新する。
#   その他のパイプラインのウォーターマークは変更しない。
#   状態管理DataFrame全体を WRITE_TRUNCATE でBigQueryに格納する。
#   ロードジョブの正常完了を確認する。
#   更新処理でエラーが発生した場合は異常終了とする。
#
# 戻り値
# 以下の形式で辞書を返してください。
# {
#     "status": "OK",
#     "row_count": 4,
#     "previous_watermark": ...,
#     "next_watermark": ...
# }
#   キー	内容
#   status	            OK または ERROR
#   row_count	        抽出した増分データの件数
#   previous_watermark	処理開始時のウォーターマーク
#   next_watermark	    正常終了後のウォーターマーク
# 増分データが0件の場合、next_watermark は現在のウォーターマークと同じ値とします。
# 異常終了の場合、status は ERROR、next_watermark は None とします。
# ウォーターマーク取得前にエラーが発生した場合は、previous_watermark を None、件数取得前であれば row_count を 0 としてください。

import pandas as pd
from google.cloud import bigquery
from google.cloud.exceptions import GoogleCloudError

def run_incremental_pipeline(df_sales, pipeline_name, state_table_id, sales_table_id):
    row_count = 0
    previous_watermark = None
    try:
        client = bigquery.Client(
            project="resonant-tract-508812-p9"
        )
        watermark_query_job = client.query(
            f"""
            SELECT
              pipeline_name,
              watermark
            FROM `{state_table_id}`
            """
        )
        watermark_df = watermark_query_job.result().to_dataframe(
            create_bqstorage_client=False
        )
        watermark_df["watermark"] = pd.to_datetime(watermark_df["watermark"]).dt.date
        pipeline_name_watermark = watermark_df[
            watermark_df["pipeline_name"] == pipeline_name
            ]
        if pipeline_name_watermark.empty:
            raise ValueError(f"指定されたパイプライン '{pipeline_name}' は存在しません。")
        else:
            pipeline_name_watermark = pipeline_name_watermark.iloc[0]
            previous_watermark = pipeline_name_watermark["watermark"]

        incremental_df = df_sales[
            df_sales["sale_date"] > pipeline_name_watermark["watermark"]
        ].copy()
        if len(incremental_df) == 0:
            return {
                "status": "OK",
                "row_count": 0,
                "previous_watermark": pipeline_name_watermark["watermark"],
                "next_watermark": pipeline_name_watermark["watermark"]
            }
        else:
            incremental_df = incremental_df.sort_values(
                by="sale_date",
                ascending=True
            )
            incremental_df = incremental_df.reset_index(drop=True)
            new_watermark = incremental_df["sale_date"].max()
            row_count = incremental_df.shape[0]

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
            sales_table_id,
            job_config=load_append_job_config
        )
        load_append_job.result()

        watermark_df.loc[
            watermark_df["pipeline_name"] == pipeline_name, "watermark"
        ] = new_watermark

        load_truncate_job_config = bigquery.LoadJobConfig(
            schema=[
                bigquery.SchemaField("pipeline_name", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("watermark", "DATE", mode="REQUIRED")
            ],
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE
        )
        load_truncate_job = client.load_table_from_dataframe(
            watermark_df,
            state_table_id,
            job_config=load_truncate_job_config
        )
        load_truncate_job.result()

        return {
            "status": "OK",
            "row_count": row_count,
            "previous_watermark": previous_watermark,
            "next_watermark": new_watermark
        }

    except (ValueError, GoogleCloudError):
        return {
            "status": "ERROR",
            "row_count": row_count,
            "previous_watermark": previous_watermark,
            "next_watermark": None
        }

# 実行・期待結果
# ケース①：増分データが存在する場合
result = run_incremental_pipeline(
    df_sales,
    "sales_incremental",
    "resonant-tract-508812-p9.sql_training.pipeline_watermarks_step7",
    "resonant-tract-508812-p9.sql_training.sales_incremental_step7"
)
print(result)
# 期待される増分データ：
#   sale_id	sale_date	product_id	quantity	unit_price
#   7	2026-11-04	P001	2	1200
#   8	2026-11-04	P002	3	2500
#   9	2026-11-05	P003	1	800
#   10	2026-11-06	P001	5	1200
# 期待される戻り値：
# {
#     "status": "OK",
#     "row_count": 4,
#     "previous_watermark": datetime.date(2026, 11, 3),
#     "next_watermark": datetime.date(2026, 11, 6)
# }
# 期待される状態管理テーブル：
#   pipeline_name	        watermark
#   inventory_incremental	2026-11-05
#   sales_incremental	    2026-11-06

# ケース②：増分データが存在しない場合
# ケース①の正常終了後、同じ引数で再度関数を実行してください。
result2 = run_incremental_pipeline(
    df_sales,
    "sales_incremental",
    "resonant-tract-508812-p9.sql_training.pipeline_watermarks_step7",
    "resonant-tract-508812-p9.sql_training.sales_incremental_step7"
)
print(result2)
# 期待される戻り値：
# {
#     "status": "OK",
#     "row_count": 0,
#     "previous_watermark": datetime.date(2026, 11, 6),
#     "next_watermark": datetime.date(2026, 11, 6)
# }
# 期待される動作：
#   増分売上テーブルへの書き込みなし。
#   状態管理テーブルへの書き込みなし。
#   増分売上テーブルの総件数は10件のまま。


### 日替わりPython・pandas｜増分データの品質検証とBigQueryへの格納制御
# 前問では、ウォーターマークを利用した増分データの抽出・格納・状態更新を実装しました。
# 今回は、増分データに不正なレコードが含まれている場合に、BigQueryへの格納およびウォーターマークの更新を行わないパイプラインを実装。
#
# 使用データ
import pandas as pd
df_sales = pd.DataFrame({
    "sale_id": [11, 12, 13, 14, 15],
    "sale_date": pd.to_datetime(["2026-11-07", "2026-11-07", "2026-11-08", "2026-11-08", "2026-11-09"]).date,
    "product_id": ["P001", "P002", None, "P003", "P001"],
    "quantity": [2, 3, 1, -2, 4],
    "unit_price": [1200, 2500, 800, 800, 1200]
})
# 既存テーブルの状態
# pipeline_watermarks_step7
#   pipeline_name	        watermark
#   inventory_incremental	2026-11-05
#   sales_incremental	    2026-11-06
#
# sales_incremental_step7
# 前問で格納した sale_id が1～10のデータが存在している状態です。

# 実装要件
# 以下の関数を作成してください。
# def run_validated_incremental_pipeline(df_sales, pipeline_name, state_table_id, sales_table_id):
#
# A. ウォーターマークの取得・増分データの抽出
#   BigQueryから状態管理テーブルを取得する。
#   指定された pipeline_name のウォーターマークを取得する。
#   指定されたパイプラインが存在しない場合は異常終了とする。
#   ウォーターマークより後の日付のデータを抽出する。
#   sale_date の昇順でソートし、インデックスを振り直す。
#   増分データの件数を取得する。
#   増分データが0件の場合は、B・Cの処理を行わず正常終了とする。
# B. 増分データの品質検証
#   Aで抽出した増分データに対して、以下の検証を行ってください。
#     検証対象      正常条件
#     sale_id     欠損がなく、増分データ内で重複していない
#     sale_date   欠損がない
#     product_id  欠損がない
#     quantity    欠損がなく、0より大きい
#     unit_price  欠損がなく、0以上である
#   いずれかの正常条件を満たさないレコードを不正レコードとします。
#   不正レコードの件数を取得する。
#   同一レコードが複数の正常条件に違反していても、1件としてカウントする。
#   不正レコードが1件以上存在する場合は異常終了とする。
#   異常終了時には、BigQueryへの増分データの格納およびウォーターマークの更新を行わない。
#   不正レコードが0件の場合のみ、Cの処理へ進む。
#   なお、今回の重複検証は増分データ内を対象とし、既存のBigQueryテーブルとの重複検証は対象外とします。
#   また、sale_date の欠損によって増分抽出の対象外となったレコードについても、今回は検証対象外とします。
# C. 増分データの格納・ウォーターマークの更新
#   増分データの sale_date の最大値を更新候補として取得する。
#   WRITE_APPEND によって増分データを格納する。
#   ロードジョブの正常完了を確認する。
#   増分データの格納が成功した場合のみ、対象パイプラインのウォーターマークを更新する。
#   対象外のパイプラインのウォーターマークは変更しない。
#   WRITE_TRUNCATE によって状態管理テーブルを更新する。
#   ロードジョブの正常完了を確認する。
# 戻り値
# 以下の形式で辞書を返してください。
# {
#     "status": ...,
#     "row_count": ...,
#     "invalid_count": ...,
#     "previous_watermark": ...,
#     "next_watermark": ...
# }
#   キー	内容
#   status	            正常終了時は OK、異常終了時は ERROR
#   row_count	        抽出した増分データの件数
#   invalid_count	    不正レコードの件数
#   previous_watermark	更新前のウォーターマーク
#   next_watermark      正常終了後のウォーターマーク
# 異常終了時の next_watermark は None としてください。
# 件数や更新前のウォーターマークについては、異常終了までに取得できた値を返してください。未取得の場合は、件数を 0、日付を None とします。
# 日付の戻り値は前問と同様に datetime.date 型とします。

import pandas as pd
from google.cloud import bigquery
from google.cloud.exceptions import GoogleCloudError

def run_validated_incremental_pipeline(df_sales, pipeline_name, state_table_id, sales_table_id):
    row_count = 0
    invalid_count = 0
    previous_watermark = None
    try:
        client = bigquery.Client(
            project="resonant-tract-508812-p9",
        )
        watermark_query_job = client.query(
            f"""
            SELECT
              pipeline_name,
              watermark,
            FROM `{state_table_id}`
            """
        )
        watermark_df = watermark_query_job.result().to_dataframe(
            create_bqstorage_client=False
        )
        watermark_df["watermark"] = pd.to_datetime(watermark_df["watermark"]).dt.date
        pipeline_name_watermark = watermark_df[
            watermark_df["pipeline_name"] == pipeline_name
        ]
        if pipeline_name_watermark.empty:
            raise ValueError(f"指定されたパイプラインは存在しません: {pipeline_name}")
        else:
            pipeline_name_watermark = pipeline_name_watermark.iloc[0]
            previous_watermark = pipeline_name_watermark["watermark"]

        incremental_df = df_sales[
            df_sales["sale_date"] > pipeline_name_watermark["watermark"]
        ].copy()
        if len(incremental_df) == 0:
            return {
                "status": "OK",
                "row_count": row_count,
                "invalid_count": invalid_count,
                "previous_watermark": previous_watermark,
                "next_watermark": previous_watermark
            }
        else:
            incremental_df = incremental_df.sort_values(
                by="sale_date",
                ascending=True
            )
            incremental_df = incremental_df.reset_index(drop=True)
            row_count = incremental_df.shape[0]

        invalid_mask = (
            incremental_df["sale_id"].isna()
            | incremental_df.duplicated(subset=["sale_id"], keep=False)
            | incremental_df["sale_date"].isna()
            | incremental_df["product_id"].isna()
            | incremental_df["quantity"].isna()
            | (incremental_df["quantity"] <= 0)
            | incremental_df["unit_price"].isna()
            | (incremental_df["unit_price"] < 0)
        )
        invalid_count = int(invalid_mask.sum())
        if invalid_count != 0:
            raise ValueError
        else:
            new_watermark = incremental_df["sale_date"].max()
            load_append_job_config = bigquery.LoadJobConfig(
                schema=[
                    bigquery.SchemaField("sale_id", "INTEGER", mode="REQUIRED"),
                    bigquery.SchemaField("sale_date", "DATE", mode="REQUIRED"),
                    bigquery.SchemaField("product_id", "STRING", mode="REQUIRED"),
                    bigquery.SchemaField("quantity", "INTEGER", mode="REQUIRED"),
                    bigquery.SchemaField("unit_price", "INTEGER", mode="REQUIRED"),
                ],
                write_disposition=bigquery.WriteDisposition.WRITE_APPEND
            )
            load_append_job = client.load_table_from_dataframe(
                incremental_df,
                sales_table_id,
                job_config=load_append_job_config
            )
            load_append_job.result()

            watermark_df.loc[
                watermark_df["pipeline_name"] == pipeline_name, "watermark"
            ] = new_watermark
            load_truncate_job_config = bigquery.LoadJobConfig(
                schema=[
                    bigquery.SchemaField("pipeline_name", "STRING", mode="REQUIRED"),
                    bigquery.SchemaField("watermark", "DATE", mode="REQUIRED")
                ],
                write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE
            )
            load_truncate_job = client.load_table_from_dataframe(
                watermark_df,
                state_table_id,
                job_config=load_truncate_job_config
            )
            load_truncate_job.result()

        return {
            "status": "OK",
            "row_count": row_count,
            "invalid_count": invalid_count,
            "previous_watermark": previous_watermark,
            "next_watermark": new_watermark
        }

    except (ValueError, GoogleCloudError):
        return {
            "status": "ERROR",
            "row_count": row_count,
            "invalid_count": invalid_count,
            "previous_watermark": previous_watermark,
            "next_watermark": None
        }

# 実行ケース
# ケース①：不正レコードが存在する場合
# 提示した df_sales をそのまま使用します。
# 期待する戻り値：
# {
#     "status": "ERROR",
#     "row_count": 5,
#     "invalid_count": 2,
#     "previous_watermark": datetime.date(2026, 11, 6),
#     "next_watermark": None
# }
# BigQuery上の期待する状態：
#   確認項目	                期待値
#   増分売上テーブルの総件数	    10件
#   sales_incremental	    2026-11-06
#   inventory_incremental	2026-11-05
result1 = run_validated_incremental_pipeline(
    df_sales,
    "sales_incremental",
    "resonant-tract-508812-p9.sql_training.pipeline_watermarks_step7",
    "resonant-tract-508812-p9.sql_training.sales_incremental_step7"
)
print(result1)

# ケース②：不正レコードを修正した場合
df_sales_corrected = df_sales.copy()
df_sales_corrected.loc[
    df_sales_corrected["sale_id"] == 13, "product_id"
] = "P003"
df_sales_corrected.loc[
    df_sales_corrected["sale_id"] == 14, "quantity"
] = 2

result2 = run_validated_incremental_pipeline(
    df_sales_corrected,
    "sales_incremental",
    "resonant-tract-508812-p9.sql_training.pipeline_watermarks_step7",
    "resonant-tract-508812-p9.sql_training.sales_incremental_step7"
)
print(result2)

# 期待する戻り値：
# {
#     "status": "OK",
#     "row_count": 5,
#     "invalid_count": 0,
#     "previous_watermark": datetime.date(2026, 11, 6),
#     "next_watermark": datetime.date(2026, 11, 9)
# }
# BigQuery上の期待する状態：
#   確認項目	                期待値
#   増分売上テーブルの総件数     15件
#   sales_incremental       2026-11-09
#   inventory_incremental	2026-11-05

# ケース③：ケース②のデータを再実行した場合
# 期待する戻り値：
# {
#     "status": "OK",
#     "row_count": 0,
#     "invalid_count": 0,
#     "previous_watermark": datetime.date(2026, 11, 9),
#     "next_watermark": datetime.date(2026, 11, 9)
# }
# BigQuery上のデータおよびウォーターマークには、変更がないことを期待します。
result3 = run_validated_incremental_pipeline(
    df_sales_corrected,
    "sales_incremental",
    "resonant-tract-508812-p9.sql_training.pipeline_watermarks_step7",
    "resonant-tract-508812-p9.sql_training.sales_incremental_step7"
)
print(result3)
















































