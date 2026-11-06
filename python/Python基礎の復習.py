
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

for nest in orders:
    print(nest)

for o in orders:
    print(o["order_id"], o["customer_id"], o["amount"], o["status"])

for youso in orders:
    for key, val in youso.items():
        print(key, val)


for key in {'one': 1, 'two': 2}:
  print(key)

xvec = [10, 20, 30]
yvec = [7, 5, 3]
sum(x*y for x, y in zip(xvec, yvec))  # 内積

