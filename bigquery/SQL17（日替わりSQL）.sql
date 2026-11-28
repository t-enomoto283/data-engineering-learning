
/*
日替わりSQL｜第1問
ECサイトの売上データから、地域別・月別の売上推移を分析するデータマートを作成してください。
今回は、売上のない月も含めて、累計売上・3か月移動平均・前月売上を計算することが要件です。

使用テーブル
  training16_customers
  training16_orders
  training16_order_items

集計条件
  対象期間：2026年7月1日〜12月31日
  対象注文：status = 'completed'
  売上金額：quantity * unit_price
  地域がNULLの場合は 'Unknown' とする
  顧客マスタに存在する全地域を出力対象とする
  売上がない月も0円として出力する

出力する列
  region：地域名
  sales_month：売上月（DATE型・月初日）
  monthly_sales：当月売上金額
  cumulative_sales：地域別の累計売上金額
  moving_avg_3：地域別の直近3か月移動平均
  prev_month_sales：地域別の前月売上金額

全地域×全月を出力。顧客マスタに存在する地域は NULLを 'Unknown' に置き換えたうえで6種類です。
3か月移動平均は当月と直前2か月の当月売上平均、7月は7月のみ、8月は7月・8月の平均、9月以降は直近3か月の平均、売上0円の月も平均に含める、小数点第二位。
前月売上は地域ごとの前月売上を取得、7月は前月が対象期間外なのでNULLとする。
結果の並び替えは region ASC, sales_month ASC
使用構文は CROSS JOIN、LEFT JOIN または RIGHT JOIN、SUM() OVER と ROWS BETWEEN、AVG() OVER と ROWS BETWEEN、LAG() OVER、CTEの使用は自由。
*/
WITH extract_order AS (
  SELECT
    DATE_TRUNC(o.order_date, MONTH) AS sales_month,
    IFNULL(c.region, 'Unknown') AS region,
    i.quantity,
    i.unit_price
  FROM `resonant-tract-508812-p9.sql_training.training16_orders` AS o
  LEFT OUTER JOIN `resonant-tract-508812-p9.sql_training.training16_order_items` AS i
    ON o.order_id = i.order_id
  LEFT OUTER JOIN `resonant-tract-508812-p9.sql_training.training16_customers` AS c
    ON o.customer_id = c.customer_id
  WHERE o.status = 'completed'
    AND (o.order_date BETWEEN DATE '2026-07-01' AND DATE '2026-12-31')
),
sales_data AS (
  SELECT
    region,
    sales_month,
    SUM(quantity * unit_price) AS monthly_sales
  FROM extract_order
  GROUP BY region, sales_month
),
make_month AS (
  SELECT DATE '2026-07-01' AS make_month
  UNION ALL
  SELECT DATE '2026-08-01'
  UNION ALL
  SELECT DATE '2026-09-01'
  UNION ALL
  SELECT DATE '2026-10-01'
  UNION ALL
  SELECT DATE '2026-11-01'
  UNION ALL
  SELECT DATE '2026-12-01'
),
region_month AS (
  SELECT
    r.region,
    m.make_month
  FROM (
    SELECT
      IFNULL(region, 'Unknown') region
    FROM `resonant-tract-508812-p9.sql_training.training16_customers`
    GROUP BY region
  ) AS r
  CROSS JOIN make_month AS m
),
region_month_sales AS (
  SELECT
    r.region,
    r.make_month AS sales_month,
    IFNULL(s.monthly_sales, 0) AS monthly_sales
  FROM sales_data AS s
  RIGHT OUTER JOIN region_month AS r
    ON r.region = s.region
      AND r.make_month = s.sales_month
)
SELECT
  region,
  sales_month,
  monthly_sales,
  SUM(monthly_sales) OVER (
    PARTITION BY region
    ORDER BY sales_month ASC
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
  ) AS cumulative_sales,
  ROUND(
    AVG(monthly_sales) OVER (
      PARTITION BY region
      ORDER BY sales_month ASC
      ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ),
    2
  ) AS moving_avg_3,
  LAG(monthly_sales) OVER (
    PARTITION BY region
    ORDER BY sales_month ASC
  ) AS prev_month_sales
FROM region_month_sales
ORDER BY region ASC, sales_month ASC;
/*実務上の改善余地
CTE make_month の部分で現在は6か月分を UNION ALL で列挙していますが、BigQueryでは次のようにも書けます。

SELECT
  month
FROM UNNEST(
  GENERATE_DATE_ARRAY(
    DATE '2026-07-01',
    DATE '2026-12-01',
    INTERVAL 1 MONTH
  )
) AS month

処理の仕組み
  GENERATE_DATE_ARRAY()：第一引数と第二引数で指定の日付を INTERVAL … の間隔で生成し、ARRAY<DATE> 型の配列を返す。
  UNNEST()：配列を展開して、各日付を1行ずつにする。
  AS month：展開された日付列に month という名前を付ける。

なお、GENERATE_DATE_ARRAY() は開始日と終了日の両方を含みます。
こちらなら、対象期間が長くなっても月を1行ずつ追加する必要がありません。*/


