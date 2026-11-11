
### STEP 3-1｜重複データの検証
#
# 今回使うPython・pandasの知識
# ① duplicated()：重複している行を判定する
# duplicated() は、指定した列の値が重複しているかを判定するメソッドです。
df.duplicated(
    subset=["order_id"]
)
# subset には、重複判定に使用する列を指定します。
# 例えば、次のデータがあるとします。
#   order_id	amount
#   1	        1000
#   2	        2000
#   1	        3000
# order_id を基準に判定すると、結果は次のようになります。
#   0     False
#   1     False
#   2     True
#   dtype: bool
# デフォルトでは、最初に出現した値は False、2回目以降は True になります。
#
# ② keep=False：重複グループのすべての行を検出する
df.duplicated(
    subset=["order_id"],
    keep=False
)
# keep=False を指定すると、重複している値について、最初の行も含めてすべて True になります。
# 先ほどのデータなら、以下の結果です。
#   0     True
#   1     False
#   2     True
#   dtype: bool
# データ品質検証では、重複しているキーに該当するレコードをすべて確認したい場面があるため、こちらも重要です。
#
# ③ any()：条件を満たす要素が1つでも存在するか
df["amount"].isna().any()
# any() は、対象の真偽値に1つでも True があれば True を返します。
# 今回は、重複の有無を判定する用途で使用できます。
#
# ④ sum()：条件に一致した件数を数える
df["amount"].isna().sum()
# True は1、False は0として数えられるため、条件に一致した件数を取得できます。
# ただし、重複行数と重複しているキーの種類数は異なるので、何を数えているかを意識してください。
#
# ⑤ nunique()：異なる値の種類数を数える
df["order_id"].nunique()
# nunique() は、重複を除いた値の種類数を返します。
# 例えば、[1, 2, 1, 3] なら結果は 3 です。
# SQLの COUNT(DISTINCT order_id) に相当します。

# 演習用データ
# 今回は既存の orders.csv を変更せず、以下の新しいDataFrameをPythonコード内で作成して使用します。
import pandas as pd
orders = pd.DataFrame(
    {"order_id": [101, 102, 103, 102, 104, 105, 105],
    "customer_id": ["C001", "C002", "C003", "C002", "C004", "C005", "C005"],
    "amount": [12000, 8000, 15000, 8000, 6000, 10000, 12000]}
)
#   行番号	order_id	customer_id	  amount
#   0	    101	        C001	      12000
#   1	    102	        C002	      8000
#   2	    103	        C003	      15000
#   3	    102	        C002	      8000
#   4	    104	        C004	      6000
#   5	    105	        C005	      10000
#   6	    105	        C005	      12000
# ここでは、order_id は注文を一意に識別するキーであり、同じ order_id が複数行に存在してはいけないという業務ルールを設定します。
# また、order_id=105 は金額が異なる2行になっています。行全体が一致していなくても、注文IDが重複していれば不正として検出する必要があります。

# 演習要件
# テストケース1：重複レコードの検出
# 次の処理を実装してください。
#   order_id を基準に重複しているレコードを、最初の行も含めてすべて抽出する。
#   抽出したDataFrameを表示する。
#   重複レコードの行数を取得して表示する。
#   重複が存在するかどうかを真偽値で取得して表示する。
#   assert で重複レコードが4行であることを検証する。
# 期待する抽出結果：
#   行番号	order_id	customer_id	amount
#   1	102	C002	8000
#   3	102	C002	8000
#   5	105	C005	10000
#   6	105	C005	12000
# 期待する判定値は True です。

dup_judge = orders.duplicated(
    subset=["order_id"],
    keep=False
)

dup_record = orders[dup_judge]
print(dup_record)

dup_row = orders.duplicated(
    subset=["order_id"],
    keep=False
).sum()
print(dup_row)

dup_exists = orders.duplicated(
    subset=["order_id"],
    keep=False
).any()
print(dup_exists)

assert dup_row == 4, "集計結果が一致しません"

# テストケース2：重複キーの種類数と一意性の検証
# 同じ orders DataFrameを使用してください。
#   order_id の異なる値の種類数を nunique() で取得する。
#   order_id の値が一意であるかを真偽値で判定する。
#   重複している order_id の値だけを抽出し、重複を除いて表示する。
#   assert で異なる order_id の種類数が5であることを検証する。
#   assert で order_id が一意ではないことを検証する。
# 期待する結果：
#   確認項目	期待値
#   order_id の種類数	5
#   order_id は一意か	False
#   重複している注文ID	102、105
# 重複している注文IDの表示順序は問いません。

unique_type = orders["order_id"].nunique()
print(unique_type)

orderid_is_unique = not orders["order_id"].duplicated().any()
print(orderid_is_unique)

unique_dup_row = dup_record.duplicated(
    subset=["order_id"]
)
unique_dup_orderid = dup_record[unique_dup_row]["order_id"]
print(unique_dup_orderid)

