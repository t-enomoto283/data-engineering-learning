
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
# logging は、プログラムの実行状況を記録するためのPython標準ライブラリです。
# これまで使用してきた print() でも処理状況を表示できますが、logging ではログの重要度や出力形式、出力先などを管理できます。
# 例えば、次のように記述します。
import logging
logging.info("データの読み込みを開始しました")
# ただし、logging.info() は、ログの設定によっては表示されません。
# そこで、ログの出力レベルを設定します。
#
# ② logging.basicConfig()：ログの基本設定
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
# 各設定の意味は次のとおりです。
#   設定                  意味
#   level=logging.INFO   INFO以上の重要度のログを出力する
#   format               ログの表示形式を指定する
#   %(levelname)s        ログレベルを表示する
#   %(message)s          ログメッセージを表示する
# 例えば、
logging.info("処理を開始しました")
# 出力例：INFO: 処理を開始しました
# なお、basicConfig() は、すでにルートロガーにハンドラーが設定されている場合、通常は設定を変更しません。
# 今回は設定の影響を分かりやすくするため、専用のロガーを作成して使用します。
#
# ③ logging.getLogger()：ロガーを取得する
logger = logging.getLogger("order_pipeline")
logger.setLevel(logging.INFO)
# getLogger() は、指定した名前のロガーを取得します。
# 同じ名前で呼び出すと、同じロガーオブジェクトを取得できます。
# 今回の演習では、この logger を使用してログを記録します。
#
# ④ ログレベルの違い
# ログには重要度を表すレベルがあります。
#   レベル      主な用途
#   DEBUG      詳細な調査・デバッグ情報
#   INFO       処理の開始・終了・処理件数
#   WARNING    処理は継続できるが注意が必要な状況
#   ERROR      処理中に発生したエラー
#   CRITICAL   システム全体に影響する重大な問題
# 今回使用するのは、主に INFO と WARNING です。
# 例えば、次のような使い分けができます。
logger.info("注文データを読み込みました")
logger.warning("未登録の顧客が存在します")
#
# ⑤ ログに変数を埋め込む
# 処理件数をログに出力する場合は、次のように記述できます。
row_count = 100
logger.info("処理件数: %d件", row_count)
# 出力例：INFO: 処理件数: 100件
# %d は整数を埋め込むための書式です。
# logging では、このようにメッセージと値を別々に渡す方法が一般的です。
#
# ⑥ logging.StreamHandler()：ログの出力先を設定する
# ログをコンソールへ出力するには、StreamHandler を使用できます。
import sys
import logging
logger = logging.getLogger("sample_pipeline")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(
    logging.Formatter("%(levelname)s: %(message)s")
)

logger.addHandler(handler)
logger.propagate = False
# StreamHandler(sys.stdout) は、標準出力にログを出力します。
# setFormatter() は、ログの表示形式を設定します。
# propagate = False は、ログが親ロガーにも渡されて重複出力されることを防ぐための設定です。
# 注意：
#   同じロガーに addHandler() を繰り返すと、ログが重複して表示される場合があります。
#   今回の演習では、ロガーの設定を最初に一度だけ実行してください

# 演習用データ
# STEP 4-1と同じ下記のデータを使用します。
orders
customers

# また、STEP 4-1で作成した以下の3つの関数をそのまま使用してください。
def filter_completed_orders(orders):
    completed = orders[
        orders["status"] == "completed"
    ].copy()
    return completed

def aggregate_customer_orders(completed):
    aggregate = completed.groupby(
        "customer_id",
        as_index=False  # 指定したキー（ここでは customer_id）をインデックス列としない =DataFrameに含まれる通常の列とする
    ).agg(
        total_amount=("amount", "sum"),
        order_count=("order_id", "count")
    )
    return aggregate

def join_customer_master(aggregate, customers):
    joined = aggregate.merge(
        customers,
        on="customer_id",
        how="left",
        validate="many_to_one",
    )
    joined["customer_name"] = joined["customer_name"].fillna("未登録")
    return joined
# これらの関数の内部にログ処理を追加する必要はありません。
# 今回は、パイプライン全体を管理する関数にログを追加することを目的とします。

