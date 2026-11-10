
### STEP 2-1｜DataFrameの作成・CSV読み込み・データ抽出
# 今回の演習では、次の操作を確認します。
#   1. CSVファイルをDataFrameとして読み込む。
#   2. DataFrameの構造・列名・データ型を確認する。
#   3. 必要な列を抽出する。
#   4. 条件に一致する行を抽出する。
#   5. loc を使って行と列を同時に指定する。

# 今回使うPython・pandasの知識
# ① pd.read_csv()：CSVの読み込み
import pandas as pd
df = pd.read_csv("orders.csv")
print(df)
# pd.read_csv() はCSVファイルを読み込み、DataFrameを作成します。
# STEP 1では csv.DictReader を使用しましたが、pandasでは1行で表形式のデータを読み込めます。
#
# ② DataFrameの構造確認
print(df.head())
print(df.shape)
print(df.columns)
print(df.dtypes)
#   メソッド・属性	 内容
#   head()       先頭5行を表示
#   shape	     行数・列数をタプルで取得
#   columns	     列名を取得
#   dtypes	     各列のデータ型を確認
# head() はメソッドなので () が必要ですが、shape、columns、dtypes は属性なので () は不要です。
#
# ③ 列の抽出
# 1列を抽出する場合：
df["customer_id"]
# 複数列を抽出する場合：
df[["customer_id", "amount"]]
# 1列の抽出は基本的に Series、複数列の抽出は DataFrame になります。
#
# ④ 条件による行の抽出
df[df["amount"] >= 10000]
# このコードでは、amount が10,000以上の行を抽出します。
# 複数条件を組み合わせる場合：
df[(df["status"] == "completed") & (df["amount"] >= 10000)]
# pandasでは、条件ごとに () で囲み、AND条件には & OR条件には | を使用します。
#
# ⑤ locによる行・列の抽出
df.loc[df["status"] == "completed", ["customer_id", "amount"]]
# loc は次の構造で使用します。
# df.loc[行の条件, 取得したい列]
# 今回のように、条件に一致する行から必要な列だけを取り出したい場合に便利です。

# 演習用データは、STEP 1-5と1-6で使用した次の内容の orders.csv を再利用します。
#   order_id,customer_id,amount,status
#   1,C001,12000,completed
#   2,C002,8000,cancelled
#   3,C001,15000,completed
#   4,C003,6000,completed
# 新しいCSVファイルを作成する必要はありません。

# 演習要件
# 今回は関数化せず、pandasの基本操作を順番に実装してください。
# 要件①：CSV読み込み
# pd.read_csv() を使用して、orders.csv をDataFrameに読み込み、変数 df に格納してください。
import pandas as pd
df = pd.read_csv("orders.csv")

# 要件②：構造確認
# 次の情報を取得・表示してください。
#   DataFrameの先頭5行
#   行数・列数
#   列名
#   各列のデータ型
print(df.head())   # 先頭5行を表示
print(df.shape)    # 行数・列数をタプルで取得
print(df.columns)  # 列名を取得
print(df.dtypes)   # 各列のデータ型を確認

# 要件③：列の抽出
# customer_id と amount の2列だけを抽出し、変数 selected_columns に格納してください。
selected_columns = df[["customer_id", "amount"]]
print(selected_columns)

# 要件④：条件による行の抽出
# status が "completed" かつ amount が10,000以上の注文を抽出し、変数 filtered_orders に格納してください。
filtered_orders = df[
    (df["status"] == "completed") & (df["amount"] >= 10000)
]
print(filtered_orders)

# 要件⑤：locによる抽出
# status が "completed" の注文について、customer_id と amount の2列だけを抽出し、変数 completed_sales に格納してください。
# この要件では loc を使用してください。
completed_sales = df.loc[
    df["status"] == "completed",
    ["customer_id", "amount"]
]  # df.loc[行の条件, 取得したい列]
print(completed_sales)

