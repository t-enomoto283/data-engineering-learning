
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
    missing_count = 0
    invalid_type_count = 0
    negative_amount_count = 0
    values = {}
    for item in orders:
        if item["status"] == target_status:
            if item.get("customer_id") is None or item.get("amount") is None:
                missing_count += 1
            elif not isinstance(item["amount"], (int, float)) or isinstance(item["amount"], bool):
                invalid_type_count += 1
            elif item["amount"] < 0:
                negative_amount_count += 1
            else:
                customer_id = item["customer_id"]
                if customer_id not in values:
                    values[customer_id] = 0
                values[customer_id] += item["amount"]
    errors = {
        "missing_count": missing_count,
        "invalid_type_count": invalid_type_count,
        "negative_amount_count": negative_amount_count
    }
    result = {"sales_by_customer": values, "error_counts": errors}
    return result

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


### STEP 1-4｜関数の分割・再利用と処理結果の管理
# これまでは、1つの aggregate_sales() 関数の中に、データの検証と売上集計の両方を書いていました。
# しかし、実務のデータパイプラインでは、処理を役割ごとに分けることが重要で、今回は次の3点を学びます。
#   1. 関数の分割：データ検証と売上集計を別々の関数にする。
#   2. 戻り値の活用：検証関数が返した結果を、別の関数で利用する。
#   3. 再利用性：同じ検証処理を複数のデータに対して使えるようにする。
# 今回もpandasは使わず、Pythonの標準機能だけで実装します。
#
# 今回使うPythonの知識
# ① 関数から複数の値を返す
# Pythonでは、return で複数の値を返せます。
def calculate(a, b):
    total = a + b
    difference = a - b
    return total, difference

result1, result2 = calculate(10, 3)
print(result1)  # 13
print(result2)  # 7
# 実際には、複数の値がタプルとして返されています。
result = calculate(10, 3)
print(result)  # (13, 7)
#
# ② 関数の戻り値を別の関数で利用する
def double_number(number):
    return number * 2

def add_ten(number):
    doubled = double_number(number)
    return doubled + 10

print(add_ten(5))  # 20
# add_ten() の内部で double_number() を呼び出しています。
# このように関数を組み合わせることで、処理を役割ごとに分けられます。
#
# ③ continue によるループのスキップ
numbers = [10, -5, 20, -3, 30]
for number in numbers:
    if number < 0:
        continue
    print(number, end=' ')  # 10 20 30
# continue が実行されると、その回のループの残りの処理を飛ばして、次の要素に進みます。
# データ処理では、不正なレコードを除外するときに便利です。
#
# ④ 辞書型の戻り値を利用する
def check_amount(amount):
    if amount < 0:
        return {"valid": False, "reason": "negative"}
    return {"valid": True, "reason": None}

result = check_amount(-100)
print(result["valid"])   # False
print(result["reason"])  # negative
# 今回の演習では、これと似た考え方で、検証結果を集計関数へ渡します。

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

# 演習要件として今回は、次の2つの関数を作成してください。
def validate_order(item):
    """注文データを検証する関数"""
    if item.get("customer_id") is None or item.get("amount") is None:
        return {"valid": False, "reason": "missing"}
    elif not isinstance(item["amount"], (int, float)) or isinstance(item["amount"], bool):
        return {"valid": False, "reason": "invalid_type"}
    elif item["amount"] < 0:
        return {"valid": False, "reason": "negative_amount"}
    else:
        return {"valid": True, "reason": None}

def aggregate_sales(items, target_status="completed"):
    """検証結果を使って売上を集計する関数"""
    missing_count = 0
    invalid_type_count = 0
    negative_amount_count = 0
    values = {}
    for item in items:
        if item["status"] == target_status:
            valid_results = validate_order(item)
            if valid_results.get("reason") == "missing":
                missing_count += 1
            elif valid_results.get("reason") == "invalid_type":
                invalid_type_count += 1
            elif valid_results.get("reason") == "negative_amount":
                negative_amount_count += 1
            elif valid_results["valid"] is True:
                customer_id = item["customer_id"]
                if customer_id not in values:
                    values[customer_id] = 0
                values[customer_id] += item["amount"]
    errors = {
        "missing_count": missing_count,
        "invalid_type_count": invalid_type_count,
        "negative_amount_count": negative_amount_count
    }
    result = {"sales_by_customer": values, "error_counts": errors}
    return result

