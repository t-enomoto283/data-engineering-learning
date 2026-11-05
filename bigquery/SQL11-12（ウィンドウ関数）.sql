-- STEP 11｜ウィンドウ関数
/*
例えば、次の注文データがあるとします。
  order_id  customer_id  amount
  1001      1            3,200
  1002      2            5,800
  1003      1            2,100
  1005      2            4,200

SELECT
  customer_id,
  SUM(amount) AS total_amount
FROM `resonant-tract-508812-p9.sql_training.orders`
WHERE order_id IN (1001, 1002, 1003, 1005)
GROUP BY customer_id
ORDER BY customer_id ASC;

GROUP BYの場合、もともと4行の注文データが結果で顧客単位の2行に集約されます。
  customer_id  total_amount
  1            5,300
  2            10,000

ウィンドウ関数の場合、次のような書き方です。
SELECT
  order_id,
  customer_id,
  amount,
  SUM(amount) OVER (
    PARTITION BY customer_id
  ) AS customer_total_amount
FROM `resonant-tract-508812-p9.sql_training.orders`
WHERE order_id IN (1001, 1002, 1003, 1005)
ORDER BY order_id ASC;

結果は次のようになり、GROUP BYは行を集約しますが、ウィンドウ関数は元の行を残したまま集計結果を付与できます。
  order_id  customer_id  amount  customer_total_amount
  1001      1            3,200   5,300
  1002      2            5,800   10,000
  1003      1            2,100   5,300
  1005      2            4,200   10,000

また PARTITION BY を省略すれば絞り込み後の全行を対象に計算しますので、例えば次のように SUM(amount) OVER () とすれば全注文の合計金額を各行に付与できます。
SELECT
  order_id,
  customer_id,
  amount,
  SUM(amount) OVER ()
FROM `resonant-tract-508812-p9.sql_training.orders`
WHERE order_id IN (1001, 1002, 1003, 1005)
ORDER BY order_id ASC;

練習問題として orders を使い、completed注文だけを取得し、各注文行に、その注文を行った顧客の合計購入金額を付与してください。
取得列は order_id、customer_id、order_date、amount、customer_total_amount：同じ顧客のcompleted注文の合計金額
SUM() OVER (PARTITION BY ...) を使用。GROUP BY は使用しない。JOIN・CTE・サブクエリは使用しない。注文IDの昇順で並べる。
*/
SELECT
  order_id,
  customer_id,
  order_date,
  amount,
  SUM(amount) OVER (
    PARTITION BY customer_id
  ) AS customer_total_amount
FROM `resonant-tract-508812-p9.sql_training.orders`
WHERE status = 'completed'
ORDER BY order_id ASC;
/*追加の確認問題
今回のSQLでは、次のように指定します。
  SUM(amount) OVER (PARTITION BY customer_id)
これを次のように変更した場合、結果は各注文行に表示される金額がどう変わるのか、また結果の行数がどうなるのかを説明してください。
  SUM(amount) OVER ()
各行の金額にはordersからWHERE句による絞り込み後の[全注文の合計額]が表示され、結果の行数は10行で変わりません。*/

/*
STEP 11-2｜OVER句のORDER BYと累積合計
次は、ウィンドウ関数の中で ORDER BY を使用します。
OVER() の中で指定する ORDER BY はウィンドウ関数が計算の順序を決定する役割で、例えば次のSQLです。
SELECT
  order_id,
  customer_id,
  order_date,
  amount,
  SUM(amount) OVER (
    PARTITION BY customer_id
    ORDER BY order_date ASC, order_id ASC
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
  ) AS cumulative_amount
FROM `resonant-tract-508812-p9.sql_training.orders`
WHERE status = 'completed'
ORDER BY customer_id ASC, order_date ASC, order_id ASC;

新しく登場したのが次の部分で、これは各行についてその顧客の最初の行から現在の行までを計算対象にするという指定です。
  ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
ROWS：行単位で計算範囲を指定
UNBOUNDED PRECEDING：パーティションの最初の行
CURRENT ROW：現在の行

BigQueryでは SUM() OVER (ORDER BY ...) のようにフレーム指定を省略すると、通常は RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW となる。
RANGE は同じ並び順の値を持つ行をまとめて扱うため ROWS と結果が異なる場合がありますが、今回は行単位の累積計算を明確にするために ROWS を指定します。

練習問題として orders のcompleted注文について、顧客別の累積購入金額を計算してください。
order_id、customer_id、order_date、amount、customer_total_amount：顧客別の合計購入金額、cumulative_amount：顧客別の累積購入金額
cumulative_amount は顧客ごとに注文日の昇順で累積計算し、同じ顧客で注文日が同じ場合は、注文IDの昇順で計算する。
JOIN・CTE・サブクエリ・GROUP BYは使用せず、最終結果は顧客ID 注文日 注文IDの昇順で並べる。*/
SELECT
  order_id,
  customer_id,
  order_date,
  amount,
  SUM(amount) OVER (
    PARTITION BY customer_id
  ) AS customer_total_amount,
  SUM(amount) OVER (
    PARTITION BY customer_id
    ORDER BY order_date ASC, order_id ASC
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
  ) AS cumulative_amount
FROM `resonant-tract-508812-p9.sql_training.orders`
WHERE status = 'completed'
ORDER BY customer_id ASC, order_date ASC, order_id ASC;
/*追加の確認問題
次の2つのSQLはどのような違いがあるか、特に同じ顧客の注文が4件あった場合それぞれの注文行にどのような金額が表示されるのか説明してください。
A：SUM(amount) OVER (
  PARTITION BY customer_id
  )
B：SUM(amount) OVER (
  PARTITION BY customer_id
  ORDER BY order_date ASC, order_id ASC
  ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
  )

Aは、customer_idごとにamountが合計され、同じ顧客の注文が4件あった場合はその4件の合計額が、同じ顧客の4行にそれぞれ表示されます。
Bは、customer_idごとのamountが最初の行から現在の行まで累計され、同じ顧客の注文が4件あった場合は行単位の累積計算された金額が、同じ顧客の各行に表示される。*/

