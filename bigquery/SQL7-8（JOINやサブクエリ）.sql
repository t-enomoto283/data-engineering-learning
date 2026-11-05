
-- STEP 7｜JOINへ
/*
まずJOIN用テーブルを1つ作り、顧客マスタ customers を追加します。
今回はJOINの挙動が分かりやすいように、注文のないcustomer 6も入れます。
これは練習問題ではなく、今後JOINを練習するための固定データセット作成です。
*/
CREATE OR REPLACE TABLE `resonant-tract-508812-p9.sql_training.customers` AS
SELECT
  1 AS customer_id,
  'Tanaka' AS customer_name,
  'Tokyo' AS prefecture
UNION ALL
SELECT
  2,
  'Sato',
  'Kanagawa'
UNION ALL
SELECT
  3,
  'Suzuki',
  'Tokyo'
UNION ALL
SELECT
  4,
  'Takahashi',
  'Chiba'
UNION ALL
SELECT
  5,
  'Ito',
  'Saitama'
UNION ALL
SELECT
  6,
  'Watanabe',
  'Tokyo';

SELECT *
FROM `resonant-tract-508812-p9.sql_training.customers`
ORDER BY customer_id ASC;

/*
STEP 7-1｜INNER JOINの構造・練習問題
今は2つのテーブルがあります。

orders_null は「注文データ」です。
order_id | customer_id | amount | ...
---------------------------------------
2001     | 1           | 5000
2002     | 1           | 3000
2003     | 2           | NULL

customers は「顧客マスタ」です。
customer_id | customer_name | prefecture
-----------------------------------------
1           | Tanaka        | Tokyo
2           | Sato          | Kanagawa
3           | Suzuki        | Tokyo

INNER JOINの基本形はこうです。
SELECT
  ...
FROM `resonant-tract-508812-p9.sql_training.orders_null` AS o
INNER JOIN `resonant-tract-508812-p9.sql_training.customers` AS c
  ON o.customer_id = c.customer_id

では最初のJOINを書いてみましょう。
orders_null と customers を INNER JOINして order_id、customer_id、customer_name、prefecture、amount を取得してください。
そして order_id の昇順にしてテーブルのエイリアスは orders_null → o、customers → c を使ってください。
customer_id は両方のテーブルに存在するので SELECTするときにも o.customer_id のようにどちらのテーブルの列なのか明示してください。
*/
SELECT
  o.order_id AS order_id,
  o.customer_id AS customer_id,
  c.customer_name AS customer_name,
  c.prefecture AS prefecture,
  o.amount AS amount
FROM `resonant-tract-508812-p9.sql_training.orders_null` AS o
INNER JOIN `resonant-tract-508812-p9.sql_training.customers` AS c
  ON o.customer_id = c.customer_id
ORDER BY order_id ASC;

/*
STEP 7-2｜INNER JOIN＋過去範囲の復習
orders_null と customers を使って、completedの注文が2件以上ある顧客を対象に、次の情報をtotal_amount の降順、同額なら customer_id の昇順で取得してください。
customer_id
customer_name
prefecture
order_count：completedの注文件数
valid_amount_count：amountがNULLでも0でもない注文件数
total_amount：amountがNULLなら0として扱った合計金額
*/
SELECT
  c.customer_id,
  c.customer_name,
  c.prefecture,
  COUNT(*) AS order_count,
  COUNT(NULLIF(o.amount, 0)) AS valid_amount_count,
  SUM(IFNULL(o.amount, 0)) AS total_amount
FROM `resonant-tract-508812-p9.sql_training.customers` AS c
INNER JOIN `resonant-tract-508812-p9.sql_training.orders_null` AS o
  ON c.customer_id = o.customer_id
WHERE o.status = 'completed'
GROUP BY c.customer_id, c.customer_name, c.prefecture
HAVING COUNT(*) >= 2
ORDER BY total_amount DESC, c.customer_id ASC;

/*
STEP 7-3｜LEFT OUTER JOINの構造・練習問題
INNER JOINは、両方に存在するものだけでした。
LEFT OUTER JOINは、左側のテーブルの行をすべて残し、右側に対応する行があれば結合し、対応する行がなければ右側の列をNULLにするというJOINです。
LEFT OUTER JOINでは、「何を必ず残したいのか？」を考えて左側を決めます。

注文が1件もない顧客も含めて、全顧客と注文情報を取得してください。
今回は customers を左側、orders_null を右側にして、customer_id でLEFT OUTER JOINしてください。
取得列は customer_id、customer_name、order_id、amount で、並び順は customer_id 昇順、order_id 昇順 としてください。
*/
SELECT
  c.customer_id, c.customer_name, o.order_id, o.amount
FROM `resonant-tract-508812-p9.sql_training.customers` AS c
LEFT OUTER JOIN `resonant-tract-508812-p9.sql_training.orders_null` AS o
  ON c.customer_id = o.customer_id
ORDER BY 1 ASC, 3 ASC;
/*上記の11行という結果は、次にやる「LEFT JOINしてからCOUNTするときの罠」につながります。
たとえば11行目 Watanabeの行は customer_id = 6、customer_name = Watanabe、order_id = NULL、amount = NULL ですよね。
この状態で顧客別に、COUNT(*) したらWatanabeは何件になるでしょうか。
一方、COUNT(o.order_id) なら何件になるでしょうか。

COUNT(*) は、結果に存在している行を数えるもので、列の中身がNULLかどうかは関係ありません。
今回 LEFT OUTER JOIN した結果、注文のないWatanabeも下記の1行が存在しますので、COUNT(*) では 1 です。
  customer_id | customer_name | order_id | amount
  6           | Watanabe      | NULL     | NULL

一方、COUNT(o.order_id) は、指定した列がNULLではない行だけ数えるものです。
Watanabeの場合、o.order_id = NULL なので、COUNT(o.order_id) は 0 になります。*/

/*
STEP 7-4｜LEFT OUTER JOIN × COUNT × NULL
customers orders_null を使い、注文が1件もない顧客も含めて、全顧客について次の4列を取得してcustomer_id の昇順にしてください。
customer_id
customer_name
row_count → LEFT OUTER JOINした結果として存在する行数
order_count → 実際に存在する注文件数
*/
SELECT
  c.customer_id,
  c.customer_name,
  COUNT(*) AS row_count,
  COUNT(o.order_id) AS order_count
FROM `resonant-tract-508812-p9.sql_training.customers` AS c
LEFT OUTER JOIN `resonant-tract-508812-p9.sql_training.orders_null` AS o
  ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.customer_name
ORDER BY 1 ASC;