/*日替わりSQL｜顧客別の購入間隔分析
使用するテーブル
  training16_customers
  training16_orders

顧客ごとの購入履歴を時系列に並べ、前回の購入日から何日経過したかを求めてください。
  status = 'completed' の注文のみを対象とする。
  顧客ごとに order_date の昇順で並べる。
  顧客ごとに購入が何回目かを purchase_number として表示する。
  前回の購入日を previous_order_date として表示する。
  前回購入日から今回購入日までの日数を days_since_previous として表示する。
  顧客の region も表示してregion がNULLの場合は 'Unknown' に置き換える。
  初回購入については、前回購入日と経過日数をNULLとする。
  同じ顧客が同じ日に複数回注文した場合も、それぞれ別の購入としてカウントしてください。購入順序は order_date、同日なら order_id の昇順とします。

出力カラム
  customer_id：顧客ID
  region：地域
  order_id：注文ID
  order_date：注文日
  purchase_number：何回目の購入か
  previous_order_date：前回購入日
  days_since_previous：前回購入からの日数
*/
WITH extract_order AS (
  SELECT
    o.customer_id,
    IFNULL(c.region, 'Unknown') AS region,
    o.order_id,
    o.order_date
  FROM `resonant-tract-508812-p9.sql_training.training16_orders` AS o
  LEFT OUTER JOIN `resonant-tract-508812-p9.sql_training.training16_customers` AS c
    ON o.customer_id = c.customer_id
  WHERE o.status = 'completed'
),
customer_order_data AS (
  SELECT
    customer_id,
    region,
    order_id,
    order_date,
    ROW_NUMBER() OVER (
      PARTITION BY customer_id
      ORDER BY order_date ASC, order_id ASC
    ) AS purchase_number,
    LAG(order_date) OVER (
      PARTITION BY customer_id
      ORDER BY order_date ASC, order_id ASC
    ) AS previous_order_date
  FROM extract_order
)
SELECT
  customer_id,
  region,
  order_id,
  order_date,
  purchase_number,
  previous_order_date,
  DATE_DIFF(order_date, previous_order_date, DAY) AS days_since_previous
FROM customer_order_data
ORDER BY customer_id ASC, order_date ASC, order_id ASC;


/*
日替わりSQL：日別ファネル分析と前日比較

使用テーブル
  resonant-tract-508812-p9.ga4_analysis.ga4_session_funnel_mart
（以前作成した、GA4のセッション単位ファネル分析用データマート）
（このテーブルは、1行＝1ユーザー×1セッションの粒度）

今回使用する既存カラムは以下のとおりです。
  カラム             内容
  user_pseudo_id    ユーザー識別子
  ga_session_id     セッションID
  session_date      セッション日付
  page_view_flag    ページ閲覧の有無（0/1）
  view_item_flag    商品閲覧の有無（0/1）
  add_to_cart_flag  カート追加の有無（0/1）

演習要件
以下の条件を満たすSQLを作成してください。
  session_date ごとにセッション数を集計する。
  各日について、view_item_flag = 1 のセッション数を集計する。
  各日について、add_to_cart_flag = 1 のセッション数を集計する。
  商品閲覧セッション数を分母、カート追加セッション数を分子として、カート追加率を算出する。
  LAG() を使用して、直前の集計対象日のセッション数を取得する。
  当日のセッション数と直前の集計対象日のセッション数の差分を算出する。
  session_date の昇順で出力する。

最終出力カラム
  session_date：セッション日付
  session_count：当日の総セッション数
  view_item_sessions：商品閲覧セッション数
  add_to_cart_sessions：カート追加セッション数
  cart_add_rate：カート追加率
  previous_session_count：直前の集計対象日の総セッション数
  session_count_diff：当日と直前の集計対象日のセッション数の差

注意事項
  カート追加率は0〜1の小数で出力してください。
  分母が0の場合は、エラーではなく NULL としてください。
  最初の集計対象日は前日比較ができないため、previous_session_count と session_count_diff は NULL で構いません。
  「直前の集計対象日」は、必ずしも暦上の前日とは限りません。
  WITH 句（CTE）の使用は自由です。
  今回は GROUP BY による日別集計と、LAG() による時系列比較を正しい順序で組み合わせることです。
  特に、セッション単位のデータを日別に集約してからウィンドウ関数を適用する点を意識してください。
*/
WITH daily_agg AS (
  SELECT
    session_date,
    COUNT(ga_session_id) AS session_count,
    COUNT(IF(view_item_flag = 1, ga_session_id, NULL)) AS view_item_sessions,
    COUNT(IF(add_to_cart_flag = 1, ga_session_id, NULL)) AS add_to_cart_sessions,
    SAFE_DIVIDE(
      COUNT(IF(add_to_cart_flag = 1, ga_session_id, NULL)),
      COUNT(IF(view_item_flag = 1, ga_session_id, NULL))
    ) AS cart_add_rate
  FROM `resonant-tract-508812-p9.ga4_analysis.ga4_session_funnel_mart`
  GROUP BY session_date
),
prev_daily_plus AS (
  SELECT
    session_date,
    session_count,
    view_item_sessions,
    add_to_cart_sessions,
    cart_add_rate,
    LAG(session_count) OVER (
      ORDER BY session_date ASC
    ) AS previous_session_count
  FROM daily_agg
)
SELECT
  session_date,
  session_count,
  view_item_sessions,
  add_to_cart_sessions,
  cart_add_rate,
  previous_session_count,
  session_count - previous_session_count AS session_count_diff