/*
STEP 11-3｜ROW_NUMBER・RANK・DENSE_RANK
次は、ウィンドウ関数を使った順位付けで、SQLには順位を計算するための代表的な関数が3つあります。
  ROW_NUMBER()：同順位を作らず、各行に連番を付ける
  RANK()：同順位を認め、次の順位を飛ばす
  DENSE_RANK()：同順位を認め、次の順位を飛ばさない

例えば、次の売上データがあるとします。
  customer_id  amount
  1            10,000
  2            8,000
  3            8,000
  4            5,000

売上金額の降順で順位を付けると、次のようになります。
  customer_id	amount  ROW_NUMBER  RANK  DENSE_RANK
  1           10,000  1           1     1
  2           8,000   2           2     2
  3           8,000   3           2     2
  4           5,000   4           4     3

ROW_NUMBER() は対象が同じ値でも異なる番号を付けるもので、同値の行のどちらが先になるかは追加の並び順を指定しない限り保証されません。
一方、RANK() と DENSE_RANK() は同値なら同順位になります。

基本構文は次です。
  ROW_NUMBER() OVER (ORDER BY amount DESC)
  RANK() OVER (ORDER BY amount DESC)
  DENSE_RANK() OVER (ORDER BY amount DESC)

PARTITION BY と組み合わせることができ、例えば顧客ごとに注文金額の高い順に順位を付けるなら次のようにします。
  RANK() OVER (PARTITION BY customer_id ORDER BY amount DESC)

練習問題として、同額の注文が存在する次のCTE sample_orders を使用して注文金額の順位付けします。
WITH sample_orders AS (
  SELECT 1 AS order_id, 1 AS customer_id, 5000 AS amount
  UNION ALL
  SELECT 2, 1, 3000
  UNION ALL
  SELECT 3, 1, 3000
  UNION ALL
  SELECT 4, 1, 1000
  UNION ALL
  SELECT 5, 2, 8000
  UNION ALL
  SELECT 6, 2, 8000
  UNION ALL
  SELECT 7, 2, 4000)
顧客ごとに注文金額の高い順で、3種類の順位を付けてください。
order_id、customer_id、amount、row_number：顧客別の連番、rank：顧客別の順位（同順位OK・飛び番OK）、dense_rank：顧客別の順位（同順位OK・飛び番NG）
GROUP BY は使用しない。顧客ごとに順位を計算する。金額の高い順に順位を付ける。最終結果は顧客IDの昇順と金額の降順と注文IDの昇順で並べる。
ROW_NUMBER() で同額の場合は注文IDの小さい行を先にする。RANK() と DENSE_RANK() では同額の注文が同順位になるようにする。
ROW_NUMBER() の並び順と、RANK()・DENSE_RANK() の並び順を同じにする必要はありません。
*/
WITH sample_orders AS (
  SELECT
    1 AS order_id, 1 AS customer_id, 5000 AS amount
  UNION ALL
  SELECT
    2, 1, 3000
  UNION ALL
  SELECT
    3, 1, 3000
  UNION ALL
  SELECT
    4, 1, 1000
  UNION ALL
  SELECT
    5, 2, 8000
  UNION ALL
  SELECT
    6, 2, 8000
  UNION ALL
  SELECT
    7, 2, 4000
)
SELECT
  order_id,
  customer_id,
  amount,
  ROW_NUMBER() OVER (
    PARTITION BY customer_id
    ORDER BY amount DESC, order_id ASC
  ) AS row_number,
  RANK() OVER (
    PARTITION BY customer_id
    ORDER BY amount DESC
  ) AS rank,
  DENSE_RANK() OVER (
    PARTITION BY customer_id
    ORDER BY amount DESC
  ) AS dense_rank
FROM sample_orders
ORDER BY customer_id ASC, amount DESC, order_id ASC;
/*追加の確認問題
顧客ID1には、次の4件の注文があります。
order_id：1, 2, 3, 4
amount：5000, 3000, 3000, 1000
このとき 注文ID4 の順位はそれぞれ何位になりますか？またなぜ3種類の順位に違いが生じるのかも説明してください。
- ROW_NUMBER()：
- RANK()：
- DENSE_RANK()：

ROW_NUMBER() の 注文ID4 は 顧客ID1 において4位で、ROW_NUMBER()が同順位を作らず各行に連番を付けるため、amountの降順で 1位 → 2位 → 3位 → 4位 です。
RANK() の 注文ID4 も 顧客ID1 において4位ですが、RANK()は同順位を認めて次の順位を飛ばすため、amountの降順で 1位 → 2位 → 2位 → 4位 です。
DENSE_RANK() の 注文ID4 は 顧客ID1 において3位で、DENSE_RANK()は同順位を認めて次の順位を飛ばさないため、amountの降順で 1位 → 2位 → 2位 → 3位 です。*/

/*
STEP 11-4｜ウィンドウ関数で上位N件を抽出する
次は、実務でもよく使う「グループごとの上位N件を取得する」処理で、例えば顧客ごとに購入金額が高い注文を2件ずつ取得するといった場面です。
ここで重要なのは、ウィンドウ関数の計算結果をどのように絞り込むかです。

BigQueryでは、次のSQLのようにWHERE句でウィンドウ関数を直接使うことはできずエラーになります。
理由は、WHERE句はウィンドウ関数の計算より前に評価されるため row_number が未定義とみなされるからです。
SELECT
  order_id,
  customer_id,
  amount,
  ROW_NUMBER() OVER (
    PARTITION BY customer_id
    ORDER BY amount DESC, order_id ASC
  ) AS row_number
FROM `resonant-tract-508812-p9.sql_training.orders`
WHERE row_number <= 2;

ウィンドウ関数で計算した順位を絞り込む方法には、主に次の2つがあります。

方法1：CTEまたはサブクエリ
一度順位を計算してから、外側のSELECTで絞り込みます。
WITH ranked_orders AS (
  SELECT
    order_id,
    customer_id,
    amount,
    ROW_NUMBER() OVER (
      PARTITION BY customer_id
      ORDER BY amount DESC, order_id ASC
    ) AS row_number
  FROM `resonant-tract-508812-p9.sql_training.orders`
  WHERE status = 'completed'
)
SELECT
  order_id,
  customer_id,
  amount,
  row_number
FROM ranked_orders
WHERE row_number <= 2
ORDER BY customer_id ASC, row_number ASC;

SELECT
  order_id,
  customer_id,
  amount,
  row_number
FROM (
  SELECT
    order_id,
    customer_id,
    amount,
    ROW_NUMBER() OVER (
      PARTITION BY customer_id
      ORDER BY amount DESC, order_id ASC
    ) AS row_number
  FROM `resonant-tract-508812-p9.sql_training.orders`
  WHERE status = 'completed'
)
WHERE row_number <= 2
ORDER BY customer_id ASC, row_number ASC;

方法2：QUALIFY句
BigQueryでは、QUALIFY を使ってウィンドウ関数の結果を直接絞り込むことができ、SELECT句で定義したウィンドウ関数の別名をQUALIFYで参照できます。
SELECT
  order_id,
  customer_id,
  amount,
  ROW_NUMBER() OVER (
    PARTITION BY customer_id
    ORDER BY amount DESC, order_id ASC
  ) AS row_number
FROM `resonant-tract-508812-p9.sql_training.orders`
WHERE status = 'completed'
QUALIFY row_number <= 2
ORDER BY customer_id ASC, row_number ASC;

QUALIFY はウィンドウ関数の計算後に条件を適用するもので、SELECT句で定義したウィンドウ関数の別名をQUALIFY句で直接参照できます。
なお、QUALIFY はBigQueryで使用できますが、すべてのデータベース製品で使用できるわけではありません。
  句       絞り込み対象
  WHERE    集計・ウィンドウ計算前の行
  HAVING   GROUP BYで集計した結果
  QUALIFY  ウィンドウ関数で計算した結果

練習問題として orders を使い、今回は順位付けと過去に学習したCTEを組み合わせ、顧客ごとにcompleted注文の中から購入金額が高い注文を最大2件ずつ取得。
取得列は customer_id、order_id、order_date、amount、order_rank：顧客別の注文金額順位
顧客ごとに金額の降順で順位を付ける。同額の場合は注文IDの昇順で順位を決める。順位は1位・2位のみ取得。顧客にcompleted注文が1件しかなければその1件だけ取得。
今回はCTEを使用して実装する。ROW_NUMBER() を使用する。最終結果は顧客IDの昇順、順位の昇順で並べる。
*/
WITH ranked_orders AS (
  SELECT
    customer_id,
    order_id,
    order_date,
    amount,
    ROW_NUMBER() OVER (
      PARTITION BY customer_id
      ORDER BY amount DESC, order_id ASC
    ) AS order_rank
  FROM `resonant-tract-508812-p9.sql_training.orders`
  WHERE status = 'completed'
)
SELECT
  customer_id,
  order_id,
  order_date,
  amount,
  order_rank