/*
STEP 7-5｜LEFT OUTER JOIN × WHEREの重要な罠
次のSQLを考えてみます。
SELECT
  c.customer_id,
  c.customer_name,
  o.order_id,
  o.status
FROM `resonant-tract-508812-p9.sql_training.customers` AS c
LEFT OUTER JOIN `resonant-tract-508812-p9.sql_training.orders_null` AS o
  ON c.customer_id = o.customer_id
WHERE o.status = 'completed'
ORDER BY c.customer_id ASC, o.order_id ASC;

一見すると、全顧客を残すためにLEFT OUTER JOINして、その中からcompleted注文を取得しているように見えます。
ところが、WatanabeについてJOIN直後は customer_id = 6、customer_name = Watanabe、o.order_id = NULL、o.status = NULL です。
そのあと WHERE o.status = 'completed' を評価すると NULL = 'completed' → UNKNOWN となります。
FROM → JOIN/ON → WHERE という流れです。
上のSQLを実行した場合、LEFT OUTER JOIN の直後にはWatanabeが残っていますが
WHEREに残るのはTRUEだけでしたから、その後の WHERE o.status = 'completed' で UNKNOWN となり除外されます。

さらにもう一歩考えて、「全顧客を残したまま、completedの注文だけを結合したい」場合
WHERE o.status = 'completed' と条件を書くことに問題があるとしたら、JOINのどこに o.status = 'completed' の条件を移せばよさそうか考えてみてください。
そこで使うのは、ON句に条件を追加するという次の書き方です。
FROM `resonant-tract-508812-p9.sql_training.customers` AS c
LEFT OUTER JOIN `resonant-tract-508812-p9.sql_training.orders_null` AS o
  ON c.customer_id = o.customer_id
  AND o.status = 'completed'

JOIN において ON と WHERE では何が違うのか理解することが重要です。
ON は、どの行同士をJOINするかを決める条件です。
WHERE は、JOINした結果からどの行を残すかを決める条件です。

  ON c.customer_id = o.customer_id
  AND o.status = 'completed'
これは、customer_idが一致し、なおかつcompletedである注文だけを右側から結合するという意味になります。
Watanabeにはcompleted注文がありませんが、LEFT OUTER JOINなので
「右側に条件を満たす行がない → それでも左側のWatanabeは残す → o 側の列をNULLにする」となります。
結果としてWatanabeの行も 6 | Watanabe | NULL | NULL が残ります。
*/

/*
STEP 7-5｜実際に比較してみましょう
今回は理解を固めるため、同じ要件を2本のSQLで比較するべく、まず1つ目として次をそのまま実行してください。
SELECT
  c.customer_id,
  c.customer_name,
  o.order_id,
  o.status
FROM `resonant-tract-508812-p9.sql_training.customers` AS c
LEFT OUTER JOIN `resonant-tract-508812-p9.sql_training.orders_null` AS o
  ON c.customer_id = o.customer_id
WHERE o.status = 'completed'
ORDER BY c.customer_id ASC, o.order_id ASC;

2つ目は、次の要件に沿って自分で書いてください。
全顧客を残したまま、completedの注文だけを結合、取得列と並び順は1つ目と同じです。
説明したとおり、2つ目では WHERE ではなくON句にcompleted条件を追加してください。
*/
SELECT
  c.customer_id,
  c.customer_name,
  o.order_id,
  o.status
FROM `resonant-tract-508812-p9.sql_training.customers` AS c
LEFT OUTER JOIN `resonant-tract-508812-p9.sql_training.orders_null` AS o
  ON c.customer_id = o.customer_id
WHERE o.status = 'completed'
ORDER BY c.customer_id ASC, o.order_id ASC;

SELECT
  c.customer_id,
  c.customer_name,
  o.order_id,
  o.status
FROM `resonant-tract-508812-p9.sql_training.customers` AS c
LEFT OUTER JOIN `resonant-tract-508812-p9.sql_training.orders_null` AS o
  ON c.customer_id = o.customer_id
  AND o.status = 'completed'
ORDER BY c.customer_id ASC, o.order_id ASC;

/*
STEP 7-6｜LEFT OUTER JOIN × 集計 × NULL × CASE
customers と orders_null を使って、注文がない顧客も含む全顧客について、completedの注文だけを対象に次の列を取得してください。
customer_id
customer_name
completed_order_count：completedの実際の注文件数です。注文のないWatanabeは 0 にしてください。
valid_amount_count：completed注文のうち、amount がNULLでも0でもない件数です。
total_amount：completed注文について、amount がNULLなら0として扱って合計してください。Watanabeについても 0 と表示してください。
customer_status：completed_order_count が2件以上 → 'active'、1件 → 'low'、0件 → 'no_order'
今回は全顧客を残すので HAVING で顧客を除外する必要はなく、並び順はcompleted_order_count の降順、total_amount の降順、customer_id の昇順です。
なおtotal_amount については少し注意点があり、Watanabeのように右側に1件もマッチしなかった場合、集計関数とNULLがどうなるかを思い出して組み立ててみてください。
*/
SELECT
  c.customer_id,
  c.customer_name,
  IFNULL(COUNT(o.order_id), 0) AS completed_order_count,
  COUNT(NULLIF(o.amount, 0)) AS valid_amount_count,
  SUM(IFNULL(o.amount, 0)) AS total_amount,
  CASE
    WHEN IFNULL(COUNT(o.order_id), 0) >= 2 THEN 'active'
    WHEN IFNULL(COUNT(o.order_id), 0) = 1 THEN 'low'
    ELSE 'no_order'
  END AS customer_status
FROM `resonant-tract-508812-p9.sql_training.customers` AS c
LEFT OUTER JOIN `resonant-tract-508812-p9.sql_training.orders_null` AS o
  ON c.customer_id = o.customer_id
  AND o.status = 'completed'
GROUP BY c.customer_id, c.customer_name
ORDER BY completed_order_count DESC, total_amount DESC, c.customer_id ASC;
/*上記は completed_order_count について IFNULL(COUNT(o.order_id), 0) としており、これは結果自体は正しくなっていますが IFNULL は不要です。
COUNT(col) は、対象となる値が1件もなければ NULL ではなく必ず 0 を返すため、COUNT(o.order_id) AS completed_order_count だけでWatanabeは 0 になります。
CASEも同様に COUNT(o.order_id) で十分です。

これは以前やった SUM()、AVG() との違いとして覚えておきましょう。
たとえば「集計対象となる値がすべてNULL」の場合
COUNT(col) → 0、SUM(col) → NULL、AVG(col) → NULL となります。*/

SELECT
  c.customer_id,
  c.customer_name,
  COUNT(o.order_id) AS completed_order_count,
  COUNT(NULLIF(o.amount, 0)) AS valid_amount_count,
  SUM(IFNULL(o.amount, 0)) AS total_amount,
  CASE
    WHEN COUNT(o.order_id) >= 2 THEN 'active'
    WHEN COUNT(o.order_id) = 1 THEN 'low'
    ELSE 'no_order'
  END AS customer_status
FROM `resonant-tract-508812-p9.sql_training.customers` AS c
LEFT OUTER JOIN `resonant-tract-508812-p9.sql_training.orders_null` AS o
  ON c.customer_id = o.customer_id
  AND o.status = 'completed'
GROUP BY c.customer_id, c.customer_name
ORDER BY completed_order_count DESC, total_amount DESC, c.customer_id ASC;

/*
STEP 7-7｜LEFT OUTER JOIN 最終問題
customers と orders_null を使用して、全顧客について次の列を取得してください。
customer_id
customer_name
prefecture
completed_order_count
valid_amount_count：amountがNULLでも0でもないcompleted注文の件数
total_amount：NULLを0として扱ったcompleted注文の合計金額とし、completed注文がない顧客も0にしてください
amount_status：valid_amount_count が2件以上 → 'sufficient'、1件 → 'limited'、0件  → 'no_valid_amount'
集計対象にする注文は status = 'completed' のものだけで、全顧客を結果に残して、total_amount 降順、valid_amount_count 降順、customer_id 昇順。
*/
SELECT
  c.customer_id,
  c.customer_name,
  c.prefecture,
  COUNT(o.order_id) AS completed_order_count,
  COUNT(NULLIF(o.amount, 0)) AS valid_amount_count,
  SUM(IFNULL(o.amount, 0)) AS total_amount,
  CASE
    WHEN COUNT(NULLIF(o.amount, 0)) >= 2 THEN 'sufficient'
    WHEN COUNT(NULLIF(o.amount, 0)) = 1 THEN 'limited'
    ELSE 'no_valid_amount'
  END AS amount_status
FROM `resonant-tract-508812-p9.sql_training.customers` AS c
LEFT OUTER JOIN `resonant-tract-508812-p9.sql_training.orders_null` AS o
  ON c.customer_id = o.customer_id
  AND o.status = 'completed'
