
-- STEP 9｜WITH句（CTE）
/*
次は、データエンジニアリングでもよく使用する CTE（WITH句）を学習します。
CTEとは Common Table Expression の略です。

これまで学習したFROM句のサブクエリでは、次のように書いていました。
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
WHERE total_amount >= 8000;

CTEを使うと、次のように書けます。
*/
WITH customer_sales AS (
  SELECT
    customer_id,
    SUM(IFNULL(amount, 0)) AS total_amount
  FROM `resonant-tract-508812-p9.sql_training.orders_null`
  WHERE status = 'completed'
  GROUP BY customer_id
)
SELECT
  customer_id,
  total_amount
FROM customer_sales
WHERE total_amount >= 8000;
/*
1つ目のFROM句のサブクエリ と 2つ目のCTEは同じ結果を返します。
CTEの違いは、集計処理に customer_sales という名前をつけ、後続のSELECTから参照できることです。
- 1. WITH customer_sales AS (...)：completed注文を顧客ごとに集計するCTEを定義
- 2. SELECT ... FROM customer_sales：名前をつけた集計結果を参照する

CTEは、複雑なSQLを処理単位に分割して読みやすくするために便利ですが、CTEを使えば必ず処理速度が上がるわけではありません。
また、通常のCTEは物理テーブルを作成するものではなく、同じSQL文の中だけで利用できる名前付きの結果です。
そのため、別のSQL文から customer_sales を参照することはできません。
*/

/*
STEP 9-1｜練習問題
orders_null を使い、completed注文の顧客別合計金額を集計し、8,000円以上の顧客を customer_id、total_amount で取得してください。
WITH 句を必ず使用して CTE名は customer_sales として、CTEの中でcompleted注文だけを集計し、NULLの金額は0として扱う。
外側のSELECTで合計金額8,000円以上に絞り込み、合計金額の降順、次に顧客IDの昇順で並べ、JOINは使用しない。
*/
WITH customer_sales AS (
  SELECT
    customer_id,
    SUM(IFNULL(amount, 0)) AS total_amount
  FROM `resonant-tract-508812-p9.sql_training.orders_null`
  WHERE status = 'completed'
  GROUP BY customer_id
)
SELECT
  customer_id,
  total_amount
FROM customer_sales
WHERE total_amount >= 8000
ORDER BY total_amount DESC, customer_id ASC;

/*
STEP 9-2｜複数のCTEを定義する
ここでは、1つのWITH句の中で複数のCTEを定義する方法、例えば次のようなSQLを学びます。
WITH completed_orders AS (
  SELECT
    order_id,
    customer_id,
    amount
  FROM `resonant-tract-508812-p9.sql_training.orders_null`
  WHERE status = 'completed'
),
customer_sales AS (
  SELECT
    customer_id,
    COUNT(order_id) AS completed_order_count,
    SUM(IFNULL(amount, 0)) AS total_amount
  FROM completed_orders
  GROUP BY customer_id
)
SELECT
  customer_id,
  completed_order_count,
  total_amount
FROM customer_sales
ORDER BY customer_id ASC;

注目してほしいのは次の3点です。
  1. 複数のCTEはカンマ(,)で区切る。
  2. 2つ目のCTEから、先に定義した completed_orders を参照できる。
  3. 最後のSELECTから、2つ目のCTEである customer_sales を参照できる。

このように、処理を複数の段階に分けられることがCTEの利点で、実務のデータ加工では抽出・整形・集計などを分けて記述する場面があります。
ただし、CTEの各段階が必ず個別に実行・保存されるわけではなく、BigQueryはSQL全体を最適化します。

練習問題として orders_null を使い、completed注文について顧客別の注文件数と合計金額を集計し、2件以上注文した顧客だけを取得してください。
取得列は customer_id、completed_order_count：completed注文件数、total_amount：completed注文の合計金額
1つ目のCTE名は completed_orders として completed注文だけを抽出、2つ目のCTE名は customer_sales として completed_orders を参照して顧客別に集計する。
NULLの金額は0として合計し、最後のSELECTで completed注文件数 が2件以上の顧客だけを取得し、合計金額の降順、次に顧客IDの昇順で並べ、JOINは使用しない。
*/
WITH completed_orders AS (
  SELECT
    customer_id,
    order_id,
    amount
  FROM `resonant-tract-508812-p9.sql_training.orders_null`
  WHERE status = 'completed'
),
customer_sales AS (
  SELECT
    customer_id,
    COUNT(order_id) AS completed_order_count,
    SUM(IFNULL(amount, 0)) AS total_amount
  FROM completed_orders
  GROUP BY customer_id
)
SELECT
  customer_id,
  completed_order_count,
  total_amount
FROM customer_sales
WHERE completed_order_count >= 2
ORDER BY total_amount DESC, customer_id ASC;
/*追加の確認問題として、今回は最後のSELECTで WHERE completed_order_count >= 2 と書けるのはなぜでしょうか？
以前学習した HAVING との違いも含めて説明してみてください。

同じSQL文の中だけで利用できるCTE customer_sales の結果に、customer_id ごとの COUNT(order_id) がある completed_order_count が定義されており
最後のSELECTは、既に定義された customer_sales の completed_order_count を参照して WHEREを指定しているだけなので、通常のWHERE句と同じように書けます。

なお BigQueryでは、HAVING句に必ずGROUP BY句が必要というわけではありません。
例えば次のSQLは有効で、GROUP BY がなくても全体を1つのグループとして集計し HAVING で判定できます。
SELECT
  COUNT(*) AS customer_count
FROM `resonant-tract-508812-p9.sql_training.customers`
HAVING COUNT(*) >= 5;

今回の最後のSELECTで WHERE を使う理由は、そのSELECT自身では集計しておらず、CTEから受け取った既存の列を絞り込んでいるからです。
                 WHERE                  HAVING
主な役割          行を絞り込む             集計結果のグループを絞り込む
集計前のデータ     対象にできる             主な用途ではない
集計済みのCTE列    通常の列として参照できる   改めて集計する場合などに利用
GROUP BYが必須か  不要                    BigQueryでは必須ではない*/

/*
STEP 9-3｜CTE × JOIN × NULL処理
ここからは、複数CTEを使って少し実務的な処理を組み立てます。
今回は、集計結果とマスタ情報を別々のCTEで管理し、最後に結合する練習です。

customers、orders_null、customer_ranks を使い、すべての顧客についてcompleted注文の集計結果と顧客ランクを取得してください。
取得する列は customer_id、customer_name、customer_rank、completed_order_count：completed注文件数、total_amount：completed注文の合計金額
次のCTEを2つ定義して、最後のSELECTで2つのCTEを結合して、合計金額の降順、次に顧客IDの昇順で並べる。
  CTE1. customer_sales：orders_null からcompleted注文を抽出し、顧客IDごとに注文件数と合計金額を集計してください。
  CTE2. customer_info：customers と customer_ranks を結合し、すべての顧客について顧客ID・顧客名・顧客ランクを取得してください。
顧客マスタの6名全員を表示し、顧客ランクが登録されていない場合は 'unranked' として、customer_ranks にしか存在しない顧客ID7は表示しない。
completed注文がない場合は注文件数と合計金額を0として、金額がNULLの注文は合計金額の計算では0として扱う。
*/
WITH customer_sales AS (
  SELECT
    customer_id,
    COUNT(order_id) AS completed_order_count,
    SUM(IFNULL(amount, 0)) AS total_amount
  FROM `resonant-tract-508812-p9.sql_training.orders_null`
  WHERE status = 'completed'
  GROUP BY customer_id
),
customer_info AS (
  SELECT
    c.customer_id,
    c.customer_name,
    IFNULL(r.customer_rank, 'unranked') AS customer_rank
  FROM `resonant-tract-508812-p9.sql_training.customers` AS c
  LEFT OUTER JOIN `resonant-tract-508812-p9.sql_training.customer_ranks` AS r
    ON c.customer_id = r.customer_id
)
SELECT
  i.customer_id,
  i.customer_name,
  i.customer_rank,
  IFNULL(s.completed_order_count, 0) AS completed_order_count,
  IFNULL(s.total_amount, 0) AS total_amount
