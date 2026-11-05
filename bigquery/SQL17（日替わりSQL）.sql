
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
































































