# テストケース（2つ）
# 今回は要件①〜⑤の処理を実装したうえで、次の2つの抽出結果を確認します。
# ケース1：条件による行の抽出
print(filtered_orders)
# 期待結果：
#      order_id customer_id  amount     status
#   0         1        C001   12000  completed
#   2         3        C001   15000  completed

# ケース2：locによる行・列の抽出
print(completed_sales)
# 期待結果：
#     customer_id  amount
#   0        C001   12000
#   2        C001   15000
#   3        C003    6000


### STEP 2-2｜pandasによるデータ集計（groupby・agg）
# STEP 2-1ではCSVの読み込み、列選択、条件抽出、loc を学びました。今回は、抽出したデータを顧客単位で集計する処理を実装します。
# データエンジニアリングでは、明細データを集計して分析用のデータマートを作る際に頻繁に使う操作です。
#
# 今回使うPython・pandasの知識
# ① groupby()：指定した列でグループ化する
# SQLの GROUP BY に相当します。
df.groupby("customer_id")
# これだけでは集計結果は完成しません。続けて sum() や agg() などを指定します。
#
# ② agg()：複数の集計処理を指定する
# 例えば、次のように記述します。
summary = df.groupby("customer_id").agg(
    total_amount=("amount", "sum"),
    order_count=("order_id", "count")
)
# .agg() の書き方は、基本的に 出力列名=("対象列", "集計関数") です。
# この処理では、顧客ごとに次の値を計算します。
#   total_amount：amount の合計
#   order_count：order_id の件数
#
# ③ reset_index()：集計キーを通常の列に戻す
summary = summary.reset_index()
# groupby() の集計キーは、通常、結果のインデックスになります。
# reset_index() を使えば、customer_id を通常の列として扱えるため、CSV出力や他のデータとの結合に利用しやすくなります。
#
# ④ sort_values()：集計結果を並べ替える
summary = summary.sort_values(
    "total_amount",
    ascending=False
)
# ascending=False は降順、つまり金額が大きい順です。

# 演習問題として顧客別の売上集計テーブルを作成する
# 入力データは STEP 2-1で使用した次の内容の orders.csv をそのまま使います。
#   order_id	customer_id	amount	status
#   1	C001	12000	completed
#   2	C002	8000	cancelled
#   3	C001	15000	completed
#   4	C003	6000	completed

# 実装要件
#   pd.read_csv() で orders.csv を読み込む。
#   status が completed の注文だけを抽出する。
#   customer_id ごとにグループ化する。
#   .agg() を使用して、顧客別の売上合計 total_amount と注文件数 order_count を算出する。
#   reset_index() で customer_id を通常の列にする。
#   sort_values() で total_amount の降順に並べ替える。
#   最終結果を print() で表示する。
#   最終的な列は、customer_id、total_amount、order_count の3列としてください。

import pandas as pd
df = pd.read_csv("orders.csv")

completed_order = df[
    df["status"] == "completed"
]

customer_summary = completed_order.groupby("customer_id").agg(
    total_amount=("amount", "sum"),
    order_count=("order_id", "count")
)

customer_summary = customer_summary.reset_index()

result = customer_summary.sort_values(
    "total_amount",
    ascending=False
)
print(result)

# 期待する出力
#   customer_id	total_amount	order_count
#   C001	27000	2
#   C003	6000	1

# テストケース
# テストケース1：通常の集計
# orders.csv を使い、期待する出力と一致することを確認してください。
#
# テストケース2：キャンセル注文の除外
# orders.csv の注文ID 2 の status を一時的に completed に変更し、再実行してください。
# 期待する結果は以下のとおりです。
#   customer_id	total_amount	order_count
#   C001	27000	2
#   C002	8000	1
#   C003	6000	1
# 確認後は orders.csv を元に戻してください。

# 行（1）と列（"status"）を両方指定して上書きする
df.loc[1, "status"] = "completed"

# 戻す
df.loc[1, 'status'] = "cancelled"