FROM prev_daily_plus
ORDER BY session_date ASC;


/*
日替わりSQL：日別注文数と累計注文数（ウィンドウ関数）

使用テーブル
  `resonant-tract-508812-p9.sql_training.training16_orders`

注文ステータスが completed の注文について、日別注文数と、その日までの累計注文数を取得してください。

取得する列
  order_date：注文日
  daily_orders：その日の注文数
  cumulative_orders：その日までの累計注文数

条件
  status = 'completed' の注文のみを対象とする。
  order_date ごとに注文数を集計する。
  SUM() OVER() を使用して、日付順に累計注文数を計算する。
  累計計算では ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW を明示する。
  最終結果は order_date の昇順とする。
*/
WITH filter_order AS (
  SELECT
    order_date,
    COUNT(order_id) AS daily_orders
  FROM `resonant-tract-508812-p9.sql_training.training16_orders`
  WHERE status = 'completed'
  GROUP BY order_date
)
SELECT
  order_date,
  daily_orders,
  SUM(daily_orders) OVER (
    ORDER BY order_date ASC
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
  ) AS cumulative_orders
FROM filter_order
ORDER BY order_date ASC;


/*
日替わりSQL：BigQuery Standard SQL｜SELECT問題｜ウィンドウ関数

使用テーブル
  resonant-tract-508812-p9.sql_training.training16_orders

各顧客について、注文日が新しい順に注文を並べ、直前の注文日を取得してください。

次の4項目を出力してください。
  customer_id
  order_id
  order_date
  previous_order_date（その注文より前の、同じ顧客の直近の注文日）

条件
  顧客ごとに注文日を昇順で評価すること。
  同じ顧客で注文日が重複する場合は、order_id の昇順で順序を確定すること。
  最初の注文の previous_order_date は NULL とすること。
  最終的な表示順は customer_id の昇順、order_date の降順、order_id の降順とすること。
*/
SELECT
  customer_id,
  order_id,
  order_date,
  LAG(order_date) OVER (
    PARTITION BY customer_id
    ORDER BY order_date ASC, order_id ASC
  ) AS previous_order_date
FROM `resonant-tract-508812-p9.sql_training.training16_orders`
ORDER BY customer_id ASC, order_date DESC, order_id DESC;


/*
python・pandasの「STEP 5-5｜BigQueryへの書き込み」における関数 load_aggregated_sales_to_bigquery を実行して
書き込み先テーブルが存在しない場合BigQueryのロードジョブにより新規作成される
resonant-tract-508812-p9.sql_training.step5_5_sales_summary について
書き込まれた内容を確認する目的のクエリ
*/
SELECT
  product_id,
  total_sales
FROM `resonant-tract-508812-p9.sql_training.step5_5_sales_summary`
ORDER BY total_sales DESC;

/*
日替わりSQL：SUM() OVER() による累計集計
今回は、前回のウィンドウ関数を発展させて、顧客ごとの累計購入金額を求めます。

以下の注文データがあります。
  customer_id	 order_date	 order_id  amount
  A	           2026-11-01	 101	     1000
  A	           2026-11-03	 102	     2000
  A	           2026-11-05	 103	     1500
  B	           2026-11-02	 104	     3000
  B	           2026-11-04	 105	     1000
このデータから、顧客ごとに注文日順の累計購入金額を求めてください。

要件
  customer_id ごとに累計を計算する。
  order_date の昇順で累計する。
  出力列は customer_id、order_date、order_id、amount、cumulative_amount の5列とする。
  最終結果は customer_id、order_date、order_id の昇順に並べる。
  SUM() OVER() を使用する。同じ日に複数注文がある場合も注文単位で累計するため、order_id も順序に含める。

実行用データ
今回は既存のテーブル構造を前提にせず、次のCTEを基に後続のSQLを書いてBigQueryで実行。
*/
WITH orders AS (
  SELECT
    'A' AS customer_id, DATE '2026-11-01' AS order_date, 101 AS order_id, 1000 AS amount
  UNION ALL
  SELECT
    'A', DATE '2026-11-03', 102, 2000
  UNION ALL
  SELECT
    'A', DATE '2026-11-05', 103, 1500
  UNION ALL
  SELECT
    'B', DATE '2026-11-02', 104, 3000
  UNION ALL
  SELECT
    'B', DATE '2026-11-04', 105, 1000
)
SELECT
  customer_id,
  order_date,
  order_id,
  amount,
  SUM(amount) OVER (
    PARTITION BY customer_id
    ORDER BY order_date ASC, order_id ASC
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
  ) AS cumulative_amount