GROUP BY c.customer_id, c.customer_name, c.prefecture
ORDER BY total_amount DESC, valid_amount_count DESC, c.customer_id ASC;

/*
STEP 7-8｜RIGHT OUTER JOIN・初回問題
これまでの customers LEFT OUTER JOIN orders_null は、左側の customers は必ず残す でした。
RIGHT OUTER JOIN はその逆で、右側のテーブルの行を必ず残すJOINです。
下記ならば、右側は customers なので、全顧客が残ります。
FROM orders_null AS o
RIGHT OUTER JOIN customers AS c
  ON o.customer_id = c.customer_id

つまり上記は、下記と同じ関係を反対側から書いたものです。
FROM customers AS c
LEFT OUTER JOIN orders_null AS o
  ON c.customer_id = o.customer_id

今回は RIGHT OUTER JOIN の初回なので、JOINの配置とキーはこちらで指定します。
左側：orders_null、右側：customers、結合キー：customer_id
RIGHT OUTER JOIN を使って、注文がない顧客も含めた全顧客について、
customer_id、customer_name、order_count を取得してください。
order_count は実際に存在する注文件数として、並び順はcustomer_id 昇順です。
今回はcompletedだけに限定せず、orders_null に存在する注文をすべて数えてください。
*/
SELECT
  c.customer_id,
  c.customer_name,
  COUNT(o.order_id) AS order_count
FROM `resonant-tract-508812-p9.sql_training.orders_null` AS o
RIGHT OUTER JOIN `resonant-tract-508812-p9.sql_training.customers` AS c
  ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.customer_name
ORDER BY c.customer_id ASC;

/*
STEP 7-9｜RIGHT OUTER JOINを自分で判断する
customers と orders_null を使い、全顧客を残したまま、completed注文だけを対象として次を取得してください。
customer_id
customer_name
completed_order_count：実際に存在するcompleted注文件数
total_amount：completed注文の amount を合計し、NULLは0として扱い、completed注文がない顧客も0とする
customer_status：completed_order_count が2件以上 → 'active'、1件 → 'low'、0件 → 'no_order'
並び順は completed_order_count 降順、total_amount 降順、customer_id 昇順です。
*/
SELECT
  c.customer_id,
  c.customer_name,
  COUNT(o.order_id) AS completed_order_count,
  SUM(IFNULL(o.amount, 0)) AS total_amount,
  CASE
    WHEN COUNT(o.order_id) >= 2 THEN 'active'
    WHEN COUNT(o.order_id) = 1 THEN 'low'
    ELSE 'no_order'
  END AS customer_status
FROM `resonant-tract-508812-p9.sql_training.orders_null` AS o
RIGHT OUTER JOIN `resonant-tract-508812-p9.sql_training.customers` AS c
  ON o.customer_id = c.customer_id
  AND o.status = 'completed'
GROUP BY c.customer_id, c.customer_name
ORDER BY completed_order_count DESC, total_amount DESC, c.customer_id ASC;

/*
STEP 7-10A｜FULL OUTER JOIN・練習テーブルの作成
左にしかない行も、右にしかない行も、両方にある行も全部残すのが FULL OUTER JOIN です。
たとえば、下記をIDで結合するとします。
左テーブル       右テーブル
ID 1             ID 2
ID 2             ID 3
INNER JOIN なら 2 だけ。LEFT OUTER JOIN なら 1 と 2 です。RIGHT OUTER JOIN なら 2 と 3 です。FULL OUTER JOIN なら 1 と 2 と 3 です。

ただし今の customers、orders_null は次の状態であるため、FULL OUTER JOIN の「左右両方の不一致行を残す」という特徴を十分に確認できません。
- customers にしか存在しないcustomer_id = 6（Watanabe）はある
- orders_null にしか存在しないcustomer_idはない

そのためCREATEの復習も兼ねて、これまで使った CREATE OR REPLACE TABLE AS と UNION ALL を使って FULL OUTER JOIN練習用の小さな固定テーブルを1つ作ります。
*/

-- CREATE OR REPLACE TABLE ... AS SELECT ... UNION ALL ...
/*
1. 基本構文
CREATE OR REPLACE TABLE `プロジェクト名.データセット名.テーブル名` AS
SELECT
  列1,
  列2
FROM 元テーブル;

- CREATE → テーブルを作る
- OR REPLACE → すでに同名テーブルがあれば置き換える
- TABLE → テーブルを
- `...` → この名前で
- AS → 以下のSELECT結果を使って
- SELECT ... → テーブルの中身を作る

つまり一言でいえば、SELECTの実行結果をそのままテーブルとして保存する構文です。
例えば下記なら 元テーブルを使ったSELECT結果を completed_orders というテーブルとして作ります。
CREATE OR REPLACE TABLE `project.dataset.completed_orders` AS
SELECT
  order_id,
  customer_id,
  amount
FROM `project.dataset.orders`
WHERE status = 'completed';


2. 元テーブルがなくてもSELECTでデータを作れる
これが今回使う方法で、BigQueryでは、下記だけでも1行の結果を作れます。
SELECT
  1 AS customer_id,
  'Tanaka' AS customer_name

この結果は次のようになります。
customer_id | customer_name
1           | Tanaka

これを CREATE OR REPLACE TABLE ... AS と組み合わせれば次のような構文になり、1行だけ入ったテーブルを作れます。
CREATE OR REPLACE TABLE `project.dataset.customers` AS
SELECT
  1 AS customer_id,
  'Tanaka' AS customer_name;


3. UNION ALL で複数行にする
1つのSELECTが1行なら、次のように複数のSELECTを UNION ALL で縦につなげれば複数行にできます。
CREATE OR REPLACE TABLE `project.dataset.customers` AS
SELECT
  1 AS customer_id,
  'Tanaka' AS customer_name
UNION ALL
SELECT
  2,
  'Sato'
UNION ALL
SELECT
  3,
  'Suzuki';

ASによる列名は最初の1行目だけつければ2行目からは不要となり値のみで構いませんが、UNION ALL では列の位置を合わせる必要があります。
今回の FULL OUTER JOIN 用で作るのは下記です。
table：customer_ranks
customer_id：2, 3, 5, 7
customer_rank：silver, gold, bronze, gold
*/
CREATE OR REPLACE TABLE `resonant-tract-508812-p9.sql_training.customer_ranks` AS
SELECT
  2 AS customer_id,
  'silver' AS customer_rank
UNION ALL
SELECT
  3,
  'gold'
UNION ALL
SELECT
  5,
  'bronze'
UNION ALL
SELECT
  7,
  'gold';

SELECT * FROM `resonant-tract-508812-p9.sql_training.customer_ranks`;

/*
STEP 7-10B｜FULL OUTER JOIN 初回
現在、2つのテーブルには次のcustomer_idがあります。
customers：1, 2, 3, 4, 5, 6
customer_ranks：2, 3, 5, 7
今回は初めての FULL OUTER JOIN なので指定しますが 左側：customers、右側：customer_ranks、結合列：customer_id
下記を取得してください。
customer_id_from_customers：customers側のcustomer_id
customer_id_from_ranks：customer_ranks側のcustomer_id
customer_name
customer_rank
*/
SELECT
  c.customer_id AS customer_id_from_customers,
  r.customer_id AS customer_id_from_ranks,
  c.customer_name,
  r.customer_rank
FROM `resonant-tract-508812-p9.sql_training.customers` AS c
FULL OUTER JOIN `resonant-tract-508812-p9.sql_training.customer_ranks` AS r
  ON c.customer_id = r.customer_id;