FROM ranked_orders
WHERE order_rank <= 2
ORDER BY customer_id ASC, order_rank ASC;

SELECT
  customer_id,
  order_id,
  order_date,
  amount,
  ROW_NUMBER() OVER (
    PARTITION BY customer_id
    ORDER BY amount DESC, order_id ASC
  ) AS order_rank
FROM `resonant-tract-508812-p9.sql_training.orders`
WHERE status = 'completed'
QUALIFY order_rank <= 2
ORDER BY customer_id ASC, order_rank ASC;
/*追加の確認問題
次の2つのSQLについて、今回の問題でAとBを同じSELECT文のWHERE句にまとめられないのはなぜか？また QUALIFY を使うとCTEを書かずに同じ処理を実現できるのはなぜか？
  A：WHERE status = 'completed'
  B：WHERE order_rank <= 2

status は orders で既に存在しますが、order_rank は ROW_NUMBER() のウィンドウ関数による列です。
FROM句の次にWHERE句が評価されるため、順序として同じSELECT文のWHERE句に status と order_rank を一緒にできず、order_rank は未定義とみなされエラーです。
QUALIFY はウィンドウ関数の計算後に評価されるため、order_rank <= 2 といった ROW_NUMBER() の結果をもとにした条件を指定できます。*/

/*
STEP 11-5｜ウィンドウ関数と集計結果の組み合わせ
今回は、GROUP BYで集計した結果に対してウィンドウ関数を使用する練習です。
これまでの問題では注文行に直接順位を付けていましたが、実務では「顧客ごとの売上合計を求め、その売上合計で順位を付ける」という処理もよくあります。
例えば、次の2段階です。
  1. 顧客ごとにcompleted注文の合計金額を求める。
  2. その合計金額を使って、顧客の売上順位を計算する。

練習問題として customers と orders を使い、顧客マスタの全顧客について、2026年1月〜3月のcompleted注文の合計金額を集計し、売上金額の高い順に順位付け。
取得列は customer_id、customer_name、completed_order_count：completed注文件数、total_amount：completed注文の合計金額
sales_rank：売上金額による順位、sales_share_pct：全顧客の売上合計に対する構成比（%）

注文件数と合計金額のNULLは0にする。sales_rank は売上金額の降順で RANK() を使用する。同額の売上金額なら同順位にする。
sales_share_pct は total_amount / 全顧客のtotal_amount × 100 で計算。SUM(...) OVER () は集計後の各顧客行に全顧客の売上合計を付与するためにも使用可能。
構成比は小数第2位まで四捨五入。CTEを2つ以上使用。最終結果は売上順位の昇順、顧客IDの昇順で並べる。
*/
WITH completed_order AS (
  SELECT
    customer_id,
    COUNT(order_id) AS completed_order_count,
    SUM(amount) AS total_amount
  FROM `resonant-tract-508812-p9.sql_training.orders`
  WHERE status = 'completed'
    AND (order_date >= DATE '2026-01-01' AND order_date < DATE '2026-04-01')
  GROUP BY customer_id
),
joined_customer AS (
  SELECT
    c.customer_id,
    c.customer_name,
    IFNULL(o.completed_order_count, 0) AS completed_order_count,
    IFNULL(o.total_amount, 0) AS total_amount
  FROM completed_order AS o
  RIGHT OUTER JOIN `resonant-tract-508812-p9.sql_training.customers` AS c
    ON o.customer_id = c.customer_id
)
SELECT
  customer_id,
  customer_name,
  completed_order_count,
  total_amount,
  RANK() OVER (
    ORDER BY total_amount DESC
  ) AS sales_rank,
  ROUND(
    total_amount / SUM(total_amount) OVER () * 100,
    2
  ) AS sales_share_pct
FROM joined_customer
ORDER BY sales_rank ASC, customer_id ASC;
/*追加の確認問題
次の2つの方法はどの段階の行を計算対象としているかが異なりますが、今回の sales_share_pct を計算する際にどのような違いがあるでしょうか？
  A. 集計後の顧客別売上に対して計算：SUM(total_amount) OVER ()
  B. 注文テーブルに対して直接計算：SUM(amount) OVER ()
今回の要件では、なぜAの考え方が適切なのかを説明してください。また、Bでも同じ全体売上を求められる条件があるか考えてみてください。

Aは顧客別に集計した結果を対象に全顧客の売上合計を求めるもので、今回であれば6行が計算対象で、Aでは60,800円になります。
Bは注文テーブルの行を対象に金額を合計するもので、WHEREで status = 'completed' かつ2026年1月～3月の期間を指定すれば、Aと同じように60,800円になります。
重要なのは集計対象の注文の範囲が一致しJOINなどによる行の重複発生がないことですが、今回の最終結果は顧客別の6行なのでその処理段階に自然に対応するのはAです。*/