# 演習要件
# 関数 run_pipeline_with_logging(orders, customers, logger)
# 以下の引数を持つ関数を作成してください。
def run_pipeline_with_logging(orders, customers, logger):
    logger.info("関数の処理開始")
    orders_row = len(orders)
    logger.info("入力された orders の行数: %d件", orders_row)
    completed = filter_completed_orders(orders)
    completed_row = len(completed)
    logger.info("completed注文の抽出件数: %d件", completed_row)
    aggregate = aggregate_customer_orders(completed)
    aggregate_row = len(aggregate)
    logger.info("顧客別集計後: %d件", aggregate_row)
    result = join_customer_master(aggregate, customers)
    result_row = len(result)
    logger.info("顧客マスタ結合後: %d件", result_row)
    unregistered = result[
        result["customer_name"] == "未登録"
    ]
    unregistered_row = len(unregistered)
    if unregistered_row > 0:
        logger.warning("未登録の顧客: %d件", unregistered_row)
    result = result.sort_values(
        "customer_id",
        ascending=True
    )
    result = result.reset_index(drop=True)
    logger.info("関数の処理完了")
    return result

# 処理の順番とログの内容は次のとおりです。
#   順番	処理             ログレベル	記録する内容
#   1	パイプライン開始	INFO	    開始したこと
#   2	入力データの確認	INFO	    注文データの件数
#   3	完了注文の抽出	    INFO	    抽出後の件数
#   4	顧客別集計	    INFO	    集計後の件数
#   5	顧客マスタ結合	    INFO	    結合後の件数
#   6	未登録顧客の確認	WARNING	    未登録顧客が存在する場合、その件数
#   7	並べ替え	        —	        customer_id 昇順、インデックス振り直し
#   8	パイプライン終了	INFO	    終了したこと
#
# 具体的な要件は以下です。ログメッセージの文章は自由ですが、処理内容と件数が分かるようにしてください。
#   関数の開始時に logger.info() で開始ログを出力する。
#   入力された orders の行数をINFOログに記録する。
#   filter_completed_orders() を実行し、結果の行数をINFOログに記録する。
#   aggregate_customer_orders() を実行し、結果の行数をINFOログに記録する。
#   join_customer_master() を実行し、結果の行数をINFOログに記録する。
#   結合結果の customer_name が "未登録" である行を数え、1行以上存在する場合のみWARNINGログを出力する。
#   最終結果を customer_id の昇順に並べ替え、インデックスを振り直す。
#   終了ログをINFOで出力し、最終DataFrameを返す。

# テストケース
# テストケース1：未登録顧客が存在する場合
# 最初に、演習用の orders と customers を使用します。
# 関数の実行前に、以下のロガーを設定してください。この設定は一度だけ実行してください。
import logging
import sys

logger = logging.getLogger("order_pipeline_step4_2")
logger.setLevel(logging.INFO)
logger.propagate = False

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(
    logging.Formatter("%(levelname)s: %(message)s")
)
logger.addHandler(handler)

# その後、run_pipeline_with_logging() を実行します。
# 期待するログの例：
#   INFO: パイプラインを開始しました
#   INFO: 入力注文件数: 6件
#   INFO: 完了注文件数: 5件
#   INFO: 顧客別集計件数: 4件
#   INFO: マスタ結合後の件数: 4件
#   WARNING: 未登録顧客が1件存在します
#   INFO: パイプラインを終了しました
# 期待する最終結果：
#   customer_id	total_amount	order_count	customer_name
#   C001	27000	2	田中
#   C002	10000	1	佐藤
#   C003	6000	1	鈴木
#   C004	5000	1	未登録
# 次の項目を assert で検証してください。
#   最終DataFrameが4行であること。
#   C004の customer_name が "未登録" であること。

testcase1 = run_pipeline_with_logging(orders, customers, logger)
print(testcase1)

assert len(testcase1) == 4, "行数が異なります"
assert testcase1.loc[
    testcase1["customer_id"] == "C004", "customer_name"
].item() == "未登録", "値が異なります"

