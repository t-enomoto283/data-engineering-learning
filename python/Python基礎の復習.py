
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