FROM orders
ORDER BY customer_id ASC, order_date ASC, order_id ASC;


/*
日替わりSQL｜LEFT JOINにおけるONとWHEREの使い分け

今回のテーマと目的：
ECサイトの顧客情報と注文情報を使います。
実務では、例えば「2026年11月に注文した顧客の購入金額を集計したい。ただし、注文していない顧客も一覧に残したい」という要件があります。
この場合、単純に LEFT JOIN すればよいわけではありません。結合条件と抽出条件をどこに記述するかによって、結果が変わる可能性があります。
今回は、その違いを理解したうえでSQLを設計してください。

使用するデータ
  customers：顧客マスタ
  customer_id	 customer_name	status
  1	           田中	           active
  2	           佐藤	           active
  3	           鈴木	           inactive
  4	           高橋	           active
  5	           伊藤	           active

  orders：注文履歴
  order_id  customer_id	 order_date	 amount
  101	      1	           2026-10-25	 5000
  102	      1	           2026-11-03	 3000
  103	      1	           2026-11-10	 2000
  104	      2	           2026-11-05	 4000
  105	      3	           2026-11-08	 6000
  106	      4	           2026-10-20	 7000
  107	      4	           2026-12-01	 8000

要件：2026年11月における、アクティブ顧客別の注文金額を集計する。
  status = 'active' の顧客のみ対象とする。
  集計対象の注文期間は2026年11月1日〜11月30日とする。
  11月に注文がないアクティブ顧客も結果に残す。
  注文がない顧客の total_amount は 0 とする。
  注文がない顧客の order_count も 0 とする。
  customer_id の昇順で並べる。

出力列は次の4列です。
  customer_id、customer_name、order_count、total_amount

実行用データ
次のCTEを基に後続のSQLを書いてBigQueryで実行
*/
WITH customers AS (
  SELECT
    1 AS customer_id, '田中' AS customer_name, 'active' AS status
  UNION ALL
  SELECT
    2, '佐藤', 'active'
  UNION ALL
  SELECT
    3, '鈴木', 'inactive'
  UNION ALL
  SELECT
    4, '高橋', 'active'
  UNION ALL
  SELECT
    5, '伊藤', 'active'
),
orders AS (
  SELECT
    101 AS order_id, 1 AS customer_id, DATE '2026-10-25' AS order_date, 5000 AS amount
  UNION ALL
  SELECT
    102, 1, DATE '2026-11-03', 3000
  UNION ALL
  SELECT
    103, 1, DATE '2026-11-10', 2000
  UNION ALL
  SELECT
    104, 2, DATE '2026-11-05', 4000
  UNION ALL
  SELECT
    105, 3, DATE '2026-11-08', 6000
  UNION ALL
  SELECT
    106, 4, DATE '2026-10-20', 7000
  UNION ALL
  SELECT
    107, 4, DATE '2026-12-01', 8000
),
active_customer AS (
  SELECT
    customer_id,
    customer_name
  FROM customers
  WHERE status = 'active'
)
SELECT
  a.customer_id,
  a.customer_name,
  COUNT(o.order_id) AS order_count,
  SUM(IFNULL(o.amount, 0)) AS total_amount
FROM active_customer AS a
LEFT OUTER JOIN orders AS o
  ON a.customer_id = o.customer_id
    AND (o.order_date BETWEEN DATE '2026-11-01' AND DATE '2026-11-30')
GROUP BY a.customer_id, a.customer_name
ORDER BY a.customer_id ASC;


/*
python・pandasの「STEP 7-3｜増分処理・再実行制御・ログ・監視の統合」において、下記の初期状態テーブルを作成
  売上テーブル：`resonant-tract-508812-p9.sql_training.sales_incremental_step7`
  状態テーブル（ウォーターマーク管理）：`resonant-tract-508812-p9.sql_training.pipeline_watermarks_step7`
これらの作成した初期状態テーブルについて確認する目的のクエリ
*/
SELECT
  *
FROM `resonant-tract-508812-p9.sql_training.sales_incremental_step7`
ORDER BY sale_id;

SELECT
  *