FROM customer_sales AS s
RIGHT OUTER JOIN customer_info AS i
  ON s.customer_id = i.customer_id
ORDER BY total_amount DESC, i.customer_id ASC;
/*追加の確認問題として、今回のCTE customer_sales には、Watanabe（顧客ID6）の行が存在しません。
それでも最終結果にWatanabeを表示できるのはなぜか、STEP 7で学習したOUTER JOINとNULLの関係を使って説明してください。

まず 2つ目のCTE customer_info にて customers LEFT OUTER JOIN customer_ranks としています。
Watanabe（顧客ID6）は、customers側の customer_id と customer_name はありますが、customer_ranks側の customer_rank はデータがありません。
LEFT OUTER JOIN で customers側の非NULL値を取得、結合した customer_ranks側の customer_rank は NULLを IFNULLで 'unranked'に置換した行を表示します。
上記が customer_info で得られる Watanabeの行で、最後のSELECT文は customer_sales を左側に、customer_info を右側に置いた RIGHT OUTER JOIN です。
Watanabeの行は customer_salese側の completed_order_count と　total_amount がNULLなので、それぞれ IFNULL で 0 に置換して最終結果に表示できます。*/

/*
STEP 9-4｜CTEを使った段階的なデータ加工
ここまでは、CTEを使って抽出・集計・JOINを行いました。
次は、あるCTEで作った計算結果を、次のCTEでさらに加工する練習で、実務では集計結果をそのまま出力するのではなく、さらに条件判定や分類を行うことがあります。
次の3段階で処理します。
1. customer_sales：completed注文の顧客別合計金額を集計
2. customer_category：1の合計金額を使って顧客を分類
3. 最後のSELECT：分類結果を条件で絞り込んで取得

練習問題として orders_null を使い、completed注文の合計金額をもとに顧客を分類し、highまたはmiddleの顧客だけを取得してください。
取得列は customer_id、total_amount：completed注文の合計金額、amount_category：金額に基づく分類
amount_categoryの分類条件は 合計金額10,000円以上：high、5,000円以上10,000円未満：middle、5,000円未満：low
JOINは使用せず、NULLの金額は0として集計し、次のCTEを定義し、最後のSELECTは high と middle の顧客だけ取得し、total_amountの降順、customer_idの昇順で並べる。
  CTE1. customer_sales：completed注文の顧客別合計金額を集計する。
  CTE2. customer_category：customer_sales を参照してCASEで分類する。
*/
WITH customer_sales AS (
  SELECT
    customer_id,
    SUM(IFNULL(amount, 0)) AS total_amount
  FROM `resonant-tract-508812-p9.sql_training.orders_null`
  WHERE status = 'completed'
  GROUP BY customer_id
),
customer_category AS (
  SELECT
    customer_id,
    total_amount,
    CASE
      WHEN total_amount >= 10000 THEN 'high'
      WHEN total_amount >= 5000 THEN 'middle'
      ELSE 'low'
    END AS amount_category
  FROM customer_sales
)
SELECT
  customer_id,
  total_amount,
  amount_category
FROM customer_category
WHERE amount_category IN ('high', 'middle')
ORDER BY total_amount DESC, customer_id ASC;
/*追加の確認問題
2つ目のCTE customer_category では、1つ目のCTEで定義した total_amount をCASE式の中でそのまま参照できます。
BigQueryでは、同じSELECT句で定義した列別名をそのSELECT句内の別の式から参照することはできませんが、列別名を ORDER BY などから参照することはできます。
なぜCTEを分けると参照できるようになるのでしょうか？

分けたCTEを参照する場合、そのCTEに定義されている列名をそのまま、後続のSELECT文で指定できます。
後続のSELECTから見ると、total_amount は単なる別名ではなく、FROM句で参照しているCTEが持つ列です。*/

/*
STEP 9-5｜CTEを複数箇所から参照する
ひとつ前では、CTEを次のCTEへ順番に渡してきました。
今回は、同じCTEを複数箇所から参照する方法で、例えば次のような構造です。
WITH customer_sales AS (
  SELECT
    customer_id,
    SUM(IFNULL(amount, 0)) AS total_amount
  FROM `resonant-tract-508812-p9.sql_training.orders_null`
  WHERE status = 'completed'
  GROUP BY customer_id
)
SELECT
  customer_id,
  total_amount,
  (
    SELECT
      AVG(total_amount)
    FROM customer_sales
  ) AS avg_total_amount
FROM customer_sales;

上記では　CTE customer_sales を2箇所で参照しており、同じCTEを再利用することで集計ロジックを重複して書かずに済みます。
  外側の FROM customer_sales で各顧客の合計金額を取得
  内側の FROM customer_sales で全顧客の合計金額の平均を計算
ただしBigQueryでは同じCTEを複数回参照した場合、必ず計算結果が一度だけ作成・再利用されるとは限らず、CTEの再利用は主にSQLの可読性や保守性を高めるためのものです。

練習問題として orders_null を使い、completed注文の顧客別合計金額を計算し、その合計金額が全顧客の平均合計金額よりも高い顧客を取得してください。
取得列は customer_id、total_amount：completed注文の合計金額、avg_total_amount：顧客別合計金額の全体平均
CTEは名前を customer_sales として1つだけ定義し、CTE内でcompleted注文の顧客別合計金額を計算し、NULLの金額は0として集計する。
最後のSELECTで customer_sales を2箇所以上参照し、JOINは使用せず、合計金額の降順、顧客IDの昇順で並べる。
顧客別合計金額が全体平均より大きい顧客だけを取得し、平均と等しい場合は含めない。
平均の計算対象は、customer_sales に存在する顧客として、completed注文のない顧客は平均の計算対象に含めない。
*/
WITH customer_sales AS (
  SELECT
    customer_id,
    SUM(IFNULL(amount, 0)) AS total_amount
  FROM `resonant-tract-508812-p9.sql_training.orders_null`
  WHERE status = 'completed'
  GROUP BY customer_id
)
SELECT
  customer_id,
  total_amount,
  (
    SELECT
      AVG(total_amount)
    FROM customer_sales
  ) AS avg_total_amount
