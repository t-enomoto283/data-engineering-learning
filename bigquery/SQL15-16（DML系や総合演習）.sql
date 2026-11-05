
-- GROUP BY × ARRAY_AGG()
WITH order_data AS (
  SELECT
    1001 AS order_id,
    1 AS customer_id,
    [
      STRUCT(101 AS product_id, 2 AS quantity),
      STRUCT(102 AS product_id, 1 AS quantity)
    ] AS items
  UNION ALL
  SELECT
    1002,
    2,
    [
      STRUCT(103 AS product_id, 1 AS quantity),
      STRUCT(104 AS product_id, 3 AS quantity)
    ]
  UNION ALL
  SELECT
    1003,
    1,
    [
      STRUCT(102 AS product_id, 2 AS quantity),
      STRUCT(105 AS product_id, 1 AS quantity)
    ]
  UNION ALL
  SELECT
    1004,
    3,
    [
      STRUCT(101 AS product_id, 1 AS quantity),
      STRUCT(999 AS product_id, 2 AS quantity)
    ]
),
product_master AS (
  SELECT
    101 AS product_id,
    'Keyboard' AS product_name,
    3000 AS unit_price
  UNION ALL
  SELECT 102, 'Mouse', 1500
  UNION ALL
  SELECT 103, 'Monitor', 20000
  UNION ALL
  SELECT 104, 'Cable', 800
  UNION ALL
  SELECT 105, 'Notebook', 500
),
joined_order_master AS (
  SELECT
    o.order_id,
    o.customer_id,
    i.product_id,
    m.product_id AS master_product_id,
    IFNULL(m.product_name, 'unknown') AS product_name,
    i.quantity,
    IFNULL(m.unit_price, 0) AS unit_price,
  FROM order_data AS o
  CROSS JOIN UNNEST(items) AS i
  LEFT OUTER JOIN product_master AS m
    ON i.product_id = m.product_id
)
SELECT
  order_id,
  customer_id,
  ARRAY_AGG(
    STRUCT(product_id, product_name, quantity, unit_price)
    ORDER BY product_id ASC
  ) AS items,
  SUM(quantity) AS total_quantity,
  SUM(quantity * unit_price) AS total_amount,
  COUNTIF(master_product_id IS NULL) AS unknown_product_count
FROM joined_order_master
GROUP BY order_id, customer_id
ORDER BY order_id ASC;


-- STEP 15｜DML（データの追加・更新・削除）
/*
INSERT：データを追加する
UPDATE：既存データを更新する
DELETE：データを削除する
MERGE：条件に応じて追加・更新・削除する
*/

/*
STEP 15-1｜INSERT：テーブルへのデータ追加
INSERT は、既存のテーブルに新しい行を追加するDMLで、BigQueryでの基本構文は次のとおりです。
  INSERT INTO `project.dataset.table_name` (
    column1, column2, column3
  )
  VALUES (value1, value2, value3);

複数行を一度に追加する場合は、次のように記述できます。
  INSERT INTO `project.dataset.table_name` (
    col1, col2, col3
  )
  VALUES (val1, val2, val3),
  (val4, val5, val6);

演習として、次のテーブルが存在すると仮定してください。
  テーブル名：resonant-tract-508812-p9.sql_training.products
  column        type
  product_id    INT64
  product_name  STRING
  category      STRING
  price         INT64
  created_date  DATE

  現在のデータ
  product_id  product_name  category	   price  created_date
  101         Keyboard      electronics  3000   2026-01-05
  102         Mouse         electronics  1500   2026-01-05
  103         Monitor       electronics  20000  2026-01-06

このテーブルに、以下の3商品を1つのINSERT文で追加してください。
  product_id  product_name  category     price  created_date
  104         Cable         accessories  800    2026-02-01
  105         Notebook      stationery   500    2026-02-02
  106         USB Hub       accessories  2500   2026-02-03
*/
INSERT INTO `resonant-tract-508812-p9.sql_training.products` (
  product_id, product_name, category, price, created_date
)
VALUES (104, 'Cable', 'accessories', 800, DATE '2026-02-01'),
(105, 'Notebook', 'stationery', 500, DATE '2026-02-02'),
(106, 'USB Hub', 'accessories', 2500, DATE '2026-02-03');
/*追加の確認問題
INSERT文で追加先の列名を明示することには、どのようなメリットがあるでしょうか？
明示することで追加する値と対象列の関係を誤りにくくなるほか、列名を明示するとテーブルの列順と異なる順序で値を指定することもできます。*/

/*
STEP 15-2｜INSERT INTO ... SELECT
SELECT文で取得したデータを、別のテーブルへ追加する方法です。

基本構文は次のとおりで、VALUES の代わりに SELECT を指定します。
SELECT文が返す行がそのまま追加対象になるため、WHERE や JOIN や GROUP BY や CASE などの処理を組み合わせられます。
なお、SELECTが返す列数と列の順序とデータ型は、INSERT先の列指定と対応している必要があります。
  INSERT INTO `project.dataset.destination_table` (
    column1, column2
  )
  SELECT
    column1, column2
  FROM `project.dataset.source_table`
  WHERE condition;

演習として、次の構造を持つ空のテーブル（売上管理用テーブル）が存在すると仮定してください。
  テーブル名：resonant-tract-508812-p9.sql_training.completed_order_sales
  column	type
  order_id	INT64
  customer_id	INT64
  order_month	DATE　※注文日が属する月の1日を格納する列
  sales_amount	INT64

空のテーブルに、次の追加元テーブルから以下の条件を満たすデータを追加してください。
  テーブル名：resonant-tract-508812-p9.sql_training.orders
  order_id  customer_id  order_date  amount  status
  1001      1            2026-01-05  3200    completed
  1002      2            2026-01-05  5800    completed
  1003      1            2026-01-12  2100    completed
  1004      3            2026-01-15  7500    cancelled
  1005      2            2026-02-03  4200    completed
  1006      4            2026-02-08  8900    completed

status = 'completed' の注文だけ対象。order_date から月初日を求めて order_month として追加。amount を sales_amount として追加。
*/
INSERT INTO `resonant-tract-508812-p9.sql_training.completed_order_sales` (
  order_id, customer_id, order_month, sales_amount
)
SELECT
  order_id, customer_id, DATE_TRUNC(order_date, MONTH) AS order_month, amount AS sales_amount