assert orders["order_id"].nunique() == 5, "集計結果が一致しません"

assert orders["order_id"].duplicated().any()

# 今回の重要ポイント
# データ品質検証では、次の3つを区別します。
#   概念            今回の期待値  意味
#   重複レコード数    4行         重複キーに属する全レコード
#   重複キーの種類数  2種類        102、105
#   注文IDの一意性   False       主キーとしての制約を満たしていない
#
# 特に実務では、重複データを発見したからといって、すぐに drop_duplicates() で削除するとは限りません。
# そのため今回は、削除や修正はせず、検出と検証のみを実装します。


### STEP 3-2｜データ型の検証
# 今回は、データの値が想定した型になっているかを確認し、不正な値を検出する処理です。
#
# 今回使うPython・pandasの知識
# ① dtypes：各列のデータ型を確認する
print(df.dtypes)
# 例えば、次のDataFrameがあるとします。
df = pd.DataFrame(
    {"order_id": [101, 102, 103],
    "amount": [1000, 2000, 3000],
    "status": ["completed", "cancelled", "completed"]}
)
# 実行すると、列ごとのデータ型を確認できます。
#   order_id     int64
#   amount       int64
#   status         str
#   dtype: object
# 文字列列のデータ型は、pandasのバージョンや設定によって str、object などになります。
#
# ② pd.to_numeric()：数値への変換
# CSVなどから読み込んだデータには、数値として扱いたい列に文字列が混在している場合があります。
df = pd.DataFrame(
    {"amount": ["1000", "2000", "3000"]}
)
df["amount"] = pd.to_numeric(
    df["amount"]
)
# pd.to_numeric() を使うと、数値として解釈できる文字列を数値型に変換できます。
#
# ③ errors="coerce"：変換できない値を欠損値にする
df = pd.DataFrame(
    {"amount": ["1000", "unknown", "3000"]}
)

converted = pd.to_numeric(
    df["amount"],
    errors="coerce"
)
# 変換結果は次のようになります。
#   元の値      変換後
#   "1000"     1000.0
#   "unknown"  NaN
#   "3000"     3000.0
# errors="coerce" を指定すると、数値に変換できない値は欠損値になります。
# ただし、元から欠損していた値も変換後は欠損値になるため、変換失敗と元々の欠損を区別する必要があります。
#
# ④ isna() と notna()：変換失敗を検出する
# 例えば、次の条件を組み合わせます。
original.notna() & converted.isna()
# これは、
#   元の値は欠損していない
#   変換後の値は欠損している
# という両方の条件を満たすデータを検出するため、数値への変換に失敗した値を特定できます。
#
# ⑤ astype()：データ型を明示的に変換する
df["order_id"] = df["order_id"].astype("int64")
# astype() は指定したデータ型に変換するメソッドです。変換できない値が含まれている場合はエラーになります。
# そのため、不正な値が混在する可能性があるデータでは、pd.to_numeric(errors="coerce") などで検証してから型変換する方法が有効です。

# 演習用データ
# 今回は次の新しいDataFrameを作成します。既存のCSVファイルは変更しません。
orders = pd.DataFrame({
    "order_id": ["101", "102", "103", "104", "105", "106"],
    "customer_id": ["C001", "C002", "C003", "C004", "C005", "C006"],
    "amount": ["12000", "8000", "unknown", "6000", None, "15000"]
})
# order_id と amount は、数値として扱う想定です。
# ただし、amount には数値に変換できない文字列と、元から欠損している値がそれぞれ1件含まれています。

# 演習要件
# テストケース1：数値変換と変換失敗の検出
#   orders の各列のデータ型を表示する。
#   amount 列を pd.to_numeric(errors="coerce") で数値に変換し、変換結果を新しい列 amount_numeric に格納する。
#   元の amount 列が欠損しておらず、amount_numeric 列が欠損している行を抽出する。
#   抽出した行の order_id、amount、amount_numeric を表示する。
#   変換に失敗した行数を取得し、assert で1件であることを検証する。
# 期待する抽出結果：
#   order_id  amount   amount_numeric
#   103       unknown  NaN
# 今回は元の amount 列を上書きせず、変換結果を別の列に保存してください。
#
# テストケース2：欠損値と正常データの検証
# テストケース1で作成した amount_numeric 列を使用してください。
#   元の amount 列が欠損している行を抽出し、order_id と amount を表示する。
#   元から欠損していた行数を取得し、assert で1件であることを検証する。
#   amount_numeric 列が欠損していない行だけを抽出する。
#   抽出したDataFrameの order_id と amount_numeric を表示する。
#   正常に数値変換できた行数を取得し、assert で4件であることを検証する。
# 元から欠損していた行の期待結果：
#   order_id  amount
#   105       None
# 正常に変換できた行の期待結果：
#   order_id   amount_numeric
#   101        12000.0
#   102	       8000.0
#   104	       6000.0
#   106	       15000.0




