FROM customer_sales
WHERE total_amount > (
  SELECT
    AVG(total_amount)
  FROM customer_sales
)
ORDER BY total_amount DESC, customer_id ASC;
/*なお、今回のように同じ平均値をSELECT句とWHERE句の両方で使用する場合、後で学習するウィンドウ関数などを使った別の書き方もあります。
追加の確認問題として、今回の平均金額を求める対象は注文1件ごとの amount ではなく顧客別に集計した total_amount ですが、この2つの平均は何が違うのでしょうか？
  指標                計算対象               意味
  AVG(amount)        各注文の金額            注文1件あたりの平均金額
  AVG(total_amount)  顧客別に集計した合計金額  顧客1人あたりの平均購入総額
今回のデータではcompleted注文が10件ありますがそのうち1件の注文はamountがNULLなので、AVG(amount) はNULLを除いた9件で計算します。
AVG(total_amount) は顧客別に集計した5行で計算します。*/

/*
STEP 9-6｜CTEで全体平均を計算し、JOINで結合する
全体平均を別のCTEとして定義し、JOINによって各顧客の集計結果と組み合わせます。
新しい構文「CROSS JOIN」の紹介で、CROSS JOIN は次ような[左側すべての行]と[右側すべての行]を組み合わせるJOINです。
テーブルA          /       テーブルB
id：1, 2, 3       /       category：X, Y

SELECT
  a.id,
  b.category
FROM テーブルA AS a
CROSS JOIN テーブルB AS b;

テーブルAとテーブルBを上記のように CROSS JOIN すると、結果は次のように テーブルAのid 3行 × テーブルBのcategory 2行 = 6行です。
  id	category
  1   X
  1   Y
  2   X
  2   Y
  3   X
  3   Y

CROSS JOIN には、通常の等価結合のような ON 条件を指定しません。
今回はこの性質を利用して、例えば右側が1行だけなら、左側の行数を増やさずに、その1行の値をすべての左側の行に付与できます。
例えば、顧客別売上が5行、全体平均が1行なら、CROSS JOINの結果は5行です。

練習問題として orders_null を使い、completed注文の顧客別合計金額と、その全体平均を取得し、全体平均より合計金額が高い顧客だけを表示してください。
取得列は customer_id、total_amount：completed注文の合計金額、avg_total_amount：顧客別合計金額の全体平均、difference：顧客別合計金額と全体平均との差額
合計金額が全体平均より大きい顧客だけを取得し、difference は total_amount - avg_total_amount で計算し、 NULLの金額は0として集計する。
次のCTEを定義し、スカラーサブクエリは使用せず、最後のSELECTでは各CTEを CROSS JOIN し、 difference の降順、customer_id の昇順で並べる。
  CTE1. customer_sales：completed注文の顧客別合計金額を集計する。
  CTE2. sales_average：customer_sales を参照し、AVG(total_amount) を計算する。
*/
WITH customer_sales AS (
  SELECT
    customer_id,
    SUM(IFNULL(amount, 0)) AS total_amount
  FROM `resonant-tract-508812-p9.sql_training.orders_null`
  WHERE status = 'completed'
  GROUP BY customer_id
),
sales_average AS (
  SELECT
    AVG(total_amount) AS avg_total_amount
  FROM customer_sales
)
SELECT
  s.customer_id,
  s.total_amount,
  a.avg_total_amount,
  s.total_amount - a.avg_total_amount AS difference
FROM customer_sales AS s
CROSS JOIN sales_average AS a
WHERE s.total_amount > a.avg_total_amount
ORDER BY difference DESC, s.customer_id ASC;
/*追加の確認問題
今回の sales_average は1行だけ返す想定ですが、仮に何らかの変更で sales_average が3行を返す場合、customer_sales が5行なら CROSS JOIN の結果は何行になるか？
また今回のような全体平均の付与処理で、なぜ右側のCTEが1行であることが重要なのでしょうか？

仮に sales_average が3行を返し、customer_sales が5行を返す状態で CROSS JOIN をしたら、3行×5行 = 15行の結果になります。
また今回のような全体平均の付与処理では、仮に右側のCTEが複数行であった場合、結果において同じ顧客の行が右側の各行と組み合わされて複製されてしまいます。
仮に顧客別集計が5行 右側の平均値が3行なら各顧客が3行ずつ現れ、この状態でさらに売上集計等をすると意図しない重複集計が発生する可能性があります。*/

/*
STEP 9-7｜CTEを使ったデータ品質チェック
少し視点を変えて、データの不整合を検出するSQLを作成します。
実務では、データを集計するだけでなく、マスタに存在しないIDや想定外のNULLが含まれていないかを確認することも重要です。
customers と customer_ranks を使います。

customers
customer_id：1, 2, 3, 4, 5, 6
customer_name：Tanaka, Sato, Suzuki, Takahashi, Ito, Watanabe

customer_ranks
customer_id：2, 3, 5, 7
customer_rank：silver, gold, bronze, gold

ここで注目してほしいのは customer_ranks の顧客ID7で、顧客ランクの情報は存在しますが顧客マスタには登録されていません。
こうしたデータを、今回は不整合として検出します。

顧客ランクが登録されているが、顧客マスタに存在しない顧客IDを customer_id、customer_rank、error_type：固定文字列 'missing_customer' を設定 の3列で取得。
今回は、これまで学習したOUTER JOINとNULL判定を組み合わせて考えてみてください。
次のCTEを定義し、JOINは種類や左右の配置を判断して使用し、最後のSELECTで顧客マスタに存在しない顧客IDだけを抽出し、顧客IDの昇順で並べる。
  CTE1. rank_data：customer_ranks の顧客IDと顧客ランクを取得する。
  CTE2. customer_data：customers の顧客IDを取得する。
*/
WITH rank_data AS (
  SELECT
    customer_id,
    customer_rank
  FROM `resonant-tract-508812-p9.sql_training.customer_ranks`
),
customer_data AS (
  SELECT
    customer_id
  FROM `resonant-tract-508812-p9.sql_training.customers`
)
SELECT
  r.customer_id,
  r.customer_rank,
  'missing_customer' AS error_type
FROM rank_data AS r
LEFT OUTER JOIN customer_data AS c
  ON r.customer_id = c.customer_id
WHERE c.customer_id IS NULL
ORDER BY r.customer_id ASC;
/*追加の確認問題
今回のような「片方のテーブルには存在するが、もう片方には存在しないデータ」を検出する処理は、NOT EXISTS でも実現できます。
OUTER JOINとNULL判定を使う方法と、NOT EXISTSを使う方法では、どのような考え方の違いがあるでしょうか？

今回は LEFT OUNTER JOIN と IS NULL を使いましたが、結合した際に値がNULLとなるテーブルの列を WHERE col IS NULL とすれば検出できます。
OUTER JOINとNULL判定を使う方法は結合結果の値がNULLであるかで考え、NOT EXISTS は値がNULLかを問わず次のSQLのように行がないかで考えます。
また NOT EXISTS は右側の一致行の有無だけを調べるため、右側に重複行があっても外側の行数は増えず、存在チェックだけが目的なら有力な選択肢です。*/
WITH rank_data AS (
  SELECT
    customer_id,
    customer_rank
  FROM `resonant-tract-508812-p9.sql_training.customer_ranks`
),
customer_data AS (
  SELECT
    customer_id
  FROM `resonant-tract-508812-p9.sql_training.customers`
)
SELECT
  r.customer_id,
  r.customer_rank,
  'missing_customer' AS error_type
FROM rank_data AS r
WHERE NOT EXISTS (
  SELECT
    1
  FROM customer_data AS c
  WHERE c.customer_id = r.customer_id
)
ORDER BY r.customer_id ASC;