FROM `resonant-tract-508812-p9.sql_training.orders`
WHERE status = 'completed';
/*追加の確認問題
同じ INSERT INTO ... SELECT を、追加先テーブルのデータを削除せずに2回実行した場合、どのような問題が発生する可能性がありますか？
SELECT … FROM … で抽出条件を満たした5行×2回の実行で合計10行が追加先のテーブルに反映され、追加先に重複行が5行発生してしまいます。
定期実行するデータ処理では同じ処理を再実行しても意図しない重複が発生しない設計（冪等性：べきとうせい）が重要で、後の MERGE でも関係します。*/

/*
STEP 15-3｜UPDATE：既存データの更新
UPDATE：更新対象のテーブルを指定する。
SET：更新する列と更新後の値を指定する。
WHERE：更新対象となる行を指定する。省略するとBigQueryでは構文エラーになるため、全行を更新する場合は WHERE TRUE と指定する。

UPDATEの基本構文
  UPDATE `project.dataset.table_name`
  SET column1 = value1, column2 = value2
  WHERE condition;

例えば、商品ID101の価格を3500に変更する場合は、次のようになります。
  UPDATE `project.dataset.products`
  SET price = 3500
  WHERE product_id = 101;

また、既存の値を使って計算することもでき、下記の場合は現在の価格に500を加算します。
  UPDATE `project.dataset.products`
  SET price = price + 500
  WHERE product_id = 101;

演習として、次のテーブルが存在すると仮定してください。
  テーブル名：resonant-tract-508812-p9.sql_training.products
  product_id  product_name  category     price
  101         Keyboard      electronics  3000
  102         Mouse         electronics  1500
  103         Monitor       electronics  20000
  104         Cable         accessories  800
  105         Notebook      stationery   500
  106         USB Hub       accessories  2500

このテーブルについて category = 'electronics' の商品について、価格を一律10%引き上げてください。
*/
UPDATE `resonant-tract-508812-p9.sql_training.products`
SET price = CAST(ROUND(price * 1.1, 0) AS INT64)
WHERE category = 'electronics';
/*追加の確認問題
今回のUPDATE文を同じテーブルに対して2回実行した場合、価格はどうなりますか？また、なぜそのような結果になるのでしょうか？
元のpriceが1.1倍された値が更に1.1倍された結果となり、例えば商品ID101の価格は3630で、これは1回目のUPDATEで1.1倍されたXが2回目で再びX*1.1されます。*/

/*
STEP 15-4｜DELETE：既存データの削除
DELETE は、WHERE に一致した行そのものを削除します。
一応、BigQueryでは全行を削除する場合に WHERE TRUE と記述することもできます。

基本構文は次のとおりで、この場合は商品ID101の行が削除されます。
  DELETE FROM `project.dataset.products`
  WHERE product_id = 101;

演習として、次のテーブルが存在すると仮定してください。
  テーブル名：resonant-tract-508812-p9.sql_training.products
  product_id  product_name  category     price
  101         Keyboard      electronics	 3000
  102         Mouse         electronics	 1500
  103         Monitor       electronics	 20000
  104         Cable         accessories	 800
  105         Notebook      stationery   500
  106         USB Hub       accessories  2500

このテーブルについて 価格が1000未満の商品を削除してください。
*/
DELETE FROM `resonant-tract-508812-p9.sql_training.products`
WHERE price < 1000;
/*追加の確認問題
DELETE FROM で条件に一致する行を削除することと、UPDATE でその行の price をNULLに変更することには、どのような違いがありますか？
DELETE文では条件に一致する行自体が削除され、UPDATEでその行の値をNULLに変更した場合は行自体が残ります。*/