# 要件①：validate_order() の作成
# 1件の注文データを受け取り、次の順序で検証してください。
#   検証順序  条件                              reason
#   1       customer_id または amount が欠損    "missing"
#   2       amount がint・float以外、またはbool  "invalid_type"
#   3       amount が負数                      "negative_amount"
#   4       すべて正常                          None
#
# 欠損には、キー自体が存在しない場合も含めます。空文字列・NaN・無限大は今回も検証対象外です。
# 戻り値は次の構造にしてください。
# 正常な場合：
# {"valid": True, "reason": None}
#
# 不正な場合（例：金額が負数）：
# {"valid": False, "reason": "negative_amount"}

# 要件②：aggregate_sales() の作成
# aggregate_sales() は、次の順序で処理してください。
  # 1. target_status に一致する注文だけを対象とする。
  # 2. 対象の注文を validate_order() に渡して検証する。
  # 3. 不正な注文は、reason に対応するエラー件数を1増やし、売上集計から除外する。
  # 4. 正常な注文は、customer_id ごとに amount を合計する。
# ステータスが一致しない注文は、検証対象にもエラー件数にも含めません。
# なお、今回は try / except の使用は必須ではありません。

# 期待する実行結果
# ケース1：completed注文
print(aggregate_sales(orders))
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
print(aggregate_sales(orders, "pending"))
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

# 今回のポイント
# 検証処理を集計処理から独立させることが最も重要です。
#   aggregate_sales()：対象ステータスの絞り込み・集計管理
#     ↓
#   validate_order()：注文1件の品質チェック
#     ↓
#   検証結果を返す：valid / reason
#     ↓
#   aggregate_sales() が結果を処理：正常なら集計、不正ならエラー件数を更新


### STEP 1-5｜例外処理とファイル操作の基礎
# 今回は、PythonでCSVファイルを読み込む際の「例外処理（try / except）」を学びます。
# データエンジニアリングでは、外部ファイルの読み込み時に、ファイルが存在しない、データ形式が不正などの問題が発生します。
#
# 今回使うPythonの知識
# ① try / except
# Pythonでは、処理中に例外が発生すると、通常はその時点で処理が中断されます。
# try / except を使うと、特定の例外を捕捉して適切に処理できます。
try:
    number = int("abc")
except ValueError:
    print("数値に変換できません")
# int("abc") では ValueError が発生しますが、except ValueError で捕捉しています。
#
# ② 複数の例外を捕捉する
def divide(a, b):
    try:
        return a / b
    except ZeroDivisionError:
        return "0では割れません"
    except TypeError:
        return "数値を指定してください"
# 例外の種類に応じて、異なる処理を実行できます。
# 今回も、ファイルの読み込みで発生する例外を区別します。
#
# ③ open() と with
# Python標準の open() を使うと、ファイルを読み込めます。
with open("sample.txt", "r", encoding="utf-8") as file:
    content = file.read()
print(content)
# "r"：読み込みモード
# encoding="utf-8"：文字コードを指定
# with：処理が終了したらファイルを自動的に閉じる
#
# ④ csv.DictReader
# CSVファイルを辞書形式で読み込むには、標準ライブラリの csv を使います。
# 例えば、次のCSVがあるとします。
#   customer_id,amount
#   C001,12000
#   C002,8000
# 読み込みコード：
import csv
with open("sample.csv", "r", encoding="utf-8") as file:
    reader = csv.DictReader(file)
    rows = list(reader)
print(rows)
# 実行結果：
# [
#     {"customer_id": "C001", "amount": "12000"},
#     {"customer_id": "C002", "amount": "8000"}
# ]
# 重要なのは、csv.DictReader で読み込んだ値は基本的に文字列になることです。
# そのため、数値として扱うには int() や float() で変換する必要があります。
#
# ⑤ raiseによる例外の発生
# raise を使うと、自分で例外を発生させることができます。
def check_amount(amount):
    if amount < 0:
        raise ValueError("金額は0以上である必要があります")
    return amount
# 今回は、CSVに必要な列が存在しない場合に raise ValueError(...) を使用します。

# 演習用データ：
# order_id,customer_id,amount,status
# 1,C001,12000,completed
# 2,C002,8000,cancelled
# 3,C001,15000,completed
# 4,C003,6000,completed
# この.pyファイルと同じディレクトリに、上記内容の orders.csv を設置済。
# 今回はCSVを読み込む処理が対象なので、pandasは使用しません。

