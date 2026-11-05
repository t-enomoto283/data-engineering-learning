-- STEP 0｜練習環境を作る
CREATE SCHEMA IF NOT EXISTS `resonant-tract-508812-p9.sql_training`
OPTIONS (
  location = 'US'
);

/*
まずは orders という注文データ1テーブルだけから始めます。JOINを学ぶ段階になったら customers などを追加します。

今このSQLでやっていること
- CREATE SCHEMA：データセットを作る
- IF NOT EXISTS：すでに存在してもエラーにしない
- sql_training：今回のSQL練習専用データセット名
- location = 'US'：データセットの保存ロケーション

つまり、
resonant-tract-508812-p9
└── sql_training

という練習場所を作るだけです。
今回はSQLの基礎学習が目的なので、このCREATE文を自力で書けるようになる必要は現時点ではありません。

次は、この中に学習でずっと使う orders テーブルを作ります。
ただし、ここは「テーブル作成SQLの勉強」が目的ではないので、私がSQLを提示します。今は中身を細かく理解しなくて大丈夫です。
*/
CREATE OR REPLACE TABLE `resonant-tract-508812-p9.sql_training.orders` AS
SELECT 1001 AS order_id, 1 AS customer_id, DATE '2026-01-05' AS order_date, 3200 AS amount, 'completed' AS status
UNION ALL
SELECT 1002, 2, DATE '2026-01-05', 5800, 'completed'
UNION ALL
SELECT 1003, 1, DATE '2026-01-12', 2100, 'completed'
UNION ALL
SELECT 1004, 3, DATE '2026-01-15', 7500, 'cancelled'
UNION ALL
SELECT 1005, 2, DATE '2026-02-03', 4200, 'completed'
UNION ALL
SELECT 1006, 4, DATE '2026-02-08', 8900, 'completed'
UNION ALL
SELECT 1007, 1, DATE '2026-02-14', 6100, 'completed'
UNION ALL
SELECT 1008, 3, DATE '2026-02-20', 3300, 'completed'
UNION ALL
SELECT 1009, 5, DATE '2026-03-02', 12000, 'completed'
UNION ALL
SELECT 1010, 2, DATE '2026-03-10', 2700, 'cancelled'
UNION ALL
SELECT 1011, 4, DATE '2026-03-18', 5400, 'completed'
UNION ALL
SELECT 1012, 1, DATE '2026-03-25', 9800, 'completed'
;

/*
このテーブルは、次の5列・12件の注文データです。
これらが後で WHERE、GROUP BY、WITH句、ウィンドウ関数などを学ぶ材料になります。
  order_id
  customer_id
  order_date
  amount
  status

わざと、次のようにしています。
- 同じ顧客が複数回注文している
- 注文日が異なる
- 金額が異なる
- completed と cancelled が混在する
*/


-- STEP 1｜SELECT / FROM / WHERE
/*
STEP 1-1｜最初の問題
orders テーブルから、
注文金額（amount）が5,000以上の注文について、order_id、customer_id、amountを取得してください。
*/
SELECT order_id, customer_id, amount
FROM `resonant-tract-508812-p9.sql_training.orders` -- `プロジェクトID.データセット名.テーブル名`
WHERE amount > 5000
;

/*
STEP 1-2｜WHEREをもう少し練習
orders テーブルから、
status が completed かつ amount が5,000以上の注文について、
order_id、customer_id、amount、status を取得してください。
*/
SELECT order_id, customer_id, amount, status
FROM `resonant-tract-508812-p9.sql_training.orders`
WHERE status = 'completed' AND amount >= 5000
;

/*
STEP 1-3｜OR
orders テーブルから、
status が cancelled または amount が8,000以上の注文について、
order_id、customer_id、amount、status を取得してください。
*/
SELECT
  order_id,
  customer_id,
  amount,
  status
FROM `resonant-tract-508812-p9.sql_training.orders`
WHERE status = 'cancelled' OR amount >= 8000;

/*
STEP 1-4｜ANDとORを組み合わせる
status が completed であり、さらに customer_id が1 または 4 の注文を取得する。
取得する列は、order_id、customer_id、amount、status
*/
SELECT
  order_id,
  customer_id,
  amount,
  status
FROM `resonant-tract-508812-p9.sql_training.orders`
WHERE status = 'completed'
  AND (customer_id = 1 OR customer_id = 4)
;
/*なぜ () が重要なのか
もし、
WHERE status = 'completed'
  AND customer_id = 1
  OR customer_id = 4

と書くと、SQLでは AND が OR より先に評価されるため、実質、
(status = 'completed' AND customer_id = 1)
OR
customer_id = 4

という意味になります。
すると、customer_id = 4なら、cancelledでも対象になり得るわけです。*/

/*
STEP 1-5｜IN
先ほどとまったく同じ条件・同じ結果になるSQLを、今度は OR を使わず、IN を使って書き直してください。
条件は、status が completed かつ customer_id が1または4 です。
取得列も同じ4列です。
*/
SELECT
  order_id,
  customer_id,
  amount,
  status
FROM `resonant-tract-508812-p9.sql_training.orders`
WHERE status = 'completed' AND customer_id IN (1, 4)
;
/*WHERE status = 'completed'
  AND customer_id IN (1, 4)
は、
WHERE status = 'completed'
  AND (customer_id = 1 OR customer_id = 4)
と今回の条件では同じ意味です。*/

/*
STEP 1-6｜BETWEEN

例えば、amountが3,000以上8,000以下 は、
amount >= 3000 AND amount <= 8000 と書けます。
SQLではこれを BETWEEN でも表現できます。
amount BETWEEN 3000 AND 8000
ここで重要なのは、BETWEEN は両端を含むことです。
つまり、3000 <= amount <= 8000 という意味です。
orders テーブルから、amount が 3,000以上8,000以下 の注文について、order_id、customer_id、amount、status を取得してください。
*/
SELECT
  order_id,
  customer_id,
  amount,
  status
FROM `resonant-tract-508812-p9.sql_training.orders`
WHERE amount BETWEEN 3000 AND 8000
;
/*もしかすると「8,000未満」にするために7999としたのかもしれませんが、問題文は「8,000以下」なので8000をそのまま指定します。
また、金額が整数とは限らないデータなら、7999 にする方法自体が危険です。たとえば 7999.50 が存在すると漏れてしまいます。*/

