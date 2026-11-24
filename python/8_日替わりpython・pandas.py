
### 日替わりPython・pandas｜データ品質検証と検証結果の辞書化
# ETLパイプラインにおいて、取得したデータを後続処理に渡す前に、必須カラムの存在、主キーの欠損、主キーの重複を検証することがあります。
# 今回は、任意のDataFrameに対してこれらの検証を行い、検証結果を辞書形式で返す汎用的な関数を実装。
# BigQueryへの接続やCSVファイルの読み書きは不要。
#
#   関連技術	用途
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


### 日替わりPython・pandas｜



















































