/*
STEP 15-5｜MERGE：条件に応じた更新・追加
ここからは、DMLの中でもデータエンジニアリングの実務で重要な MERGE を学習します。
MERGE は、ソース表とターゲット表を照合し、条件に応じて更新や追加などを行うDMLで、基本構文は下記例。

MERGE INTO `project.dataset.target_table` AS t -- 行の更新や追加をしたいターゲット表
  USING `project.dataset.source_table` AS s -- 基となるソース表
  ON (t.列 = s.列) -- ソース表の行とターゲット表の行を関連付けるための条件
  WHEN MATCHED THEN -- ターゲット表でON句の条件を満たす行は下記のような形でUPDATEを実行
    UPDATE SET ターゲット表の列 = 値
  WHEN NOT MATCHED THEN -- ターゲット表でON句の条件を満たさない行は下記のような形でINSERTを実行
    INSERT (タゲ列, タゲ列, タゲ列) -- ここで指定したターゲット表の列に対して後続するVALUESの値を新しい行としてINSERT
    VALUES (s.列, s.列, s.列);

WHEN MATCHED における UPDATE SET の対象に条件を指定したい場合は下記となります。
なお、ON句によってターゲット表の列とソース表の列が紐付いています。
そのため、条件式には s.列 = 値 のようなソース表の参照も、t.列 = 値 のようなターゲット表の参照も両方可能です。
  WHEN MATCHED AND 条件式 THEN
    UPDATE SET ターゲット表の列 = 値

逆に、WHEN NOT MATCHED における INSERT … VALUES … の対象に条件を指定したい場合、下記となります。
なお、WHEN NOT MATCHED は「ソース表にはデータがあるがターゲット表には一致するキーがなかった」という意味です。
そのため、条件式には t.列 = 値 のようなターゲット表の参照はできず、s.列 = 値 のようなソース表の参照のみ可能です。
  WHEN NOT MATCHED AND 条件式 THEN
    INSERT (タゲ列, タゲ列, タゲ列)
    VALUES (s.列, s.列, s.列)

MERGE文を使って行を削除したい場合、UPDATE とは切り離して、WHEN MATCHED AND <削除条件> THEN DELETE という独立したブロック（句）を書けます。
MERGE INTO `project.dataset.target_table` AS t
  USING `project.dataset.source_table` AS s
  ON (t.列 = s.列)
  WHEN MATCHED AND 条件式 THEN
    DELETE

さらに、DELETE と UPDATE を組み合わせることも可能です。
MERGE INTO `project.dataset.target_table` AS t
  USING `project.dataset.source_table` AS s
  ON (t.列 = s.列)
  WHEN MATCHED AND 条件式 THEN
    DELETE
  WHEN MATCHED THEN
    UPDATE SET ターゲット表の列 = 値

USING句にソース表の表名を指定しますが、表の代わりに「ビュー」や「副問合せ」を指定することも可能。
ON句にソース表の行とターゲット表の行を関連付けるための条件を指定しますが、BigQueryではON句で指定した列もUPDATEできる。
BigQueryでは UPDATE SET の左辺や INSERT の列一覧には、ターゲット表の列について t. のような表の接頭辞を無しで記述する。
一方で、UPDATE SET の右辺や VALUES では、ソース表の列について s. のような表の接頭辞を使って記述する。
WHEN MATCHED のブロックを省略して、WHEN NOT MATCHED のブロックのみを指定することもでき、この逆パターンも可能。


演習として、次のテーブルが存在すると仮定してください。
  更新対象テーブル名：resonant-tract-508812-p9.sql_training.product_master
  product_id  product_name  category     price
  101         Keyboard      electronics  3000
  102         Mouse         electronics  1500
  103         Monitor       electronics  20000
  104         Cable         accessories  800

  更新元テーブル名：resonant-tract-508812-p9.sql_training.product_updates
  product_id  product_name    category     price
  102         Wireless Mouse  electronics  2200
  103         4K Monitor      electronics  28000
  105         Notebook        stationery   500
  106         USB Hub         accessories  2500

MERGE を使用して商品マスタを更新してください。
商品IDが一致した場合 product_name と category と price を更新。
商品IDが一致しない場合 product_id と product_name と category と price を新しい行として追加。
*/
MERGE INTO `resonant-tract-508812-p9.sql_training.product_master` AS t
  USING `resonant-tract-508812-p9.sql_training.product_updates` AS s
  ON (t.product_id = s.product_id)
  WHEN MATCHED THEN
    UPDATE SET product_name = s.product_name, category = s.category, price = s.price
  WHEN NOT MATCHED THEN
    INSERT (product_id, product_name, category, price)
    VALUES (s.product_id, s.product_name, s.category, s.price);
/*追加の確認問題
今回のMERGE文を同じデータに対して2回実行した場合、2回目にも商品ID105・106は新しい行として追加されるでしょうか？ その理由も説明してください。
商品ID105と106はソース表にありターゲット表にないため、ON句の t.producct_id = s.product_id において
1回目のMERGEでは WHEN NOT MATCHED THEN で True となりターゲット表へ新しい行としてINSERTされます。
2回目のMERGEでは WHEN MATCHED THEN で True となり、WHEN NOT MATCHED THEN では False なので新しい行としてINSERTされません。*/

/*
STEP 15-6｜MERGE × 条件付きUPDATE
次は、MERGEの基本を少し発展させます。
今回は、商品IDが一致し、さらに価格が変更されている場合だけUPDATEする処理を作成します。

演習として、次のテーブルが存在すると仮定してください。
  更新対象テーブル名：resonant-tract-508812-p9.sql_training.product_master
  product_id  product_name  category     price
  101         Keyboard      electronics  3000
  102         Mouse         electronics  1500
  103         Monitor       electronics  20000
  104         Cable         accessories  800

  更新元テーブル名：resonant-tract-508812-p9.sql_training.product_updates
  product_id  product_name    category     price
  101         Keyboard        electronics  3000
  102         Wireless Mouse  electronics  2200
  103         4K Monitor      electronics  20000
  105         Notebook        stationery   500

商品IDが一致かつターゲット表とソース表の価格が異なる場合 product_name と category と price を更新。
商品IDが一致していても価格が同じなら他の列が異なっていても更新しない。商品IDが一致しなければ、4列すべてをINSERTする。
*/
MERGE INTO `resonant-tract-508812-p9.sql_training.product_master` AS t
  USING `resonant-tract-508812-p9.sql_training.product_updates` AS s
  ON (t.product_id = s.product_id)
  WHEN MATCHED AND t.price != s.price THEN
    UPDATE SET product_name = s.product_name, category = s.category, price = s.price
  WHEN NOT MATCHED THEN
    INSERT (product_id, product_name, category, price)
    VALUES (s.product_id, s.product_name, s.category, s.price);
/*追加の確認問題
商品ID103は商品名が異なっていますが、今回のMERGEでは更新されません。これはSQLのどの条件によって決まるのでしょうか？
今回のSQLにおける ON句の t.product_id = s.product_id が True かつ、price != s.price が　True の場合に UPDATE SET … が実行されます。
つまり、ソース表と商品IDが一致かつソース表と価格が異なるターゲット表の行に限り、商品名とカテゴリと価格が更新されます。*/