/*
STEP 1-7｜「以上・未満」
今度は条件を少し変えます。
amount が 3,000以上8,000未満 の注文について、order_id、customer_id、amount、statusを取得してください。
今回は、BETWEENは使わないでください。ポイントは、3,000以上 8,000未満 という日本語を、それぞれどの比較演算子にするかです。
*/
SELECT
  order_id, customer_id, amount, status
FROM `resonant-tract-508812-p9.sql_training.orders`
WHERE amount >= 3000 AND amount < 8000
;

/*
STEP 1-8｜日付をWHEREで絞る
次は order_date を使います。
BigQueryでは今回の order_date は DATE型として作ってあります。
orders テーブルから、2026年2月1日から2026年2月28日までに注文されたデータについて、order_id、customer_id、order_date、amount を取得してください。
今回はまず、これまで覚えた BETWEENを使って書いてみましょう。
一つだけ新しい情報を出します。BigQueryでDATE型の日付を直接書く場合は、DATE '2026-02-01'と書けます。
*/
SELECT
  order_id, customer_id, order_date, amount
FROM `resonant-tract-508812-p9.sql_training.orders`
WHERE order_date BETWEEN DATE'2026-02-01' AND DATE '2026-02-28'
;
/*あなたは、WHERE order_date BETWEEN '2026-02-01' AND '2026-02-28' と書きました。
今回はBigQueryが文字列をDATE型として扱える形だったため実行できています。
ただ、order_date は今回 DATE型として作った列なので、型を明示して、
WHERE order_date BETWEEN DATE '2026-02-01' AND DATE '2026-02-28'
と書く方が、「DATE型とDATE型を比較している」ことが明確です。今回の学習ではこちらを基本形として覚えましょう。*/

/*
STEP 1-9｜ここまでの複合問題
少しだけこれまでの内容を組み合わせます。
orders テーブルから、2026年2月1日～2026年3月31日の注文のうち、status が completed で、amount が 5,000以上の注文を取得してください。
取得する列は、order_id、customer_id、order_date、amount、status
*/
SELECT
 order_id, customer_id, order_date, amount, status
FROM `resonant-tract-508812-p9.sql_training.orders`
WHERE order_date BETWEEN DATE '2026-02-01' AND DATE '2026-03-31'
  AND status = 'completed'
  AND amount >= 5000
;

/*
STEP 1-10｜複合条件
2026年1月1日～2026年3月31日の注文のうち、status が completed で、さらに「customer_id が1または2」または「amountが10,000以上」の注文を取得する。
取得列：order_id、customer_id、order_date、amount、status
日本語の論理構造は、期間内 AND completed AND（customer_idが1または2 OR amountが10,000以上）です。
ただし、この構造をそのままSQLに写すだけではなく、どう書けばこの意味になるかを自分で考えてください。
*/
SELECT
  order_id, customer_id, order_date, amount, status
FROM `resonant-tract-508812-p9.sql_training.orders`
WHERE order_date BETWEEN DATE '2026-01-01' AND DATE '2026-03-31'
  AND status = 'completed'
  AND (customer_id IN (1, 2) OR amount >= 10000)
;


-- STEP 2｜ORDER BY / LIMIT / DISTINCT
/*
STEP 2-1｜最初の問題
orders テーブルから、order_id、customer_id、amount を取得し、amountが高い順に並べてください。
*/
SELECT
  order_id, customer_id, amount
FROM `resonant-tract-508812-p9.sql_training.orders`
ORDER BY amount DESC
;

/*
STEP 2-2｜複数列でORDER BY
実務では、第1条件が同じだった場合に、第2条件で並べることがよくあります。
基本形は、ORDER BY 列A ASC, 列B DESC です。
これは、まず列Aで昇順 → 列Aが同じ行同士では列Bで降順 という意味です。
orders テーブルから、order_id、customer_id、order_date、amount を取得する。
まずcustomer_idの小さい順に並べ、同じcustomer_idの中ではamountの高い順に並べてください。
*/
SELECT
  order_id, customer_id, order_date, amount
FROM `resonant-tract-508812-p9.sql_training.orders`
ORDER BY 2 ASC, 4 DESC
;

/*
STEP 2-3｜LIMIT
LIMIT は、結果を最大何行まで返すかを指定します。
LIMIT 5なら最大5行です。
orders テーブルから、order_id、customer_id、amountを取得し、注文金額が高い順に上位3件だけ取得してください。
*/
SELECT
  order_id, customer_id, amount
FROM `resonant-tract-508812-p9.sql_training.orders`
ORDER BY amount DESC
LIMIT 3
;

/*
STEP 2-4｜DISTINCT
orders テーブルから、注文履歴に存在する customer_id を、重複なしで取得してください。さらに、customer_id の小さい順に並べてください。
今回は新しく DISTINCT を使います。ヒントとして基本形だけ示すと、SELECT DISTINCT 列名　FROM ...　です。
*/
SELECT
  DISTINCT customer_id
FROM `resonant-tract-508812-p9.sql_training.orders`
ORDER BY 1 ASC
;
/*DISTINCT は「特定の列だけの重複を消す」と覚えると、後で少し混乱します。正確には、SELECTした列の組み合わせについて重複を除くものです。
たとえば、SELECT DISTINCT customer_id, status FROM ...とすると、customer_id × status の組み合わせが同じ行を重複として除外するという意味になります。*/

/*
STEP 2-5｜複数列のDISTINCT
orders テーブルから、customer_id と status の組み合わせを重複なしで取得してください。
さらに、customer_id の小さい順、同じcustomer_idなら status の昇順 にしてください。
取得するのはこの2列だけです。customer_id、status
*/
SELECT DISTINCT
  customer_id, status
FROM `resonant-tract-508812-p9.sql_training.orders`
ORDER BY 1 ASC, 2 ASC
;

/*
STEP 2-6｜仕上げ問題
ORDER BY + LIMIT + DISTINCTを一度組み合わせてみましょう。
orders テーブルから、completed の注文をしたことがある customer_id を重複なしで取得し、customer_idの大きい順に並べ、上位3件だけ取得してください。
取得する列は customer_id だけです。
*/
SELECT DISTINCT
  customer_id
FROM `resonant-tract-508812-p9.sql_training.orders`
WHERE status = 'completed'
ORDER BY 1 DESC
LIMIT 3
;