/*
STEP 9-8｜CTEを使ったデータ加工パイプライン
データエンジニアリングでよくある「抽出 → 整形 → 集計 → 分類」の流れをSQLで作成します。
これまで学習したCTEを使い、処理を段階的に組み立ててください。

orders_null の注文データから、顧客別の購買状況を集計し、購入金額に応じて顧客を分類してください。
使用テーブルは orders_null と customers で、取得列は下記で、最後のSELECTで purchase_category を作成してください。
customer_id
customer_name
completed_order_count：completed注文件数
total_amount：completed注文の合計金額
average_order_amount：completed注文の平均金額
purchase_category：total_amountが10,000以上	high、5,000以上10,000未満	middle、5,000未満	low
次のCTEを定義し、合計金額の降順、次に顧客IDの昇順で並べてください。
  CTE1. completed_orders：orders_null からcompleted注文だけを抽出する。金額がNULLの場合は0に変換する。必要な列だけを取得する。
  CTE2. customer_sales：completed_orders を参照する。顧客IDごとに注文件数、合計金額、平均金額を計算する。
  CTE3. customer_summary：customers と customer_sales を結合。顧客マスタの6名全員を残す。completed注文がない顧客は、注文件数・合計金額・平均金額をすべて0。
*/
WITH completed_orders AS (
  SELECT
    customer_id,
    order_id,
    IFNULL(amount, 0) AS completed_amount
  FROM `resonant-tract-508812-p9.sql_training.orders_null`
  WHERE status = 'completed'
),
customer_sales AS (
  SELECT
    customer_id,
    COUNT(order_id) AS completed_order_count,
    SUM(completed_amount) AS total_amount,
    AVG(completed_amount) AS average_order_amount
  FROM completed_orders
  GROUP BY customer_id
),
customer_summary AS (
  SELECT
    c.customer_id,
    c.customer_name,
    IFNULL(s.completed_order_count, 0) AS completed_order_count,
    IFNULL(s.total_amount, 0) AS total_amount,
    IFNULL(s.average_order_amount, 0) AS average_order_amount
  FROM customer_sales AS s
  RIGHT OUTER JOIN `resonant-tract-508812-p9.sql_training.customers` AS c
    ON s.customer_id = c.customer_id
)
SELECT
  customer_id,
  customer_name,
  completed_order_count,
  total_amount,
  average_order_amount,
  CASE
    WHEN total_amount >= 10000 THEN 'high'
    WHEN total_amount >= 5000 THEN 'middle'
    ELSE 'low'
  END AS purchase_category
FROM customer_summary
ORDER BY total_amount DESC, customer_id ASC;
/*追加の確認問題
今回、CTE1. completed_orders で金額のNULLを0に変換してから、CTE2. customer_sales で平均を計算しています。
NULLを0に変換してから AVG() する場合と、NULLのまま AVG() する場合では、平均金額にどのような違いが生じるか、今回の顧客ID2（Sato）を例に説明してください。

顧客ID2（Sato）は、orders_null にて amountが7000でcancelledの注文 と amountがNULLでcompletedの注文、合計2件があります。
前提として今回はcompleted注文だけを抽出しており、顧客ID2（Sato）でこの条件に合うのは、amountがNULLでcompletedの注文1件だけです。
この状態で amount NULL を0に変換してから AVG() した場合、0(amount) ÷ 1(件) = 0 となります。
この状態で amount NULLのまま AVG() した場合、AVG および SUM は集計対象となる値がすべてNULLであれば結果は NULL を返します。
なお、COUNT(col) は集計対象となる値がすべてNULLであれば 0 を返し、COUNT(*) は値がNULLか問わず行があればカウントするので 1 を返します。*/

/*
STEP 9-9｜CTEを使ったデータ品質チェックと集計
ここでは、集計処理に加えてデータ品質の確認結果を出力する問題に進みます。
データエンジニアリングでは、売上を集計するだけでなく、欠損値がどれだけ含まれているかを確認することも重要です。

orders_null のcompleted注文について、顧客別に以下の情報を取得して、null_amount_count の降順、customer_id の昇順で並べてください。
customer_id
completed_order_count：completed注文件数
null_amount_count：金額がNULLのcompleted注文件数
total_amount：completed注文の合計金額
data_quality：NULL金額の注文が1件以上	needs_review、NULL金額の注文が0件	ok
次のCTEを定義し、最終SELECTでは quality_check を参照し、5列すべてを取得し、JOINは使用せず、completed注文がない顧客は今回の対象に含めない。
  CTE1. completed_orders：orders_null からcompleted注文だけを抽出。customer_id、order_id、amount を取得。ここではamountのNULLを0に変換しない。
  CTE2. customer_sales：completed_orders を参照。顧客単位に集計。completed注文件数を計算。金額がNULLの注文件数を計算。合計金額はNULLを0として扱う。
  CTE3. quality_check：customer_sales を参照する。null_amount_count を使って data_quality の分類を作成する。
*/
WITH completed_orders AS (
  SELECT
    customer_id,
    order_id,
    amount
  FROM `resonant-tract-508812-p9.sql_training.orders_null`
  WHERE status = 'completed'
),
customer_sales AS (
  SELECT
    customer_id,
    COUNT(order_id) AS completed_order_count,
    COUNT(*) - COUNT(amount) AS null_amount_count,
    SUM(IFNULL(amount, 0)) AS total_amount
  FROM completed_orders
  GROUP BY customer_id
),
quality_check AS (
  SELECT
    customer_id,
    completed_order_count,
    null_amount_count,
    total_amount,
    CASE
      WHEN null_amount_count >= 1 THEN 'needs_review'
      ELSE 'ok'
    END AS data_quality
  FROM customer_sales
)
SELECT
  customer_id,
  completed_order_count,
  null_amount_count,
  total_amount,
  data_quality
FROM quality_check
ORDER BY null_amount_count DESC, customer_id ASC;
/*追加の確認問題
今回、CTE1. completed_orders で amount のNULLを0に変換してしまうと、CTE2. customer_sales でNULL金額の注文件数を正しく数えられなくなります。
なぜ最初の段階でNULLを0に変換してしまうと、元のNULL件数が分からなくなるのでしょうか？
また、実務のデータ加工では、NULLを補完する前に欠損件数を確認することにどのような意味があると思いますか？

COUNT(*) は値がNULLか問わず行があればカウントし、COUNT(col) はNULLを除外して行をカウントします。
最初の段階でNULLを0に変換しない状態であれば、COUNT(*) - COUNT(amount) は「NULLも含む全行 - amountが非NULLの行 = amountがNULLの行数」になります。
最初の段階でNULLを0に変換してしまうと、上記の計算を使った元のNULL件数が出せません。
また、実務のデータ加工でNULLの補完前に欠損件数を確認することは、対象のデータが利活用に足る粒度か判断できる（欠損が多ければ使わない等）という意義があります。

COUNT(*) - COUNT(amount) については、BigQueryでは次のように書くこともでき、どちらも今回の要件では同じ結果になります。
COUNTIF(amount IS NULL)
COUNT(*) - COUNT(amount) はNULLの集計規則を利用した方法、COUNTIF(amount IS NULL) は条件に一致する行を直接数える方法です。

ただし「欠損が多いから使えない/少ないから使える」のではなく、例えば売上額の欠損が全体の1%でも、その1%が高額注文に集中していれば売上集計の影響が大きいです。
また、今回のようにNULLを0へ変換した場合は後からその0が「最初から0円」か「欠損を補完した0円」なのか区別できなくなります。
そのため実務では次のようなSQL設計も択で、これは元の値を保持しながら加工後の値と欠損フラグを別列に持たせる方法で、後からデータの状態を検証する際に使えます。*/
SELECT
  order_id,
  amount,
  IFNULL(amount, 0) AS transformed_amount,
  IF(amount IS NULL, 1, 0) AS amount_null_flag