/*
STEP 11-6｜ウィンドウ関数の復習と応用
これまで学習したウィンドウ関数を組み合わせます。
今回は顧客ごとの最新注文を1件取得し、その注文金額が顧客の累計売上に占める割合を計算する問題です。

customers と orders を使い、全顧客の2026年1〜3月のcompleted注文のうち各顧客の最新注文を1件取得し、その注文額がその顧客のcompleted注文合計額に占める割合を計算。
  customer_id
  customer_name
  order_id：最新注文の注文ID
  order_date：最新注文日
  latest_order_amount：最新注文の金額
  customer_total_amount：顧客のcompleted注文合計金額
  latest_order_share_pct：小数第2位まで四捨五入した最新注文金額の構成比（%）
同日の複数注文は注文IDが大きいものを最新とする。CTEを使用する。顧客IDの昇順で並べる。
注文がない顧客も表示するがその order_id、order_date、latest_order_amount、latest_order_share_pct はNULLで customer_total_amount は0とする。
*/
WITH order_completed AS (
  SELECT
    customer_id,
    order_id,
    order_date,
    amount AS latest_order_amount,
    SUM(amount) OVER (
      PARTITION BY customer_id
    ) AS customer_total_amount,
    ROW_NUMBER() OVER (
      PARTITION BY customer_id
      ORDER BY order_date DESC, order_id DESC
    ) AS row_rank
  FROM `resonant-tract-508812-p9.sql_training.orders`
  WHERE status = 'completed'
    AND (order_date >= DATE '2026-01-01' AND order_date < DATE '2026-04-01')
  QUALIFY row_rank = 1
)
SELECT
  c.customer_id,
  c.customer_name,
  o.order_id,
  o.order_date,
  o.latest_order_amount,
  IFNULL(o.customer_total_amount, 0) AS customer_total_amount,
  ROUND(
    SAFE_DIVIDE(o.latest_order_amount, o.customer_total_amount) * 100,
    2
  ) AS latest_order_share_pct
FROM order_completed AS o
RIGHT OUTER JOIN `resonant-tract-508812-p9.sql_training.customers` AS c
  ON o.customer_id = c.customer_id
ORDER BY c.customer_id ASC;
/*追加の確認問題
今回、最新注文を取得する際に MAX(order_date) だけでは不十分なのはなぜでしょうか？
また、最新注文の1行だけを残してから SUM(amount) OVER (PARTITION BY customer_id) を計算すると、どのような問題が起こるでしょうか？

MAX(order_date) だけでは最新の注文IDや金額を特定できず、仮に同じ顧客の同日複数注文がある場合は MAX(order_date) だけではどの注文が最新か判断できません。
今回の要件では同日の注文について注文IDが大きいものを選ぶ必要があり、ROW_NUMBER() OVER (…) で注文日と注文IDの両方を降順で指定する方法が適切です。
また、最新注文の1行だけを残してから SUM(amount) OVER (PARTITION BY customer_id) を計算すると、顧客ごとのcompleted注文合計金額が出ません。
仮に ROW_NUMBER() OVER (…) と QUALIFY で1行だけに残した後の SUM(amount) OVER (PARTITION BY customer_id) は、
customer_id ごとの amount がそれぞれ1行なので今回のSQLにおける amount AS latest_order_amount の結果と同じ金額が出てしまいます。*/

/*
STEP 11-7｜ウィンドウ関数の総合演習
これまで学習した GROUP BY、CTE、JOIN、RANK()、SUM() OVER ()、QUALIFY などから必要な構文を選んでください。
すべての構文を使う必要はなく、要件を満たすSQLを設計することが目的です。

customers と orders を使い、2026年1〜3月のcompleted注文について全顧客別の合計売上を集計し、そのうえで都道府県ごとに売上金額の高い顧客を最大2名ずつ取得。
  prefecture
  customer_id
  customer_name
  completed_order_count：completed注文件数
  total_amount：顧客別の合計売上
  prefecture_total_amount：同じ都道府県の全顧客の合計売上（上位2名に絞り込む前の全顧客を対象に計算）
  sales_share_pct：都道府県内での売上構成比（顧客売上 ÷ 都道府県売上 × 100で計算し小数第2位まで四捨五入）
  prefecture_rank：都道府県内の売上順位
注文がない顧客の注文件数と合計売上は0とする。
都道府県別の順位は合計売上の降順で付ける。同額の顧客がいる場合は顧客IDの昇順で順位を決める。
各都道府県の上位2名のみ表示する。CTEを使用する。最終結果は都道府県の昇順と順位の昇順で並べる。
*/
WITH order_completed AS (
  SELECT
    customer_id,
    COUNT(order_id) AS completed_order_count,
    SUM(amount) AS total_amount
  FROM `resonant-tract-508812-p9.sql_training.orders`
  WHERE status = 'completed'
    AND (order_date >= DATE '2026-01-01' AND order_date < DATE '2026-04-01')
  GROUP BY customer_id
),
customer_joined AS (
  SELECT
    c.prefecture,
    c.customer_id,
    c.customer_name,
    IFNULL(o.completed_order_count, 0) AS completed_order_count,
    IFNULL(o.total_amount, 0) AS total_amount,
    SUM(IFNULL(o.total_amount, 0)) OVER (
      PARTITION BY c.prefecture
    ) AS prefecture_total_amount
  FROM order_completed AS o
  RIGHT OUTER JOIN `resonant-tract-508812-p9.sql_training.customers` AS c
    ON o.customer_id = c.customer_id
)
SELECT
  prefecture,
  customer_id,
  customer_name,
  completed_order_count,
  total_amount,
  prefecture_total_amount,
  ROUND(
    SAFE_DIVIDE(total_amount, prefecture_total_amount) * 100,
    2
  ) AS sales_share_pct,
  ROW_NUMBER() OVER (
    PARTITION BY prefecture
    ORDER BY total_amount DESC, customer_id ASC
  ) AS prefecture_rank
FROM customer_joined
QUALIFY prefecture_rank <= 2
ORDER BY prefecture ASC, prefecture_rank ASC;
/*追加の確認問題
今回は東京都にTanaka・Suzuki・Watanabeの3名がいますが、上位2名に絞り込んだ後で都道府県別売上を合計するとどのような問題が起こるでしょうか？
また、正しい都道府県別売上を維持したまま上位2名だけを表示するには、どの段階でウィンドウ関数を計算する必要があるでしょうか？

対象の都道府県に3名がいる中で上位2名に絞り込んだ後に都道府県別売上を合計した場合、全3名ではなく上位2名での都道府県別売上額となってしまいます。
今回は上位2名に絞り込んだ際に除外されるのは注文がない顧客のWatanabeですが、通常は都道府県売上が変わると都道府県内での売上構成比も変化してしまいます。
正しい都道府県別売上を維持したまま上位2名を表示するには、まず都道府県別の顧客とその各売上を集計した段階でそれらを基にした都道府県別売上を合計します。
それぞれ都道府県別売上の合計が出た後にウィンドウ関数による順位付けを行い、QUALIFY句などを使いその順位を基に上位2名に絞り込む方法があります。*/