-- STEP 3｜集計関数
/*
STEP 3-1｜COUNT
orders テーブルについて、statusがcompletedの注文が全部で何件あるかを求めてください。
結果は注文データそのものではなく、completed_order_count:○○ という1行1列になるようにしてください。
*/
SELECT
  COUNT(*) AS completed_order_count
FROM `resonant-tract-508812-p9.sql_training.orders`
WHERE status = 'completed'
;

/*
STEP 3-2｜SUM
orders テーブルについて、status が completed の注文だけを対象として、注文金額 amount の合計を求めてください。
結果の列名は、completed_total_amount としてください。
*/
SELECT
  SUM(amount) AS completed_total_amount
FROM `resonant-tract-508812-p9.sql_training.orders`
WHERE status = 'completed'
;

/*
STEP 3-3｜AVG
orders テーブルについて、status が completed の注文だけを対象として、注文金額 amount の平均値を求めてください。
結果の列名は、completed_avg_amount としてください。
*/
SELECT
  AVG(amount) AS completed_avg_amount
FROM `resonant-tract-508812-p9.sql_training.orders`
WHERE status = 'completed'
;

/*
STEP 3-4｜MIN / MAX
orders テーブルの completed の注文について、次の4つを同時に求めてください。
注文件数、合計金額、最小注文金額、最大注文金額
列名はそれぞれ、order_count、total_amount、min_amount、max_amount としてください。
*/
SELECT
  COUNT(*) AS order_count,
  SUM(amount) AS total_amount,
  MIN(amount) AS min_amount,
  MAX(amount) AS max_amount
FROM `resonant-tract-508812-p9.sql_training.orders`
WHERE status = 'completed'
;

/*
STEP 3-5｜COUNTのもう一段深い理解
次へ行く前に、COUNT について一つ覚えておきたい違いがあります。
COUNT(*) と、COUNT(amount) は、常に同じとは限りません。
基本的には、
- COUNT(*) → 行そのものを数える
- COUNT(amount) → amountがNULLではない行を数える
という違いがあります。今の orders には amount のNULLがないので、どちらも12になります。
ただし実務データではNULLは普通に出てくるので、これは後の STEP 6｜NULL で実際にデータを追加して詳しくやります。
*/

/*
STEP 3-5｜集計関数の仕上げ問題
orders テーブルについて、2026年2月の completed 注文だけを対象として、注文件数・平均注文金額・最小注文金額・最大注文金額を求めてください。
列名は、order_count、avg_amount、min_amount、max_amount としてください。
*/
SELECT
  COUNT(amount) AS order_count,
  AVG(amount) AS avg_amount,
  MIN(amount) AS min_amount,
  MAX(amount) AS max_amount
FROM `resonant-tract-508812-p9.sql_training.orders`
WHERE order_date BETWEEN DATE '2026-02-01' AND DATE '2026-02-28'
  AND status = 'completed'
;
/*今回、COUNT(amount) と書いていますね。これは今回は正しく4になります。amount にNULLがないからです。
ただ、問題文は「注文件数」でした。この意味をより忠実にSQLへ落とすなら、COUNT(*) のほうが適しています。
つまり、
COUNT(*)       -- 条件に該当する注文（行）は何件か
COUNT(amount)  -- amountがNULLではないものは何件か です。*/


-- STEP 4｜GROUP BY
/*
STEP 4-1 問題
orders テーブルについて、customer_idごとの注文件数を求めてください。customer_idの小さい順に並べてください。
取得列は、customer_id、order_countです。
*/
SELECT
  customer_id,
  COUNT(*) AS order_count
FROM `resonant-tract-508812-p9.sql_training.orders`
GROUP BY customer_id
ORDER BY 1 ASC
;

/*
STEP 4-2｜WHERE + GROUP BY
status が completed の注文だけを対象として、customer_idごとの合計注文金額を求めてください。合計注文金額が大きい順に並べてください。
取得列は、customer_id、total_amount とし、total_amount は SUM(amount) で求めます。
*/
SELECT
  customer_id,
  SUM(amount) AS total_amount
FROM `resonant-tract-508812-p9.sql_training.orders`
WHERE status = 'completed'
GROUP BY customer_id
ORDER BY 2 DESC
;

/*
STEP 4-3｜HAVING
orders テーブルから、completed の注文だけを対象として、customer_idごとの合計注文金額を求め、合計注文金額が10,000以上の顧客だけ取得してください。
合計注文金額の大きい順に並べてください。
取得列は、customer_id、total_amountです。
*/
SELECT
  customer_id,
  SUM(amount) AS total_amount
FROM `resonant-tract-508812-p9.sql_training.orders`
WHERE status = 'completed'
GROUP BY customer_id
HAVING SUM(amount) >= 10000
ORDER BY 2 DESC;

/*
STEP 4-4｜複数列でGROUP BY
orders テーブルについて、customer_idとstatusの組み合わせごとに、注文件数と合計注文金額を求めてください。
customer_idの小さい順、同じcustomer_idならstatusの昇順に並べてください。
取得列は、customer_id、status、order_count、total_amount としてください。
*/
SELECT
  customer_id,
  status,
  COUNT(*) AS order_count,
  SUM(amount) AS total_amount
FROM `resonant-tract-508812-p9.sql_training.orders`
GROUP BY customer_id, status
ORDER BY 1 ASC, 2 ASC;

/*
STEP 4-5｜GROUP BY / HAVING 仕上げ
orders テーブルから、completedの注文だけを対象として、customer_idごとの注文件数と平均注文金額を求めてください。
そのうち、completedの注文を2件以上している顧客だけを取得してください。
注文件数の多い順、注文件数が同じ場合は平均注文金額の高い順に並べてください。
取得列は、customer_id、order_count、avg_amount です。
*/
SELECT
  customer_id,
  COUNT(*) AS order_count,
  AVG(amount) AS avg_amount
FROM `resonant-tract-508812-p9.sql_training.orders`
WHERE status = 'completed'
GROUP BY customer_id
HAVING COUNT(*) >= 2
ORDER BY 2 DESC, 3 DESC;


-- STEP 5｜CASE
/*
CASE は、条件によって返す値を変える構文です。Pythonでいう if / elif / else に近い役割ですね。
基本形はこうです。
CASE
  WHEN 条件1 THEN 値1
  WHEN 条件2 THEN 値2
  ELSE 値3
END

大事なのは、CASE は上から順番に条件判定するということです。
たとえば注文金額を分類するなら、下記です。
*/
SELECT
  order_id,
  amount,
  CASE
    WHEN amount >= 8000 THEN 'high'
    WHEN amount <= 4000 THEN 'low'
    ELSE 'normal'
  END AS amount_category