# テストケース2：未登録顧客が存在しない場合
# テストケース1の orders は変更せず、顧客マスタに C004 を追加した新しいDataFrameを作成してください。
# 例えば、customers_complete という変数名にして、C004の顧客名は "高橋" としてください。
# この新しい顧客マスタを使って、同じ run_pipeline_with_logging() を実行します。
# 期待するログの例：
#   INFO: パイプラインを開始しました
#   INFO: 入力注文件数: 6件
#   INFO: 完了注文件数: 5件
#   INFO: 顧客別集計件数: 4件
#   INFO: マスタ結合後の件数: 4件
#   INFO: パイプラインを終了しました
# このテストケースでは、WARNINGログが出力されないことが重要です。
# 期待する最終結果：
#   customer_id	total_amount	order_count	customer_name
#   C001	27000	2	田中
#   C002	10000	1	佐藤
#   C003	6000	1	鈴木
#   C004	5000	1	高橋
# 次の項目を assert で検証してください。
#   最終DataFrameが4行であること。
#   C004の customer_name が "高橋" であること。
# ログについては、実際に出力されたログを提示して確認できれば十分です。 ログ内容を自動的に検証するコードを追加する必要はありません。

customers_complete = customers.copy()
customers_complete.loc[
    len(customers_complete)] = {
    "customer_id": "C004",
    "customer_name": "高橋"
}

testcase2 = run_pipeline_with_logging(orders, customers_complete, logger)
print(testcase2)

assert len(testcase2) == 4, "行数が異なります"
assert testcase2.loc[
    testcase2["customer_id"] == "C004", "customer_name"
].item() == "高橋", "値が異なります"


### STEP 4-3｜設定管理
# STEP 4-2では、パイプラインの各工程にログを追加し、処理件数や未登録顧客の存在を確認できるようにしました。
# 今回は、パイプラインの処理条件を関数内に直接記述せず、設定値として外部から渡す方法です。
# これにより、同じパイプラインを、処理条件だけ変更して再利用できるようになります。
#
# 今回使うPython・pandasの知識
# ① ハードコーディングとは
# 例えば、STEP 4-1では次のように記述しました。
def filter_completed_orders(orders):
    completed = orders[
        orders["status"] == "completed"
    ].copy()
    return completed
# ここでは "completed" という条件を関数内に直接記述しています。
# これをハードコーディングと呼びます。
# もし "pending" の注文を抽出したい場合、関数のコード自体を修正する必要があります。
# そこで、処理条件を引数として受け取るようにします。
def filter_orders_by_status(orders, status):
    filtered = orders[
        orders["status"] == status
    ].copy()
    return filtered
# これなら、同じ関数で異なる条件を使用できます。
completed = filter_orders_by_status(orders, "completed")
pending = filter_orders_by_status(orders, "pending")
# 関数の処理内容は変更していません。
#
# ② 辞書（dict）による設定管理
# 複数の設定値をまとめて管理する場合、辞書を使用できます。
config = {
    "target_status": "completed",
    "sort_column": "customer_id",
    "ascending": True
}
# 設定値を取得するには、キーを指定します。
status = config["target_status"]
sort_column = config["sort_column"]
# このようにすれば、処理条件を1か所にまとめられます。
#
# ③ 設定値を関数に渡す
# 関数に設定辞書を渡すこともできます。
def filter_orders(orders, config):
    target_status = config["target_status"]
    result = orders[
        orders["status"] == target_status
    ].copy()
    return result
# 実行例：
config = {
    "target_status": "completed"
}
filtered = filter_orders(orders, config)
# この設計では、関数の処理ロジックと処理条件を分離できます。
#
# ④ dict.get() と dict[] の違い
# 設定値の取得方法には、主に2つあります。
config = {
    "target_status": "completed"
}
config["target_status"]      # → 指定したキーが存在しない場合、KeyError が発生します。
config.get("target_status")  # → 指定したキーが存在しない場合、None を返します。
# また、次のようにデフォルト値を指定することもできます。
status = config.get("target_status", "completed")
# この場合、target_status が存在しなければ "completed" を使用します。
# ただし、必須の設定値には config["キー名"] を使用し、設定漏れを検知する設計も有効です。
# 今回は、必要な設定が不足している場合に明確なエラーを発生させる方法を使用します。
#
# ⑤ ValueError による設定値の検証
# STEP 3で学習した例外処理の復習です。
def validate_status(status):
    allowed_statuses = ["completed", "cancelled"]
    if status not in allowed_statuses:
        raise ValueError("不正なステータスです")
    return True
# 設定値が想定外の場合、処理を開始する前にエラーを発生させられます。
# 設定管理では、設定値を受け取るだけでなく、その値が正しいかを検証することも重要です。