-- STEP 12｜ウィンドウ関数の応用
/*
ここからは前後の行を参照するウィンドウ関数で、最初に扱うのは LAG() と LEAD() で、これらはデータ分析の実務でも使用頻度の高い関数です。
  LAG()：指定した順序で、前の行の値を取得する
  LEAD()：指定した順序で、次の行の値を取得する

例えば、次の注文データを考えます。
  order_id  customer_id  order_date  amount
  1001      1            2026-01-05  3,200
  1003      1            2026-01-12  2,100
  1007      1            2026-02-14  6,100
  1012      1            2026-03-25  9,800

LAG(amount) を使うと次のようになり、最初の注文には前の注文が存在しないためNULLになります。
  order_id  amount  previous_amount
  1001      3,200   NULL
  1003      2,100   3,200
  1007      6,100   2,100
  1012      9,800   6,100

基本構文は次の通りで、下記例では PARTITION BY customer_id によって顧客ごとに前の注文を取得します。
ORDER BY によって何を「前」とするかを決定します。
  LAG(amount) OVER (
    PARTITION BY customer_id
    ORDER BY order_date ASC, order_id ASC
  )

LEAD() も同様で、下記例では「次」の注文金額を取得します。
  LEAD(amount) OVER (
    PARTITION BY customer_id
    ORDER BY order_date ASC, order_id ASC
  )
*/
SELECT
  customer_id,
  order_id,
  amount,
  order_date,
  LAG(amount) OVER (
    PARTITION BY customer_id
    ORDER BY order_date ASC, order_id ASC
  ) AS previous_amount,
  LEAD(amount) OVER (
    PARTITION BY customer_id
    ORDER BY order_date ASC, order_id ASC
  ) AS next_amount
FROM `resonant-tract-508812-p9.sql_training.orders`;

/*
STEP 12-1｜練習問題：前回注文と次回注文
orders を使い、2026年1月〜3月のcompleted注文について顧客ごとに前回注文日・次回注文日を取得してください。
  order_id、customer_id、order_date、amount、previous_order_date：前回注文日、next_order_date：次回注文日
  days_since_previous：前回注文から今回注文までの日数、days_until_next：今回注文から次回注文までの日数
注文日の昇順で判定する。同じ顧客が同じ日に複数注文している場合は注文IDの昇順で判定する。
前回注文がない場合 previous_order_date と days_since_previous はNULL。次回注文がない場合 next_order_date と days_until_next はNULL。
LAG() と LEAD() を使用する。DATE_DIFF() を使用する。CTEを1つ以上使用する。最終結果は顧客ID、注文日、注文IDの昇順で並べる。
*/
WITH order_extract AS (
  SELECT
    order_id,
    customer_id,
    order_date,
    amount,
    LAG(order_date) OVER (
      PARTITION BY customer_id
      ORDER BY order_date ASC, order_id ASC
    ) AS previous_order_date,
    LEAD(order_date) OVER (
      PARTITION BY customer_id
      ORDER BY order_date ASC, order_id ASC
    ) AS next_order_date
  FROM `resonant-tract-508812-p9.sql_training.orders`
  WHERE status = 'completed'
    AND (order_date >= DATE '2026-01-01' AND order_date < DATE '2026-04-01')
)
SELECT
  order_id,
  customer_id,
  order_date,
  amount,
  previous_order_date,
  next_order_date,
  DATE_DIFF(order_date, previous_order_date, DAY) AS days_since_previous,
  DATE_DIFF(next_order_date, order_date, DAY) AS days_until_next
FROM order_extract
ORDER BY customer_id ASC, order_date ASC, order_id ASC;
/*追加の確認問題
今回のクエリで LAG() と LEAD() の PARTITION BY customer_id を省略すると、どのような問題が発生するでしょうか？
また、ORDER BY order_date ASC のみを指定し、order_id ASC を省略した場合、どのようなリスクがありますか？

LAG() と LEAD() の PARTITION BY customer_id を省略した場合、顧客別の注文日の区分けではなく全ての注文日を対象とした前回と次回の結果になります。
また ORDER BY order_date ASC のみを指定して order_id ASC を省略した場合、同じ顧客の同日注文については前回と次回の定義が保証されなくなります。
そのリスクとして LAG() や LEAD() が参照する行が安定せず、再実行時に異なる結果になる可能性があります。*/

/*
STEP 12-2｜LAGを使った前回注文との金額比較
これまで学習した LAG()、CASE、SAFE_DIVIDE()、ROUND() などを要件に応じて組み合わせ、前回注文から購入金額がどの程度変化したかを分析します。

orders を使い、2026年1〜3月のcompleted注文について顧客ごとに前回注文の金額を取得し、今回注文との差額と増減率を計算してください。
  order_id、customer_id、order_date、amount：今回注文金額、previous_amount：前回注文金額、amount_diff：今回注文金額 − 前回注文金額
  change_pct：前回注文からの増減率を小数第2位まで四捨五入（%）{差分 = amount - previous_amount } / previous_amount * 100
  change_type：前回注文が存在しない first_order、今回注文金額が前回より大きい increased、前回より小さい decreased、前回注文金額が同じ unchanged
顧客ごとに注文日と注文IDの昇順で前回注文を判定する。LAG() を使用。CTEを使用。最終結果は顧客IDと注文日と注文IDの昇順で並べる。
前回注文が存在しない場合は previous_amount と amount_diff と change_pct はNULLとする。前回注文金額が0円の場合、change_pct はNULLとする。
*/
WITH order_extract AS (
  SELECT
    order_id,
    customer_id,
    order_date,
    amount,
    LAG(amount) OVER (
      PARTITION BY customer_id
      ORDER BY order_date ASC, order_id ASC
    ) AS previous_amount,
    amount - LAG(amount) OVER (
      PARTITION BY customer_id
      ORDER BY order_date ASC, order_id ASC
    ) AS amount_diff
  FROM `resonant-tract-508812-p9.sql_training.orders`
  WHERE status = 'completed'
    AND (order_date >= DATE '2026-01-01' AND order_date < DATE '2026-04-01')
)
SELECT
  order_id,
  customer_id,
  order_date,
  amount,
  previous_amount,
  amount_diff,
  ROUND(
    SAFE_DIVIDE(amount_diff, previous_amount) * 100,
    2
  ) AS change_pct,
  CASE
    WHEN previous_amount IS NULL THEN 'first_order'
    WHEN amount > previous_amount THEN 'increased'
    WHEN amount < previous_amount THEN 'decreased'
    ELSE 'unchanged'
  END AS change_type
FROM order_extract
ORDER BY customer_id ASC, order_date ASC, order_id ASC;
/*追加の確認問題
次の2つについて説明してください。
  A. 前回注文金額が0円だった場合、増減率を通常の除算で計算すると、どのような問題が発生するでしょうか？
  B. 今回のSQLで前回注文が存在しない行について previous_amount を IFNULL(previous_amount, 0) で0に置き換えるとどのような問題が起こるか？

Aは「増減率 = {今回注文額-前回注文額}による差分 / 前回注文金額=0」で分母側が[0]の式となり、ゼロ除算エラーとなります。
Bが行われた行は、「前回注文がない=初回注文」と「前回注文が0円」という意味の異なるデータの境界がなくなり、差分の計算も変化が強く出てしまいかねません。*/