### STEP 2-3｜pandasのmergeによるテーブル結合
# 今回は、データエンジニアの実務でも頻繁に使う データ同士の結合（JOIN） がテーマです。
# SQLでの LEFT JOIN と INNER JOIN を、pandasの merge() で再現します。
#
# 今回使うPython・pandasの知識
# ① pd.DataFrame()：データを作成する
# Pythonの辞書からDataFrameを作成できます。
import pandas as pd
customers = pd.DataFrame(
    {"customer_id": ["C001", "C002", "C003"],
    "customer_name": ["田中", "佐藤", "鈴木"]}
)
# 今回は、既存の orders.csv に結合する顧客マスタとして使用します。
#
# ② merge()：DataFrameを結合する
# 基本構文は以下です。
result = pd.merge(
    left_df,                # 左側のDataFrame
    right_df,               # 右側のDataFrame
    on="customer_id",       # 結合の基準にする列（キー）
    how="left",             # 結合方法
    validate="many_to_one"  # 左側のキーは複数（many）を許容、右側のキーは一意（one）を期待する制約
)
# ③ 結合先にデータが存在しない場合
# 例えば、注文データに C004 が存在していて、顧客マスタには C004 が存在しないとします。
#   注文データ                 |   顧客マスタ
#   order_id	customer_id  |   customer_id   customer_name
#   1           C001         |   C001          田中
#   2           C004         |   C002          佐藤
# LEFT JOIN に相当する how="left" では、C004 の注文も残り、顧客名は欠損値 NaN になります。
# INNER JOIN に相当する how="inner" では、C004 の注文は結果から除外されます。
#
# ④ 結合させるCOLUMN名が表間で異なる場合
# 仮に table_a では "product_code"、table_b では "product"　という、それぞれ異なる列名によって結合を行う場合、
df_merged = pd.merge(
    table_a,
    table_b,
    left_on="product_code",
    right_on="product",
    how="left"
)
# これはSQLのJOIN構文でON句を下記のように書くのと同じ
#   ON table_a.product_code = table_b.product

# 演習問題として使用する注文データは次の内容の orders.csv をそのまま使います。
#   order_id	customer_id	amount	status
#   1	C001	12000	completed
#   2	C002	8000	cancelled
#   3	C001	15000	completed
#   4	C003	6000	completed
#
# 顧客マスタ
# 今回は、次のコードでDataFrameを作成してください。新しいCSVファイルを作る必要はありません。
customers = pd.DataFrame(
    {"customer_id": ["C001", "C002"],
    "customer_name": ["田中", "佐藤"]}
)

# 実装要件
# 次の処理を行うPythonコードを作成してください。
#   pd.read_csv() で orders.csv を読み込む。
#   上記の customers DataFrameを作成する。
#   customer_id をキーに、orders と customers を merge() で結合する。
#   結合方法は how="left" を指定する。
#   validate="many_to_one" を指定する。
#   結合後、order_id、customer_id、amount、status、customer_name の5列をこの順番で出力する。

# テストケース
# テストケース1：LEFT JOIN
# ここでは、顧客マスタに存在しない C003 の注文が残ることを確認します。
# 期待する結果：
#   order_id	customer_id	amount	status	customer_name
#   1	C001	12000	completed	田中
#   2	C002	8000	cancelled	佐藤
#   3	C001	15000	completed	田中
#   4	C003	6000	completed	NaN
#
# テストケース2：INNER JOIN
# テストケース1のコードを変更して、how="inner" で結合してください。C003 の注文が除外され、3行になることを確認してください。
# 期待する結果：
#   order_id	customer_id	amount	status	customer_name
#   1	C001	12000	completed	田中
#   2	C002	8000	cancelled	佐藤
#   3	C001	15000	completed	田中

# 今後CSVファイル内の値を実際に変更する際に備えて orders.csv のコピーを作成
buckup_orders = pd.read_csv("orders.csv")
buckup_orders.to_csv("orders_origin.csv", index=False)

df = pd.read_csv("orders.csv")

customers = pd.DataFrame(
    {"customer_id": ["C001", "C002"],
     "customer_name": ["田中", "佐藤"]}
)

df.merge(
    customers,
    on="customer_id",
    how="left",
    validate="many_to_one"
)