FROM `resonant-tract-508812-p9.sql_training.orders_null`
WHERE status = 'completed';

/*
STEP 9-10｜CTE総合演習：データ品質と顧客集計
複数CTE、JOIN、NULL処理、集計、CASEによる分類を学習しました。
今回はそれらを組み合わせ、顧客マスタを基準とした集計・品質チェック用データを作成します。

customers と orders_null を使い、顧客マスタに登録されている全6名について、次の7列を取得し、completed注文の購買状況とデータ品質を一覧化してください。
customer_id
customer_name
completed_order_count：completed注文件数
null_amount_count：金額がNULLのcompleted注文件数
total_amount：completed注文の合計金額
purchase_category：合計金額10,000以上 high、5,000以上10,000未満 middle、合計金額5,000未満 low
data_quality：completed注文が0件 no_orders、completed注文が1件以上かつNULL金額が1件以上 needs_review、completed注文が1件以上かつNULL金額が0件 ok
NULL金額の件数は元のNULLを基準に計算、合計金額はNULLを0として扱い、completed注文がない顧客は注文件数・NULL金額件数・合計金額をすべて0とする。
CTEを3つ以上定義し、顧客マスタの6名全員を表示し、合計金額の降順と顧客IDの昇順で並べ、JOINの種類やCTE名や処理の分割方法は自分で判断する。
*/
WITH completed_extract AS (
  SELECT
    customer_id,
    COUNT(order_id) AS completed_order_count,
    COUNTIF(amount IS NULL) AS null_amount_count,
    SUM(IFNULL(amount, 0)) AS total_amount
  FROM `resonant-tract-508812-p9.sql_training.orders_null`
  WHERE status = 'completed'
  GROUP BY customer_id
),
customer_joined AS (
  SELECT
    c.customer_id,
    c.customer_name,
    IFNULL(e.completed_order_count, 0) AS completed_order_count,
    IFNULL(e.null_amount_count, 0) AS null_amount_count,
    IFNULL(e.total_amount, 0) AS total_amount
  FROM completed_extract AS e
  RIGHT OUTER JOIN `resonant-tract-508812-p9.sql_training.customers` AS c
    ON e.customer_id = c.customer_id
),
purchase_categorize AS (
  SELECT
    customer_id,
    customer_name,
    completed_order_count,
    null_amount_count,
    total_amount,
    CASE
      WHEN total_amount >= 10000 THEN 'high'
      WHEN total_amount >= 5000 THEN 'middle'
      ELSE 'low'
    END AS purchase_category
  FROM customer_joined
)
SELECT
  customer_id,
  customer_name,
  completed_order_count,
  null_amount_count,
  total_amount,
  purchase_category,
  CASE
    WHEN completed_order_count >= 1 AND null_amount_count >= 1 THEN 'needs_review'
    WHEN completed_order_count >= 1 AND null_amount_count = 0 THEN 'ok'
    ELSE 'no_orders'
  END AS data_quality
FROM purchase_categorize
ORDER BY total_amount DESC, customer_id ASC;
/*追加の確認問題
今回の data_quality は no_orders、needs_review、ok の3種類を区別しています。
なぜcompleted注文が0件の顧客を単純に ok と分類しないほうがよいのか、データ品質を確認する立場から考えてみてください。

completed注文が0件の顧客を単純に ok と分類した場合、completed注文が存在してamountもNULLではない＝欠損のないデータとの判定基準が曖昧になります。
ok はあくまで今回定義した「金額NULLチェックに問題がない」という意味で、データ全体の品質が保証されるわけではありません。*/


-- STEP 10｜日付・時刻の扱い
/*
BigQueryでは、日付や時刻を扱うために主に次のデータ型が用意されています。
  データ型    内容                              値の例
  DATE       年月日                            2026-01-05
  TIME       時分秒                            14:30:00
  DATETIME   年月日と時分秒（タイムゾーンなし）     2026-01-05 14:30:00
  TIMESTAMP  特定の時点                         2026-01-05 05:30:00 UTC
今回使用している orders と orders_null には　DATE型の order_date という列があり、この列を使って日付の抽出・計算・集計を学習します。

DATE型の基本操作として、まずは日付から年・月・日を取り出す方法で、BigQueryでは次のように EXTRACT() を使用できます。
*/
SELECT
  order_id,
  order_date,
  EXTRACT(YEAR FROM order_date) AS order_year,
  EXTRACT(MONTH FROM order_date) AS order_month,
  EXTRACT(DAY FROM order_date) AS order_day
FROM `resonant-tract-508812-p9.sql_training.orders`
ORDER BY order_id ASC;
/*EXTRACT() は日付や時刻から指定した部分を取り出す関数で、基本構文は次のとおりです。
  EXTRACT(取り出したい部分 FROM 日付や時刻)
なお、EXTRACT(MONTH ...) の結果は 1〜12 の整数で、02 のような文字列ではありません。*/

/*
STEP 10-1｜練習問題
練習問題として orders を使い、2026年2月のcompleted注文を取得し、注文日から年・月・日をそれぞれ抽出してください。
取得列は order_id、customer_id、order_date、order_year：注文年、order_month：注文月、order_day：注文日の日部分、amount
status = 'completed' の注文かつ2026年2月の注文のみ対象、EXTRACT() を使用、注文日の昇順と注文IDの昇順で並べ、JOINやCTEは使用しない。
*/
SELECT
  order_id,
  customer_id,
  order_date,
  EXTRACT(YEAR FROM order_date) AS order_year,
  EXTRACT(MONTH FROM order_date) AS order_month,
  EXTRACT(DAY FROM order_date) AS order_day,
  amount
FROM `resonant-tract-508812-p9.sql_training.orders`
WHERE status = 'completed'
  AND (order_date >= DATE '2026-02-01' AND order_date < DATE '2026-03-01')
ORDER BY order_date ASC, order_id ASC;
/*追加の確認問題
2026年2月の注文を抽出する場合、次の2つの条件にはどのような違いがあるでしょうか？
  1. EXTRACT(YEAR FROM order_date) = 2026 AND EXTRACT(MONTH FROM order_date) = 2
  2. order_date >= DATE '2026-02-01' AND order_date < DATE '2026-03-01'
上記はどちらでも今回の要件を満たせますが、BigQueryで大量のデータを扱う際はパーティションの設定次第で処理効率に違いが生じることがあり、この点も今後扱います。

今回の order_date がDATE型であれば、上の 1 と 2 は同じ日付を抽出しますが、違いは日付列をどう扱っているかです。
  1. EXTRACT方式：日付から年と月を取り出し、それぞれ比較する。
  2. 範囲指定方式：日付列そのものを開始日・終了日と比較する。

BigQueryで order_date が日付パーティション列になっている場合、後者のように列へ直接範囲条件を指定する方法は、パーティションの絞り込みを明確にしやすいです。
一方、EXTRACT() を使った条件も状況によって最適化される可能性があり、必ず処理量に差が出るわけではありません。
なお今回のようなDATE型では、終了日を含めない 2026-03-01 未満という指定が便利で、これは月末が28日、29日、30日、31日のどれかを意識する必要がありません。*/