/*
STEP 12-3｜移動平均（Moving Average）
次は、ウィンドウ関数のフレーム指定を応用します。
移動平均は、売上推移や利用状況の変化を分析するときに使われます。

STEP 11では下記のように累積売上を計算しました。
  SUM(amount) OVER (
      PARTITION BY customer_id
      ORDER BY order_date ASC, order_id ASC
      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    )

今回は直近3件の注文金額の平均を求めるもので、例えば顧客ID1の注文を考えます。
なお、今回の「直近3件」というは現在の注文を含めた最大3件で、例えば注文1012の場合 (2100+6100+9800)/3=6000 となります。
  order_id  amount  直近3件の平均
  1001      3,200   3,200.00
  1003      2,100   2,650.00
  1007      6,100   3,800.00
  1012      9,800   6,000.00

ウィンドウ関数による移動平均の構文は次の通りで、下記例の ROWS BETWEEN 2 PRECEDING AND CURRENT ROW は「現在行とその直前の最大2行」が計算対象です。
最初の注文のように前の行が存在しない場合は、存在する行だけで平均を計算します。
  AVG(amount) OVER (
    PARTITION BY customer_id
    ORDER BY order_date ASC, order_id ASC
    ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
  )

練習問題として orders を使い、2026年1〜3月のcompleted注文について顧客ごとに直近3件の平均注文金額を計算し、さらに今回注文金額と直近3件の平均注文金額を比較。
  order_id、customer_id、order_date、amount、moving_avg_3：直近3件の平均注文金額、diff_from_avg：今回注文金額−直近3件の平均注文金額
  amount_level：今回注文金額が移動平均より大きい above_avg、移動平均より小さい below_avg、移動平均と等しい equal_avg
顧客ごとに注文日と注文IDの昇順で計算する。直近3件には現在の注文を含める。3件未満の場合は存在する注文だけで平均する。
AVG() とウィンドウフレームを使用。moving_avg_3 と diff_from_avg は小数第2位まで四捨五入。CTEを使用。最終結果は顧客IDと注文日と注文IDの昇順で並べる。
*/
WITH order_extract AS (
  SELECT
    order_id,
    customer_id,
    order_date,
    amount,
    AVG(amount) OVER (
      PARTITION BY customer_id
      ORDER BY order_date ASC, order_id ASC
      ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) AS moving_avg_3
  FROM `resonant-tract-508812-p9.sql_training.orders`
  WHERE status = 'completed'
    AND (order_date >= DATE '2026-01-01' AND order_date < DATE '2026-04-01')
)
SELECT
  order_id,
  customer_id,
  order_date,
  amount,
  ROUND(moving_avg_3, 2) AS moving_avg_3,
  ROUND(amount - moving_avg_3, 2) AS diff_from_avg,
  CASE
    WHEN amount > moving_avg_3 THEN 'above_avg'
    WHEN amount < moving_avg_3 THEN 'below_avg'
    ELSE 'equal_avg'
  END AS amount_level
FROM order_extract
ORDER BY customer_id ASC, order_date ASC, order_id ASC;
/*追加の確認問題
A. ROWS BETWEEN 2 PRECEDING AND CURRENT ROW と ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW では計算対象がどう異なるでしょうか？
B. 今回の移動平均で、PARTITION BY customer_id を省略するとどのような問題が起こるでしょうか？
C. 今回の移動平均は直近3件の注文が対象ですが「直近30日間の注文」を対象とする場合、同じ ROWS BETWEEN 2 PRECEDING AND CURRENT ROW を使用してよいでしょうか？

Aは前者が[現在行とその直前の最大2行]が計算対象で、後者が[パーティションの最初行から現在行までの累計」が計算対象です。
Bを行うと移動平均の注文金額は顧客ごとの区分けが保証されず、異なる顧客間での注文金額が入り混じった移動平均となる可能性があります。
Cで言及の対象に変更する場合は同じ ROWS BETWEEN … は不適当で、これは[現在行とその直前の最大2行]に直近30日間という時系列が保証されていないからです。
なお、期間に基づく集計では、日付条件を使った集計や、RANGE フレームなどを検討する必要があります。*/

/*
STEP 12-4｜FIRST_VALUEとLAST_VALUE
FIRST_VALUE()：ウィンドウフレーム内の最初の行の値を取得
LAST_VALUE()：ウィンドウフレーム内の最後の行の値を取得

例えば顧客ID1のcompleted注文は次の4件で、この顧客の初回注文金額は3,200円、最終注文金額は9,800円です。
  order_id  order_date  amount
  1001      2026-01-05  3,200
  1003      2026-01-12  2,100
  1007      2026-02-14  6,100
  1012      2026-03-25  9,800

初回注文金額は、次のように取得できます。
  FIRST_VALUE(amount) OVER (
    PARTITION BY customer_id
    ORDER BY order_date ASC, order_id ASC
    ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
  )

最終注文金額は次のように取得できます。
  LAST_VALUE(amount) OVER (
    PARTITION BY customer_id
    ORDER BY order_date ASC, order_id ASC
    ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
  )

新しく登場したのが UNBOUNDED FOLLOWING で、これはパーティションの最後の行までをウィンドウフレームに含める指定です。

練習問題で orders を使い、2026年1〜3月のcompleted注文で各注文行にその顧客の初回注文金額と最終注文金額を付与し、さらに初回注文から最終注文までの金額変化を計算。
  order_id、customer_id、order_date、amount、first_order_amount：顧客の初回注文金額、last_order_amount：顧客の最終注文金額
  first_last_diff：最終注文金額 − 初回注文金額、first_last_change_pct：初回注文から最終注文までの増減率（first_last_diff / 初回注文金額 * 100）

顧客ごとに注文日と注文IDの昇順で初回・最終注文を判定。FIRST_VALUE() と LAST_VALUE() を使用し両方の関数でウィンドウフレームを明示する。
初回・最終注文金額は同じ顧客のすべての注文行で同じ値になるようにする。first_last_change_pct は小数第2位まで四捨五入。
初回注文金額が0円の場合は増減率はNULLとする。CTEを使用する。最終結果は顧客IDと注文日と注文IDの昇順で並べる。
*/
WITH order_extract AS (
  SELECT
    order_id,
    customer_id,
    order_date,
    amount,
    FIRST_VALUE(amount) OVER (
      PARTITION BY customer_id
      ORDER BY order_date ASC, order_id ASC
      ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
    ) AS first_order_amount,
    LAST_VALUE(amount) OVER (
      PARTITION BY customer_id
      ORDER BY order_date ASC, order_id ASC
      ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
    ) AS last_order_amount
  FROM `resonant-tract-508812-p9.sql_training.orders`
  WHERE status = 'completed'
    AND (order_date >= DATE '2026-01-01' AND order_date < DATE '2026-04-01')
)
SELECT
  order_id,
  customer_id,
  order_date,
  amount,
  first_order_amount,
  last_order_amount,
  last_order_amount - first_order_amount AS first_last_diff,
  ROUND(
    SAFE_DIVIDE(last_order_amount - first_order_amount, first_order_amount) * 100,
    2
  ) AS first_last_change_pct