FROM `resonant-tract-508812-p9.sql_training.orders`;

/*
STEP 5-1｜まずは単純なCASE
全注文について、order_id、amount と、金額を分類した amount_category を取得する。
amount が 5,000以上なら 'high'、それ未満なら 'low' とする。order_id の小さい順に並べる。
取得列は、order_id、amount、amount_category です。
*/
SELECT
  order_id,
  amount,
  CASE
    WHEN amount >= 5000 THEN 'high'
    ELSE 'low'
  END AS amount_category
FROM `resonant-tract-508812-p9.sql_training.orders`
ORDER BY 1 ASC;

/*
STEP 5-2｜複数のWHEN
全注文について、order_id、amount、amount_category を取得してください。
金額が 8,000以上 → 'high'、5,000以上8,000未満 → 'middle'、5,000未満 → 'low' とします。
order_id の小さい順に並べてください。
*/
SELECT
  order_id,
  amount,
  CASE
    WHEN amount >= 8000 THEN 'high'
    WHEN amount < 5000 THEN 'low'
    ELSE 'middle'
  END AS amount_category
FROM `resonant-tract-508812-p9.sql_training.orders`
ORDER BY 1 ASC;
/*もう一つ書き方があります。
  CASE
    WHEN amount >= 8000 THEN 'high'
    WHEN amount >= 5000 THEN 'middle'
    ELSE 'low'
  END
これも同じ結果になります。なぜ WHEN amount >= 5000 だけでいいかというと、CASEは上から評価されるからです。*/

/*
STEP 5-3｜CASEの順番を考える問題
全注文について、order_id、amount、amount_rank を取得してください。
amount が 10,000以上 → 'S'、8,000以上10,000未満 → 'A'、5,000以上8,000未満 → 'B'、5,000未満 → 'C'
amount の高い順に並べてください。
今回はできるだけ、WHEN amount >= 8000 AND amount < 10000 のように上下限を両方書かず、CASEが上から評価される性質を利用して書いてみてください。
*/
SELECT
  order_id,
  amount,
  CASE
    WHEN amount >= 10000 THEN 'S'
    WHEN amount >= 8000 THEN 'A'
    WHEN amount >= 5000 THEN 'B'
    ELSE 'C'
  END AS amount_rank
FROM `resonant-tract-508812-p9.sql_training.orders`
ORDER BY 2 DESC;

/*
STEP 5-4｜条件付き集計
ここから CASE を集計関数と組み合わせます。たとえば「completedの件数」を求める方法は、すでに習った下記があります。
SELECT
  COUNT(*) AS completed_count
FROM ...
WHERE status = 'completed';
でも今度は、completedは何件？cancelledは何件？を1行に横並びで出したいとします。
完成イメージは、下記です。
completed_count  cancelled_count
10               2
ここで使える考え方が、下記です。
  SUM(
    CASE
      WHEN 条件 THEN 1
      ELSE 0
    END
  )
たとえば各注文について、completedなら  → 1、それ以外なら   → 0 に変換してから全部 SUM すれば、completedの件数になります。

orders テーブル全体から、completed の注文件数と、cancelled の注文件数を、1行2列で取得してください。
列名は、completed_count、cancelled_count とします。
今回は WHEREを使わないでください。2つの SUM(CASE ... END) をSELECT句に並べる形で考えてみてください。
*/
SELECT
  SUM(
    CASE
      WHEN status = 'completed' THEN 1
      ELSE 0
    END
  ) AS completed_count,
  SUM(
    CASE
      WHEN status = 'cancelled' THEN 1
      ELSE 0
    END
  ) AS cancelled_count
FROM `resonant-tract-508812-p9.sql_training.orders`;

/*
STEP 5-5｜GROUP BY × 条件付き集計
customer_idごとに、全注文件数、completedの注文件数、cancelledの注文件数を取得してください。
customer_idの小さい順に並べてください。
取得列は、customer_id、order_count、completed_count、cancelled_count とします。
今回は WHERE を使いません。
*/
SELECT
  customer_id,
  COUNT(*) AS order_count,
  SUM(
    CASE
      WHEN status = 'completed' THEN 1
      ELSE 0
    END
  ) AS completed_count,
  SUM(
    CASE
      WHEN status = 'cancelled' THEN 1
      ELSE 0
    END
  ) AS cancelled_count
FROM `resonant-tract-508812-p9.sql_training.orders`
GROUP BY customer_id
ORDER BY 1 ASC;

/*
STEP 5-6｜件数ではなく「金額」を条件付き集計
ここまでの条件付き集計では、下記のようにしていました。
  CASE
    WHEN 条件 THEN 1
    ELSE 0
  END
でも THEN で返すものは必ずしも 1 である必要はありません。たとえば列の値を指定して、
    WHEN status = 'completed' THEN amount
    ELSE 0
  END
とすれば completed → amountをそのまま返す、cancelled → 0 となります。これを SUM すれば、completedだけの金額合計を求められます。

orders テーブルについて、customer_idごとに次の3つを取得してください。
total_amount → ステータスに関係なく全注文のamount合計
completed_amount → completedだけのamount合計
cancelled_amount → cancelledだけのamount合計
customer_idの小さい順に並べてください。今回は WHERE は使わず、条件付き集計で金額を振り分けるのがポイントです。
*/
SELECT
  customer_id,
  SUM(amount) AS total_amount,
  SUM(
    CASE
      WHEN status = 'completed' THEN amount
      ELSE 0
    END
  ) AS completed_amount,
  SUM(
    CASE
      WHEN status = 'cancelled' THEN amount
      ELSE 0
    END
  ) AS cancelled_amount
FROM `resonant-tract-508812-p9.sql_training.orders`
GROUP BY customer_id
ORDER BY 1 ASC;