/*
STEP 15-7｜DML総合演習
今回は、MERGEを使って売上集計テーブルを更新する処理を考えます。

演習として、次のテーブルが存在すると仮定してください。
  更新対象テーブル名：resonant-tract-508812-p9.sql_training.monthly_sales
  sales_month はDATE型、category はSTRING型、total_amount はINT64型です。
  sales_month  category     total_amount
  2026-08-01   electronics  50000
  2026-08-01   accessories  12000
  2026-09-01   electronics  65000

  更新元テーブル名：resonant-tract-508812-p9.sql_training.monthly_sales_updates
  sales_month  category     total_amount
  2026-08-01   electronics  55000
  2026-08-01   accessories  12000
  2026-09-01   electronics  70000
  2026-09-01   accessories  8000
  2026-10-01   electronics  30000

sales_month と category の2列を照合キーにする。両方のキーが一致かつ total_amount が異なる場合 total_amount を更新。
キーが一致していても total_amount が同じ場合は更新しない。キーが一致しない場合3列すべてをINSERTする。
*/
MERGE INTO `resonant-tract-508812-p9.sql_training.monthly_sales` AS t
  USING `resonant-tract-508812-p9.sql_training.monthly_sales_updates` AS s
  ON (t.sales_month = s.sales_month AND t.category = s.category)
  WHEN MATCHED AND t.total_amount != s.total_amount THEN
    UPDATE SET total_amount = s.total_amount
  WHEN NOT MATCHED THEN
    INSERT (sales_month, category, total_amount)
    VALUES (CAST(s.sales_month AS DATE), CAST(s.category AS STRING), CAST(s.total_amount AS INT64));
/*追加の確認問題
今回のMERGEで、ON 句の照合条件を sales_month だけにした場合、どのような問題が生じるか具体的なデータを踏まえて説明してください。
ターゲット表の sales_month には 2026-08-01 が2行あり、ソース表の sales_month には 2026-08-01 と 2026-09-01 が共に2行ずつあります。
MERGE文ではターゲット表の1行に対してソース表の行が2行以上マッチしてはならないので、エラーです。
そのため今回は、ON (t.sales_month = s.sales_month AND t.category = s.category) という組み合わせをキー指定する必要があります。 */


-- STEP 16｜SQL総合演習
/*
これまでSTEP 1〜15で学習したBigQuery SQLを組み合わせて、実務に近いデータ加工・集計処理を自力で「設計」する練習をします。
要件に対して、どのSQL構文を使うべきかも自分で判断します。
*/

/*
STEP 16-1｜月次・カテゴリ別売上データマート
あなたはECサイトのデータエンジニアで、分析担当者から次の依頼を受けました。
  2026年8月〜10月の売上を、月別・商品カテゴリ別に分析したいです。
  各月・各カテゴリについて、売上金額、注文件数、購入顧客数を確認できるデータを作成してください。
  売上金額が大きいカテゴリから順番に見られるようにしてください。

使用するテーブル
  training16_orders：注文ID、顧客ID、注文日、注文状態
  training16_order_items：注文ID、商品ID、数量、販売単価
  training16_products：商品ID、商品名、カテゴリ、基準価格

抽出条件
  order_date が2026年8月1日〜10月31日の注文を対象とする。
  status = 'completed' の注文のみを対象とする。
  売上金額は quantity * unit_price で計算する。
  商品マスタに存在しない商品IDについては、カテゴリを 'unknown' として集計に含める。

集計条件
以下の5列を売上月 × 商品カテゴリ単位で出力、sales_month の昇順で total_sales の降順で category の昇順。
  sales_month：売上月（月初日、DATE型）
  category：商品カテゴリ
  total_sales：売上金額の合計
  order_count：重複を除いた注文件数
  customer_count：重複を除いた購入顧客数
*/
WITH order_extract AS (
  SELECT
    order_id,
    customer_id,
    DATE_TRUNC(order_date, MONTH) AS sales_month
  FROM `resonant-tract-508812-p9.sql_training.training16_orders`
  WHERE status = 'completed'
    AND (order_date BETWEEN DATE '2026-08-01' AND DATE '2026-10-31')
),
items_reference AS (
  SELECT
    o.sales_month,
    IFNULL(p.category, 'unknown') AS category,
    i.quantity * i.unit_price AS sales,
    o.order_id,
    o.customer_id
  FROM order_extract AS o
  INNER JOIN `resonant-tract-508812-p9.sql_training.training16_order_items` AS i
    ON o.order_id = i.order_id
  LEFT OUTER JOIN `resonant-tract-508812-p9.sql_training.training16_products` AS p
    ON i.product_id = p.product_id
)
SELECT
  sales_month,
  category,
  SUM(sales) AS total_sales,
  COUNT(DISTINCT order_id) AS order_count,
  COUNT(DISTINCT customer_id) AS customer_count
FROM items_reference
GROUP BY sales_month, category
ORDER BY sales_month ASC, total_sales DESC, category ASC;

/*
STEP 16-2｜顧客別購買分析
ECサイトのマーケティング担当者から、次の依頼を受けました。
  顧客ごとの購買状況を一覧で確認したいです。
  購入回数や累計購入金額を集計し、まだ購入していない顧客も含めて分析できるようにしてください。

使用するテーブル
  training16_customers
  training16_orders
  training16_order_items

対象条件
  2026年7月1日〜12月31日の注文を対象とする。
  status = 'completed' の注文のみを購入実績として扱う。
  顧客マスタに存在する全30顧客を出力する。
  購入実績のない顧客も除外しない。

出力条件
  customer_id：顧客ID
  region：顧客の地域
  order_count：購入した注文件数（重複除外）
  total_spent：累計購入金額
  first_order_date：最初の購入日
  last_order_date：最後の購入日

購入実績のない顧客は、order_count と total_spent を 0、first_order_date と last_order_date を NULL としてください。
並び替えは total_spent の降順、同額の場合は customer_id の昇順。出力は全30顧客の行。region がNULLの顧客も出力される。
*/
WITH order_extract AS (
  SELECT
    order_id,
    customer_id,
    order_date
  FROM `resonant-tract-508812-p9.sql_training.training16_orders`
  WHERE status = 'completed'
    AND (order_date >= DATE '2026-07-01' AND order_date < DATE '2027-01-01')
),
customer_reference AS (
  SELECT
    c.customer_id,
    c.region,
    o.order_id,
    i.quantity * i.unit_price AS spent,
    o.order_date
  FROM order_extract AS o
  RIGHT OUTER JOIN `resonant-tract-508812-p9.sql_training.training16_customers` AS c
    ON o.customer_id = c.customer_id
  LEFT OUTER JOIN `resonant-tract-508812-p9.sql_training.training16_order_items` AS i
    ON o.order_id = i.order_id
)
SELECT
  customer_id,
  region,
  COUNT(DISTINCT order_id) AS order_count,
  IFNULL(SUM(spent), 0) AS total_spent,
  MIN(order_date) AS first_order_date,
  MAX(order_date) AS last_order_date