FROM `resonant-tract-508812-p9.sql_training.pipeline_watermarks_step7`
ORDER BY pipeline_name;


/*
python・pandasの「STEP 7-4｜最終総合演習」における関数 run_final_sales_pipeline によって作られた
集計結果の保存用BigQueryテーブル（下記）を確認する目的のクエリ
  保存先テーブル：`resonant-tract-508812-p9.sql_training.sales_summary_final_step7`
*/
SELECT
  *
FROM `resonant-tract-508812-p9.sql_training.sales_summary_final_step7`
ORDER BY product_id;


/*
日替わりSQL｜BigQueryの列指向データウェアハウスに対する _TABLE_SUFFIX を使った参照カラム限定（スキャン量低減）

GA4のイベントデータを使い、日付ごとのイベント発生状況を集計します。

使用データ
  bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*
使用カラム
  event_date      イベント発生日（YYYYMMDD形式）
  event_name      イベント名
  user_pseudo_id  ユーザー識別子
  _TABLE_SUFFIX   ワイルドカードテーブルの日付部分

今回は page_view、add_to_cart、purchase の3種類のイベントを対象にします。
指定期間における日別のイベント発生状況を集計し、購入イベントが1件以上発生した日だけを抽出してください。

以下の要件をすべて満たすSQLを作成してください。
A. データ抽出
  _TABLE_SUFFIX を使い、2021年1月1日〜1月7日のデータに限定する。
   event_name が page_view、add_to_cart、purchase のいずれかであるレコードだけを対象にする。
B. データ集計
  event_date 単位で集計し、以下のカラムを出力する。
  event_date    イベント発生日
  page_views    page_view の発生件数
  add_to_carts  add_to_cart の発生件数
  purchases     purchase の発生件数
  unique_users  対象3イベントにおける重複を除いたユーザー数
C. 集計後の絞り込み
  HAVING を使用し、purchase が1件以上発生した日だけを抽出する。
D. 並び替え
  event_date の昇順に並び替える。

注意事項
  COUNTIF() を使って各イベントの件数を求めてください。
  unique_users はイベント件数ではなく、ユーザー識別子の重複を除いた数です。
  WHERE と HAVING の役割の違いを意識してください。
  purchase 以外のイベントも集計対象として残す必要があります。
  今回はCTEやウィンドウ関数を使用する必要はありません。
*/
SELECT
  event_date,
  COUNTIF(event_name = 'page_view') AS page_views,
  COUNTIF(event_name = 'add_to_cart') AS add_to_carts,
  COUNTIF(event_name = 'purchase') AS purchases,
  COUNT(DISTINCT user_pseudo_id) AS unique_users
FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
WHERE _TABLE_SUFFIX BETWEEN '20210101' AND '20210107'
  AND event_name IN ('page_view', 'add_to_cart', 'purchase')
GROUP BY event_date
HAVING purchases >= 1
ORDER BY event_date ASC;


/*
日替わりSQL｜PARSE_DATE() による文字列からDATE型への変換

BigQueryのGA4公開サンプルデータを使用し、日別のカート追加イベント数・購入イベント数・購入率を算出します。

対象テーブル
  bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*
対象期間
  2021年1月1日〜2021年1月7日
使用するカラム
  event_date     イベント発生日（YYYYMMDD形式の文字列）
  event_name     イベント名
  _TABLE_SUFFIX  ワイルドカードテーブルの日付部分
今回は add_to_cart と purchase の2種類のイベントのみを使用します。

演習
指定期間の日別カート追加イベント数と購入イベント数を集計し、購入イベント数をカート追加イベント数で割った割合を算出してください。
以下の要件を満たすSQLを作成してください。
A. データ抽出・日付変換
  WITH 句を使用してCTE base を作成してください。
  _TABLE_SUFFIX で2021年1月1日〜7日に限定する。
  event_name が add_to_cart または purchase の行だけを抽出する。
  PARSE_DATE('%Y%m%d', event_date) を使用して、event_date をDATE型に変換する。
  CTE base の出力カラムは event_date（DATE型）、event_name とする。
B. 日別集計
  CTE daily_summary を作成し、base を日別に集計してください。
  出力カラム     内容
  event_date    DATE型の日付
  add_to_carts  add_to_cart のイベント件数
  purchases     purchase のイベント件数
  イベント件数の算出には COUNTIF() を使用してください。
C. 購入率の計算
  最終的な SELECT で、次のカラムを追加してください。
  出力カラム           内容
  purchase_rate_pct  購入イベント数 ÷ カート追加イベント数 × 100
  計算には SAFE_DIVIDE() を使用し、ROUND() で小数点以下2桁に丸めてください。
  なお、カート追加イベント数が0の場合、purchase_rate_pct は NULL のままで構いません。
D. 並び替え
  event_date の昇順に並び替えてください。
*/
WITH base AS (
  SELECT
    PARSE_DATE('%Y%m%d', event_date) AS event_date,
    event_name
  FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20210101' AND '20210107'
    AND event_name IN ('add_to_cart', 'purchase')
)
SELECT
  event_date,
  COUNTIF(event_name = 'add_to_cart') AS add_to_carts,
  COUNTIF(event_name = 'purchase') AS purchases,
  ROUND(
    SAFE_DIVIDE(
      COUNTIF(event_name = 'purchase'), COUNTIF(event_name = 'add_to_cart')
      ) * 100,
    2
  ) AS purchase_rate_pct