/*
STEP 5-7｜CASE + GROUP BY
これまでは CASE を、次のように集計関数の中に入れました。
  SUM(
    CASE
      WHEN ... THEN ...
      ELSE ...
    END
  )
今度は逆に、CASE で作った分類そのものを GROUP BY してみます。

全注文を amount によって、8000以上 → high、5000以上8000未満 → middle、5000未満 → low の3つに分類し、分類ごとの注文件数と合計注文金額を求めてください。
取得列は、amount_category、order_count、total_amount とします。
期待する考え方は、各注文 → CASEで high / middle / low に分類 → 同じ分類をGROUP BY → COUNTとSUM です。
新しいポイントとして、SELECT句には当然、CASE  ... END AS amount_category が必要です。
では、このCASEで作った分類をどう GROUP BY すればいいか？
BigQueryではいくつか書き方がありますが、まずは今まで学んだ知識から「こうでは？」と思うSQLを書いて、エラーになっても構いませんので実行してみてください。

BigQueryでCASEで作った分類をGROUP BYするには、たとえばSELECT句の位置を使って、次のように書けます。
SELECT
  CASE
    WHEN amount >= 8000 THEN 'high'
    WHEN amount >= 5000 THEN 'middle'
    ELSE 'low'
  END AS amount_category,
  COUNT(*) AS order_count
FROM `resonant-tract-508812-p9.sql_training.orders`
GROUP BY 1;
この、GROUP BY 1 は、以前使った、ORDER BY 1 と似た考え方です。
SELECT の1番目、CASE ... END AS amount_category の結果をグループ化しています。
なおBigQueryでは別名 amount_category を使った書き方もできますが、まずは今まで使ってきた位置指定につなげて GROUP BY 1 から覚えましょう。
*/
SELECT
  CASE
    WHEN amount >= 8000 THEN 'high'
    WHEN amount >= 5000 THEN 'middle'
    ELSE 'low'
  END AS amount_category,
  COUNT(*) AS order_count,
  SUM(amount) AS total_amount
FROM `resonant-tract-508812-p9.sql_training.orders`
GROUP BY 1;
/*今回新しく身につけたのは、元テーブルには存在しない、CASEで作った分類を集計単位にできるということです。
これは実務でもよく使い、たとえば「価格帯別」「年齢層別」「流入チャネル分類別」の集計などです。
今回、GROUP BY 1 としましたが、BigQueryでは今回のようなケースなら、GROUP BY amount_category とも書けます。
Oracleで使っていた位置指定の感覚から GROUP BY 1 を使うのもBigQueryでは可能です。*/

/*
STEP 5-8｜CASEの仕上げ
completed の注文だけを対象として、注文金額を次のように分類する。
8,000以上 → high、5,000以上8,000未満 → middle、5,000未満 → low
そのうえで、金額分類ごとの注文件数と平均注文金額を求め、平均注文金額が高い順に並べる。
取得列は、amount_category、order_count、avg_amount です。
*/
SELECT
  CASE
    WHEN amount >= 8000 THEN 'high'
    WHEN amount >= 5000 THEN 'middle'
    ELSE 'low'
  END AS amount_category,
  COUNT(*) AS order_count,
  ROUND(AVG(amount), 2) AS avg_amount
FROM `resonant-tract-508812-p9.sql_training.orders`
WHERE status = 'completed'
GROUP BY amount_category
ORDER BY avg_amount DESC;


-- STEP 6｜NULL
/*
STEP 6-1｜INSERT INTO
まずNULL入りのデータが必要なので、今回は新しく INSERT INTO を覚えます。
基本形は下記です。
INSERT INTO `テーブル名` (
  列1,
  列2,
  列3
)
VALUES (
  値1,
  値2,
  値3
);

今回の orders の列は、
  order_id, customer_id, order_date, amount, status でした。
そこでNULL学習用として、次の注文を追加します。
  order_id=1013, customer_id=6, order_date=2026-03-28, amount=NULL, status=completed
*/
INSERT INTO `resonant-tract-508812-p9.sql_training.orders` (
  order_id,
  customer_id,
  order_date,
  amount,
  status
)
VALUES (
  1013,
  6,
  DATE '2026-03-28',
  NULL,
  'completed'
);
/*このプロジェクトは「課金なし・BigQuery無料枠で進める」という前提でしたが、今の環境では INSERT のようなDMLが許可されていませんでした。
既存の orders を壊さず、NULL練習用のテーブルを新しく作り orders → これまでの基本練習用、orders_null → NULLを含む練習用 と分けます。
最初に orders を作ったときと同じように、クエリ結果から新規テーブルを作る形なら、今の環境でも進められます。
下記で新しく orders_null を作り、CAST(NULL AS INT64) などが初登場していますが、今は覚えなくて大丈夫です。
「NULLにはそれ自体の値から型を判断できないので、テストデータ作成の都合上、型を明示している」くらいでOKで、CAST 自体は後できちんと扱います。*/
CREATE OR REPLACE TABLE `resonant-tract-508812-p9.sql_training.orders_null` AS
SELECT
  2001 AS order_id,
  1 AS customer_id,
  DATE '2026-04-01' AS order_date,
  5000 AS amount,
  'completed' AS status,
  'web' AS coupon_code
UNION ALL
SELECT
  2002,
  1,
  DATE '2026-04-03',
  3000,
  'completed',
  CAST(NULL AS STRING)
UNION ALL
SELECT
  2003,
  2,
  DATE '2026-04-05',
  CAST(NULL AS INT64),
  'completed',
  'spring'
UNION ALL
SELECT
  2004,
  2,
  DATE '2026-04-08',
  7000,
  'cancelled',
  CAST(NULL AS STRING)
UNION ALL
SELECT
  2005,
  3,
  DATE '2026-04-10',
  9000,
  'completed',
  'vip'
UNION ALL
SELECT
  2006,
  3,
  DATE '2026-04-15',
  CAST(NULL AS INT64),
  'cancelled',
  CAST(NULL AS STRING)
UNION ALL
SELECT
  2007,
  4,
  DATE '2026-04-18',
  4500,
  'completed',
  CAST(NULL AS STRING)
UNION ALL
SELECT
  2008,
  4,
  DATE '2026-04-21',
  8000,
  'completed',
  'spring';

SELECT
  *
FROM `resonant-tract-508812-p9.sql_training.orders_null`
ORDER BY order_id;

/*
STEP 6-1｜COUNT(*) と COUNT(列名)
orders_null テーブル全体について、次の3つを1行で取得してください。
全注文件数、amountに値が入っている注文件数、coupon_codeに値が入っている注文件数
列名は、order_count、amount_count、coupon_count としてください。
*/
SELECT
  COUNT(*) AS order_count,
  COUNT(amount) AS amount_count,
  COUNT(coupon_code) AS coupon_count