FROM customer_reference
GROUP BY customer_id, region
ORDER BY total_spent DESC, customer_id ASC;

/*
STEP 16-3｜商品別売上ランキング
ECサイトの商品企画担当者から、次の依頼を受けました。
  2026年7月〜12月の商品別売上実績を確認したいです。
  商品カテゴリごとに売上金額のランキングを作成し、売上上位の商品を把握できるようにしてください。
  なお、売上が同額の商品は同じ順位にしてください。

使用するテーブル
  training16_orders
  training16_order_items
  training16_products

抽出条件
  注文日が2026年7月1日〜12月31日の注文を対象とする。
  status = 'completed' の注文のみ対象とする。
  商品マスタに登録されている商品のみを対象とする。商品ID999は除外する。
  売上金額は quantity * unit_price とする。

集計条件
商品単位で以下の項目を出力、category の昇順 sales_rank の昇順 同順位の場合は product_id の昇順
  category：商品カテゴリ
  product_id：商品ID
  product_name：商品名
  total_sales：商品ごとの売上金額合計
  total_quantity：商品ごとの販売数量合計
  sales_rank：同一カテゴリ内の売上金額順位。商品カテゴリごとに独立。売上金額の多い商品ほど上位、同額商品は同順位、同順位複数の場合は次の順位を飛ばす。
*/
WITH order_extract AS (
  SELECT
    order_id
  FROM `resonant-tract-508812-p9.sql_training.training16_orders`
  WHERE status = 'completed'
    AND (order_date BETWEEN DATE '2026-07-01' AND DATE '2026-12-31')
),
item_reference AS (
  SELECT
    p.category,
    p.product_id,
    p.product_name,
    SUM(i.quantity * i.unit_price) AS total_sales,
    SUM(i.quantity) AS total_quantity
  FROM order_extract AS o
  INNER JOIN `resonant-tract-508812-p9.sql_training.training16_order_items` AS i
    ON o.order_id = i.order_id
  INNER JOIN `resonant-tract-508812-p9.sql_training.training16_products` AS p
    ON i.product_id = p.product_id
  GROUP BY p.category, p.product_id, p.product_name
)
SELECT
  category,
  product_id,
  product_name,
  total_sales,
  total_quantity,
  RANK() OVER (
    PARTITION BY category
    ORDER BY total_sales DESC
  ) AS sales_rank
FROM item_reference
ORDER BY category ASC, sales_rank ASC, product_id ASC;

/*
STEP 16-4｜月次売上の推移・前月比較
ECサイトの事業責任者から、次の依頼を受けました。
  2026年7月〜12月の月次売上を一覧にして、前月から売上がどれだけ増減したのかを確認したいです。
  金額の差だけでなく、前月比も確認できるようにしてください。

使用するテーブル
  training16_orders
  training16_order_items

抽出条件
  注文日が2026年7月1日〜12月31日の注文を対象とする。
  status = 'completed' の注文のみを対象とする。
  売上金額は quantity * unit_price で計算する。

出力条件
月単位で以下の5列を出力してください。
  sales_month：売上月（月初日、DATE型）
  total_sales：当月の売上金額
  previous_month_sales：前月の売上金額
  sales_diff：当月売上 − 前月売上
  mom_rate：前月比（%）mom_rate = 当月売上-前月売上/前月売上 * 100 を小数第2位までに丸める。
今回は商品マスタとの結合は不要で商品ID999の明細も売上に含める。
最初の月（2026年7月）は比較対象となる前月がないため、previous_month_sales、sales_diff、mom_rate はすべてNULLとする。
前月売上が0の場合、mom_rate はNULLとする。最終結果は sales_month の昇順。
*/
WITH order_extract AS (
  SELECT
    order_id,
    DATE_TRUNC(order_date, MONTH) AS sales_month
  FROM `resonant-tract-508812-p9.sql_training.training16_orders`
  WHERE status = 'completed'
    AND (order_date >= DATE '2026-07-01' AND order_date < DATE '2027-01-01')
),
item_reference AS (
  SELECT
    o.sales_month,
    SUM(i.quantity * i.unit_price) AS total_sales
  FROM order_extract AS o
  INNER JOIN `resonant-tract-508812-p9.sql_training.training16_order_items` AS i
    ON o.order_id = i.order_id
  GROUP BY o.sales_month
)
SELECT
  sales_month,
  total_sales,
  LAG(total_sales) OVER (
    ORDER BY sales_month ASC
  ) AS previous_month_sales,
  total_sales - LAG(total_sales) OVER (
    ORDER BY sales_month ASC
  ) AS sales_diff,
  ROUND(
    SAFE_DIVIDE(
      total_sales - LAG(total_sales) OVER (ORDER BY sales_month ASC),
      LAG(total_sales) OVER (ORDER BY sales_month ASC)
    ) * 100, 2
  ) AS mom_rate
FROM item_reference
ORDER BY sales_month ASC;