# 演習用データ
# 今回は、STEP 4-2と同じ注文データを使用します。
orders
customers
# 今回使用する設定辞書は以下です。
config = {
    "target_status": "completed",
    "sort_column": "customer_id",
    "ascending": True
}
# 各設定の意味は次のとおりです。
#   設定キー	        型	    用途
#   target_status	str	    抽出対象の注文ステータス
#   sort_column	    str	    最終結果の並べ替えに使用する列
#   ascending	    bool	昇順ならTrue、降順ならFalse
#
# 今回のパイプライン構成
#   設定辞書 config 抽出条件・並べ替え条件
#     ↓
#   ① 設定値の検証 validate_config()
#     ↓
#   ② 注文データの抽出 filter_orders_by_status()
#     ↓
#   ③ 顧客別集計・マスタ結合 STEP 4-1の関数を再利用
#     ↓
#   ④ 設定に従って並べ替え 最終DataFrame

# 演習要件
# 今回は、新しく3つの関数を実装してください。
# 関数① validate_config(config)
# 設定辞書を検証する関数です。
# 要件：
#   target_status、sort_column、ascending の3つのキーがすべて存在するか確認する。
#   不足しているキーがある場合、ValueError を発生させ、不足しているキー名をエラーメッセージに含める。
#   target_status が "completed" または "cancelled" のいずれかであることを確認する。
#   sort_column が "customer_id"、"total_amount"、"order_count" のいずれかであることを確認する。
#   ascending が bool 型（True または False）であることを確認する。
#   設定がすべて正しい場合は True を返す。
#   設定値が不正な場合は ValueError を発生させる。
#   target_status と sort_column は文字列型であることも必要です。許可された文字列との比較によって検証できます。

def validate_config(config):
    allowed_statuses = ["target_status", "sort_column", "ascending"]
    shortage = [key for key in allowed_statuses if key not in config]
    if shortage:
        raise ValueError(f"キー不足: {shortage}")
    else:
        check = (
            config.get("target_status") in {"completed", "cancelled"}
            and config.get("sort_column") in {"customer_id", "total_amount", "order_count"}
            and isinstance(config.get("ascending"), bool)
        )
        if not check:
            raise ValueError("設定値が不正")
    return check

# 関数② filter_orders_by_status(orders, target_status)
# 指定されたステータスの注文だけを抽出する関数です。
# 要件：
#   orders["status"] が target_status と一致するレコードを抽出する。
#   .copy() を使用してDataFrameのコピーを作成する。
#   抽出結果を返す。
# 今回は関数①で設定値を検証するため、この関数内でのステータス検証は不要です。

def filter_orders_by_status(orders, target_status):
    filtered = orders[
        orders["status"] == target_status
    ].copy()
    return filtered

# 関数③ run_pipeline_with_config(orders, customers, config)
# 設定辞書を利用して、パイプライン全体を実行する関数です。
# 要件：
#   最初に validate_config(config) を実行する。
#   config["target_status"] を使い、filter_orders_by_status() を実行する。
#   抽出結果をSTEP 4-1の aggregate_customer_orders() に渡す。
#   集計結果をSTEP 4-1の join_customer_master() に渡す。
#   config["sort_column"] と config["ascending"] を使って最終結果を並べ替える。
#   インデックスを0から振り直す。
#   最終DataFrameを返す。
# 今回は設定管理に集中するため、STEP 4-2のログ処理を組み込む必要はありません。
# また、STEP 4-1の aggregate_customer_orders() と join_customer_master() は変更せずに再利用してください。

def run_pipeline_with_config(orders, customers, config):
    validate_config(config)
    target_status = config["target_status"]
    filterd = filter_orders_by_status(orders, target_status)
    aggregate = aggregate_customer_orders(filterd)
    result = join_customer_master(aggregate, customers)
    result = result.sort_values(
        config["sort_column"],
        ascending=config["ascending"]
    )
    result = result.reset_index(drop=True)
    return result

# テストケース
# テストケース1：設定を変更して結果が変わることを確認する
# 以下の2つの設定辞書を用意してください。
config_completed = {
    "target_status": "completed",
    "sort_column": "customer_id",
    "ascending": True
}