FROM `resonant-tract-508812-p9.sql_training.orders_null`;

/*
STEP 6-2｜IS NULL / IS NOT NULL
orders_null から、amountがNULLになっている注文だけを取得してください。
取得する列は、order_id、customer_id、order_date、amount、status
並び順は order_id の昇順です。
*/
SELECT
  order_id, customer_id, order_date, amount, status
FROM `resonant-tract-508812-p9.sql_training.orders_null`
WHERE amount IS NULL
ORDER BY 1 ASC;

/*
STEP 6-3｜IS NOT NULL + 復習
orders_null から、次の条件をすべて満たす注文を取得してください。
amount がNULLではない、status が completed、amount が5,000以上
取得列：order_id, customer_id, amount, coupon_code
amount の高い順、同額なら order_id の昇順
*/
SELECT
  order_id, customer_id, amount, coupon_code
FROM `resonant-tract-508812-p9.sql_training.orders_null`
WHERE amount IS NOT NULL
  AND status = 'completed'
  AND amount >= 5000
ORDER BY 3 DESC, 1 ASC;

/*
STEP 6-4｜NULL × CASE
次のルールで、各注文に coupon_status という列を追加してください。
coupon_code が NULL → 'no_coupon'、coupon_code が NULL以外 → 'coupon_used'
取得する列は、order_id、customer_id、coupon_code、coupon_status です。
さらに、order_id の昇順に並べてください。
*/
SELECT
  order_id,
  customer_id,
  coupon_code,
  CASE
    WHEN coupon_code IS NULL THEN 'no_coupon'
    ELSE 'coupon_used'
  END AS coupon_status
FROM `resonant-tract-508812-p9.sql_training.orders_null`
ORDER BY 1 ASC;

/*
STEP 6-5｜NULL × CASE × GROUP BY
今度は、先ほど作った no_coupon、coupon_used という区分ごとに、注文件数を集計してください。
取得したい結果は coupon_status、order_count です。
条件は、
- coupon_code IS NULL → no_coupon
- それ以外 → coupon_used
- coupon_status ごとに集計
- order_count の多い順
- 件数が同じ場合は coupon_status の昇順 です。
*/
SELECT
  CASE
    WHEN coupon_code IS NULL THEN 'no_coupon'
    ELSE 'coupon_used'
  END AS coupon_status,
  COUNT(*) AS order_count
FROM `resonant-tract-508812-p9.sql_training.orders_null`
GROUP BY coupon_status
ORDER BY order_count DESC, coupon_status ASC;

/*
STEP 6-6｜NULLと集計関数
COUNT(amount) はNULLを数えないことを確認しましたが、SUM や AVG はどうなるでしょうか。
orders_null の amount は 5000、3000、NULL、7000、9000、NULL、4500、8000 です。
テーブル全体について、次の4つを1行で取得してください。
全注文件数                → order_count
amountがNULLでない件数    → amount_count
amountの合計              → total_amount
amountの平均              → avg_amount
*/
SELECT
  COUNT(*) AS order_count,
  COUNT(amount) AS amount_count,
  SUM(amount) AS total_amount,
  AVG(amount) AS avg_amount
FROM `resonant-tract-508812-p9.sql_training.orders_null`;

/*
STEP 6-7｜COALESCE
BigQueryでは、COALESCE(値1, 値2, 値3, ...) と書くと、左から順番に見て、最初に見つかった非NULL値を返します。
たとえば、COALESCE(amount, 0) なら、amount = 5000 → 5000、amount = NULL → 0　です。
ただし COALESCE は2つだけではなく、COALESCE(a, b, c, 0) のように複数候補を並べられるのがポイントです。
文字列でも使えるので例えば、COALESCE(coupon_code, 'no_coupon') なら、NULLの coupon_code を 'no_coupon' として表示できます。

先ほどは、AVG(amount) なのでNULLを除外し、36500 ÷ 6 でした。
ところが、AVG(COALESCE(amount, 0)) ならNULLが0に変わってからAVGされるので、(5000 + 3000 + 0 + 7000 + 9000 + 0 + 4500 + 8000) ÷ 8 になります。
つまり、「NULLを除外して平均する」のか「NULLを0として平均する」のかは、分析上まったく意味が違うということです。

orders_null 全体について、次の2つを取得してください。
NULLを除外したamountの平均 → avg_amount_excluding_null、NULLを0として扱ったamountの平均 → avg_amount_as_zero
小数点以下は、以前あなたが使った ROUND を再登場させて、小数第2位までにしてください。
*/
SELECT
  ROUND(AVG(amount), 2) AS avg_amount_excluding_null,
  ROUND(AVG(COALESCE(amount, 0)), 2) AS avg_amount_as_zero
FROM `resonant-tract-508812-p9.sql_training.orders_null`;

/*
STEP 6-8｜COALESCEを複数候補で使う
たとえば、COALESCE(NULL, NULL, 'A', 'B') なら結果は 'A' で、最初のNULLではない値を見つけた時点でそれを返します。
IFNULL はこのあと実際に使い、oracle の NVL2 相当もその後にやります。

orders_null から全注文について order_id、amount、coupon_code、coupon_display、amount_status の5列をorder_id の昇順に取得してください。
coupon_display はCOALESCEを使って、coupon_code が NULL → 'none'、NULLではない → coupon_codeをそのまま表示とします。
amount_status はCASEを使って amountがNULL → 'unknown'、amountが8000以上 → 'high'、amountが5000以上 → 'middle'、それ以外 → 'low' と分類してください。
*/
SELECT
  order_id,
  amount,
  coupon_code,
  COALESCE(coupon_code, 'none') AS coupon_display,
  CASE
    WHEN amount IS NULL THEN 'unknown'
    WHEN amount >= 8000 THEN 'high'
    WHEN amount >= 5000 THEN 'middle'
    ELSE 'low'
  END AS amount_status
FROM `resonant-tract-508812-p9.sql_training.orders_null`
ORDER BY 1 ASC;