/*
STEP 16-5｜初回購入・リピート購入分析
ECサイトのマーケティング担当者から、次の依頼を受けました。
  月ごとに、初めて購入した顧客と、過去にも購入したことがある顧客を分けて集計したいです。
  新規顧客とリピート顧客の人数、およびそれぞれの売上金額を確認できるデータを作成してください。

使用するテーブル
  training16_orders
  training16_order_items

対象条件
  2026年7月1日〜12月31日の注文を対象とする。
  status = 'completed' の注文のみを対象とする。
  売上金額は quantity * unit_price とする。
  キャンセル・処理中の注文は、購入履歴にも売上にも含めない。

新規・リピートの判定ルールとして、顧客ごとに対象期間内で最初に購入した日を初回購入日とします。
  新規顧客：その月が初回購入日の属する月である顧客。
  リピート顧客：その月より前に初回購入日が存在する顧客。
  同じ月に2回以上購入していても、その月が初回購入月なら、その月の購入はすべて新規顧客の売上として扱います。

出力条件
月ごとに、以下の5列を出力してください。
  sales_month：売上月（月初日、DATE型）
  new_customer_count：当月の新規購入顧客数
  repeat_customer_count：当月のリピート購入顧客数
  new_customer_sales：新規顧客による当月売上
  repeat_customer_sales：リピート顧客による当月売上

購入実績のある顧客だけを人数に含め、人数と売上金額は該当がなければ0としてください。最終結果は sales_month の昇順。
2026年7月〜12月の6行が出力され、7月は対象期間の最初の月なのでリピート顧客数・リピート売上ともに0になる。
同じ顧客が同月に複数回注文しても、顧客数は重複して数えない。
*/
WITH order_extract AS (
  SELECT
    o.order_id,
    i.quantity * i.unit_price AS sales,
    o.customer_id,
    DATE_TRUNC(o.order_date, MONTH) AS sales_month,
    FIRST_VALUE(o.order_date) OVER (
      PARTITION BY o.customer_id
      ORDER BY o.order_date ASC
      ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
    ) AS first_order
  FROM `resonant-tract-508812-p9.sql_training.training16_orders` AS o
  INNER JOIN `resonant-tract-508812-p9.sql_training.training16_order_items` AS i
    ON o.order_id = i.order_id
  WHERE o.status = 'completed'
    AND (o.order_date BETWEEN DATE '2026-07-01' AND DATE '2026-12-31')
),
month_flag AS (
  SELECT
    order_id,
    sales,
    customer_id,
    sales_month,
    first_order,
    DATE_DIFF(sales_month, first_order, MONTH) AS month_diff
  FROM order_extract
)
SELECT
  sales_month,
  COUNT(DISTINCT IF(month_diff = 0, customer_id, NULL)) AS new_customer_count,
  COUNT(DISTINCT IF(month_diff != 0, customer_id, NULL)) AS repeat_customer_count,
  IFNULL(
    SUM(IF(month_diff = 0, sales, NULL)),
    0
  ) AS new_customer_sales,
  IFNULL(
    SUM(IF(month_diff != 0, sales, NULL)),
    0
  ) AS repeat_customer_sales
FROM month_flag
GROUP BY sales_month
ORDER BY sales_month ASC;

/*
STEP 16-6｜顧客セグメント分析
ECサイトのマーケティング担当者から、次の依頼を受けました。
  2026年7月〜12月の購入金額をもとに、顧客を購買金額別のセグメントに分類したいです。
  各セグメントの顧客数、売上金額、顧客1人あたりの平均購入金額を集計してください。購入実績のない顧客も分析対象に含めてください。

使用するテーブル
  training16_customers
  training16_orders
  training16_order_items

集計対象
  2026年7月1日〜12月31日の注文。status = 'completed' のみ。
  売上金額は quantity * unit_price とする。
  顧客マスタに登録された全員対象。購入実績のない顧客の累計購入金額は0円とする。

セグメントの分類ルールとして、顧客ごとの対象期間内の累計購入金額によって次の4区分に分類、各顧客はいずれか1つのセグメントに属す。
  high：100,000円以上
  middle：50,000円以上100,000円未満
  low：1円以上50,000円未満
  no_purchase：0円

出力条件
  segment：セグメント名
  customer_count：セグメントに属する顧客数
  total_sales：セグメント内の累計購入金額合計
  avg_sales_per_customer：顧客1人あたりの平均累計購入金額で小数第2位まで

no_purchase の total_sales と avg_sales_per_customer は0とする。
high → middle → low → no_purchase の順序で出力。
今回は顧客単位の集計 → セグメント分類 → セグメント単位の集計という処理を設計してください。
*/
WITH order_extract AS (
  SELECT
    c.customer_id,
    IFNULL(SUM(i.quantity * i.unit_price), 0) AS sales,
    CASE
      WHEN IFNULL(SUM(i.quantity * i.unit_price), 0) >= 100000 THEN 1
      WHEN IFNULL(SUM(i.quantity * i.unit_price), 0) >= 50000 THEN 2
      WHEN IFNULL(SUM(i.quantity * i.unit_price), 0) >= 1 THEN 3
      ELSE 4
    END AS div_segment,
    CASE
      WHEN IFNULL(SUM(i.quantity * i.unit_price), 0) >= 100000 THEN 'high'
      WHEN IFNULL(SUM(i.quantity * i.unit_price), 0) >= 50000 THEN 'middle'
      WHEN IFNULL(SUM(i.quantity * i.unit_price), 0) >= 1 THEN 'low'
      ELSE 'no_purchase'
    END AS segment
  FROM `resonant-tract-508812-p9.sql_training.training16_orders` AS o
  RIGHT OUTER JOIN `resonant-tract-508812-p9.sql_training.training16_customers` AS c
    ON o.customer_id = c.customer_id
      AND o.status = 'completed'
      AND (o.order_date BETWEEN DATE '2026-07-01' AND DATE '2026-12-31')
  LEFT OUTER JOIN `resonant-tract-508812-p9.sql_training.training16_order_items` AS i
    ON o.order_id = i.order_id
  GROUP BY c.customer_id
),
segment_sales AS (
  SELECT
    div_segment,
    segment,
    COUNT(customer_id) AS customer_count,
    IFNULL(SUM(sales), 0) AS total_sales,
    ROUND(IFNULL(AVG(sales), 0), 2) AS avg_sales_per_customer
  FROM order_extract
  GROUP BY div_segment, segment
)
SELECT
  segment,
  customer_count,
  total_sales,
  avg_sales_per_customer
FROM segment_sales
ORDER BY div_segment ASC;