# 演習要件として次の関数を作成してください。
def load_orders_csv(file_path):
    required_columns = ["order_id", "customer_id", "amount", "status"]
    result = []
    import csv
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            dict_csv = csv.DictReader(file)
            if not dict_csv.fieldnames or not all(column in dict_csv.fieldnames for column in required_columns):
                raise ValueError
            for row in dict_csv:
                row["amount"] = int(row["amount"])
                result.append(row)
    except FileNotFoundError:
        print("ファイルが存在しません")
        return None
    except ValueError:
        print("CSVデータが不正です")
        raise
    return result

# 要件①：CSVファイルの読み込み
# file_path で指定されたCSVファイルを、csv.DictReader を使用して読み込んでください。
# 読み込んだデータは、辞書のリストに変換します。

# 要件②：必須列の検証
# CSVに以下の4列が存在するかを検証してください。
# required_columns = [
#     "order_id",
#     "customer_id",
#     "amount",
#     "status"
# ]
# 1列でも存在しない場合は、ValueError を発生させてください。
# 今回は、列の存在確認だけを対象とします。列の順序は問いません。余分な列が存在していても問題ありません。

# 要件③：amountの数値変換
# CSVから読み込んだ amount を整数（int）に変換してください。
# 変換できない値があった場合は、その ValueError を呼び出し側に伝えてください。
# 今回は不正な行のスキップやエラー件数の集計は行いません。

# 要件④：例外処理
# 関数の内部では、次の例外を捕捉してください。
#   例外                発生する状況                            処理
#   FileNotFoundError  指定したCSVファイルが存在しない            "ファイルが存在しません" と表示して None を返す
#   ValueError         必須列が不足、または金額が整数に変換できない  "CSVデータが不正です" と表示したうえで、raise で例外を再送出する
# ここでの raise は、捕捉した例外を呼び出し側へそのまま伝えるために使用します。

# テストケース
# ケース1：正常なCSVファイル
result = load_orders_csv("orders.csv")
print(result)
# 期待結果：
# [
#     {"order_id": "1", "customer_id": "C001", "amount": 12000, "status": "completed"},
#     {"order_id": "2", "customer_id": "C002", "amount": 8000, "status": "cancelled"},
#     {"order_id": "3", "customer_id": "C001", "amount": 15000, "status": "completed"},
#     {"order_id": "4", "customer_id": "C003", "amount": 6000, "status": "completed"}
# ]
#
# ケース2：存在しないCSVファイル
result = load_orders_csv("not_found.csv")
print(result)
# 期待結果：
# ファイルが存在しません
# None

# 実装のヒント
# CSVの列名は、csv.DictReader の fieldnames で取得できます。
reader = csv.DictReader(file)
print(reader.fieldnames)
#
# また、必須列がすべて存在するかは、次のような考え方で確認できます。
all(column in reader.fieldnames for column in required_columns)
# all() は、すべての条件が True の場合に True を返します。
#
# 例外の再送出は、次の構造を参考にしてください。
try:
    # ファイル読み込みやデータ変換
    ...
except FileNotFoundError:
    # ファイルが存在しない場合
    ...
except ValueError:
    # データ不正の場合
    raise


### STEP 1-6｜Python基礎の総合演習：CSV読み込み・検証・売上集計
# 今回は、CSVの読み込みからデータ検証、売上集計、処理結果の返却までを一連の処理として実装します。
# 実務のデータパイプラインを意識して、次の流れを実装します。
#   CSVファイル：注文データの入力
#     ↓
#   load_orders_csv()：読み込み・必須列チェック・数値変換
#     ↓
#   aggregate_sales()：ステータス絞り込み・注文検証・集計
#     ↓
#   run_pipeline()： 処理全体を管理し、結果を返す

# 今回使うPythonの知識
# ① 関数を組み合わせて処理を実行する
# STEP 1-4で学んだ、関数の分割と再利用です。
def multiply(a, b):
    return a * b

def calculate(a, b):
    result = multiply(a, b)
    return {"result": result}

print(calculate(3, 4))  # {'result': 12}
# 今回も、すでに作成した関数を別の関数から呼び出します。
#
# ② 関数の戻り値が None か確認する
# STEP 1-5では、ファイルが存在しない場合に None を返しました。
data = load_orders_csv(file_path)
if data is None:
    # ファイル読み込みに失敗した場合
    ...
# None と比較するときは、is None を使用します。
#
# ③ 辞書から値を取り出して新しい辞書を作る
result = {
    "sales_by_customer": {"C001": 12000},
    "error_counts": {"missing_count": 0}
}