/*
STEP 6-9｜IFNULL
次は、先ほど名前が出ていた IFNULL ですが BigQueryでは、IFNULL(式, NULLだった場合の値) と書けます。
COALESCEとの大きな違いは引数の数で IFNULL(a, b) は2つ、一方COALESCEは COALESCE(a, b, c, d) のように複数候補を指定できます。
ですから「aがNULLならb」だけなら IFNULL で書けますし、「aがNULLならb、bもNULLならc、cもNULLなら……」なら COALESCE が向いています。

orders_null からcustomer_idごとに集計してください。
取得する列は customer_id、order_count、amount_count、total_amount です。
order_count は全注文件数、amount_count は amount がNULLではない注文件数、total_amount は、NULLのamountを0として扱った合計金額にしてください。
今回は total_amount の計算で、IFNULL(...) を使ってください。total_amountの降順、同額ならcustomer_idの昇順です。
*/
SELECT
  customer_id,
  COUNT(*) AS order_count,
  COUNT(amount) AS amount_count,
  SUM(IFNULL(amount, 0)) AS total_amount
FROM `resonant-tract-508812-p9.sql_training.orders_null`
GROUP BY customer_id
ORDER BY total_amount DESC, customer_id ASC;

/*
STEP 6-9 確認問題
orders_null 全体について、amount がNULLなら 1000 として扱った合計金額を、adjusted_total_amountという名前で取得してください。今回は IFNULL を使います。
*/
SELECT
  SUM(IFNULL(amount, 1000)) AS adjusted_total_amount
FROM `resonant-tract-508812-p9.sql_training.orders_null`;

/*
STEP 6-10｜OracleのNVL2はBigQueryではどうする？
Oracleの NVL2 は、NVL2(式, NULLではない場合, NULLの場合) でしたね。
たとえば、NVL2(coupon_code, 'coupon_used', 'no_coupon') なら coupon_code = 'web' → coupon_used、coupon_code = NULL → no_coupon です。
BigQueryにはOracleと同じ NVL2 はありませんが、その代わりこれまで学習したCASEでそのまま表現できます。
  CASE
    WHEN coupon_code IS NOT NULL THEN 'coupon_used'
    ELSE 'no_coupon'
  END
さらにBigQueryには IF もあり、次のようにも書けます。
  IF(
    coupon_code IS NOT NULL,
    'coupon_used',
    'no_coupon'
  )
整理すると IFNULL(a, b) → aがNULLならb、IF(条件, a, b) → 条件がTRUEならa、そうでなければb です。

今回はCASEを使って、Oracleの NVL2 と同じ処理を書いてみましょう。
orders_null から order_id、customer_id、amount、amount_status を取得してください。
amount_status の条件は、amountがNULLではない → 'known'、amountがNULL → 'unknown' です。
status = 'completed' の注文だけを対象にして、order_id の降順にしてください。
*/
SELECT
  order_id,
  customer_id,
  amount,
  CASE
   WHEN amount IS NOT NULL THEN 'known'
   ELSE 'unknown'
  END AS amount_status
FROM `resonant-tract-508812-p9.sql_training.orders_null`
WHERE status = 'completed'
ORDER BY 1 DESC;

-- ここで orders_null を作り直し
CREATE OR REPLACE TABLE `resonant-tract-508812-p9.sql_training.orders_null` AS
SELECT
  2001 AS order_id,
  1 AS customer_id,
  DATE '2026-04-01' AS order_date,
  5000 AS amount,
  'completed' AS status,
  'web' AS coupon_code
UNION ALL
SELECT
  2002,
  1,
  DATE '2026-04-03',
  3000,
  'completed',
  CAST(NULL AS STRING)
UNION ALL
SELECT
  2003,
  2,
  DATE '2026-04-05',
  CAST(NULL AS INT64),
  'completed',
  'spring'
UNION ALL
SELECT
  2004,
  2,
  DATE '2026-04-08',
  7000,
  'cancelled',
  CAST(NULL AS STRING)
UNION ALL
SELECT
  2005,
  3,
  DATE '2026-04-10',
  9000,
  'completed',
  'vip'
UNION ALL
SELECT
  2006,
  3,
  DATE '2026-04-15',
  CAST(NULL AS INT64),
  'cancelled',
  CAST(NULL AS STRING)
UNION ALL
SELECT
  2007,
  4,
  DATE '2026-04-18',
  4500,
  'completed',
  CAST(NULL AS STRING)
UNION ALL
SELECT
  2008,
  4,
  DATE '2026-04-21',
  8000,
  'completed',
  'spring'
UNION ALL
SELECT
  2009,
  5,
  DATE '2026-04-23',
  0,
  'completed',
  CAST(NULL AS STRING)
UNION ALL
SELECT
  2010,
  5,
  DATE '2026-04-25',
  6000,
  'completed',
  'web';

SELECT
  *
FROM `resonant-tract-508812-p9.sql_training.orders_null`
ORDER BY order_id ASC;

/*
STEP 6-11｜NULLIF
偶然登場した NULLIF を正式に覚えます。
構文は、NULLIF(式1, 式2) です。
意味は、式1と式2が等しければNULL、等しくなければ式1を返す です。
例えば NULLIF(5000, 0) なら 5000 ですが、NULLIF(0, 0) なら NULL になり、NULLIF(null, 0) なら NULL です。

orders_null について order_id、amount、normalized_amount を取得して order_id の昇順に並べてください。
normalized_amount は、amount が0ならNULL、それ以外なら元の amount をそのまま返すものとしてNULLIFを使ってください。
*/
SELECT
  order_id,
  amount,
  NULLIF(amount, 0) AS normalized_amount
FROM `resonant-tract-508812-p9.sql_training.orders_null`
ORDER BY 1 ASC;

/*
STEP 6-12｜NULLIFは何に使うのか
NULLIF の代表的な用途の一つが、特定の値を「欠損値扱い」にして集計から除外することです。
今の amount には、NULL → 2件、0 → 1件 があります。
すでに学んだとおり、AVG(amount) ではNULLは平均の対象から除外されます。
しかし 0 はNULLではないので、0円も平均の対象に含まれます。
一方、AVG(NULLIF(amount, 0)) とすると、0 → NULLIF → NULL → AVG → 集計対象から除外 となります。

orders_null 全体について、次の4項目を1行で取得してください。
全注文件数 → order_count
amountがNULLではない件数 → amount_count
NULLだけを除外したamountの平均 → avg_amount
NULLと0の両方を除外したamountの平均 → avg_amount_excluding_zero
平均値はどちらも、以前使った ROUND で小数第2位までにしてください。
*/
SELECT
  COUNT(*) AS order_count,
  COUNT(amount) AS amount_count,
  ROUND(AVG(amount), 2) AS avg_amount,
  ROUND(AVG(NULLIF(amount, 0)), 2) AS avg_amount_excluding_zero