/*
STEP 10-2｜DATE_ADD・DATE_SUB
日付に対して日数や月数を加算・減算する関数を学習します。
BigQueryでは、日付の加算に「DATE_ADD」を、日付の減算に「DATE_SUB」を使います。

基本的な構文は下記です。
  DATE_ADD(日付, INTERVAL 数値 DAY)
  DATE_SUB(日付, INTERVAL 数値 DAY)

SELECT
  DATE_ADD(DATE '2026-02-14', INTERVAL 7 DAY) AS seven_days_later,
  DATE_SUB(DATE '2026-02-14', INTERVAL 7 DAY) AS seven_days_earlier;

例えば上記のSQL結果は下記です。
  seven_days_later    seven_days_earlier
  2026-02-21          2026-02-07
DAY 以外にも WEEK や MONTH や YEAR などを指定でき、例えば INTERVAL 1 MONTH とすれば1か月の加算・減算です。

練習問題として orders を使い、completed注文のうち、2026年2月に発生した注文を取得してください。
取得列は order_id、customer_id、order_date、seven_days_later：注文日の7日後、three_days_earlier：3日前、one_month_later：1か月後、amount
DATE_ADD() と DATE_SUB() の両方を使用し、注文日の昇順と注文IDの昇順で並べ、JOIN・CTEは使用しない。
*/
SELECT
  order_id,
  customer_id,
  order_date,
  DATE_ADD(order_date, INTERVAL 7 DAY) AS seven_days_later,
  DATE_SUB(order_date, INTERVAL 3 DAY) AS three_days_earlier,
  DATE_ADD(order_date, INTERVAL 1 MONTH) AS one_month_later,
  amount
FROM `resonant-tract-508812-p9.sql_training.orders`
WHERE status = 'completed'
  AND (EXTRACT(YEAR FROM order_date) = 2026 AND EXTRACT(MONTH FROM order_date) = 2)
ORDER BY order_date ASC, order_id ASC;
/*追加の確認問題
2026年2月には31日が存在しませんが、次のSQLを実行するとBigQueryがどのような処理をして日付が返ると思いますか？
SELECT
  DATE_ADD(DATE '2026-01-31', INTERVAL 1 MONTH) AS result_date;

OracleのPL/SQLで 次のような構文の ADD_MONTHS() 関数がありました。
これは月末の日付に対して自動的な調整を行う仕様で、元の日付がその月の最終日（月末）ならば ADD_MONTHS は移行先の月の最終日（月末）を返します。
  ADD_MONTHS(TO_DATE('2026-01-31', 'YYYY-MM-DD'), 1) → 2026-02-28

BigQueryの DATE_ADD() は、MONTH、QUARTER、YEAR を指定した場合、移動先の月に同じ日が存在しなければ、その月の最終日に調整します。
  DATE_ADD(DATE '2026-01-31', INTERVAL 1 MONTH) → 2026-02-28
ただし、Oracleの ADD_MONTHS() と完全に同じではなく、例えば次のようなケースです。
            処理                               結果
  PL/SQL.ADD_MONTHS()：2026-02-28 ＋ 1 MONTH   2026-03-31
  BigQuery.DATE_ADD()：2026-02-28 ＋ 1 MONTH   2026-03-28
Oracleの ADD_MONTHS() は「元の日付が月末なら、移動先でも月末にする仕様」です。
BigQueryの DATE_ADD() は「移動先に同じ日が存在すれば、その日を使用する」なので、この違いは月次処理や請求日計算などで注意が必要です。*/

/*
STEP 10-3｜DATE_DIFF：日付間の差を計算する
次は、2つの日付の差を求める DATE_DIFF() で、次のような基本構文となり、第1引数から第2引数を引く順番です。
  DATE_DIFF(終了日, 開始日, DAY)

次のSQLの結果は4です。
SELECT
  DATE_DIFF(DATE '2026-02-14', DATE '2026-02-10', DAY)

次のSQLのように日付の順番を逆にすると負の値になり、結果は -4 です。
SELECT
  DATE_DIFF(DATE '2026-02-10', DATE '2026-02-14', DAY)

DAY以外の指定もでき、WEEK（週数）・MONTH（月数）・年数（YEAR）などを計算できます。
  DATE_DIFF(end_date, start_date, WEEK)
  DATE_DIFF(end_date, start_date, MONTH)
  DATE_DIFF(end_date, start_date, YEAR)

ただし、MONTH や YEAR のDATE_DIFFは、単純な経過日数を月数・年数に換算する関数ではありません。
SELECT
  DATE_DIFF(DATE '2026-03-01', DATE '2026-02-28', MONTH)
この結果は 1 で、実際の経過日数は1日ですが、これは2月から3月へ月の境界を月としてまたいでいるためです。

練習問題として今回は新しく学習した DATE_DIFF() に加え、customers と orders を使い、以前学習したCTE・集計関数・JOIN・NULL処理を復習します。
顧客マスタに登録されている全6名について、2026年1月1日から2026年3月31日までのcompleted注文を対象に、最初の注文日・最後の注文日・注文日の間隔について下記列で取得。
  customer_id
  customer_name
  completed_order_count：completed注文件数
  first_order_date：最初のcompleted注文日
  last_order_date：最後のcompleted注文日
  days_between_orders：最初と最後の注文日の差（日数）
CTEを2つ以上定義する。MIN()とMAX()を使って最初と最後の注文日を求める。completed注文がない顧客の completed_order_count は0とする。
completed注文がない顧客の first_order_date、last_order_date、days_between_orders はNULLのままとする。顧客IDの昇順で並べる。
*/
WITH completed_order AS (
  SELECT
    customer_id,
    COUNT(order_id) AS completed_order_count,
    MIN(order_date) AS first_order_date,
    MAX(order_date) AS last_order_date
  FROM `resonant-tract-508812-p9.sql_training.orders`
  WHERE status = 'completed'
    AND (order_date >= DATE '2026-01-01' AND order_date <= DATE '2026-03-31')
  GROUP BY customer_id
),
joined_customer AS (
  SELECT
    c.customer_id,
    c.customer_name,
    IFNULL(o.completed_order_count, 0) AS completed_order_count,
    o.first_order_date,
    o.last_order_date
  FROM completed_order AS o
  RIGHT OUTER JOIN `resonant-tract-508812-p9.sql_training.customers` AS c
    ON o.customer_id = c.customer_id
)
SELECT
  customer_id,
  customer_name,
  completed_order_count,
  first_order_date,
  last_order_date,
  DATE_DIFF(last_order_date, first_order_date, DAY) AS days_between_orders
FROM joined_customer
ORDER BY customer_id ASC;
/*追加の確認問題
completed注文が1件だけの顧客が存在しますが、今回のSQLではその顧客について下記を計算すると結果は何になるでしょうか？
DATE_DIFF(last_order_date, first_order_date, DAY)
また、completed注文が0件の顧客の場合はどうなるでしょうか？

completed注文が1件だけということは注文日が1つだけなので、MIN(order_date) と MAX(order_date) の DIFFがなく結果（日数差）は 0 です。
completed注文が0件の顧客というのは今回、2つ目のCTEでRIGHT OUTER JOINにて生まれた completed_order_count のNULLをIFNULLで0にしたものです。
completed注文が0件の顧客は MIN(order_date) と MAX(order_date) が NULLで、DATE_DIFF()の列にてNULL処理をしていないため結果もNULLです。*/