df.merge(
    customers,
    on="customer_id",
    how="inner",
    validate="many_to_one"
)


### STEP 2-4｜pandasの欠損値処理
# 今回は、欠損値（NULL）の検出・補完・除外です。
#
# 今回使うPython・pandasの知識
# ① isna()：欠損値を検出する
# pandasでは、欠損値を NaN や None、pd.NA などで表現します。
df["customer_name"].isna()
# 例えば、以下のDataFrameがあるとします。
#   customer_id	customer_name
#   C001	田中
#   C002	佐藤
#   C003	NaN
# isna() の結果は次のとおりです。
#   0    False
#   1    False
#   2    True
# 欠損値の行だけを抽出する場合は、次のように書きます。
missing_rows = df[
    df["customer_name"].isna()
]
#
# ② notna()：欠損値ではない行を検出する
# notna() は isna() の逆です。
valid_rows = df[
    df["customer_name"].notna()
]
#
# ③ fillna()：欠損値を補完する
# 欠損値を指定した値で置き換えられます。
df["customer_name"] = df["customer_name"].fillna("未登録")
# 実行後：
#   customer_id	customer_name
#   C001	田中
#   C002	佐藤
#   C003	未登録
# なお、fillna() は、戻り値を代入しなければ元のDataFrameを変更しません。
#
# ④ dropna()：欠損値を含む行を除外する
valid_df = df.dropna(
    subset=["customer_name"]
)
# subset には、欠損値の判定対象とする列を指定します。
# この例では customer_name が欠損している行だけが除外され、他の列の欠損は除外条件になりません。
#
# ⑤ isna().sum()：欠損件数を数える
missing_count = df["customer_name"].isna().sum()
# True が1、False が0として集計されるため、欠損件数を取得できます。
# データ品質チェックでは頻繁に使用する書き方です。

# 今回の演習データとして次の内容の orders.csv と、後述の顧客マスタを引き続き使用します。
#   orders.csv
#   order_id	customer_id	amount	status
#   1	C001	12000	completed
#   2	C002	8000	cancelled
#   3	C001	15000	completed
#   4	C003	6000	completed
#
#   顧客マスタ（Python内で作成）
customers = pd.DataFrame(
    {"customer_id": ["C001", "C002"],
     "customer_name": ["田中", "佐藤"]}
)

# 演習要件として今回は 2つのテストケース を実施します。
# テストケース1：欠損値の検出と補完
#   orders.csv を読み込む。
#   顧客マスタを作成する。
#   customer_id をキーに LEFT JOIN 相当の merge() を行う。validate="many_to_one" も指定する。
#   customer_name の欠損件数を isna().sum() で取得して表示する。
#   customer_name が欠損している行だけを isna() で抽出して表示する。
#   fillna() で欠損した顧客名を "未登録" に補完する。
#   補完後のDataFrameを表示する。
#
# テストケース2：欠損行の除外
# テストケース1で作成した 補完前の結合結果 を使用してください。
#   customer_name が欠損していない行だけを notna() で抽出する。
#   別途、dropna(subset=["customer_name"]) でも欠損行を除外する。
#   両方の結果を表示し、同じ3行になることを確認する。

df = pd.read_csv("orders.csv")

customers = pd.DataFrame(
    {"customer_id": ["C001", "C002"],
     "customer_name": ["田中", "佐藤"]}
)

order_customer = df.merge(
    customers,
    on="customer_id",
    how="left",
    validate="many_to_one"
)

name_na_count = order_customer["customer_name"].isna().sum()
print(name_na_count)

name_na_row = order_customer[
    order_customer["customer_name"].isna()
]
print(name_na_row)

# 作成したコピーにて fillna()
order_customer_fll = order_customer.copy()
order_customer_fll["customer_name"] = order_customer_fll["customer_name"].fillna("未登録")
print(order_customer_fll)

name_notna_row = order_customer[
    order_customer["customer_name"].notna()
]
print(name_notna_row)