FROM `resonant-tract-508812-p9.sql_training.orders_null`;

/*
STEP 6-13｜NULLIF × CASE × GROUP BY
今回は、NULLIF + COUNT + CASE + GROUP BY + ORDER BY を組み合わせます。
一点だけヒントで、以前やった CASE WHEN COUNT(*) >= 2 THEN ... のように、CASEのWHEN条件の中にも集計関数を書けます。

orders_null を customer_id ごとに集計して、次の4列を取得し、valid_amount_count の降順、同数なら customer_id の昇順
customer_id
order_count : その顧客の全注文件数
valid_amount_count : NULLと0を除外したamountの件数で NULLIF を使ってください
amount_data_status : NULLと0を除外したamountの件数が2件以上 → 'sufficient'、それ以外 → 'insufficient' でCASEを使ってください
*/
SELECT
  customer_id,
  COUNT(*) AS order_count,
  COUNT(NULLIF(amount, 0)) AS valid_amount_count,
  CASE
    WHEN COUNT(NULLIF(amount, 0)) >= 2 THEN 'sufficient'
    ELSE 'insufficient'
  END AS amount_data_status
FROM `resonant-tract-508812-p9.sql_training.orders_null`
GROUP BY customer_id
ORDER BY valid_amount_count DESC, customer_id ASC;

/*
STEP 6-14｜NULL関連の総合問題
customer_id ごとに、completedの注文だけを対象として次の5列を取得し total_amount の降順、同額なら customer_id の昇順 に並べてください。
customer_id
completed_order_count : completedの全注文件数
valid_amount_count : amountがNULLでも0でもない注文件数
total_amount : amountがNULLなら0として扱った合計金額
data_status : CASEで valid_amount_count が2件以上 → 'sufficient'、それ以外 → 'insufficient'
*/
SELECT
  customer_id,
  COUNT(*) AS completed_order_count,
  COUNT(NULLIF(amount, 0)) AS valid_amount_count,
  SUM(IFNULL(amount, 0)) AS total_amount,
  CASE
    WHEN COUNT(NULLIF(amount, 0)) >= 2 THEN 'sufficient'
    ELSE 'insufficient'
  END AS data_status
FROM `resonant-tract-508812-p9.sql_training.orders_null`
WHERE status = 'completed'
GROUP BY customer_id
ORDER BY total_amount DESC, customer_id ASC;

/*
STEP 6-15｜NULLを含む論理条件
以前、NULL = 0 は FALSE ではなく UNKNOWN になる、と話しました。
SQLでは条件判定が実質 TRUE、FALSE、UNKNOWN の3つになります。
これが WHERE と組み合わさったときに重要で例えば WHERE amount != 0 と書いたとします。
直感的には、0ではないもの全部 なので「NULLも0ではないんだから取れるのでは？」と思うかもしれません。
ところが [5000 != 0 → TRUE] [0 != 0 → FALSE] [NULL != 0 → UNKNOWN] です。
WHERE が残すのはTRUEになった行だけなので、FALSEだけでなくUNKNOWNの行も結果から落ちます。
つまり、WHERE amount != 0 は、0だけではなくNULLも結果に出てきません。

orders_null から、amount が0ではない注文を取得してください。
取得列は order_id、amount だけ。
条件には、!= を使い、order_id の昇順にしてください。
ここではあえて IS NULL は使わず、WHERE amount != 0 にしたとき、NULLの2003・2006がどうなるかを実際に確認します。
*/
SELECT
  order_id, amount
FROM `resonant-tract-508812-p9.sql_training.orders_null`
WHERE amount != 0
ORDER BY 1 ASC;

SELECT
  order_id, amount
FROM `resonant-tract-508812-p9.sql_training.orders_null`
WHERE amount != 0 OR amount IS NULL
ORDER BY 1 ASC;

/*
STEP 6-16｜NULL × AND / OR × CASE
orders_null の全注文について order_id、amount、status、order_category を取得し、order_id の昇順にしてください。
order_category はCASEで次のように分類してください。
amount が NULL → 'unknown'
amount が 0 → 'zero'
status が 'completed' かつ amount が 5000以上 → 'completed_high'
それ以外 → 'other'
*/
SELECT
  order_id,
  amount,
  status,
  CASE
    WHEN amount IS NULL THEN 'unknown'
    WHEN amount = 0 THEN 'zero'
    WHEN status = 'completed' AND amount >= 5000 THEN 'completed_high'
    ELSE 'other'
  END AS order_category
FROM `resonant-tract-508812-p9.sql_training.orders_null`
ORDER BY 1 ASC;

/*
STEP 6-17｜実践問題
orders_null から status が completed であり、かつ amount が5000以上 または NULL を満たす注文を取得してください。
取得列は order_id、customer_id、amount、status とし、order_id の昇順にしてください。
*/
SELECT
  order_id, customer_id, amount, status
FROM `resonant-tract-508812-p9.sql_training.orders_null`
WHERE status = 'completed'
  AND (amount >= 5000 OR amount IS NULL)
ORDER BY 1 ASC;

/*
STEP 6-18｜NULL総合問題
orders_null を使って、completedの注文だけを対象に、amount を次の3種類に分類してください。
amount が NULL または 0 → 'invalid'
amount が 8000以上 → 'high'
それ以外 → 'normal'
そして、分類ごとに amount_category、order_count、valid_amount_count、total_amount の4列を取得してください。
条件は以下です。
- order_count：その分類に属する注文件数
- valid_amount_count：amount がNULLでも0でもない件数
- total_amount：NULLを0として扱った合計金額
- 注文件数が2件以上の分類だけを最終結果に残す
- total_amount の降順、同額なら amount_category の昇順
*/
SELECT
  CASE
    WHEN amount IS NULL OR amount = 0 THEN 'invalid'
    WHEN amount >= 8000 THEN 'high'
    ELSE 'normal'
  END AS amount_category,
  COUNT(*) AS order_count,
  COUNT(NULLIF(amount, 0)) AS valid_amount_count,
  SUM(IFNULL(amount, 0)) AS total_amount
FROM `resonant-tract-508812-p9.sql_training.orders_null`
WHERE status = 'completed'
GROUP BY amount_category
HAVING COUNT(*) >= 2
ORDER BY total_amount DESC, amount_category ASC;