config_cancelled = {
    "target_status": "cancelled",
    "sort_column": "total_amount",
    "ascending": False
}
# それぞれの設定を使って、run_pipeline_with_config() を実行してください。
# ① config_completed の期待結果
#   customer_id	total_amount	order_count	customer_name
#   C001	27000	2	田中
#   C002	10000	1	佐藤
#   C003	6000	1	鈴木
#   C004	5000	1	未登録
#
# ② config_cancelled の期待結果
#   customer_id	total_amount	order_count	customer_name
#   C002	8000	1	佐藤
#
# 次の項目を assert で検証してください。
#   完了注文の集計結果が4行であること。
#   キャンセル注文の集計結果が1行であること。
#   キャンセル注文の total_amount が8000であること。
#   それぞれの結果が、指定した列・昇順または降順の条件に従って並べ替えられていること。
# なお、キャンセル注文の結果は1行しかないため、降順の効果は見た目では確認できません。
# 今回は設定値を使った sort_values() の実装をコードで確認します。

testcase1_1 = run_pipeline_with_config(orders, customers, config_completed)
print(testcase1_1)

testcase1_2 = run_pipeline_with_config(orders, customers, config_cancelled)
print(testcase1_2)

assert len(testcase1_1) == 4, "行数が異なります"
assert len(testcase1_2) == 1, "行数が異なります"
assert testcase1_2["total_amount"].item() == 8000, "値が異なります"

# テストケース2：不正な設定値の検証
# 次の設定辞書を使用してください。
config_invalid = {
    "target_status": "unknown",
    "sort_column": "customer_id",
    "ascending": True
}
# validate_config(config_invalid) を実行し、ValueError が発生することを確認してください。
# 検証要件：
#   try / except ValueError を使用する。
#   ValueError が発生した場合、エラーメッセージを表示する。
#   ValueError が発生しなかった場合は、assert False などでテストを失敗させる。
#   今回は、この不正な設定辞書1種類だけをテストしてください。その他の不正パターンのテストを追加する必要はありません。

try:
    validate_config(config_invalid)
except ValueError as ve:
    print(ve)
else:
    assert False, "ValueErrorが発生しませんでした"


### STEP 4-4｜エラー処理
#
# 今回使うPython・pandasの知識
# ① try / except による例外処理
# Pythonでは、処理中に例外が発生した場合、通常はその時点で関数の実行が中断されます。
# try / except を使用すると、発生した例外を捕捉し、その内容に応じた処理を実行できます。
def divide(a, b):
    try:
        result = a / b
        return result
    except ZeroDivisionError as e:
        print(f"計算エラー: {e}")
        return None
# この例では、ゼロ除算が発生した場合に例外を捕捉し、None を返します。
#
# ② 複数の例外を捕捉する
# 例外には種類があり、原因に応じて異なる例外クラスが使用されます。
try:
    number = int("abc")
except ValueError as e:
    print(f"値が不正です: {e}")
# ValueError は、値が不正な場合などに発生する例外です。
# pandasでは、例えば merge() の結合関係が validate の指定に違反した場合、pandas.errors.MergeError が発生します。
#
# ③ logging.exception() によるエラーログ
# これまで使用した logging.info()、logging.warning()、logging.error() に加えて、例外処理で便利なのが logging.exception() です。
import logging
try:
    int("abc")
except ValueError:
    logging.exception("数値変換に失敗しました")
# logging.exception() は、エラーメッセージに加えて、例外の発生箇所を追跡するための情報も記録します。
# パイプラインでは、エラーを捕捉することと、エラー発生後に処理を継続するか中断するかを決めることが重要です。

# 演習問題
# STEP 4-3で作成した run_pipeline_with_config() にエラー処理を追加し、
# 処理が成功した場合と失敗した場合の結果を、一定の形式で返す関数を作成してください。
# STEP 4-3までに作成した以下の関数を利用します。
def validate_config(config):
    allowed_statuses = ["target_status", "sort_column", "ascending"]
    shortage = [key for key in allowed_statuses if key not in config]
    if shortage:
        raise ValueError(f"キー不足: {shortage}")
    else:
        check = (
            config.get("target_status") in {"completed", "cancelled"}
            and config.get("sort_column") in {"customer_id", "total_amount", "order_count"}
            and isinstance(config.get("ascending"), bool)
        )
        if not check:
            raise ValueError("設定値が不正")
    return check