/*
STEP 10-4｜DATE_TRUNC：日付を指定した単位に切りそろえる
DATE_TRUNC() は、実務にて日別データを月別・週別などにまとめる際に使用します。

基本構文例は下記です。
  DATE_TRUNC(日付, MONTH)

SELECT
  DATE_TRUNC(DATE '2026-02-14', MONTH) AS month_start,
  DATE_TRUNC(DATE '2026-02-14', YEAR) AS year_start

上記SQLの結果は下記となり、DATE_TRUNC() はMONTHやYEARなど指定した単位の[開始日]に日付を切りそろえるもので[MONTH なら月初]で[YEAR なら年初]です。
  month_start  year_start
  2026-02-01   2026-01-01

SELECT
  EXTRACT(MONTH FROM DATE '2026-02-14') AS order_month,
  DATE_TRUNC(DATE '2026-02-14', MONTH) AS order_month_start

上記SQLの結果は下記となり、月次集計では DATE_TRUNC() を使うと年月を含む日付として扱えるため便利です。
  order_month   order_month_start
  2             2026-02-01
- EXTRACT(MONTH ...)：月を整数で取り出す。
- DATE_TRUNC(..., MONTH)：月初の日付をDATE型で返す。

練習問題として今回は新しい DATE_TRUNC() に加え、orders を使い、以前学習した GROUP BY、集計関数、COUNTIF()、HAVING を組み合わせます。
2026年1月〜3月の月別注文状況をcompleted注文だけでなくcancelled注文も含めて集計して下記列を取得してください。
  order_month：注文月の月初日
  total_order_count：全注文件数
  completed_order_count：completed注文件数
  cancelled_order_count：cancelled注文件数
  completed_total_amount：completed注文の合計金額
DATE_TRUNC() で月初日を取得。completed注文が2件以上存在する月だけを出力する。注文月の昇順で並べる。JOINとCTEは使用しない。
*/
SELECT
  order_month,
  COUNT(order_id) AS total_order_count,
  COUNTIF(status = 'completed') AS completed_order_count,
  COUNTIF(status = 'cancelled') AS cancelled_order_count,
  SUM(IF(status = 'completed', amount, 0)) AS completed_total_amount
FROM (
  SELECT
    DATE_TRUNC(order_date, MONTH) AS order_month,
    order_id,
    status,
    amount
  FROM `resonant-tract-508812-p9.sql_training.orders`
  WHERE order_date >= DATE '2026-01-01' AND order_date < DATE '2026-04-01'
)
GROUP BY order_month
HAVING COUNTIF(status = 'completed') >= 2
ORDER BY order_month ASC;
/*追加の確認問題
今回のSQLでは、次の2つの条件を区別する必要がありますが、この2つの条件について WHERE と HAVING のどちらで指定するのが適切でしょうか？
  A：2026年1月〜3月の注文だけを集計対象にする。
  B：集計した結果、completed注文が2件以上ある月だけを表示する。

A に適切なのはWHERE句で、これは DATEの order_date から2026年1月〜3月の行を絞り込む必要があるからです。
B に適切なのはHAVING句で、これは集計結果のグループについてcompleted注文が2件以上ある月だけをさらに絞り込む必要があるからです。*/

/*
STEP 10-5｜CURRENT_DATEと日付型の変換
次は、現在の日付の取得と、文字列からDATE型への変換です。

- CURRENT_DATE()：現在の日付を取得する
- CURRENT_DATE('Asia/Tokyo')：日本時間で現在の日付を取得する
SELECT
  CURRENT_DATE()
  CURRENT_DATE('Asia/Tokyo')
CURRENT_DATE() は、タイムゾーンを省略するとUTC基準になり、日本時間で日付を扱いたい場合 'Asia/Tokyo' を指定できます。

- CAST(文字列 AS DATE)：文字列をDATE型に変換する
- SAFE_CAST(文字列 AS DATE)：変換できない場合、エラーではなくNULLを返す
SELECT
  CAST('2026-02-14' AS DATE) AS order_date,
  SAFE_CAST('invalid-date' AS DATE) AS invalid_date
結果
  order_date    invalid_date
  2026-02-14    NULL
CAST('invalid-date' AS DATE) はエラーになりますが SAFE_CAST(…) ならNULLになり、データ取り込み時に日付として不正な文字列がある場合などに使えます。

- FORMAT_DATE()：DATE型を指定した形式の文字列に変換する
SELECT
  FORMAT_DATE('%Y/%m/%d', DATE '2026-02-14') AS formatted_date,
  FORMAT_DATE('%Y-%m', DATE '2026-02-14') AS year_month
結果
  formatted_date   year_month
  2026/02/14       2026-02
FORMAT_DATE() の結果はDATE型ではなく、STRING型です。

練習問題として今回は SAFE_CAST() と、以前学習した CASE・CTEを組み合わせます。
実際のデータ取り込みでは日付が文字列で保存されていることがありその中に不正な値が混ざっていた場合を想定し、今回はテーブルを新規作成せず次のCTEをそのまま使用します。
WITH raw_orders AS (
  SELECT
    1 AS order_id,
    '2026-01-05' AS order_date_text
  UNION ALL
  SELECT
    2, '2026-02-14'
  UNION ALL
  SELECT
     3, 'invalid-date'
  UNION ALL
  SELECT
    4, '2026-03-25'
  UNION ALL
  SELECT
    5, NULL
  UNION ALL
  SELECT
    6, '2026-02-30'
)
各注文について、日付文字列をDATE型に変換し、データ品質を分類してください。
取得列は order_id、order_date_text、order_date：DATE型に変換した日付、year_month：YYYY-MM形式の文字列
date_quality：元の日付文字列がNULLなら missing、元の文字列がNULLではないがDATE型に変換できないなら invalid、DATE型に正常に変換できたなら valid
提示した raw_orders CTEを使用し、CTEをさらに1つ以上追加。SAFE_CAST() を使用。FORMAT_DATE() を使用。6件すべて表示する。注文IDの昇順で並べる。
*/
WITH raw_orders AS (
  SELECT
    1 AS order_id,
    '2026-01-05' AS order_date_text
  UNION ALL
  SELECT
    2, '2026-02-14'
  UNION ALL
  SELECT
     3, 'invalid-date'
  UNION ALL
  SELECT
    4, '2026-03-25'
  UNION ALL
  SELECT
    5, NULL
  UNION ALL
  SELECT
    6, '2026-02-30'
),
transformed_date AS (
  SELECT
    order_id,
    order_date_text,
    SAFE_CAST(order_date_text AS DATE) AS order_date,
    FORMAT_DATE('%Y-%m', SAFE_CAST(order_date_text AS DATE)) AS year_month
  FROM raw_orders
)
SELECT
  order_id,
  order_date_text,
  order_date,
  year_month,
  CASE
    WHEN order_date_text IS NULL THEN 'missing'
    WHEN order_date IS NULL THEN 'invalid'
    ELSE 'valid'
  END AS date_quality