/*
STEP 16-7｜データ品質チェック
データ基盤チームから、次の依頼を受けました。
  ECサイトのデータを分析用データマートに取り込む前に、データ品質を確認したいです。
  顧客・商品・注文・注文明細の各テーブルについて、NULL、重複、マスタとの不整合を検出し、チェック結果を一覧化してください。

使用するテーブル
  training16_customers
  training16_products
  training16_orders
  training16_order_items

次の6つのチェック項目について、不正・不整合に該当する件数を集計してください。
  null_region：customers.region がNULLの顧客数
  duplicate_customer_id：顧客IDの重複行数
  duplicate_order_id：注文IDの重複行数
  invalid_customer_id：顧客マスタに存在しない顧客IDを持つ注文数
  invalid_product_id：商品マスタに存在しない商品IDを持つ注文明細数
  invalid_quantity：order_items.quantity がNULLまたは0以下の明細数

重複行数の定義
  例えば、同じ顧客IDが3行存在する場合、正常な1行を除いた余分な2行を重複行数としてカウントしてください。
  重複しているIDの種類数ではありません。

出力条件
以下の2列、各チェック項目を1行として合計6行を出力。
  check_name：チェック項目名、error_count：該当する件数

最終結果は check_name の昇順。今回は注文期間やステータスによる絞り込みは行いません。4テーブルの全レコードを検査対象とする。
*/
SELECT
  'null_region' AS check_name,
  COUNTIF(region IS NULL) AS error_count
FROM `resonant-tract-508812-p9.sql_training.training16_customers`
UNION ALL
SELECT
  'duplicate_customer_id',
  COUNT(customer_id) - COUNT(DISTINCT customer_id)
FROM `resonant-tract-508812-p9.sql_training.training16_customers`
UNION ALL
SELECT
  'duplicate_order_id',
  COUNT(order_id) - COUNT(DISTINCT order_id)
FROM `resonant-tract-508812-p9.sql_training.training16_orders`
UNION ALL
SELECT
  'invalid_customer_id',
  COUNT(*)
FROM `resonant-tract-508812-p9.sql_training.training16_orders` AS o
WHERE NOT EXISTS (
  SELECT
    1
  FROM `resonant-tract-508812-p9.sql_training.training16_customers` AS c
  WHERE c.customer_id = o.customer_id
)
UNION ALL
SELECT
  'invalid_product_id',
  COUNT(*)
FROM `resonant-tract-508812-p9.sql_training.training16_order_items` AS i
WHERE NOT EXISTS (
  SELECT
    1
  FROM `resonant-tract-508812-p9.sql_training.training16_products` AS p
  WHERE p.product_id = i.product_id
)
UNION ALL
SELECT
  'invalid_quantity',
  COUNTIF(quantity IS NULL OR quantity <= 0)
FROM `resonant-tract-508812-p9.sql_training.training16_order_items`
ORDER BY check_name ASC;

/*
STEP 16-8｜注文単位の売上データマート作成
ECサイトの分析担当者から、次の依頼を受けました。
  注文単位で売上情報を確認できるデータマートが欲しいです。
  注文ごとの売上金額と商品点数を集計し、顧客の地域情報も付与してください。また、注文金額に基づいて注文ランクを分類したいです。

使用するテーブル
  training16_orders
  training16_order_items
  training16_customers

2026年7月1日〜12月31日の完了注文を対象として、1注文につき1行のデータマートを作成してください。
出力列
  order_id：注文ID
  customer_id：顧客ID
  region：顧客の地域
  order_date：注文日
  total_quantity：注文内の商品数量の合計
  total_sales：注文内の売上金額合計
  order_rank：注文金額15,000円以上 'large'、7,000円以上15,000円未満 'medium'、7,000円未満 'small'

売上金額は quantity * unit_price で計算する。顧客の region がNULLの場合は 'Unknown' として出力する。
対象期間内の完了注文をすべて出力する。注文明細が存在しない注文があった場合もその注文を残して total_quantity と total_sales を0とする。
order_id の昇順に並び替える。今回は注文を必ず残す結合設計と、注文単位での集計・分類がポイントです。
*/
WITH order_extract AS (
  SELECT
    o.order_id,
    o.customer_id,
    IFNULL(c.region, 'Unknown') AS region,
    o.order_date,
    i.quantity,
    i.unit_price
  FROM `resonant-tract-508812-p9.sql_training.training16_orders` AS o
  LEFT OUTER JOIN `resonant-tract-508812-p9.sql_training.training16_customers` AS c
    ON o.customer_id = c.customer_id
  LEFT OUTER JOIN `resonant-tract-508812-p9.sql_training.training16_order_items` AS i
    ON o.order_id = i.order_id
  WHERE o.status = 'completed'
    AND (o.order_date >= DATE '2026-07-01' AND o.order_date < DATE '2027-01-01')
)
SELECT
  order_id,
  customer_id,
  region,
  order_date,
  IFNULL(SUM(quantity), 0) AS total_quantity,
  IFNULL(SUM(quantity * unit_price), 0) AS total_sales,
  CASE
    WHEN IFNULL(SUM(quantity * unit_price), 0) >= 15000 THEN 'large'
    WHEN IFNULL(SUM(quantity * unit_price), 0) >= 7000 THEN 'medium'
    ELSE 'small'
  END AS order_rank
FROM order_extract
GROUP BY order_id, customer_id, region, order_date
ORDER BY order_id ASC;

