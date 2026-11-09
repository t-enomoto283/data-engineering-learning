
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


