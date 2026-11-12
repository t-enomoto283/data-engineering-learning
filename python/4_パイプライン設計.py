
### STEP 4-1｜処理の関数化
# 複数の処理を関数に分割し、順番に実行します。
#
# 今回使うPython・pandasの知識
# ① 関数を分割する目的
# これまでの演習では、1つの関数の中で複数の処理を実行することがありました。
# 例えば、次のコードです。
def process_orders(df):
    df = df[
        df["status"] == "completed"
    ]
    df = df.groupby(
        "customer_id",
        as_index=False
    )["amount"].sum()
    return df
# この関数では、次の2つの処理を行っています。
#   1. 完了した注文だけを抽出する。
#   2. 顧客別に注文金額を集計する。
# 処理が小規模な場合は問題ありませんが、実際のパイプラインでは、入力データの検証や保存なども必要になります。
# そのため、処理の役割ごとに関数を分割する設計が有効です。
#
# ② 関数からDataFrameを返す
# 例えば、完了した注文を抽出する処理を独立させます。
def filter_completed(df):
    result = df.loc[
        df["status"] == "completed"
    ].copy()
    return result
# この関数は、注文の抽出だけを担当します。
# .copy() を使用することで、抽出結果を独立したDataFrameとして扱えます。
#
# ③ 関数の戻り値を次の関数へ渡す
# 次のような2つの関数があるとします。
def multiply_by_two(value):
    return value * 2

def add_ten(value):
    return value + 10

# これらを順番に実行できます。
step1 = multiply_by_two(5)
step2 = add_ten(step1)
print(step2)
# 出力結果：20
# このように、前の処理の出力を次の処理の入力にすることが、パイプラインの基本的な考え方です。
#
# ④ groupby() と agg() による集計
# STEP 2の復習です。
summary = df.groupby(
    "customer_id",
    as_index=False
).agg(
    total_amount=("amount", "sum"),
    order_count=("order_id", "count")
)
# 顧客別に、注文金額の合計と注文件数を集計できます。
# 今回もこの処理を利用します。
#
# ⑤ merge(validate=...) によるマスタ結合
# STEP 3-4の復習です。
result = summary.merge(
    customers,
    on="customer_id",
    how="left",
    validate="many_to_one",
    indicator=True,
)
# 顧客マスタの customer_id が一意であることを検証しながら結合します。
# 今回の演習では、マスタに存在しない顧客がいた場合も、LEFT JOINによって集計結果を保持します。

# 演習用データ
# 以下のDataFrameを使用してください。
import pandas as pd

orders = pd.DataFrame(
    {"order_id": [101, 102, 103, 104, 105, 106],
    "customer_id": ["C001", "C002", "C001", "C003", "C002", "C004"],
    "amount": [12000, 8000, 15000, 6000, 10000, 5000],
    "status": ["completed", "cancelled", "completed", "completed", "completed", "completed"]}
)

customers = pd.DataFrame(
    {"customer_id": ["C001", "C002", "C003"],
    "customer_name": ["田中", "佐藤", "鈴木"]}
)
# 今回の処理では、次の順番でデータを加工します。
#   orders：注文データ 6行
#     ↓
#   ① 完了注文の抽出 filter_completed_orders()
#     ↓
#   ② 顧客別集計 aggregate_customer_orders()
#     ↓
#   ③ 顧客マスタ結合 join_customer_master()
#     ↓
#   最終DataFrame 4行

# 演習要件
# 今回は、次の4つの関数を実装してください。
#
# 関数① filter_completed_orders(orders)
# 完了した注文だけを抽出する関数です。
# 要件：
#   status が "completed" のレコードだけを抽出する。
#   抽出したDataFrameのコピーを作成する。
#   抽出結果を返す。

def filter_completed_orders(orders):
    completed = orders[
        orders["status"] == "completed"
    ].copy()
    return completed

# 関数② aggregate_customer_orders(orders)
# 完了注文を顧客別に集計する関数です。
# 要件：
#   customer_id ごとに集計する。
#   amount の合計を total_amount として取得する。
#   order_id の件数を order_count として取得する。
#   customer_id が通常の列（DataFrameのインデックスではなく、df.columns に含まれる列）として存在するDataFrameを返す。
# この関数では、注文のステータスによる絞り込みは行わないでください。

def aggregate_customer_orders(completed):
    aggregate = completed.groupby(
        "customer_id",
        as_index=False  # 指定したキー（ここでは customer_id）をインデックス列としない =DataFrameに含まれる通常の列とする
    ).agg(
        total_amount=("amount", "sum"),
        order_count=("order_id", "count")
    )
    return aggregate