FROM base
GROUP BY event_date
ORDER BY event_date ASC;


/*
日替わりSQL｜顧客別の最新注文と同順位の扱い

ECサイトの注文履歴から、顧客ごとの最新注文を取得するSQLを作成してください。
実務では、顧客マスタに最新の購入情報を付与したり、直近の購買状況を分析したりする場面があります。
ただし、同じ顧客が同じ日に複数の注文を行っている場合、単純に最新日付だけで絞り込むと複数行が残ることがあります。
今回は、そのようなケースも考慮し、顧客ごとに最新注文を必ず1件だけ取得することが要件です。

使用するデータ
今回は、BigQueryでそのまま実行できる小規模なサンプルデータを後述CTEとして使用、SQLの冒頭に記載。

要件：顧客ごとに最新注文を1件取得し、次の条件を満たしてください。
  最新注文は、order_date が最も新しい注文とする。
  同一顧客で最新注文日が複数存在する場合は、order_id が最も大きい注文を採用する。
  顧客ごとに必ず1行だけ出力する。
  注文履歴に存在するすべての顧客を出力する。
  結果は customer_id の昇順とする。

出力するカラム
  customer_id  顧客ID
  order_id     最新注文の注文ID
  order_date   最新注文日
  amount       最新注文の金額

補足
今回の中心となる技術は、既習のウィンドウ関数です。
例えば、ROW_NUMBER() を利用すれば顧客ごとの注文に順位を付けられ、またウィンドウ関数の計算結果に基づいて行を絞り込める QUALIFY 句もあります。
*/
WITH orders AS (
  SELECT 101 AS order_id, 1 AS customer_id, DATE '2026-11-01' AS order_date, 3000 AS amount
  UNION ALL
  SELECT 102, 1, DATE '2026-11-10', 5000
  UNION ALL
  SELECT 103, 1, DATE '2026-11-10', 2000
  UNION ALL
  SELECT 104, 2, DATE '2026-11-03', 4000
  UNION ALL
  SELECT 105, 2, DATE '2026-11-15', 7000
  UNION ALL
  SELECT 106, 3, DATE '2026-11-05', 6000
  UNION ALL
  SELECT 107, 3, DATE '2026-11-05', 8000
  UNION ALL
  SELECT 108, 4, DATE '2026-11-08', 2500
)
SELECT
  customer_id,
  order_id,
  order_date,
  amount
FROM (
  SELECT
    customer_id,
    order_id,
    order_date,
    amount,
    ROW_NUMBER() OVER (
      PARTITION BY customer_id
      ORDER BY order_date DESC, order_id DESC
    ) AS ranked
  FROM orders
  QUALIFY ranked = 1
  )
ORDER BY customer_id ASC;


