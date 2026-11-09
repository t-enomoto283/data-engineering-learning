
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