name_na_except = order_customer.dropna(
    subset=["customer_name"]
)
print(name_na_except)


### STEP 2-5｜CSV出力・再読み込み・データ検証
# 今回は、データ加工後の結果をCSVファイルとして保存し、そのファイルを再度読み込んで検証する処理です。
# DataFrame → CSV保存 → CSV再読み込み → 検証という一連の流れを実装します。
#
# 今回使うPython・pandasの知識
# ① to_csv()：DataFrameをCSVファイルに保存する
df.to_csv("output.csv", index=False)
# 例えば、次のDataFrameがあるとします。
#   customer_id	total_amount
#   C001	27000
#   C002	8000
# index=False で保存すると、CSVの中身は次のようになります。
#   customer_id,total_amount
#   C001,27000
#   C002,8000
# index=False を指定しない場合は、左端にインデックスの列が追加されます。
# なお、同じ名前のCSVファイルが既に存在する場合、to_csv() は上書きします。
#
# ② pd.read_csv()：保存したCSVを再読み込みする
loaded_df = pd.read_csv("output.csv")
# これにより、保存したCSVを新しいDataFrameとして読み込めます。
# 注意点として、CSVファイルにはpandasのデータ型情報が保存されません。
# そのため、再読み込み時にデータ型が推定され、保存前と変わる場合があります。
#
# ③ len()：DataFrameの行数を取得する
row_count = len(df)
# SQLの COUNT(*) に近い考え方です。
# ただし、len(df) はDataFrameの行数を取得するPythonの関数です。
#
# ④ DataFrame.equals()：2つのDataFrameを比較する
is_equal = df1.equals(df2)
# 2つのDataFrameの形状、対応する値、インデックス、列ラベルなどが一致しているかを判定します。
# 対応する列のデータ型が異なる場合でも、値によっては True になります。
print(is_equal)  # 結果：True
# 今回の演習では、CSV保存前と再読み込み後のデータが一致しているか確認するために使用します。
#
# ⑤ assert：条件が成立することを検証する
# Pythonの assert は、指定した条件が True であることを確認します。
assert len(df) == 3
# 条件が True の場合は、そのまま次の処理に進みます。
# 条件が False の場合は AssertionError が発生します。
assert len(df) == 3, "行数が一致しません"  # このようにメッセージを指定することもできます。
# データ処理では、想定した件数や値が得られているかを確認する簡単な検証に利用できます。
# なお、assert はPythonの最適化実行（-O）で無効化されるため、本番環境で必ず実行すべきデータ品質検証には明示的な例外処理を使用します。

# 演習データとして今回も次の内容の既存 orders.csv を使用します。今回は顧客マスタとの結合は行いません。
  # order_id	customer_id	amount	status
  # 1	C001	12000	completed
  # 2	C002	8000	cancelled
  # 3	C001	15000	completed
  # 4	C003	6000	completed

# 演習要件として今回は2つのテストケースを実施します。
# テストケース1：集計データの保存と検証
#   orders.csv を読み込む。
#   status が "completed" の注文だけを抽出する。
#   customer_id ごとに amount の合計を算出する。
#   集計結果の列名を customer_id、total_amount とする。
#   total_amount の降順で並べる。
#   index=False を指定し、customer_summary.csv という名前でCSVファイルに保存する。
#   保存した customer_summary.csv を pd.read_csv() で再読み込みする。
#   保存前と再読み込み後のDataFrameを equals() で比較し、結果を表示する。
#   assert を使用して、再読み込み後の行数が2行であることを検証する。
# 期待する集計結果：
#   customer_id	total_amount
#   C001	27000
#   C003	6000
# 期待する検証結果：
# True
# assert は正常に通過すれば何も表示されません。

df = pd.read_csv("orders.csv")

completed_order = df[
    df["status"] == "completed"
]

total_amount = completed_order.groupby("customer_id").agg(
    total_amount=("amount", "sum")
)

sort_total_amount = total_amount.sort_values(
    "total_amount",
    ascending=False  # ascending=False は降順
)

package_data = sort_total_amount.reset_index()