pipeline_result = {
    "status": "success",
    "sales": result["sales_by_customer"],
    "errors": result["error_counts"]
}
# このように、既存の関数が返した辞書を使って、処理全体の結果を組み立てられます。
#
# ④ 例外を呼び出し側で捕捉する
# STEP 1-5で学んだ raise の復習です。
def convert_number(value):
    return int(value)

def process(value):
    try:
        return convert_number(value)
    except ValueError:
        return {"status": "error"}
# convert_number() で発生した ValueError は、呼び出し側の process() で捕捉できます。
# 今回はこの仕組みを利用します。

# 演習用データ：
# STEP 1-5で使用した、下記内容の orders.csv をそのまま使います。 新しいCSVファイルを作成する必要はありません。
#   order_id,customer_id,amount,status
#   1,C001,12000,completed
#   2,C002,8000,cancelled
#   3,C001,15000,completed
#   4,C003,6000,completed
# このCSVには不正データが含まれていないため、正常に読み込んだ場合、データ検証のエラー件数はすべて0になります。

# 演習要件として今回は、これまで作成した次の3つの関数を再利用します。
def load_orders_csv(file_path):
    ...

def validate_order(item):
    ...

def aggregate_sales(items, target_status="completed"):
    ...

# 上の3つはSTEP 1-4、1-5で完成させた関数を利用して構いません。
# 今回、新たに作成する関数は次の1つです。
def run_pipeline(file_path, target_status="completed"):
    ...

# 要件①：CSVの読み込み
# run_pipeline() の中から load_orders_csv(file_path) を呼び出してください。
# CSVが存在しない場合、load_orders_csv() は None を返します。
# その場合は、次の辞書を返してください。
# {
#     "status": "error",
#     "message": "file_not_found",
#     "sales_by_customer": {},
#     "error_counts": {}
# }

# 要件②：売上集計
# CSVを正常に読み込めた場合は、aggregate_sales() を呼び出してください。
# その際、run_pipeline() に渡された target_status を、そのまま aggregate_sales() に渡してください。

# 要件③：正常時の戻り値
# 集計が成功した場合は、次の構造で返してください。
# {
#     "status": "success",
#     "message": None,
#     "sales_by_customer": {
#         "C001": 27000,
#         "C003": 6000
#     },
#     "error_counts": {
#         "missing_count": 0,
#         "invalid_type_count": 0,
#         "negative_amount_count": 0
#     }
# }

# 要件④：ValueErrorの処理
# load_orders_csv() で ValueError が発生した場合は、run_pipeline() 側で捕捉してください。
# その場合は、次の辞書を返してください。
# {
#     "status": "error",
#     "message": "invalid_csv",
#     "sales_by_customer": {},
#     "error_counts": {}
# }
# STEP 1-5の load_orders_csv() 自体は変更せず、再送出された例外を run_pipeline() で処理する設計です。

# 要件⑤：処理の役割を分離する
# 各関数の役割は次のようにしてください。run_pipeline() の中に、CSV読み込みや顧客別集計の処理を重複して実装しないでください。
#   関数	                担当する処理
#   load_orders_csv()	CSV読み込み、必須列チェック、金額の整数変換
#   validate_order()	注文1件のデータ検証
#   aggregate_sales()	注文の絞り込み、検証、顧客別集計
#   run_pipeline()      各処理の呼び出し、成功・失敗の結果管理

# テストケース1：正常なCSVファイル
result = run_pipeline("orders.csv")
print(result)
# 期待結果：
# {
#     "status": "success",
#     "message": None,
#     "sales_by_customer": {
#         "C001": 27000,
#         "C003": 6000
#     },
#     "error_counts": {
#         "missing_count": 0,
#         "invalid_type_count": 0,
#         "negative_amount_count": 0
#     }
# }

# テストケース2：存在しないCSVファイル
result = run_pipeline("not_found.csv")
print(result)
# 期待結果：
# ファイルが存在しません
# {'status': 'error', 'message': 'file_not_found', 'sales_by_customer': {}, 'error_counts': {}}

# 実装のヒント
# 今回は、run_pipeline() が全体の制御役です。
# 処理の流れは以下のようになります。
#   1. try の中でCSV読み込み関数を呼び出す。
#   2. ValueError が発生したら、エラー結果を返す。
#   3. 読み込み結果が None なら、ファイル未存在のエラー結果を返す。
#   4. それ以外なら売上集計関数を呼び出す。
#   5. 集計結果から必要な値を取り出し、成功結果の辞書を返す。
# なお、ファイルが存在しない場合と、CSVの内容が不正な場合は、異なるエラーとして扱うことがポイントです。