FROM order_extract
ORDER BY customer_id ASC, order_date ASC, order_id ASC;
/*追加の確認問題
A. LAST_VALUE() において、次の2つのフレーム指定では結果がどのように異なりますか？
  ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
  ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
B. 今回、顧客ID1の注文1001と注文1007では、last_order_amount にそれぞれどの金額が表示されるべきでしょうか？理由も説明してください。
C. FIRST_VALUE() と LAST_VALUE() を使わず、ROW_NUMBER() と QUALIFY で初回・最終注文をそれぞれ1行ずつ得る方法もありますが、取得できる行の構成の違いは？

Aの上は[パーティションの最初行から現在行まで」を対象としたLAST_VALUE(値)で、下は[パーティションの最初行から最後行まで]を対象としたLAST_VALUE(値)です。
Bの対象でそれぞれ表示されるのは同じ最終注文金額で、今回は顧客ごとの区切りで[パーティションの最初行から最後行まで]を対象としたLAST_VALUE(値)を取得するためです。
Cの ROW_NUMBER() と QUALIFY でも注文数（行数）が異なる顧客の最終注文は取得でき、それは注文日・注文IDを降順に並べて ROW_NUMBER() = 1 とすれば可能です。
Cにおける両者の違いは、次のように「行を残す」か「絞り込む」かです。
  - FIRST_VALUE()・LAST_VALUE()：各注文行を残したまま、初回・最終注文の値を付与する。
  - ROW_NUMBER()・QUALIFY：条件に合う注文行だけを絞り込む（抽出する）。*/

