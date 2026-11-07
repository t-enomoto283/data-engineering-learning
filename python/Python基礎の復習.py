
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
def aggregate_sales(order, target_status="completed"):
    value = {}
    excluded_count = 0
    for item in order:
        if item["status"] == target_status:
            if item.get("customer_id") is None or item.get("amount") is None:
                excluded_count += 1
            else:
                customer_id = item["customer_id"]
                if customer_id not in value:
                    value[customer_id] = 0
                value[customer_id] += item["amount"]
    res = {"sales_by_customer": value, "excluded_count": excluded_count}
    return res

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


### STEP 1-3｜入力データの検証と例外処理
# データエンジニアリングでは、外部から取得したデータが必ずしも正しいとは限りません。
#
# 例えば、売上金額に文字列が混入していると集計処理でエラーになる可能性があり、今回は以下の4点を確認します。
#   1. isinstance() を使ってデータ型を検証する。
#   2. try / except を使って想定外の入力を処理する。
#   3. 不正データを除外し、理由別に件数を記録する。
#   4. 正常データだけで売上集計を継続する。
# 今回も pandasは使わず、Pythonの標準機能だけで実装してください。
#
# 演習用データ：
orders = [
    {"order_id": 1, "customer_id": "C001", "amount": 12000, "status": "completed"},
    {"order_id": 2, "customer_id": "C002", "amount": 8000, "status": "cancelled"},
    {"order_id": 3, "customer_id": "C001", "amount": 15000, "status": "completed"},
    {"order_id": 4, "customer_id": "C003", "amount": None, "status": "completed"},
    {"order_id": 5, "customer_id": "C002", "amount": "10000", "status": "completed"},
    {"order_id": 6, "customer_id": None, "amount": 9000, "status": "completed"},
    {"order_id": 7, "customer_id": "C003", "amount": -5000, "status": "completed"},
    {"order_id": 8, "customer_id": "C004", "amount": 5000, "status": "pending"},
    {"order_id": 9, "customer_id": "C001", "status": "completed"},
    {"order_id": 10, "customer_id": "C005", "amount": "abc", "status": "completed"},
    {"order_id": 11, "customer_id": "C003", "amount": 6000, "status": "completed"},
]

# 演習要件として次の関数を作成してください。
def aggregate_sales(orders, target_status="completed"):
    pass
    # ここに処理を書く

# 今回使うPythonの知識
# isinstance() による型チェック
isinstance(12000, (int, float))    # True
isinstance(12000.5, (int, float))  # True
isinstance("12000", (int, float))  # False
isinstance(True, (int, float))     # True
# 最後の True は注意点です。Pythonでは bool が int を継承しているため、別途除外する必要があります。
#
# try / except による例外処理
try:
    amount = 1000 + "500"
except TypeError:
    print("数値と文字列は加算できません")
# try 内で TypeError が発生すると、except TypeError の処理に移ります。
# ただし、データ型が不正かどうかは、基本的に isinstance() で事前に検証してください。
# すべてのエラーを try / except で処理する必要はありません。

# 要件①：ステータスによる絞り込み
# 最初に status を確認し、target_status に一致する注文だけを処理してください。
# ステータスが一致しない注文は、集計にもエラー件数にも含めません。
# 今回は、各注文に status キーが存在することを前提とします。

# 要件②：入力データの検証
# ステータスが一致した注文に対して、次の順序で検証してください。
#   順序  検証内容        不正とする条件
#   1    欠損チェック     customer_id または amount が None、もしくはキーが存在しない
#   2    金額の型チェック  amount が int または float ではない
#   3    金額の値チェック  amount が0未満
#
# 今回は customer_id が空文字列の場合や、金額が NaN・無限大の場合は検証対象外とします。
# また、bool は int のサブクラスですが、今回は金額として不正扱いにしてください。
# 1件の注文に複数の問題がある場合は、最初に該当した理由だけをカウントします。

# 要件③：エラー件数を理由別に記録
# 以下の3種類をカウントしてください。
#   キー                   意味
#   missing_count          欠損がある注文数
#   invalid_type_count     金額の型が不正な注文数
#   negative_amount_count  金額が負数の注文数

# 要件④：正常データの売上集計
# すべての検証を通過した注文だけを、customer_id ごとに集計してください。
# なお、金額が 0 の注文は正常データとして扱います。

# 期待する実行結果
# ケース1：completed注文
result = aggregate_sales(orders)
print(result)
# 期待結果：
# {
#     "sales_by_customer": {
#         "C001": 27000,
#         "C003": 6000
#     },
#     "error_counts": {
#         "missing_count": 3,
#         "invalid_type_count": 2,
#         "negative_amount_count": 1
#     }
# }
#
# ケース2：pending注文
result = aggregate_sales(orders, "pending")
print(result)
# 期待結果：
# {
#     "sales_by_customer": {
#         "C004": 5000
#     },
#     "error_counts": {
#         "missing_count": 0,
#         "invalid_type_count": 0,
#         "negative_amount_count": 0
#     }
# }