/*
STEP 16-9｜地域別・月別売上分析
ECサイトの営業担当者から、次の依頼を受けました。
  地域ごとの月次売上推移を比較したいです。
  地域別・月別の売上金額、注文数、購入顧客数を集計し、前月からの売上増減も確認できるようにしてください。

使用するテーブル
  training16_customers
  training16_orders
  training16_order_items

2026年7月〜12月の完了注文を対象に、地域別・月別の売上データマートを作成してください。
出力列
  region：顧客の地域
  sales_month：売上月（月初日）
  order_count：注文数
  customer_count：購入顧客数
  total_sales：売上金額
  prev_month_sales：前月の売上金額
  mom_growth_rate：前月比売上増減率（%）(当月売上-前月売上)/前月売上 * 100 を小数第二位

売上金額は quantity * unit_price とする。地域がNULLの場合は 'Unknown' とする。注文数は重複しない注文IDの件数。購入顧客数は重複しない顧客IDの人数。
同じ地域内で前月の売上と比較。前月の売上が0円の場合 増減率はNULLとする。前月のデータが存在しない場合 prev_month_sales と mom_growth_rate はNULLとする。
売上が存在しない月は、order_count、customer_count、total_sales を0として出力。結果の並び替えは region の昇順と sales_month の昇順。
*/
WITH order_extract AS (
  SELECT
    IFNULL(c.region, 'Unknown') AS region,
    DATE_TRUNC(o.order_date, MONTH) AS sales_month,
    o.order_id,
    o.customer_id,
    i.quantity,
    i.unit_price
  FROM `resonant-tract-508812-p9.sql_training.training16_orders` AS o
  LEFT OUTER JOIN `resonant-tract-508812-p9.sql_training.training16_customers` AS c
    ON o.customer_id = c.customer_id
  LEFT OUTER JOIN `resonant-tract-508812-p9.sql_training.training16_order_items` AS i
    ON o.order_id = i.order_id
  WHERE o.status = 'completed'
    AND (o.order_date >= DATE '2026-07-01' AND o.order_date < DATE '2027-01-01')
),
sales_data AS (
  SELECT
    region,
    sales_month,
    COUNT(DISTINCT order_id) AS order_count,
    COUNT(DISTINCT customer_id) AS customer_count,
    SUM(quantity * unit_price) AS total_sales
  FROM order_extract
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
target_list AS (
  SELECT
    IFNULL(r.region, 'Unknown') AS region,
    m.make_month
  FROM (
    SELECT
      region
    FROM `resonant-tract-508812-p9.sql_training.training16_customers`
    GROUP BY region
  ) AS r
  CROSS JOIN make_month AS m
),
area_month_sales AS (
  SELECT
    t.region,
    t.make_month AS sales_month,
    IFNULL(s.order_count, 0) AS order_count,
    IFNULL(s.customer_count, 0) AS customer_count,
    IFNULL(s.total_sales, 0) AS total_sales
  FROM sales_data AS s
  RIGHT OUTER JOIN target_list AS t
    ON t.region = s.region
      AND t.make_month = s.sales_month
),
plus_prev_sales AS (
  SELECT
    region,
    sales_month,
    order_count,
    customer_count,
    total_sales,
    LAG(total_sales) OVER (
      PARTITION BY region
      ORDER BY sales_month ASC
    ) AS prev_month_sales
  FROM area_month_sales
)
SELECT
  region,
  sales_month,
  order_count,
  customer_count,
  total_sales,
  prev_month_sales,
  ROUND(
    SAFE_DIVIDE(total_sales - prev_month_sales, prev_month_sales) * 100,
    2
  ) AS mom_growth_rate
FROM plus_prev_sales
ORDER BY region ASC, sales_month ASC;

/*
STEP 16-10｜SQL総合演習・最終課題
ECサイトの分析担当者から、次の依頼を受けました。
  商品ごとの売上実績を集計し、カテゴリ内での売上順位を確認したいです。
  また、売上が発生していない商品も含め、各商品がカテゴリ全体の売上にどれだけ貢献しているかを確認できるデータマートを作成してください。

使用するテーブル
  training16_products
  training16_orders
  training16_order_items

2026年7月1日〜12月31日の完了注文を対象に、商品別の売上分析データマートを作成してください。
出力列
  category：商品カテゴリ
  product_id：商品ID
  product_name：商品名
  order_count：その商品を含む注文数
  total_quantity：販売数量合計
  total_sales：売上金額合計
  category_sales：その商品のカテゴリ全体の売上
  sales_share_pct：カテゴリ売上に占める商品売上の割合（%）total_sales/category_sales * 100 を小数第二位
  category_rank：カテゴリ内の売上順位

売上金額は quantity * unit_price で計算。商品マスタに存在すれば売上のない商品も注文数・販売数量・売上金額を0として出力。商品マスタに存在しない商品は除外。
カテゴリ売上が0円の場合 sales_share_pct はNULLとする。category_rank はカテゴリ内で total_sales の高い順で RANK() として同額なら同順位とする。
結果の並び替えは category 昇順 category_rank 昇順 product_id 昇順
*/
WITH extract_order AS (
  SELECT
    o.order_id,
    i.product_id,
    i.quantity,
    i.unit_price
  FROM `resonant-tract-508812-p9.sql_training.training16_orders` AS o
  INNER JOIN `resonant-tract-508812-p9.sql_training.training16_order_items` AS i
    ON o.order_id = i.order_id
  WHERE o.status = 'completed'
    AND (o.order_date BETWEEN DATE '2026-07-01' AND DATE '2026-12-31')
),
product_joined AS (
  SELECT
    p.category,
    p.product_id,
    p.product_name,
    e.order_id,
    e.quantity,
    e.unit_price
  FROM `resonant-tract-508812-p9.sql_training.training16_products` AS p
  LEFT OUTER JOIN extract_order AS e
    ON p.product_id = e.product_id
),
category_product AS (
  SELECT
    category,
    product_id,
    product_name,
    COUNT(DISTINCT order_id) AS order_count,
    IFNULL(SUM(quantity), 0) AS total_quantity,
    IFNULL(SUM(quantity * unit_price), 0) total_sales
  FROM product_joined
  GROUP BY category, product_id, product_name
),
category_sales_rank AS (
  SELECT
    category,
    product_id,
    product_name,
    order_count,
    total_quantity,
    total_sales,
    SUM(total_sales) OVER (
      PARTITION BY category
    ) AS category_sales,
    RANK() OVER (
      PARTITION BY category
      ORDER BY total_sales DESC
    ) AS category_rank
  FROM category_product
)
SELECT
  category,
  product_id,
  product_name,
  order_count,
  total_quantity,
  total_sales,
  category_sales,
  ROUND(
    SAFE_DIVIDE(total_sales, category_sales) * 100,
    2
  ) AS sales_share_pct,
  category_rank
FROM category_sales_rank
ORDER BY category ASC, category_rank ASC, product_id ASC;