/*
STEP 7-11｜FULL OUTER JOIN × COALESCE
先ほどの結果には少し扱いづらいところがあります。
ID 1なら customer_id_from_customers = 1、customer_id_from_ranks = NULL
ID 7なら customer_id_from_customers = NULL、customer_id_from_ranks = 7
でしたが、最終的な分析結果としては次のように1本のcustomer_id列が欲しいことがあります。
customer_id：1, 2, 3, 4, 5, 6, 7

ここで、STEP 6でやった COALESCE が再登場します。
COALESCE(値1, 値2, ...) は、左から順番に見て 最初のNULLではない値を返す でした。
したがって COALESCE(c.customer_id, r.customer_id) なら下記となります。
ID 1：COALESCE(1, NULL) → 1
ID 2：COALESCE(2, 2) → 2
ID 7：COALESCE(NULL, 7) → 7

先ほどと同じ2テーブルを使って、次の3列を取得してください。
customer_id
customer_name
customer_rank
要件として、customers にしか存在しないIDも、customer_ranks にしか存在しないIDも、両方に存在するIDもすべて取得してください。
customer_id は、どちらか一方にしか存在しない場合でもNULLにならないようにして、customer_id 昇順で並べてください。
*/
SELECT
  COALESCE(c.customer_id, r.customer_id) AS customer_id,
  c.customer_name,
  r.customer_rank
FROM `resonant-tract-508812-p9.sql_training.customers` AS c
FULL OUTER JOIN `resonant-tract-508812-p9.sql_training.customer_ranks` AS r
  ON c.customer_id = r.customer_id
ORDER BY customer_id ASC;

/*
STEP 7-12｜JOIN種類を自分で選ぶ
今後は、日本語の要件を読んで、自分でJOIN種類を選ぶ練習に移します。
次の要件を満たすSQLを書いてください。
customers と customer_ranks を使用して下記列を取得してください。
customer_id
customer_name
customer_rank
ただし対象とするのは、customers と customer_ranks の両方に存在する顧客だけとします。
さらに、customer_rank が、gold　silver のどちらかである顧客だけに絞って、customer_rank 昇順、customer_id 昇順です。
*/
SELECT
  c.customer_id,
  c.customer_name,
  r.customer_rank
FROM `resonant-tract-508812-p9.sql_training.customers` AS c
INNER JOIN `resonant-tract-508812-p9.sql_training.customer_ranks` AS r
  ON c.customer_id = r.customer_id
WHERE r.customer_rank IN ('gold', 'silver')
ORDER BY r.customer_rank ASC, c.customer_id ASC;

/*
STEP 7-13｜JOIN種類を自分で選ぶ × 集計
orders_null と customers を使い「completed注文が1件以上存在する顧客だけ」を対象として、次の列を取得し、total_amount 降順、customer_id 昇順です。
customer_id
customer_name
prefecture
completed_order_count
valid_amount_count：completed注文のうち amount がNULLでも0でもない件数
total_amount：completed注文についてNULLを0として合計
amount_category：total_amount が10000以上 → 'high'、5000以上10000未満 → 'middle'、5000未満 → 'low'
*/
SELECT
  c.customer_id,
  c.customer_name,
  c.prefecture,
  COUNT(o.order_id) AS completed_order_count,
  COUNT(NULLIF(o.amount, 0)) AS valid_amount_count,
  SUM(IFNULL(o.amount, 0)) AS total_amount,
  CASE
    WHEN SUM(IFNULL(o.amount, 0)) >= 10000 THEN 'high'
    WHEN SUM(IFNULL(o.amount, 0)) >= 5000 THEN 'middle'
    ELSE 'low'
  END AS amount_category
FROM `resonant-tract-508812-p9.sql_training.orders_null` AS o
INNER JOIN `resonant-tract-508812-p9.sql_training.customers` AS c
  ON o.customer_id = c.customer_id
  AND o.status = 'completed'
GROUP BY c.customer_id, c.customer_name, c.prefecture
HAVING COUNT(o.order_id) >= 1
ORDER BY total_amount DESC, c.customer_id ASC;
/*上記の HAVING COUNT(o.order_id) >= 1 は正しいですが、今回のデータでは省略できます。
INNER JOIN によって注文が存在する顧客だけが残り、さらに ON でcompleted注文に限定しているからです。
また、INNER JOIN では今回の o.status = 'completed' を ON に書いても WHERE に書いても同じ結果になります。
ただし、LEFT OUTER JOIN では結果が変わり得ることを忘れないでください。
*/

SELECT
  c.customer_id,
  c.customer_name,
  c.prefecture,
  COUNT(o.order_id) AS completed_order_count,
  COUNT(NULLIF(o.amount, 0)) AS valid_amount_count,
  SUM(IFNULL(o.amount, 0)) AS total_amount,
  CASE
    WHEN SUM(IFNULL(o.amount, 0)) >= 10000 THEN 'high'
    WHEN SUM(IFNULL(o.amount, 0)) >= 5000 THEN 'middle'
    ELSE 'low'
  END AS amount_category
FROM `resonant-tract-508812-p9.sql_training.orders_null` AS o
INNER JOIN `resonant-tract-508812-p9.sql_training.customers` AS c
  ON o.customer_id = c.customer_id
WHERE o.status = 'completed'
GROUP BY c.customer_id, c.customer_name, c.prefecture
ORDER BY total_amount DESC, c.customer_id ASC;

/*
STEP 7-14｜JOINの総合問題
customers と customer_ranks を使用して、customers に登録されている全顧客について、次の列を取得してください。
customer_id：顧客ID
customer_name：顧客名
customer_rank：ランク、登録がなければ 'unranked'
rank_category：goldなら 'premium'、silverなら 'standard'、それ以外は 'other'
並び順は、customer_id の昇順です。
なお、customer_ranks にしか存在しないID 7は、結果に含めないでください。
*/
SELECT
  c.customer_id,
  c.customer_name,
  IFNULL(r.customer_rank, 'unranked') AS customer_rank,
  CASE
    WHEN r.customer_rank = 'gold' THEN 'premium'
    WHEN r.customer_rank = 'silver' THEN 'standard'
    ELSE 'other'
  END AS rank_category
FROM `resonant-tract-508812-p9.sql_training.customers` AS c
LEFT OUTER JOIN `resonant-tract-508812-p9.sql_training.customer_ranks` AS r
  ON c.customer_id = r.customer_id
ORDER BY c.customer_id ASC;

/*
STEP 7-15｜JOINによる行数の増加
ここまでで4種類のJOINを学習しましたが、実務ではもう一つ重要な問題があり、JOINすると元テーブルより行数が増える場合があるということです。
たとえば、以前使用した customers と orders_null を思い出してください。

customers では、
customer_id	customer_name
1	          Tanaka
2	          Sato
3	          Suzuki

orders_null には次の注文があります。
order_id	customer_id
2001	    1
2002	    1
2003	    2
2004	    2
2005	    3
customer_id で結合すると、Tanakaは1人ですが、注文が2件あるため、結果には2行登場しますが、これは 1対多（1:N） の関係です。
特にデータ分析では、多対多（N：N）のJOINによって金額などを二重計上してしまう事故が起こり得ます。
*/

