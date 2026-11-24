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


### 日替わりPython・pandas｜
































