package_data.to_csv("customer_summary.csv", index=False)

reload_df = pd.read_csv("customer_summary.csv")
print(reload_df)

is_equal = package_data.equals(reload_df)
print(is_equal)

assert len(reload_df) == 2, "行数が一致しません"

# テストケース2：保存したデータの内容を検証する
# テストケース1で再読み込みしたDataFrameを使用してください。
#   customer_id が "C001" の行を抽出する。
#   その行の total_amount を取得する。
#   assert を使用して、その値が 27000 であることを検証する。
#   検証した値を表示する。
# 期待する出力：
# 27000

extract_row = reload_df[
    reload_df["customer_id"] == "C001"
]

extract_value = extract_row["total_amount"].item()
print(extract_value)

assert extract_value == 27000, "値が一致しません"

# 今回の実務的なポイント
# 今回の演習は、データパイプラインにおける次の流れに相当します。
#   Extract（抽出）：orders.csvを読み込む
#     ↓
#   Transform（変換）：completedの抽出・顧客別集計
#     ↓
#   Load（保存）：customer_summary.csvに出力
#     ↓
#   Validate（検証）：再読み込み・一致確認・件数と値の検証


### STEP 2-6｜pandas基礎の総合演習
# read_csv()、条件抽出、groupby()、merge()、欠損値処理、CSV出力・検証を組み合わせて、複数の処理を1つの関数にまとめます。
#
# 今回使うPython・pandasの知識
# ① def：一連の処理を関数にまとめる
# PythonのSTEP 1で学習した関数を、pandasのデータ加工にも利用します。
# 例えば、次のようにDataFrameを受け取り、加工結果を返す関数を作れます。
def filter_completed(df):
    result = df[
        df["status"] == "completed"
    ]
    return result
# 呼び出す側は次のようになります。
completed_df = filter_completed(df)
# このようにすると、同じ処理を別のデータに対しても繰り返し利用できます。
#
# ② rename()：列名を変更する
df = df.rename(
    columns={"amount": "sales_amount"}
)
# amount 列を sales_amount に変更します。
# なお、rename() は通常、新しいDataFrameを返すため、結果を変数に代入します。
#
# ③ sort_values()：複数の条件で並べ替える
result = df.sort_values(
    by=["total_amount", "customer_id"],
    ascending=[False, True]
)
# この場合、次の順序で並べ替えます。
#   1. total_amount の降順
#   2. 金額が同じ場合は customer_id の昇順
#
# ④ DataFrame.equals()：加工結果を比較する
is_equal = result1.equals(result2)
# 今回は、関数から返された結果と、期待するDataFrameを比較するために使います。
# 比較では、行の順序とインデックスにも注意してください。
#
# ⑤ assert：処理結果を検証する
assert result.equals(expected), "集計結果が一致しません"
# 条件が成立しない場合は AssertionError が発生します。
# 今回の演習では、関数の処理結果が要件を満たしているか確認するために使用します。

# 演習で使用するデータ
# これまでと同じファイルの orders.csv を使用します。
#   order_id	customer_id	amount	status
#   1	C001	12000	completed
#   2	C002	8000	cancelled
#   3	C001	15000	completed
#   4	C003	6000	completed
#
# 顧客マスタ
# 以下のコードで作成してください。
customers = pd.DataFrame(
    {"customer_id": ["C001", "C002"],
    "customer_name": ["田中", "佐藤"]}
)

# 演習要件
# 次の関数を作成してください。
import pandas as pd
orders = pd.read_csv("orders.csv")

def create_customer_sales_summary(orders_df, customers_df):
    completed_orders = orders_df[
        orders_df["status"] == "completed"
    ]
    customer_sales = completed_orders.groupby("customer_id").agg(
        total_amount=("amount", "sum"),
        order_count=("order_id", "count")
    )
    joined_customer = customer_sales.merge(
        customers_df,
        on="customer_id",
        how="left",
        validate="many_to_one"
    )
    joined_customer["customer_name"] = joined_customer["customer_name"].fillna("未登録")
    change_to_order = joined_customer[
        ["customer_id", "customer_name", "total_amount", "order_count"]
    ]
    order_by_data = change_to_order.sort_values(
        by=["total_amount", "customer_id"],
        ascending=[False, True]
    )
    result = order_by_data.reset_index(drop=True)
    return result