/*
STEP 7-15A｜まず予想する問題
次の2つの仮想テーブルを考えてください。
テーブルA
customer_id	category
1	          A
1	          B
2	          C

テーブルB
customer_id	score
1	          100
1	          200
1	          300
2	          400

この2つを、下記のように結合するとします。
FROM テーブルA AS a
INNER JOIN テーブルB AS b
  ON a.customer_id = b.customer_id

質問です。
- 1. customer_id = 1 の行は、JOIN後に何行になりますか？
- 2. JOIN結果全体では何行になりますか？

customer_id = 1 については、2 × 3 = 6行になります。
- テーブルA：2行（A、B）
- テーブルB：3行（100、200、300）
customer_id = 2 は、両テーブルに1行ずつなので1行です。

実際のJOIN結果は次のとおりです。
customer_id	category	score
1	          A	        100
1	          A        	200
1	          A	        300
1	          B	        100
1         	B       	200
1	          B       	300
2          	C         400

なぜデータ分析で重要なのかというと、例えばテーブルBの score を合計したい場合です。
JOIN前のテーブルBでは 100 + 200 + 300 + 400 = 1000 ですが
JOIN後に単純に SUM(score) すると 100 + 200 + 300 + 100 + 200 + 300 + 400 = 1600 になります。
JOINによって行が増え、集計値まで増えてしまうわけなので、この問題は今後のデータエンジニアリングや分析業務でも重要になります。
*/

/*
STEP 7-15B｜JOINによる二重計上を考える
先ほどと同じテーブルAとテーブルBを想定し、customer_idごとに、テーブルBのscoreの合計を取得したいとして、期待する結果は次のとおりです。
customer_id	total_score
1	          600
2	          400

ところが、次のSQLでは期待した結果になりません。
SELECT
  a.customer_id,
  SUM(b.score) AS total_score
FROM テーブルA AS a
INNER JOIN テーブルB AS b
  ON a.customer_id = b.customer_id
GROUP BY a.customer_id
ORDER BY a.customer_id ASC;

このSQLの実行結果は、下記となってしまいます。
customer_id	total_score
1         	1200
2           400

この二重計上を防ぐには、JOINする前のテーブルAまたはBに対して、どのような処理をすればよいと思いますか？
これまで学習した DISTINCT や GROUP BY が関係しますが、単純に SUM(DISTINCT score) とすれば必ず解決するわけではありません。

ここで次に学ぶ予定だった「サブクエリ」が登場します。次のSQLを見てください。
SELECT
  a.customer_id,
  SUM(b.score) AS total_score
FROM (
  SELECT DISTINCT
    customer_id
  FROM テーブルA
  ) AS a
INNER JOIN テーブルB AS b
  ON a.customer_id = b.customer_id
GROUP BY a.customer_id
ORDER BY a.customer_id ASC;

注目するのは下記で、これはFROM句の中にSELECT文を置く書き方で、括弧内のSELECTが返す結果を、ひとつの仮想的なテーブルとして扱います。
FROM (
  SELECT DISTINCT
    customer_id
  FROM テーブルA
  ) AS a

なお DISTINCT は列ではなくSELECT全体に作用するため、構文上は SELECT DISTINCT と同行に書くのが一般的です。
こうすると、customer_id = 1 は下記になるため、SUM(b.score) は正しく600になります。
- A側：1行
- B側：3行
- JOIN後：1 × 3 = 3行
ただし、これはA側からcustomer_idだけを使いたい場合の解決策です。
category も必要なら、単純に DISTINCT customer_id とするだけでは情報が失われるので、category も必要な場合は別の設計が必要です。
*/

/*
STEP 7-15C｜最後の確認問題
今回はSQLを書かずに、JOIN後の行数を予想する問題で、次の2つのテーブルがあります。

テーブルA
customer_id
1
1
1
2

テーブルB
customer_id	score
1	          100
1	          200
2	          300

この2つを、次の条件で結合します。
FROM テーブルA AS a
INNER JOIN テーブルB AS b
  ON a.customer_id = b.customer_id

問題1. そのまま INNER JOIN した場合、結果は全部で何行になるでしょうか？
問題2. JOINする前に、テーブルAに対して次の処理を行い、テーブルBと INNER JOIN した場合、結果は全部で何行になるでしょうか？
FROM(
  SELECT DISTINCT
    customer_id
  FROM テーブルA
  ) AS a
INNER JOIN テーブルB AS b
  ON a.customer_id = b.customer_id

重要なのは、JOINでは値の種類の数ではなく、結合条件を満たす「行」同士の組み合わせを数えることです。
問題1. DISTINCTせずにINNER JOIN
customer_id	A側の行数	B側の行数	JOIN後
1	          3        2        6
2           1        1        1
合計                           7

問題2. A側をDISTINCTしてからINNER JOIN
customer_id	A側の行数	B側の行数	JOIN後
1           1        2        2
2           1        1        1
合計                           3
*/


-- STEP 8｜サブクエリ
/*
ここからは、先ほどの[STEP 7-15B]で少し登場したサブクエリを基礎から学習します。
サブクエリとは、SQL文の中に別のSELECT文を入れることです。
例えば、これまでのSQLは次のような形でした。
SELECT
  customer_id,
  amount
FROM `resonant-tract-508812-p9.sql_training.orders_null`;

サブクエリを使うと、次のように書けます。
SELECT
  customer_id,
  amount
FROM (
  SELECT
    customer_id,
    amount
  FROM `resonant-tract-508812-p9.sql_training.orders_null`
  WHERE status = 'completed'
  ) AS o
ORDER BY customer_id ASC;

このSQLは、内側のSELECTでcompleted注文を取得し、その結果を外側のSELECTが参照しています。
処理のイメージは次のとおりです。
- 1. 内側のSELECT：orders_null からcompleted注文を抽出
- 2. サブクエリの結果：completed注文だけを持つ仮想的なテーブル o
- 3. 外側のSELECT：必要な列を取得し、並び替える

上記のようにFROM句に書くサブクエリは、一般に「FROM句のサブクエリ（派生テーブル）」と呼ばれます。
ただしサブクエリはFROM句以外の場所にも書けますので、それらは順番に学習していきましょう。
*/

/*
STEP 8-1｜最初の練習問題
使用するテーブルは、これまでの orders_null です。
要まず内側のSELECTで、status = 'completed' の注文について order_id、customer_id、amount の3列を取得してください。
その結果を外側のSELECTから参照し、同じ3列を取得して、最後に order_id の昇順で並べてください。
この問題は通常のWHERE句だけでも解けますが、今回はあえてサブクエリを使い、構文とインデントに慣れることが目的です。
*/
SELECT
  order_id,
  customer_id,
  amount
FROM (
  SELECT
    order_id,
    customer_id,
    amount
  FROM `resonant-tract-508812-p9.sql_training.orders_null`
  WHERE status = 'completed'
) AS o
ORDER BY 1 ASC;

/*
STEP 8-2｜FROM句のサブクエリ × GROUP BY・練習問題
今回は、内側のSELECTで集計を行い、その集計結果を外側のSELECTで利用する練習で、次のような処理です。
- 1. 内側のSELECT：顧客ごとのcompleted注文の合計金額を集計する
- 2. サブクエリの結果：customer_id と total_amount を持つ仮想的なテーブル
- 3. 外側のSELECT：集計結果から、合計金額が一定以上の顧客を取得する
これによって、集計処理と、その集計結果に対する処理を分けて記述できます。

練習問題として orders_null を使い、completed注文について、顧客ごとの合計金額を集計し、合計金額が8,000円以上の顧客だけを次の2列で取得してください。
customer_id：顧客ID
total_amount：completed注文の合計金額で、NULLは0として扱う

次の2段階に分けて処理してください。
内側のSELECT
- completed注文だけを対象にする。
- customer_id ごとに集計する。
- SUM とNULL処理を使って total_amount を求める。

外側のSELECT
- 内側で求めた total_amount が8,000以上の行だけを取得する。
- total_amount の降順、次に customer_id の昇順で並べる。

今回は、外側のWHERE句で集計済みの列を絞り込むのがポイントです。
内側のSELECTで集計が完了しているため、外側ではその結果の total_amount を通常の列として扱えます。
なお、この要件はサブクエリを使わず GROUP BY, HAVING でも実現できますが、今回はサブクエリの練習です。
*/
SELECT
  customer_id,
  total_amount