# 関数③ join_customer_master(summary, customers)
# 集計結果に顧客名を付与する関数です。
# 要件：
#   customer_id をキーとしてLEFT JOINする。
#   validate="many_to_one" を指定する。
#   顧客マスタに存在しない場合、customer_name を "未登録" に置き換える。
#   結合結果を返す。

def join_customer_master(aggregate, customers):
    joined = aggregate.merge(
        customers,
        on="customer_id",
        how="left",
        validate="many_to_one",
    )
    joined["customer_name"] = joined["customer_name"].fillna("未登録")
    return joined

# 関数④ run_pipeline(orders, customers)
# 上記3つの関数を順番に呼び出す関数です。
# 要件：
#   filter_completed_orders() を実行する。
#   その戻り値を aggregate_customer_orders() に渡す。
#   集計結果を join_customer_master() に渡す。
#   最終結果を customer_id の昇順に並べ替える。
#   インデックスを0から振り直す。
#   最終DataFrameを返す。
# 各関数の役割を分離することが今回の主な目的です。

def run_pipeline(orders, customers):
    completed = filter_completed_orders(orders)
    aggregate = aggregate_customer_orders(completed)
    result = join_customer_master(aggregate, customers)
    result = result.sort_values(
        "customer_id",
        ascending=True
    )
    result = result.reset_index(drop=True)
    return result

# テストケース
# テストケース1：各関数の処理結果の確認
# 作成した関数①～③を個別に呼び出し、結果を表示してください。
# ① 完了注文の抽出結果
#   期待する行数：5行
# ② 顧客別集計結果
#   customer_id	total_amount	order_count
#   C001	27000	2
#   C002	10000	1
#   C003	6000	1
#   C004	5000	1
# ③ 顧客マスタ結合結果
#   customer_id	total_amount	order_count	customer_name
#   C001	27000	2	田中
#   C002	10000	1	佐藤
#   C003	6000	1	鈴木
#   C004	5000	1	未登録
# 次の項目を assert で検証してください。
# - 完了注文が5行であること。
# - 顧客別集計結果が4行であること。
# - C001の total_amount が27000であること。
# - C004の customer_name が "未登録" であること。

testcase1_1 = filter_completed_orders(orders)
print(testcase1_1)

testcase1_2 = aggregate_customer_orders(testcase1_1)
print(testcase1_2)

testcase1_3 = join_customer_master(testcase1_2, customers)
print(testcase1_3)

assert len(testcase1_1) == 5, "行数が異なります"
assert len(testcase1_2) == 4, "行数が異なります"
assert testcase1_3.loc[
    testcase1_3["customer_id"] == "C001", "total_amount"
].item() == 27000, "値が異なります"
assert testcase1_3.loc[
    testcase1_3["customer_id"] == "C004", "customer_name"
].item() == "未登録", "値が異なります"

# テストケース2：パイプライン全体の検証
# run_pipeline(orders, customers) を実行してください。
#
# 期待する最終結果：
#   customer_id	total_amount	order_count	customer_name
#   C001	27000	2	田中
#   C002	10000	1	佐藤
#   C003	6000	1	鈴木
#   C004	5000	1	未登録
#
# 次の項目を検証してください。
#   最終結果を表示する。
#   期待するDataFrameを自分で作成する。
#   assert と DataFrame.equals() を使用して、最終結果が期待するDataFrameと一致することを検証する。
#   列の順序は、上記の表と同じにしてください。

testcase2 = run_pipeline(orders, customers)
print(testcase2)

expected2 = pd.DataFrame(
    {"customer_id": ["C001", "C002", "C003", "C004"],
    "total_amount": [27000, 10000, 6000, 5000],
     "order_count": [2, 1, 1, 1],
     "customer_name": ["田中", "佐藤", "鈴木", "未登録"]}
)

assert expected2.equals(testcase2), "結果が一致しません。"


### STEP 4-2｜ログによる処理状況の記録
# STEP 4-1では、注文データの抽出・集計・マスタ結合をそれぞれ関数化し、run_pipeline() から順番に実行する構成を作りました。
# 今回は、そのパイプラインにPython標準ライブラリの logging を導入します。
# 目標は、処理がいつ開始・終了し、各工程で何件のデータを処理したのかを、ログから確認できるようにすることです。
#
# 今回使うPythonの知識
# ① logging とは

































































































