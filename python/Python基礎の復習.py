
### STEP 1｜Python基礎の復習
# 最初は、データ処理の基本になる リスト・辞書・ループ・条件分岐・関数 を組み合わせた演習から始めます。
# ECサイトの注文データが、次のようなPythonのリストに格納されています。

orders = [
    {"order_id": 1, "customer_id": "C001", "amount": 12000, "status": "completed"},
    {"order_id": 2, "customer_id": "C002", "amount": 8000, "status": "cancelled"},
    {"order_id": 3, "customer_id": "C001", "amount": 15000, "status": "completed"},
    {"order_id": 4, "customer_id": "C003", "amount": 6000, "status": "completed"},
    {"order_id": 5, "customer_id": "C002", "amount": 10000, "status": "pending"},
    {"order_id": 6, "customer_id": "C003", "amount": 9000, "status": "completed"},
]

# 要件
# orders を受け取って、顧客別の売上合計を返す関数 aggregate_sales(orders) を作成してください。
# - status が "completed" の注文だけを集計する。
# - customer_id ごとに amount を合計する。
# - 戻り値は辞書型（dict）にする。
# - pandasは使用せず、Pythonの標準機能だけで実装する。
# 期待する結果は次のとおりです。
# {
#     "C001": 27000,
#     "C003": 15000
# }

def aggregate_sales(order):
    res = {}
    for o in order:
        if o["status"] == "completed":
            cid = o["customer_id"]
            if cid not in res:
                res[cid] = 0
            res[cid] += o["amount"]
    return res

aggregate_sales(orders)


### STEP 1-2｜関数・引数・戻り値と欠損データの処理
# データエンジニアリングでは、CSVやAPIなどから取得したデータに、欠損値や想定外の値が含まれていることがあります。
#
# 今回は、以下の3点を確認します。
#   1. 引数：集計対象のステータスを関数の外から指定する。
#   2. 欠損値：None やキーが存在しないデータを適切に処理する。
#   3. 戻り値：集計結果だけでなく、除外したデータの件数も返す。
# pandasはまだ使用しません。Pythonの標準機能で実装します。
#
# 演習用データ：
orders = [
    {"order_id": 1, "customer_id": "C001", "amount": 12000, "status": "completed"},
    {"order_id": 2, "customer_id": "C002", "amount": 8000, "status": "cancelled"},
    {"order_id": 3, "customer_id": "C001", "amount": 15000, "status": "completed"},
    {"order_id": 4, "customer_id": "C003", "amount": None, "status": "completed"},
    {"order_id": 5, "customer_id": "C002", "amount": 10000, "status": "completed"},
    {"order_id": 6, "customer_id": None, "amount": 9000, "status": "completed"},
    {"order_id": 7, "customer_id": "C003", "amount": 6000, "status": "completed"},
    {"order_id": 8, "customer_id": "C004", "amount": 5000, "status": "pending"},
    {"order_id": 9, "customer_id": "C001", "status": "completed"},
]
# 前回との違いは、customer_id や amount に欠損が含まれていることです。
# 演習要件として、以下の関数を作成してください。
def aggregate_sales(orders, target_status="completed"):
    pass
    # ここに処理を書く

# 要件①：ステータスを引数で指定する
# target_status に一致する注文だけを集計してください。
# 引数を省略した場合は "completed" を対象とします。
aggregate_sales(orders)
aggregate_sales(orders, "pending")

# 要件②：欠損データを除外する
# 次のいずれかに該当する注文は集計対象から除外してください。なお、今回は空文字列や負の金額などの検証は対象外です。
#  customer_id が None
#  amount が None
#  customer_id または amount のキー自体が存在しない

# 要件③：除外件数をカウントする
# target_status に一致する注文のうち、要件②の欠損が理由で除外した件数を数えてください。
# ステータスが一致しない注文は、除外件数に含めません。

# 要件④：辞書型で結果を返す
# 戻り値は、次の構造にしてください。
# {
#     "sales_by_customer": {
#         "C001": 27000,
#         "C002": 10000,
#         "C003": 6000
#     },
#     "excluded_count": 3
# }

# 期待する実行結果
# ケース1：completed注文を集計
result = aggregate_sales(orders)
print(result)
# 期待結果：
# {
#     "sales_by_customer": {
#         "C001": 27000,
#         "C002": 10000,
#         "C003": 6000
#     },
#     "excluded_count": 3
# }
#
# ケース2：pending注文を集計
result = aggregate_sales(orders, "pending")
print(result)
# 期待結果：
# {
#     "sales_by_customer": {
#         "C004": 5000
#     },
#     "excluded_count": 0
# }

# 実装のヒント
# 今回、新しく意識してほしいのは辞書の .get() メソッドです。
#
# 例えば、
order = {"customer_id": "C001", "status": "completed"}
print(order.get("amount"))   # None
# order["amount"] と書くと、キーが存在しない場合に KeyError が発生します。
# 一方、order.get("amount") なら、キーが存在しない場合はデフォルトで None が返ります。
#
# また、引数に初期値を指定する書き方も確認してください。
# これにより、引数を省略した場合と指定した場合で、関数の動作を変更できます。
def example(status="completed"):
    return status