FROM (
  SELECT
    customer_id,
    SUM(IFNULL(amount, 0)) AS total_amount
  FROM `resonant-tract-508812-p9.sql_training.orders_null`
  WHERE status = 'completed'
  GROUP BY customer_id
) AS o
WHERE total_amount >= 8000
ORDER BY total_amount DESC, customer_id ASC;
/*以前学習した HAVING との違いも整理しておきましょう。
どちらが常に優れているというわけではなく、処理を段階的に分けたいときサブクエリが役立ちます。
                    HAVING                       サブクエリの外側のWHERE
何を絞り込むか         GROUP BY後のグループ           内側のSELECTが返した行
集計関数を直接使えるか   使える                       外側で新たに集計しない限り使わない
今回の条件             HAVING SUM(...) >= 8000     WHERE total_amount >= 8000*/
SELECT
  customer_id,
  SUM(IFNULL(amount, 0)) AS total_amount
FROM `resonant-tract-508812-p9.sql_training.orders_null`
GROUP BY customer_id
HAVING SUM(IFNULL(amount, 0)) >= 8000
ORDER BY 2 DESC, 1 ASC;

/*
STEP 8-3｜サブクエリ × JOIN × 集計
orders_null と customers を使用して、completed注文の合計金額が8,000円以上の顧客について、次の列をtotal_amount の降順、customer_id の昇順で取得してください。
- customer_id：顧客ID
- customer_name：顧客名
- prefecture：都道府県
- completed_order_count：completed注文件数
- total_amount：completed注文の合計金額。NULLは0として扱う
サブクエリでは、orders_null を使って顧客ごとのcompleted注文件数と合計金額を集計します。
その集計結果を customers とJOINし、顧客名と都道府県を取得してください。
最後に、合計金額が8,000以上の顧客だけを残します。
*/
SELECT
  o.customer_id,
  c.customer_name,
  c.prefecture,
  o.completed_order_count,
  o.total_amount
FROM (
  SELECT
    customer_id,
    COUNT(order_id) AS completed_order_count,
    SUM(IFNULL(amount, 0)) AS total_amount
  FROM `resonant-tract-508812-p9.sql_training.orders_null`
  WHERE status = 'completed'
  GROUP BY customer_id
) AS o
INNER JOIN `resonant-tract-508812-p9.sql_training.customers` AS c
  ON o.customer_id = c.customer_id
WHERE o.total_amount >= 8000
ORDER BY o.total_amount DESC, o.customer_id ASC;

/*
STEP 8-4｜WHERE句のサブクエリ・練習問題
次はWHERE句の中にSELECT文を書く方法で、例えば「全注文の平均金額よりも、金額が大きい注文を取得したい」とします。

平均金額を固定値で書くなら、次のようなSQLになります。
SELECT
  order_id,
  amount
FROM `resonant-tract-508812-p9.sql_training.orders_null`
WHERE amount > 5000;

しかし今回知りたいのは5,000円を超える注文ではなく、実際のデータから計算した平均金額を超える注文です。
そこで次のように、WHERE句にサブクエリを使います。
SELECT
  order_id,
  amount
FROM `resonant-tract-508812-p9.sql_training.orders_null`
WHERE amount > (
  SELECT
    AVG(amount)
  FROM `resonant-tract-508812-p9.sql_training.orders_null`
);

なおこのとき AVG(amount) はNULLを集計対象から除外します。
上記の内側のSELECTは、1行1列の値を返し、このようなサブクエリを スカラーサブクエリ と呼びます。

練習問題として orders_null を使い、completed注文の平均金額よりも、金額が大きいcompleted注文を取得してください。
取得する列は order_id、customer_id、amount の3列です。
平均金額の計算にはWHERE句のスカラーサブクエリを使用、金額の降順、次に注文IDの昇順で並べ、平均金額と等しい注文は含めない。
*/
SELECT
  order_id,
  customer_id,
  amount
FROM `resonant-tract-508812-p9.sql_training.orders_null`
WHERE amount > (
  SELECT
    AVG(amount)
  FROM `resonant-tract-508812-p9.sql_training.orders_null`
  WHERE status = 'completed'
)
  AND status = 'completed'
ORDER BY amount DESC, order_id ASC;

/*
STEP 8-5｜スカラーサブクエリの復習と応用
ひとつ前では「平均金額より大きい注文」を取得しましたが、今回は 平均金額との差額 も表示することを考えます。
ここで新しく覚えるのは、スカラーサブクエリはWHERE句だけでなく、「SELECT句にも書ける」ということで、例えば次のクエリです。
SELECT
  order_id,
  amount,
  (
    SELECT
      AVG(amount)
    FROM `resonant-tract-508812-p9.sql_training.orders_null`
  ) AS avg_amount
FROM `resonant-tract-508812-p9.sql_training.orders_null`;

この場合、avg_amount という列に、サブクエリで計算した平均金額が表示されます。
SELECT句に置いたスカラーサブクエリは、外側の各行に対して1つの値を返す式として使えます。

練習問題として orders_null を使い、completed注文の平均金額と、各注文金額との差額を表示する。
取得列は order_id、customer_id、amount、difference_from_avg：注文金額 − completed注文の平均金額
金額がNULLの注文は除外し、difference_from_avg の降順、次に order_id の昇順で並べる。
平均金額を超えていない注文も表示、差額がマイナスでも構わない。
*/
SELECT
  order_id,
  customer_id,
  amount,
  amount - (
    SELECT
      AVG(amount)
    FROM `resonant-tract-508812-p9.sql_training.orders_null`
    WHERE status = 'completed'
  ) AS difference_from_avg
FROM `resonant-tract-508812-p9.sql_training.orders_null`
WHERE status = 'completed'
  AND amount IS NOT NULL
ORDER BY difference_from_avg DESC, order_id ASC;

/*
STEP 8-6｜WHERE句のサブクエリ × IN
次は、複数行の値を返すサブクエリです。
例えば「注文履歴がある顧客だけを、顧客マスタから取得したい」とします。
この場合、次のように WHERE句に IN とサブクエリを組み合わせることができます。
SELECT
  customer_id,
  customer_name
FROM `resonant-tract-508812-p9.sql_training.customers`
WHERE customer_id IN (
  SELECT
    customer_id
  FROM `resonant-tract-508812-p9.sql_training.orders_null`
);

内側のSELECTは、注文テーブルから顧客IDを取得します。
この結果には同じ顧客IDが複数回登場する可能性がありますが、IN は値が含まれているかどうかを判定するため、重複があっても外側の顧客行は増えません。
ここがJOINとの重要な違いです。

練習問題として customers と orders_null を使用し、completed注文を1件以上持つ東京都在住の顧客を取得してください。
取得する列は customer_id、customer_name、prefecture の3列です。
今回はJOINを使用せず、顧客IDの昇順で並べる。
*/
SELECT
  customer_id,
  customer_name,
  prefecture
FROM `resonant-tract-508812-p9.sql_training.customers`
WHERE customer_id IN (
  SELECT
    customer_id
  FROM `resonant-tract-508812-p9.sql_training.orders_null`
  WHERE status = 'completed'
)
  AND prefecture = 'Tokyo'
ORDER BY customer_id ASC;