/*
STEP 12-5｜ウィンドウ関数の総合演習

orders を使い、2026年1月〜3月のcompleted注文について各顧客の注文推移を分析してください。
  customer_id、order_id、order_date、amount：今回注文金額、previous_amount：前回注文金額、amount_diff：前回注文からの金額差
  cumulative_amount：今回注文までの累計売上、moving_avg_3：今回注文を含む直近3件の平均注文金額、customer_total_amount：顧客の全completed注文の合計金額
顧客ごとに注文日・注文IDの昇順で処理する。前回注文がない場合 previous_amount と amount_diff はNULL。累計売上は現在行までの注文金額の合計。
移動平均は現在行を含む最大3件で計算して小数第2位まで四捨五入。CTEを使用。最終結果は顧客IDと注文日と注文IDの昇順。
*/
WITH order_extract AS (
  SELECT
    customer_id,
    order_id,
    order_date,
    amount,
    LAG(amount) OVER (
      PARTITION BY customer_id
      ORDER BY order_date ASC, order_id ASC
    ) AS previous_amount,
    SUM(amount) OVER (
      PARTITION BY customer_id
      ORDER BY order_date ASC, order_id ASC
      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS cumulative_amount,
    AVG(amount) OVER (
      PARTITION BY customer_id
      ORDER BY order_date ASC, order_id ASC
      ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) AS moving_avg_3,
    SUM(amount) OVER (
      PARTITION BY customer_id
    ) AS customer_total_amount
  FROM `resonant-tract-508812-p9.sql_training.orders`
  WHERE status = 'completed'
    AND (order_date >= DATE '2026-01-01' AND order_date < DATE '2026-04-01')
)
SELECT
  customer_id,
  order_id,
  order_date,
  amount,
  previous_amount,
  amount - previous_amount AS amount_diff,
  cumulative_amount,
  ROUND(moving_avg_3, 2) AS moving_avg_3,
  customer_total_amount
FROM order_extract
ORDER BY customer_id ASC, order_date ASC, order_id ASC;
/*追加の確認問題
今回のSQLでは、cumulative_amount と customer_total_amount の両方を SUM(amount) OVER (...) で計算します。
この2つのウィンドウ関数では、ORDER BY とウィンドウフレームの指定をどのように使い分ける必要がありますか？

cumulative_amount は今回注文までの累計なので、ORDER BY … で計算順を確定させ ROWS BETWEEN … で[パーティションの最初行から現在行まで」を指定します。
customer_total_amount は顧客別の全completed注文額なので、計算順は関係なく ORDER BY … と ROWS BETWEEN … のウィンドウフレームは省略できます。*/

/*
STEP 12-6｜ウィンドウ関数 × JOIN × 条件付き集計
これまでのウィンドウ関数に、以前学習した JOIN、COUNTIF()、IFNULL() を組み合わせます。

customers と orders を使い、2026年1～3月の注文がない顧客も含めた顧客別の注文実績と売上ランキング
  customer_id、customer_name、prefecture、completed_count：completed注文数、cancelled_count：cancelled注文数
  total_amount：completed注文の合計金額、prefecture_total_amount：同じ都道府県のcompleted売上合計、prefecture_sales_rank：都道府県内の売上順位
注文履歴がない顧客は注文数と売上金額は0とする。prefecture_sales_rank は都道府県ごとに total_amount の降順で同額の場合は同順位として次の順位は飛ばす。
COUNTIF()、CTE、明示的なJOIN、ウィンドウ関数を使用する。最終結果は prefecture ASC, prefecture_sales_rank ASC, customer_id ASC で並べる。
*/
WITH order_extract AS (
  SELECT
    customer_id,
    COUNTIF(status = 'completed') AS completed_count,
    COUNTIF(status = 'cancelled') AS cancelled_count,
    SUM(
      IF(status = 'completed', amount, 0)
    ) AS total_amount
  FROM `resonant-tract-508812-p9.sql_training.orders`
  WHERE order_date >= DATE '2026-01-01' AND order_date < DATE '2026-04-01'
  GROUP BY customer_id
)
SELECT
  c.customer_id,
  c.customer_name,
  c.prefecture,
  IFNULL(o.completed_count, 0) AS completed_count,
  IFNULL(o.cancelled_count, 0) AS cancelled_count,
  IFNULL(o.total_amount, 0) AS total_amount,
  SUM(IFNULL(o.total_amount, 0)) OVER (
    PARTITION BY c.prefecture
  ) AS prefecture_total_amount,
  RANK() OVER (
    PARTITION BY c.prefecture
    ORDER BY IFNULL(o.total_amount, 0) DESC
  ) AS prefecture_sales_rank
FROM order_extract AS o
RIGHT OUTER JOIN `resonant-tract-508812-p9.sql_training.customers` AS c
  ON o.customer_id = c.customer_id
ORDER BY c.prefecture ASC, prefecture_sales_rank ASC, c.customer_id ASC;
/*追加の確認問題
注文履歴のない顧客を含めるために、customers と orders を結合するとします。
注文のステータスを WHERE status = 'completed' で絞り込んでから顧客別集計を行う方法では、今回の要件を満たせないのはなぜでしょうか？

FROMの次にWHEREが実行されるため completed注文に絞った状態で COUNTIF を行うことになり、顧客別のcancelled注文数を正しく集計できなくなります。
また WHERE status = 'completed' で絞ると、completed注文がない顧客は集計結果から消えることになります。
今回のように注文ステータス別の件数を比較したい場合は、WHERE でステータスを絞らず COUNTIF() や SUM(IF()) で条件を指定する設計が適切です。*/

/*
STEP 12-7｜ウィンドウ関数 × 集計 × ランキング
STEP 12の最後は、少し実務寄りの総合問題です。
今回は、顧客ごとの月次売上を集計し、前月との比較と月内ランキングを算出するSQLを作成します。

orders と customers を使い、2026年1～3月のcompleted注文について顧客ごとの月次売上を集計し、前月との比較と月内ランキングを算出
  sales_month：売上月（月初日の日付）、customer_id、customer_name、monthly_amount：その月のcompleted売上、previous_month_amount：前月のcompleted売上
  month_diff：前月からの売上増減額、month_change_pct：前月比増減率（差分/前回）、monthly_rank：その月の顧客別売上順位
注文がない月も含めて全6顧客 × 3か月 = 18行を出力。注文がない月の monthly_amount は0とする。
previous_month_amount は同じ顧客の前月の売上金額として1月はNULL。 month_diff は 今回月の売上 − 前月売上 で1月はNULL。
month_change_pct は小数第2位まで四捨五入して前月売上が0円または前月が存在しない場合はNULL。
monthly_rank は各月の売上金額の降順で順位付けし同額の場合は同順位として次の順位は飛ばす。
CTEを使用する。最終結果は sales_month ASC, monthly_rank ASC, customer_id ASC で並べる。
*/
WITH order_extract AS (
  SELECT
    sales_month,
    customer_id,
    SUM(amount) AS monthly_amount
  FROM (
    SELECT
      DATE_TRUNC(order_date, MONTH) AS sales_month,
      customer_id,
      amount
    FROM `resonant-tract-508812-p9.sql_training.orders`
    WHERE status = 'completed'
      AND (order_date >= DATE '2026-01-01' AND order_date < DATE '2026-04-01')
  )
  GROUP BY sales_month, customer_id
),
month_make AS (
  SELECT
    DATE '2026-01-01' AS target_month
  UNION ALL
  SELECT
    DATE '2026-02-01'
  UNION ALL
  SELECT
    DATE '2026-03-01'
),
joined_month_customer AS (
  SELECT
    m.target_month,
    c.customer_id,
    c.customer_name
  FROM month_make AS m
  CROSS JOIN `resonant-tract-508812-p9.sql_training.customers` AS c
),
amount_month_customer AS (
  SELECT
    j.target_month,
    j.customer_id,
    j.customer_name,
    IFNULL(o.monthly_amount, 0) AS monthly_amount
  FROM joined_month_customer AS j
  LEFT OUTER JOIN order_extract AS o
    ON j.customer_id = o.customer_id
      AND j.target_month = o.sales_month
)
SELECT
  target_month AS sales_month,
  customer_id,
  customer_name,
  monthly_amount,
  LAG(monthly_amount) OVER (
    PARTITION BY customer_id
    ORDER BY target_month ASC
  ) AS previous_month_amount,
  monthly_amount - LAG(monthly_amount) OVER (
    PARTITION BY customer_id
    ORDER BY target_month ASC
  ) AS month_diff,
  ROUND(
    SAFE_DIVIDE(monthly_amount - LAG(monthly_amount) OVER (PARTITION BY customer_id ORDER BY target_month ASC),
    LAG(monthly_amount) OVER (PARTITION BY customer_id ORDER BY target_month ASC)
    ) * 100, 2
  ) AS month_change_pct,
  RANK() OVER (
    PARTITION BY target_month
    ORDER BY monthly_amount DESC
  ) AS monthly_rank
FROM amount_month_customer
ORDER BY sales_month ASC, monthly_rank ASC, customer_id ASC;
/*追加の確認問題
今回の問題で月次売上を集計した結果にそのまま LAG(monthly_amount) を適用すると、注文のない月が存在する顧客についてどのような問題が起こるでしょうか？

注文のない月がある顧客の月間売上が抜け落ちて、全顧客6名×対象3か月分による18行の全結果ではなく、注文がある月に絞られた顧客別月次売上になってしまいます。
さらに厳密に言えば、注文のない月が抜けることで LAG() が取得する値について比較対象となる月が欠けてしまう問題が起こります。

・今回の LAG() について。
  LAG(monthly_amount) OVER (
    PARTITION BY customer_id
    ORDER BY target_month ASC
  ) AS previous_month_amount

LAG() は指定した並び順における前の行の値を取得するウィンドウ関数で、今回の要件は「同じ顧客の前月売上を取得すること」なので次の2つの指定が必要です。
  PARTITION BY customer_id：顧客ごとに計算を独立させる。顧客ID1のTanakaと顧客ID2のSatoは、それぞれ別の計算グループになります。
  ORDER BY target_month ASC：各顧客の月を古い順に並べる。1月 → 2月 → 3月の順に並ぶため、LAG() で直前の月の売上を取得できます。

PARTITION BYを省略したらどうなるかというと、全顧客が同じグループとして扱われて別顧客の売上を前月売上として取得してしまいかねません。
ORDER BYを省略したらどうなるかというと、LAG() はどの行が前の行なのかを判断するための順序が必要なので、LAG() のウィンドウ指定には ORDER BY が必須です。

・今回の LAG() と RANK() を同じSELECTで使ってよい理由について。
今回のSQLでは、次の LAG() と RANK() を同じSELECT内で使用しています。

  LAG(monthly_amount) OVER (
    PARTITION BY customer_id
    ORDER BY target_month ASC
  )

  RANK() OVER (
    PARTITION BY target_month
    ORDER BY monthly_amount DESC
  )

これはウィンドウ関数ごとに独立した OVER() を指定できるため問題なく、LAG()は顧客単位で RANK()は月単位で　それぞれ計算されます。
また最終的な ORDER BY sales_month ASC, monthly_rank ASC, customer_id ASC は出力行の並び順を指定するもので、LAG()やRANK()の計算順序を変更しません。*/