/*
日替わりSQL｜特定期間に購入実績のない顧客の抽出

業務背景・目的
ECサイトを運営する企業では、既存顧客に対する購入促進施策を検討しています。
2026年10月には購入実績があるものの、2026年11月には購入実績がない有効顧客を抽出し、施策対象者の一覧を作成することになりました。
対象顧客については、10月の購入件数と購入金額の合計も取得してください。

使用するデータ
後述するCTEをサンプルデータとして使用、SQLの冒頭に記載。

業務要件
以下の条件をすべて満たす顧客を抽出してください。
  顧客ステータスが Active であること。
  2026年10月に1件以上の購入実績があること。
  2026年11月に購入実績がないこと。
  購入実績として扱うのは、order_status = 'Completed' の注文のみとすること。
  対象顧客ごとに、2026年10月の購入件数と購入金額の合計を算出すること。
  顧客1人につき1レコードとすること。
  10月の購入金額の降順、同額の場合は customer_id の昇順で並び替えること。
  なお、2026年12月以降の購入実績は、今回の抽出条件および集計結果に影響させないでください。

出力カラム
  customer_id、oct_order_count 2026年10月の購入件数、oct_total_amount	2026年10月の購入金額の合計

今回のポイントは、購入実績がないことと、注文データ自体が存在しないことを区別することです。
実務における休眠顧客の抽出だけでなく、未処理データの特定、テーブル間の差分検出、データ品質検証などにも応用できる技術の復習です。
*/
WITH customers AS (
  SELECT 1 AS customer_id, 'Active' AS status
  UNION ALL
  SELECT 2, 'Active'
  UNION ALL
  SELECT 3, 'Active'
  UNION ALL
  SELECT 4, 'Inactive'
  UNION ALL
  SELECT 5, 'Active'
  UNION ALL
  SELECT 6, 'Active'
  UNION ALL
  SELECT 7, 'Active'
),
orders AS (
  SELECT 101 AS order_id, 1 AS customer_id, DATE '2026-10-05' AS order_date, 3000 AS amount, 'Completed' AS order_status
  UNION ALL
  SELECT 102, 1, DATE '2026-10-20', 5000, 'Completed'
  UNION ALL
  SELECT 103, 2, DATE '2026-10-10', 4000, 'Completed'
  UNION ALL
  SELECT 104, 2, DATE '2026-11-05', 6000, 'Completed'
  UNION ALL
  SELECT 105, 3, DATE '2026-10-15', 7000, 'Completed'
  UNION ALL
  SELECT 106, 3, DATE '2026-11-10', 2000, 'Cancelled'
  UNION ALL
  SELECT 107, 4, DATE '2026-10-08', 9000, 'Completed'
  UNION ALL
  SELECT 108, 5, DATE '2026-11-12', 3000, 'Completed'
  UNION ALL
  SELECT 109, 6, DATE '2026-10-25', 4000, 'Cancelled'
  UNION ALL
  SELECT 110, 7, DATE '2026-10-31', 7000, 'Completed'
  UNION ALL
  SELECT 111, 7, DATE '2026-12-01', 5000, 'Completed'
),
joined AS (
  SELECT
    c.customer_id,
    o.order_id,
    DATE_TRUNC(o.order_date, MONTH) AS order_date,
    o.amount
  FROM customers AS c
  INNER JOIN orders AS o
    ON c.customer_id = o.customer_id
  WHERE c.status = 'Active'
    AND o.order_status = 'Completed'
    AND (o.order_date >= DATE '2026-10-01' AND o.order_date < DATE '2026-12-01')
)
SELECT
  customer_id,
  oct_order_count,
  oct_total_amount
FROM (
  SELECT
    customer_id,
    COUNTIF(order_date = DATE '2026-10-01') AS oct_order_count,
    COUNTIF(order_date = DATE '2026-11-01') AS nov_order_count,
    SUM(
      CASE
        WHEN order_date = DATE '2026-10-01' THEN amount
        ELSE NULL  -- SUM(IF(…))ではなく意図的にCASE式かつELSE句を明示的に使用
      END
    ) AS oct_total_amount
  FROM joined
  GROUP BY customer_id
  HAVING oct_order_count >= 1
    AND nov_order_count = 0
  )
ORDER BY oct_total_amount DESC, customer_id ASC;


/*
日替わりSQL｜欠損日の補完と日次売上の前日比分析

業務背景・目的
ECサイトを運営する企業では、日次売上の推移を確認するためのダッシュボードを構築しています。
しかし、注文データには購入実績のない日付のレコードが存在しません。
そのまま日次集計を行うと、購入実績のない日付が欠落し、正確な前日比を算出できないという問題があります。
そこで、購入実績のない日付も含めた連続的な日次売上データを作成し、前日の売上金額、前日との差額、前日比増減率を算出することになりました。

使用するデータ
後述するCTEをサンプルデータとして使用、SQLの冒頭に記載。

業務要件
以下の条件をすべて満たす日次売上データを作成してください。
  集計対象期間は2026年11月1日〜11月7日とする。
  売上として扱うのは order_status = 'Completed' の注文のみとする。
  購入実績の有無にかかわらず、対象期間のすべての日付を出力する。
  購入実績がない日の売上金額は0とする。
  各日付について、前日の売上金額を取得する。
  各日付について、前日との売上差額および前日比増減率（%）｛前日との売上差額/前日の売上金額×100｝を算出する。
  集計対象期間の初日は、前日の売上金額・売上差額・前日比増減率をすべてNULLとする。
  前日の売上金額が0の場合、前日比増減率はNULLとする。
  前日比増減率は小数点以下第2位までとする。
  1日につき1レコードとし、日付の昇順で並び替える。
  なお、前日とは、直前に購入実績があった日ではなく、暦上の前日を意味します。

出力カラム
  sales_date         集計対象日（DATE型）
  daily_sales        当日の売上金額
  prev_daily_sales   前日の売上金額
  sales_diff         前日との売上差額
  sales_change_pct   前日比増減率（%）
*/
WITH orders AS (
  SELECT 101 AS order_id, DATE '2026-11-01' AS order_date, 3000 AS amount, 'Completed' AS order_status
  UNION ALL
  SELECT 102, DATE '2026-11-01', 2000, 'Completed'
  UNION ALL
  SELECT 103, DATE '2026-11-02', 7500, 'Completed'
  UNION ALL
  SELECT 104, DATE '2026-11-03', 4000, 'Cancelled'
  UNION ALL
  SELECT 105, DATE '2026-11-04', 6000, 'Completed'
  UNION ALL
  SELECT 106, DATE '2026-11-04', 3000, 'Completed'
  UNION ALL
  SELECT 107, DATE '2026-11-05', 4500, 'Completed'
  UNION ALL
  SELECT 108, DATE '2026-11-07', 8000, 'Completed'
  UNION ALL
  SELECT 109, DATE '2026-11-08', 5000, 'Completed'
),
daily AS (
  SELECT
    sales_date
  FROM UNNEST (
    GENERATE_DATE_ARRAY(
      DATE '2026-11-01',
      DATE '2026-11-07',
      INTERVAL 1 DAY
    )
  ) AS sales_date
),
joined AS (
  SELECT
    d.sales_date,
    SUM(IFNULL(o.amount, 0)) AS daily_sales
  FROM daily AS d
  LEFT OUTER JOIN orders AS o
    ON d.sales_date = o.order_date
      AND o.order_status = 'Completed'
  GROUP BY d.sales_date
)
SELECT
  sales_date,
  daily_sales,
  prev_daily_sales,
  daily_sales - prev_daily_sales AS sales_diff,
  ROUND(
    SAFE_DIVIDE(daily_sales - prev_daily_sales, prev_daily_sales) * 100,
    2
  ) AS sales_change_pct