/*
STEP 8-7｜WHERE句のサブクエリ × NOT IN
IN が「含まれているか」を判定するのに対し、NOT IN は「含まれていないか」を判定します。
例えば次のクエリでは、注文テーブルに顧客IDが存在しない顧客を取得できます。
WHERE customer_id NOT IN (
  SELECT
    customer_id
  FROM `resonant-tract-508812-p9.sql_training.orders_null`
)

ただし NOT IN にはNULLに関する注意点があり、サブクエリの結果にNULLが含まれると、想定どおりに行が取得できない場合があります。
例えば、下記のような条件では、customer_id = 3 であっても、判定結果はTRUEではなくNULL（UNKNOWN）となり、WHERE句を通過しません。
WHERE customer_id NOT IN (1, 2, NULL)

この性質はSTEP 6で学習したNULLの3値論理とつながっています。
なお、今回使用する orders_null の customer_id にはNULLがないため、まずは基本的な NOT IN を練習します。

練習問題として completed注文を1件も持たない顧客を取得してください。
使用するテーブルは customers と orders_null で customer_id、customer_name、prefecture の3列で顧客IDの昇順で並べる。
- customers を外側のSELECTで使用、orders_null を内側のSELECTで使用する。
- NOT IN とサブクエリを使用する。
- キャンセル注文はcompleted注文として数えず、都道府県による絞り込みはせず、JOINは使用しない。
*/
SELECT
  customer_id,
  customer_name,
  prefecture
FROM `resonant-tract-508812-p9.sql_training.customers`
WHERE customer_id NOT IN (
  SELECT
    customer_id
  FROM `resonant-tract-508812-p9.sql_training.orders_null`
  WHERE status = 'completed'
)
ORDER BY customer_id ASC;

/*
STEP 8-8｜NOT INとNULLの関係
先ほど説明した NOT IN の注意点を、実際に確認してみましょう。
1. NULLが含まれない場合
SELECT
  customer_id,
  customer_name
FROM `resonant-tract-508812-p9.sql_training.customers`
WHERE customer_id NOT IN (1, 2);
この場合、顧客IDが1でも2でもない顧客を取得できます。

2. NULLが含まれる場合
SELECT
  customer_id,
  customer_name
FROM `resonant-tract-508812-p9.sql_training.customers`
WHERE customer_id NOT IN (1, 2, NULL);
こちらはどうなるでしょうか。
SQLの3値論理では、例えば顧客ID3について
3 NOT IN (1, 2, NULL)

これは、概念的には次の条件と同じです。
3 != 1
  AND 3 != 2
  AND 3 != NULL
最後の 3 != NULL でTRUEでもFALSEでもなく、NULL（UNKNOWN）になります。
そのため、条件結果がUNKNOWNとなり、WHERE句では除外されます。
つまり、NOT INの比較対象にNULLが含まれると、意図しない結果になる可能性があります。

確認問題として、実行結果を予測します。
次のSQLを実行した場合、何行取得されると思いますか？
問題1.
SELECT
  customer_id
FROM `resonant-tract-508812-p9.sql_training.customers`
WHERE customer_id NOT IN (1, 2, 3);
customers は customer_id が UNIQUEで1～6だったため、NOT IN (1, 2, 3) により 4, 5, 6 の3行が取得されます。

問題2.
SELECT
  customer_id
FROM `resonant-tract-508812-p9.sql_training.customers`
WHERE customer_id NOT IN (1, 2, 3, NULL);
WHERE は条件で TRUE の値のみを返しますが、NOT IN (1, 2, 3, NULL) では customer_id 1～6 は下記となるので、0行が取得されます。
  1 != 1 AND 1 != 2 AND 1 != 3 AND 1 != NULL → {1 != 1} の時点で FALSE
  2 != 1 AND 2 != 2 AND 2 != 3 AND 2 != NULL → {2 != 2} の時点で FALSE
  3 != 1 AND 3 != 2 AND 3 != 3 AND 3 != NULL → {3 != 3} の時点で FALSE
  4 != 1 AND 4 != 2 AND 4 != 3 AND 4 != NULL → UNKNOWN
  5 != 1 AND 5 != 2 AND 5 != 3 AND 5 != NULL → UNKNOWN
  6 != 1 AND 6 != 2 AND 6 != 3 AND 6 != NULL → UNKNOWN
*/

/*
STEP 8-9｜EXISTSの基礎
EXISTS は、サブクエリの結果が1行以上存在するかどうかを判定する構文です。
IN との違いを確認しましょう。
            IN                     EXISTS
判定内容      値が集合に含まれるか      サブクエリが1行以上返すか
着目するもの   比較する値              行の存在
典型的な用途   指定されたIDに該当するか  関連するデータが存在するか

今回は新しく、相関サブクエリという考え方が登場します。
相関サブクエリは、例えば次のように、内側のSELECTが外側のSELECTの列を参照するサブクエリです。
SELECT
  c.customer_id,
  c.customer_name
FROM `resonant-tract-508812-p9.sql_training.customers` AS c
WHERE EXISTS (
  SELECT
    1
  FROM `resonant-tract-508812-p9.sql_training.orders_null` AS o
  WHERE o.customer_id = c.customer_id
);

注目するのは、内側のWHERE句 WHERE o.customer_id = c.customer_id です。
o.customer_id は内側の orders_null の列、c.customer_id は外側の customers の列
つまり、外側の顧客に対応する注文が存在するかどうかを調べています。
なお、SELECT 1 は、EXISTSでよく使われる書き方で、EXISTSは返される列の値ではなく行の存在を判定するため、通常は SELECT 1 で十分です。

概念的には、次のような判定になりますが、これはあくまで論理的な理解のための説明であり、BigQueryが物理的に必ず顧客を1行ずつ処理するという意味ではありません。
外側の顧客：Tanaka（customer_id = 1）
- orders_null に customer_id = 1 の注文は存在するか？
  存在する → EXISTSはTRUE
外側の顧客：Watanabe（customer_id = 6）
- orders_null に customer_id = 6 の注文は存在するか？
  存在しない → EXISTSはFALSE

練習問題として customers と orders_null を使い、completed注文を1件以上持つ顧客を取得してください。
取得列は customer_id、customer_name、prefecture の3列で、JOINやINは使用せず、都道府県による絞り込みはせず、顧客IDの昇順で並べる。
外側のSELECTは customers、内側のSELECTは orders_null、EXISTS を使いcompleted注文が存在するか判定、内側のSELECTから外側の customer_id を参照する。
ポイントは、内側のWHERE句に2つの条件が必要になることで、1つは外側の顧客と内側の注文を対応づける条件、もう1つは注文ステータスの条件です。
*/
SELECT
  c.customer_id,
  c.customer_name,
  c.prefecture
FROM `resonant-tract-508812-p9.sql_training.customers` AS c
WHERE EXISTS (
  SELECT
    1
  FROM `resonant-tract-508812-p9.sql_training.orders_null` AS o
  WHERE o.customer_id = c.customer_id
    AND o.status = 'completed'
)
ORDER BY c.customer_id ASC;
/*上記の EXISTS (...) 部分には2つの条件があります。
  条件                             役割
  o.customer_id = c.customer_id   外側の顧客と内側の注文を対応づける（相関サブクエリ）
  o.status = 'completed'          completed注文だけを存在判定の対象にする
この両方を満たす注文が1行以上存在すれば、EXISTS はTRUEになります。

また、EXISTSでは注文が何件あっても顧客行は増えません。
例えば、Tanaka（顧客ID1）にはcompleted注文が2件あります。
しかし、EXISTS が確認するのは、あくまで条件に合う行が存在するかどうかです。
そのため、Tanakaは2行ではなく1行だけ取得されます。
一方で、Watanabe（顧客ID6）には注文がないため、取得されません。*/