summary = create_customer_sales_summary(orders, customers)
print(summary)

# 関数には2つのDataFrameを渡し、顧客別の売上集計結果をDataFrameとして返します。
# 関数内で実装する処理は次のとおりです。
#   orders_df から status == "completed" の注文だけを抽出する。
#   customer_id ごとに amount の合計と注文件数を集計する。
#   集計結果の列名は total_amount、order_count とする。
#   customers_df と customer_id をキーにLEFT JOIN相当の merge() を行う。
#   validate="many_to_one" を指定する。
#   顧客名が欠損している場合は "未登録" で補完する。
#   最終的な列の順序を customer_id、customer_name、total_amount、order_count とする。
#   total_amount の降順、同額の場合は customer_id の昇順で並べ替える。
#   インデックスを0から振り直し、加工結果のDataFrameを返す。
#
# 注文件数は、order_id の count で集計してください。
# 今回は関数内でCSVの読み書きは行いません。 CSVの読み込みと、必要な保存処理は関数の外側で行います。

# テストケース
# テストケース1：通常データの集計
# orders.csv と、顧客マスタの customers を関数に渡してください。
# 期待する結果：
#   customer_id	customer_name	total_amount	order_count
#   C001	田中	27000	2
#   C003	未登録	6000	1
# また、次の検証を行ってください。
#   len() と assert で、結果が2行であることを確認する。
#   equals() と assert で、期待するDataFrameと一致することを確認する。
# 期待する結果のDataFrameは、次のコードで作成できます。
expected1 = pd.DataFrame(
    {"customer_id": ["C001", "C003"],
    "customer_name": ["田中", "未登録"],
    "total_amount": [27000, 6000],
    "order_count": [2, 1]}
)

assert len(summary) == 2, "行数が一致しません"
assert summary.equals(expected1), "集計結果が一致しません"

# テストケース2：注文データを変更して再集計
# 元の orders.csv は変更せず、読み込んだDataFrameのコピーを作成してください。
# そのコピーに対して、次の変更を行います。
#   order_id == 2 の status を "cancelled" から "completed" に変更する。
#   order_id == 4 の amount を 6000 から 8000 に変更する。
# 変更したDataFrameと、同じ顧客マスタを関数に渡してください。
# 期待する結果：
#   customer_id	customer_name	total_amount	order_count
#   C001	田中	27000	2
#   C002	佐藤	8000	1
#   C003	未登録	8000	1
# こちらも len() と assert で3行であることを確認し、equals() と assert で期待するDataFrameとの一致を検証してください。
# 期待するDataFrame：
expected2 = pd.DataFrame({
    "customer_id": ["C001", "C002", "C003"],
    "customer_name": ["田中", "佐藤", "未登録"],
    "total_amount": [27000, 8000, 8000],
    "order_count": [2, 1, 1]
})

testcase2 = orders.copy()

testcase2.loc[testcase2["order_id"] == 2, "status"] = "completed"  # order_id == 2 の status を "completed" に変更

testcase2.loc[testcase2["order_id"] == 4, "amount"] = 8000         # order_id == 4 の amount を 8000 に変更

summary2 = create_customer_sales_summary(testcase2, customers)
print(summary2)

assert len(summary2) == 3, "行数が一致しません"
assert summary2.equals(expected2), "集計結果が一致しません"

# 今回のポイント
# 今回、特に意識してほしいのは 処理の順序と関数の再利用性 です。
#   入力：orders_df / customers_df
#     ↓
#   抽出・集計：completed抽出 -> 顧客別集計
#     ↓
#   結合・補完：merge -> fillna
#     ↓
#   整形：列の並べ替え -> sort_values -> reset_index
#     ↓
#   出力：return DataFrame