FROM (
  SELECT
    sales_date,
    daily_sales,
    LAG(daily_sales) OVER (
      ORDER BY sales_date ASC
    ) AS prev_daily_sales
  FROM joined
  )
ORDER BY sales_date ASC;


/*
日替わりSQL｜注文データに含まれる商品明細の集計

使用データ
仮想のECサイトの注文データです。
1レコードが1注文を表しており、注文内の商品明細は配列として格納されています。
後述するCTEを使用、SQLの冒頭に記載。

業務背景
ECサイトの運営担当者から、商品ごとの販売実績を把握したいという依頼がありました。
注文データには複数の商品明細が含まれており、同一注文内に同じ商品が複数の明細として存在する場合もあります。
商品単位で販売実績を集計し、売上金額の大きい商品を確認できるデータを作成してください。

要件
  商品ID単位で集計すること。
  商品ごとの総販売数量を取得すること。
  商品ごとの総売上金額を取得すること。
  商品ごとの注文数を取得すること。
  商品ごとの購入顧客数を取得すること。
  同一注文内に同じ商品が複数存在する場合、販売数量・売上金額はすべての明細を集計すること。
  同一注文内に同じ商品が複数存在する場合でも、注文数は1件として扱うこと。
  同一顧客が同じ商品を複数回購入した場合でも、購入顧客数は1人として扱うこと。
  商品明細が存在しない注文は集計対象外とすること。
  総売上金額の降順で出力すること。

出力カラム
  product_id 商品ID、total_quantity	総販売数量、total_sales	総売上金額、order_count	注文数、customer_count 購入顧客数
*/
WITH orders AS (
  SELECT
    1001 AS order_id,
    DATE '2026-11-01' AS order_date,
    'C001' AS customer_id,
    [
      STRUCT('P001' AS product_id, 2 AS quantity, 1200 AS unit_price),
      STRUCT('P002' AS product_id, 1 AS quantity, 2500 AS unit_price)
    ] AS items
  UNION ALL
  SELECT
    1002,
    DATE '2026-11-01',
    'C002',
    [
      STRUCT('P001', 3, 1200),
      STRUCT('P003', 2, 800)
    ]
  UNION ALL
  SELECT
    1003,
    DATE '2026-11-02',
    'C001',
    [
      STRUCT('P002', 2, 2500),
      STRUCT('P003', 1, 800)
    ]
  UNION ALL
  SELECT
    1004,
    DATE '2026-11-02',
    'C003',
    [
      STRUCT('P001', 1, 1200),
      STRUCT('P001', 2, 1200),
      STRUCT('P003', 3, 800)
    ]
  UNION ALL
  SELECT
    1005,
    DATE '2026-11-03',
    'C002',
    [
      STRUCT('P002', 1, 2500),
      STRUCT('P003', 4, 800)
    ]
  UNION ALL
  SELECT
    1006,
    DATE '2026-11-03',
    'C004',
    ARRAY<STRUCT<product_id STRING, quantity INT64, unit_price INT64>>[]
)
SELECT
  items.product_id AS product_id,
  SUM(items.quantity) AS total_quantity,
  SUM(items.quantity * items.unit_price) AS total_sales,
  COUNT(DISTINCT order_id) AS order_count,
  COUNT(DISTINCT customer_id) AS customer_count
FROM orders
CROSS JOIN UNNEST(items) AS items
GROUP BY items.product_id
ORDER BY total_sales DESC;