/*
STEP 8-10｜NOT EXISTS
NOT EXISTS は、[条件に合う行が1行も存在しない場合]にTRUEになります。
基本形は次の通りで、このSQLでは注文履歴が1件も存在しない顧客を取得します。
SELECT
  c.customer_id,
  c.customer_name
FROM `resonant-tract-508812-p9.sql_training.customers` AS c
WHERE NOT EXISTS (
  SELECT
    1
  FROM `resonant-tract-508812-p9.sql_training.orders_null` AS o
  WHERE o.customer_id = c.customer_id
);

[STEP 8-8]では、WHERE customer_id NOT IN (1, 2, NULL) のように NOT IN は比較対象にNULLが含まれると意図しない結果になる可能性があると学習しました。
例えば customer_id = 3 NOT IN (1, 2, NULL) は概念的に 3 != 1 AND 3 != 2 AND 3 != NULL → [最後の 3 != NULL] で UNKNOWNになるという話です。
一方、NOT EXISTS はサブクエリが返す行の有無を判定します。
                 NOT IN                 NOT EXISTS
判定対象          値が集合に含まれないか     条件に合う「行」が存在しないか
サブクエリのNULL   結果に影響する場合がある   SELECT で返す値がNULLでも、行の存在判定には影響しない
相関条件          必須ではない             今回の使い方では外側の列を参照する

ただし NOT EXISTS でも内側のWHERE条件にNULLが関係すれば、その条件の評価には影響します。
つまり NOT EXISTS でも NULLを一切気にしなくてよいという意味ではありません。

練習問題として、customers と orders_null を使い、completed注文を1件も持たない顧客の customer_id、customer_name、prefecture を取得してください。
NOT EXISTS と相関サブクエリを使用し、JOIN と IN と NOT INは使用せず、顧客IDの昇順で並べる。
*/
SELECT
  c.customer_id,
  c.customer_name,
  c.prefecture
FROM `resonant-tract-508812-p9.sql_training.customers` AS c
WHERE NOT EXISTS (
  SELECT
    1
  FROM `resonant-tract-508812-p9.sql_training.orders_null` AS o
  WHERE o.customer_id = c.customer_id
    AND o.status = 'completed'
)
ORDER BY c.customer_id ASC;
/*また追加の確認問題として、仮に orders_null に次の1行が追加された場合、今回のSQLの取得結果はどう変わりますか？
order_id  customer_id  amount  status
2011      6            3000    cancelled

まず [WHERE o.customer_id = c.customer_id AND o.status = 'completed'] の条件において、追加された行はo.statusの条件でFALSEです。
追加された行は、この条件結果によってFALSEで行が出てこない → NOT EXISTS で TRUEとなり、今回のSQLの取得結果で得られます。*/

/*
STEP 8-11｜相関サブクエリ × 集計
これまでの EXISTS / NOT EXISTS では、外側の顧客に対応する注文が存在するか/存在しないかを調べました。
今回は、外側の顧客に対応する注文の平均金額を計算する方法を学びます。
次の「相関スカラーサブクエリ」を見てください。
SELECT
  c.customer_id,
  c.customer_name,
  (
    SELECT
      AVG(o.amount)
    FROM `resonant-tract-508812-p9.sql_training.orders_null` AS o
    WHERE o.customer_id = c.customer_id
  ) AS avg_amount
FROM `resonant-tract-508812-p9.sql_training.customers` AS c
ORDER BY c.customer_id ASC;

注目するのは WHERE o.customer_id = c.customer_id の条件で、これは外側の c.customer_id を使って、顧客ごとの平均注文金額を計算しています。

これまでの EXISTS と異なり、今回は内側のSELECTが AVG() によって1つの値を返しており、このようなSQLを相関スカラーサブクエリと呼びます。
なお、BigQueryが実際に顧客ごとにサブクエリを繰り返し実行するとは限らず、ここではSQLの論理的な意味を学んでいます。

練習問題として customers と orders_null を使い、すべての顧客についてcompleted注文の平均金額を取得してください。
取得列は customer_id、customer_name、avg_completed_amount：completed注文の平均金額 の3列です。
平均金額はcompleted注文のみから計算し、completed注文が存在しない顧客も表示し、平均を計算できない場合はNULLのまま表示する。
JOINは使用せず、顧客IDの昇順で並べる。
*/
SELECT
  c.customer_id,
  c.customer_name,
  (
    SELECT
      AVG(o.amount)
    FROM `resonant-tract-508812-p9.sql_training.orders_null` AS o
    WHERE o.customer_id = c.customer_id
      AND o.status = 'completed'
  ) AS avg_completed_amount
FROM `resonant-tract-508812-p9.sql_training.customers` AS c
ORDER BY c.customer_id ASC;

/*
STEP 8-12｜相関サブクエリ × 顧客別平均との比較
[STEP 8-4]では、全顧客のcompleted注文の平均金額より高い注文を抽出しましたが、今回はその注文をした顧客自身の平均金額より高い注文を抽出します。
例えば、Tanakaのcompleted注文は次の2件です。
order_id  amount
2001      5000
2002      3000
Tanaka自身の平均金額は4,000円なので、注文2001だけが対象になります。

練習問題として orders_null を使い、各顧客についてその顧客自身のcompleted注文の平均金額よりも高いcompleted注文を取得してください。
取得列は order_id、customer_id、amount で、customer_id の昇順、次に amount の降順、最後に order_id の昇順で並べる。
JOINは使用せず、WHERE句に相関スカラーサブクエリを使用し、amount が平均金額と等しい場合とNULLの場合は取得しない。
*/
SELECT
  o1.order_id,
  o1.customer_id,
  o1.amount
FROM `resonant-tract-508812-p9.sql_training.orders_null` AS o1
WHERE o1.amount > (
  SELECT
    AVG(o2.amount)
  FROM `resonant-tract-508812-p9.sql_training.orders_null` AS o2
  WHERE o2.customer_id = o1.customer_id
    AND o2.status = 'completed'
)
  AND o1.status = 'completed'
ORDER BY o1.customer_id ASC, o1.amount DESC, o1.order_id ASC;

/*
STEP 8-13｜サブクエリの総合演習
ここまでで、次の構文を学習しました。
- FROM句のサブクエリ、WHERE句のスカラーサブクエリ、SELECT句のスカラーサブクエリ、IN / NOT IN、EXISTS / NOT EXISTS、相関サブクエリ
今回は、これらを組み合わせる総合問題です。

顧客マスタに登録されているすべての顧客について、completed注文の集計結果を次の5列で取得してください。
customer_id
customer_name
completed_order_count：completed注文件数
total_amount：completed注文の合計金額
amount_category：合計金額が10,000円以上	high、5,000円以上10,000円未満	middle、5,000円未満	low

completed注文がない顧客も必ず表示し、合計金額の降順、次に顧客IDの昇順で並べる。
completed注文件数が0件なら completed_order_count = 0 に、completed注文の金額がすべてNULLの場合とcompleted注文がない顧客の合計金額は0とする。
今回は必ずFROM句のサブクエリを使用し、サブクエリで注文データを集計してから顧客マスタと結合する構成を考えてみてください。
*/
SELECT
  c.customer_id,
  c.customer_name,
  IFNULL(o.completed_order_count, 0) AS completed_order_count,
  IFNULL(o.total_amount, 0) AS total_amount,
  CASE
    WHEN IFNULL(o.total_amount, 0) >= 10000 THEN 'high'
    WHEN IFNULL(o.total_amount, 0) >= 5000 THEN 'middle'
    ELSE 'low'
  END AS amount_category
FROM (
  SELECT
    customer_id,
    COUNT(order_id) AS completed_order_count,
    SUM(IFNULL(amount, 0)) AS total_amount
  FROM `resonant-tract-508812-p9.sql_training.orders_null`
  WHERE status = 'completed'
  GROUP BY customer_id
) AS o
RIGHT OUTER JOIN `resonant-tract-508812-p9.sql_training.customers` AS c
  ON c.customer_id = o.customer_id
ORDER BY total_amount DESC, c.customer_id ASC;