FROM transformed_date
ORDER BY order_id ASC;
/*追加の確認問題
今回のデータには order_date_text に '2026-02-30' と NULL が含まれており、どちらも SAFE_CAST(... AS DATE) の結果はNULLになります。
それにもかかわらず、date_quality を invalid と missing に分ける必要があるのはなぜでしょうか？
また、今回のSQLで SAFE_CAST() の結果だけを見て分類すると、どのような問題が起こるでしょうか？

order_date_text がそもそもNULLである=missing と、NULLではないがDATEに変換できない（有効ではない）=invalid は意味が異なるからです。
SAFE_CAST(…) AS order_date の結果だけを見ると、それらが元々欠損状態か欠損ではないが不正な値（DATAに有効ではないデータ型）か判断できません。*/

/*
STEP 10-6｜DATETIME・TIMESTAMP・タイムゾーン
データ型     意味                         例
DATE        日付                         2026-10-18
DATETIME    タイムゾーン情報を持たない日時   2026-10-18 15:30:00
TIMESTAMP   世界共通の特定の時点           2026-10-18 06:30:00 UTC

DATETIME '2026-10-18 15:30:00' だけではそれが日本時間なのかUTCなのか分からず、例えば日本時間の2026-10-18 15:30は、UTCでは同日6:30です。
BigQueryでは次のように変換できます。
SELECT
  TIMESTAMP(DATETIME '2026-10-18 15:30:00', 'Asia/Tokyo')

また、TIMESTAMPから日本時間の日時を取り出す場合は、次のようにします。
SELECT
  DATETIME(TIMESTAMP '2026-10-18 06:30:00+00', 'Asia/Tokyo')

練習問題として今回はタイムゾーンによる日付のずれを確認します。
次のCTEを使用してください。
WITH events AS (
  SELECT
    1 AS event_id,
    TIMESTAMP '2026-10-17 14:30:00+00' AS event_timestamp
  UNION ALL
  SELECT
    2,
    TIMESTAMP '2026-10-17 15:30:00+00'
  UNION ALL
  SELECT
    3,
    TIMESTAMP '2026-10-18 06:00:00+00'
  UNION ALL
  SELECT
    4,
    TIMESTAMP '2026-10-18 16:00:00+00'
)

各イベントについて、UTCと日本時間の日付を比較してください。
取得列は event_id、event_timestamp、event_date_utc：UTC基準の日付、event_date_jst：日本時間の日付、event_datetime_jst：日本時間のDATETIME
date_changed：UTCと日本時間で日付が異なれば1、同じなら0
DATE() を使用してUTCと日本時間の日付を取得。DATETIME() を使用して日本時間の日時を取得。
CASE または IF を使用して date_changed を作成。4件すべてを表示。event_id の昇順で並べる。JOIN・集計・COUNTIFは不要。*/
WITH events AS (
  SELECT
    1 AS event_id,
    TIMESTAMP '2026-10-17 14:30:00+00' AS event_timestamp
  UNION ALL
  SELECT
    2,
    TIMESTAMP '2026-10-17 15:30:00+00'
  UNION ALL
  SELECT
    3,
    TIMESTAMP '2026-10-18 06:00:00+00'
  UNION ALL
  SELECT
    4,
    TIMESTAMP '2026-10-18 16:00:00+00'
),
get_date AS (
  SELECT
    event_id,
    event_timestamp,
    DATE(event_timestamp) AS event_date_utc,
    DATE(event_timestamp, 'Asia/Tokyo') AS event_date_jst,
    DATETIME(event_timestamp, 'Asia/Tokyo') AS event_datetime_jst
  FROM events
)
SELECT
  event_id,
  event_timestamp,
  event_date_utc,
  event_date_jst,
  event_datetime_jst,
  IF(
    DATE_DIFF(event_date_utc, event_date_jst, DAY) != 0, 1, 0
  ) AS date_changed
FROM get_date
ORDER BY event_id ASC;
/*追加の確認問題
GA4などのイベントデータを日別に集計するとき
UTCの日付をそのまま使う場合と、日本時間に変換してから日付を取得する場合では、どのような問題が生じる可能性があるでしょうか？

例えば月別での集計において日本時間に変換すると月をまたいでしまうケースや、特定期間のキャンペーン施策を検討する際に時差が出るなどの問題があります。
GA4の event_date は通常はプロパティで設定されたタイムゾーンに基づく日付で、event_timestamp はUTC基準で表すため、両者を組み合わせる際は注意です。*/

/*
STEP 10-7｜日付・時刻の総合演習
日付処理・CTE・JOIN・集計関数・CASE・NULL処理を復習します。
顧客マスタに登録されている全6名について、2026年1月1日以上で2026年4月1日未満のcompleted注文を集計し、最終注文日から基準日までの経過日数に応じて顧客を分類。
customers と orders を使い、completed注文がない顧客の注文件数・合計金額は0として、completed注文がない顧客の最終注文日・経過日数はNULLとする。
  customer_id
  customer_name
  completed_order_count：completed注文件数
  total_amount：completed注文の合計金額
  last_order_date：最後のcompleted注文日
  days_since_last_order：基準日2026年4月1日から最終注文日までの経過日数
  customer_status：completed注文が0件 no_orders、最終注文日からの経過日数が30日以内 active、経過日数が31日以上60日以内 at_risk、61日以上 inactive
CTEを2つ以上使用。DATE_DIFF() を使用。CASE を使用。顧客IDの昇順で並べる。
*/
WITH order_from202601_to202603 AS (
  SELECT
    customer_id,
    COUNT(order_id) AS completed_order_count,
    SUM(amount) AS total_amount,
    MAX(order_date) AS last_order_date,
    DATE_DIFF(DATE '2026-04-01', MAX(order_date), DAY) AS days_since_last_order
  FROM `resonant-tract-508812-p9.sql_training.orders`
  WHERE status = 'completed'
    AND (order_date >= DATE '2026-01-01' AND order_date < DATE '2026-04-01')
  GROUP BY customer_id
),
customer_joined AS (
  SELECT
    c.customer_id,
    c.customer_name,
    IFNULL(o.completed_order_count, 0) AS completed_order_count,
    IFNULL(o.total_amount, 0) AS total_amount,
    o.last_order_date,
    o.days_since_last_order
  FROM order_from202601_to202603 AS o
  RIGHT OUTER JOIN `resonant-tract-508812-p9.sql_training.customers` AS c
    ON o.customer_id = c.customer_id
)
SELECT
  customer_id,
  customer_name,
  completed_order_count,
  total_amount,
  last_order_date,
  days_since_last_order,
  CASE
    WHEN completed_order_count = 0 THEN 'no_orders'
    WHEN days_since_last_order <= 30 THEN 'active'
    WHEN days_since_last_order BETWEEN 31 AND 60 THEN 'at_risk'
    ELSE 'inactive'
  END AS customer_status
FROM customer_joined
ORDER BY customer_id ASC;
/*追加の確認問題
今回のような顧客分類を行う場合、基準日を CURRENT_DATE() ではなく、固定の DATE '2026-04-01' にすることには、どのような利点があるでしょうか？
特に、同じSQLを後日再実行した場合の結果という観点から考えてください。

CURRENT_DATE() は実行時点における現在の日付を返すため、CURRENT_DATE() を基準日にすると実行タイミングによって経過日数のずれが生じます。
固定の基準日を使うことで、実行タイミングに関係なく経過日数に応じた顧客分類について再現性のある結果が得られます。
例えば、過去の2026年4月1日時点の顧客分類を再計算したい場合、CURRENT_DATE() を使うと当時の状態を再現できません。*/