def filter_orders_by_status(orders, target_status):
    filtered = orders[
        orders["status"] == target_status
    ].copy()
    return filtered

def aggregate_customer_orders(completed):
    aggregate = completed.groupby(
        "customer_id",
        as_index=False  # 指定したキー（ここでは customer_id）をインデックス列としない =DataFrameに含まれる通常の列とする
    ).agg(
        total_amount=("amount", "sum"),
        order_count=("order_id", "count")
    )
    return aggregate

def join_customer_master(aggregate, customers):
    joined = aggregate.merge(
        customers,
        on="customer_id",
        how="left",
        validate="many_to_one",
    )
    joined["customer_name"] = joined["customer_name"].fillna("未登録")
    return joined

def run_pipeline_with_config(orders, customers, config):
    validate_config(config)
    target_status = config["target_status"]
    filterd = filter_orders_by_status(orders, target_status)
    aggregate = aggregate_customer_orders(filterd)
    result = join_customer_master(aggregate, customers)
    result = result.sort_values(
        config["sort_column"],
        ascending=config["ascending"]
    )
    result = result.reset_index(drop=True)
    return result

# 新しく作成する関数
def run_pipeline_with_error_handling(orders, customers, config):
    report = {}
    try:
        result = run_pipeline_with_config(orders, customers, config)
    except ValueError as ve:
        report["status"] = "ERROR"
        report["data"] = None
        report["error"] = str(ve)
        logging.exception("パイプラインの処理失敗")
        return report
    except KeyError as ke:
        report["status"] = "ERROR"
        report["data"] = None
        report["error"] = f"キーが見つかりません: {str(ke)}"
        logging.exception("パイプラインの処理失敗")
        return report
    else:
        report["status"] = "OK"
        report["data"] = result
        report["error"] = None
        logging.info("パイプラインの処理完了")
    return report

# 要件
#   run_pipeline_with_config() を呼び出し、既存のパイプラインを実行する。
#   try / except を使用して、実行中に発生する ValueError と KeyError を捕捉する。
#   正常終了した場合は、次の辞書を返す。
#     status："OK"
#     data：パイプラインの処理結果（DataFrame）
#     error：None
#   例外が発生した場合は、次の辞書を返す。
#     status："ERROR"
#     data：None
#     error：発生した例外のメッセージ（文字列）
#   正常終了時は logging.info()、例外発生時は logging.exception() でログを出力する。
#   エラーが発生した場合は、後続のパイプライン処理を実行しない。
# 今回は既存の集計・結合・設定管理のロジックを書き換える必要はありません。
# 新しい関数から既存のパイプラインを呼び出し、その実行結果と例外を管理してください。

# テストケース
# テストケース①：正常終了
config1 = {
    "target_status": "completed",
    "sort_column": "total_amount",
    "ascending": False
}
result1 = run_pipeline_with_error_handling(orders, customers, config1)
print(result1)
# 期待する結果：
#   result["status"] == "OK"
#   result["data"] に処理結果のDataFrameが格納されている。
#   result["error"] is None
#   INFOログが出力される。

# テストケース②：不正な設定値
config2 = {
    "target_status": "unknown",
    "sort_column": "total_amount",
    "ascending": False
}
result2 = run_pipeline_with_error_handling(orders, customers, config2)
print(result2)
# 期待する結果：
#   result["status"] == "ERROR"
#   result["data"] is None
#   result["error"] に例外メッセージが格納されている。
#   エラーログが出力される。


### STEP 4-5｜再実行
# 今回は、一度実行したパイプラインを、同じ入力データ・同じ設定で再実行した場合に、結果が変わらないことを確認する仕組みを実装します。
#
# 今回使うPython・pandasの知識
# ① 冪等性（べきとうせい）
# データエンジニアリングでは、同じ処理を再実行することがあります。
# 例えば、パイプラインの実行中に障害が発生した場合や、処理結果を再作成したい場合です。
# 冪等性とは、同じ処理を繰り返しても、最終的な結果が変わらない性質です。
# 今回の演習では、同じ入力データと設定で2回実行し、得られたDataFrameが一致することを確認します。
# ただし、これは再実行結果の一致を確認する演習で、データベースへの重複書き込み防止などを含む冪等性ではありません。
#
# ② DataFrame.equals()
# pandasの equals() は、2つのDataFrameの内容が一致しているかを判定するメソッドです。





































