
-- STEP 13｜集合演算（UNION ALL / UNION DISTINCT / INTERSECT DISTINCT / EXCEPT DISTINCT）
/*
今回からは、複数のSELECT文の結果を縦方向に組み合わせたり共通するデータや差分を抽出したりする集合演算に進みます。
データエンジニアの実務では、月別データの統合、異なるシステムのデータ結合、マスタ間の差分検出などで使用します。
集合演算には、主に次の4種類があります。
  演算子               動作
  UNION ALL           両方の結果をすべて結合し、重複行を残す
  UNION DISTINCT      両方の結果を結合し、重複行を除去（重複行が1行にまとめられて片方だけ残る）
  INTERSECT DISTINCT  両方の結果に共通する行だけ取得
  EXCEPT DISTINCT     左側の結果にだけ存在する行を取得（重複除去を伴う）

UNION ALL と UNION DISTINCT
  table_A       table_B
  customer_id   customer_id
  1             2
  2             3
  3             4

UNION ALL：1, 2, 3, 2, 3, 4
UNION DISTINCT：1, 2, 3, 4

なお UNION DISTINCT は特定の1列の値だけではなく、「行単位における列全体の値」を比較して重複を判定します。
例えば次の2行は customer_id が同じでも、order_id が異なるため別の行（!=重複）として扱われます。
  order_id  customer_id
  1001      1
  1003      1

BigQueryで書くと次のような構文で、基本的には各SELECTの列数が一致し、対応する列のデータ型に互換性が必要です。
通常の集合演算では、列の対応は位置で決まります。
*/
SELECT
  customer_id
FROM `resonant-tract-508812-p9.sql_training.orders`
UNION ALL -- UNION DISTINCT
SELECT
  customer_id
FROM `resonant-tract-508812-p9.sql_training.customers`
ORDER BY 1 ASC;

/*
STEP 13-1｜月別注文データの統合

orders を使い、2026年1月と2月のcompleted注文を、それぞれ別のSELECTで抽出して UNION ALL で統合してください。
  order_id、customer_id、order_date、amount、sales_month：注文月（月初日の日付）
最終結果は order_date ASC, order_id ASC で並べる。期待される行数は 7行（1月3行＋2月4行） です。今回はCTEを使用してもしなくても構いません。
*/
SELECT
  order_id, customer_id, order_date, amount, DATE_TRUNC(order_date, MONTH) AS sales_month
FROM `resonant-tract-508812-p9.sql_training.orders`
WHERE status = 'completed'
  AND (order_date >= DATE '2026-01-01' AND order_date < DATE '2026-02-01')
UNION ALL
SELECT
  order_id, customer_id, order_date, amount, DATE_TRUNC(order_date, MONTH) AS sales_month
FROM `resonant-tract-508812-p9.sql_training.orders`
WHERE status = 'completed'
  AND (order_date >= DATE '2026-02-01' AND order_date < DATE '2026-03-01')
ORDER BY order_date ASC, order_id ASC;
/*追加の確認問題
今回の注文データでは、UNION ALL を UNION DISTINCT に変更しても実行結果は変わらないはずです。
なぜ今回のデータでは結果が変わらないのか、また、どのような場合に結果が変わるのかを説明してください。
今回の取得データは「行単位における列全体の値」が全て重複している行はないため、 UNION DISTINCT に変更しても結果が変わりません。*/

/*
STEP 13-2｜UNION ALL × 集計 × 重複の扱い
次は、UNION ALL で統合したデータを集計します。
今回は、同じ注文が複数のSELECTから取得された場合、集計結果にどのような影響が出るかを確認する問題です。

orders を使い、A[2026年1月～2月のcompleted注文]とB[2026年2月～3月のcompleted注文]を抽出して統合、つまり2月の注文はAとB両方に含まれます。
  sales_month：注文月（月初日の日付）、order_count：注文件数、total_amount：注文金額の合計

AとBはそれぞれ独立したSELECT文で作成。まず UNION ALL で統合。統合後 order_id を基準に重複注文を除去。重複除去後のデータを sales_month ごとに集計。
CTEを使用する。最終結果は sales_month ASC で並べる。重複除去には ROW_NUMBER() と QUALIFY またはCTEを組み合わせる方法が使えます。
*/
WITH merge_order AS (
  SELECT
    DATE_TRUNC(order_date, MONTH) AS sales_month, order_id, amount
  FROM `resonant-tract-508812-p9.sql_training.orders`
  WHERE status = 'completed'
    AND (order_date >= DATE '2026-01-01' AND order_date < DATE '2026-03-01')
  UNION ALL
  SELECT
    DATE_TRUNC(order_date, MONTH) AS sales_month, order_id, amount
  FROM `resonant-tract-508812-p9.sql_training.orders`
  WHERE status = 'completed'
    AND (order_date >= DATE '2026-02-01' AND order_date < DATE '2026-04-01')
)
SELECT
  sales_month,
  COUNT(order_id) AS order_count,
  SUM(amount) AS total_amount
FROM (
  SELECT
    sales_month,
    order_id,
    amount,
    ROW_NUMBER() OVER (
      PARTITION BY order_id
      ORDER BY sales_month ASC
    ) AS rm
  FROM merge_order
  QUALIFY rm = 1
)
GROUP BY sales_month
ORDER BY sales_month ASC;
/*追加の確認問題
今回 UNION ALL で統合した結果を重複除去せず、そのまま月別集計すると、2月の order_count と total_amount はそれぞれいくつになるでしょうか？
重複除去後の2月はorder_countが4でtotal_amountが22500なので、重複除去前の2月はこれらが倍のorder_countが8でtotal_amountが45000です。*/

/*
STEP 13-3｜UNION DISTINCT × 複数データソース
次は、UNION DISTINCT を使って複数のデータソースに登場する顧客IDを統合します。
UNION DISTINCT は、それぞれのSELECT内の重複も含めて除去するため、各SELECTに個別の DISTINCT を付ける必要はありません。

orders と customer_ranks と customers を使い、completed注文のある顧客とランク情報が登録されている顧客を統合し、対象顧客の一覧を取得してください。
  customer_id、customer_name：マスタに存在しない場合はNULL、prefecture：マスタに存在しない場合はNULL
orders から status = 'completed' の顧客IDを取得。customer_ranks から顧客IDを取得。2つの結果を UNION DISTINCT で統合。
統合後の顧客IDを customers と結合して顧客名と都道府県を取得。customers に存在しない顧客IDも結果に残す。CTEを使用。最終結果は customer_id昇順。
期待される結果は 6行 です。今回、customer_ranks には customers に存在しない顧客IDも登録されています。JOINの種類に注意してください。
*/
WITH merge_cus AS (
  SELECT
    customer_id
  FROM `resonant-tract-508812-p9.sql_training.orders`
  WHERE status = 'completed'
  UNION DISTINCT
  SELECT
  customer_id
  FROM `resonant-tract-508812-p9.sql_training.customer_ranks`
)
SELECT
  m.customer_id,
  c.customer_name,
  c.prefecture
FROM merge_cus AS m
LEFT OUTER JOIN `resonant-tract-508812-p9.sql_training.customers` AS c
  ON m.customer_id = c.customer_id
ORDER BY m.customer_id ASC;
/*追加の確認問題
今回の課題で UNION DISTINCT の代わりに UNION ALL を使用し、そのまま customers と結合した場合は結果にどのような違いが生じるでしょうか？
orders と customer_ranks 両方の customer_id が重複を含めすべて取得され、customers との結合により同じ顧客IDと顧客名と都道府県の行が複数生じます。*/

/*
STEP 13-4｜INTERSECT DISTINCT：共通データの抽出
INTERSECT DISTINCT は、2つのSELECT結果の両方に存在する行だけを取得する集合演算です。

例えば次の2つのデータがあり INTERSECT DISTINCT した場合、両方に共通する3と4だけが残ります。
  table_A       table_B
  customer_id   customer_id
  1             3
  2             4
  3             5
  4

BigQueryでは次の構文です。
  SELECT
    customer_id
  FROM table_a
  INTERSECT DISTINCT
  SELECT
    customer_id
  FROM table_b;

orders と customer_ranks と customers を使い、completed注文がありかつランク情報も登録されている顧客を抽出してください。
  customer_id、customer_name、prefecture、customer_rank、completed_count：completed注文件数、total_amount：completed注文の売上合計
completed注文の件数と売上合計を顧客別に算出。CTEを使用。最終結果は total_amount DESC, customer_id ASC で並べる。
*/
WITH merge_cus AS (
  SELECT
    customer_id
  FROM `resonant-tract-508812-p9.sql_training.orders`
  WHERE status = 'completed'
  INTERSECT DISTINCT
  SELECT
    customer_id
  FROM `resonant-tract-508812-p9.sql_training.customer_ranks`
),
base AS (
  SELECT
    m.customer_id,
    c.customer_name,
    c.prefecture,
    r.customer_rank
  FROM merge_cus AS m
  INNER JOIN `resonant-tract-508812-p9.sql_training.customers` AS c
    ON m.customer_id = c.customer_id
  INNER JOIN `resonant-tract-508812-p9.sql_training.customer_ranks` AS r
    ON m.customer_id = r.customer_id
),
order_extract AS (
  SELECT
    customer_id,
    COUNT(order_id) AS completed_count,
    SUM(amount) AS total_amount
  FROM `resonant-tract-508812-p9.sql_training.orders`
  WHERE status = 'completed'
  GROUP BY customer_id
)
SELECT
  b.customer_id,
  b.customer_name,
  b.prefecture,
  b.customer_rank,
  o.completed_count,
  o.total_amount
FROM base AS b
INNER JOIN order_extract AS o
  ON b.customer_id = o.customer_id
ORDER BY o.total_amount DESC, b.customer_id ASC;
/*追加の確認問題
今回の INTERSECT DISTINCT で抽出できる顧客IDは、INNER JOIN を使っても取得できます。
では、INTERSECT DISTINCT と INNER JOIN では、重複行の扱いにどのような違いがあるでしょうか？
INTERSECT DISTINCT はそれぞれのSELECT内の重複も含めて除去しますが、INNER JOIN はそれぞれのSELECT内の重複を除去しません。*/

/*
STEP 13-5｜EXCEPT DISTINCT：差分データの抽出
EXCEPT DISTINCT は、左側のSELECTに存在し、右側のSELECTには存在しない行を取得する集合演算です。

例えば次の2つのデータがあり左側にAで右側にBで EXCEPT DISTINCT した場合、Aだけに存在する 1, 2 が残ります。
なお、INTERSECT DISTINCT と異なり、EXCEPT DISTINCT はSELECTの左右を入れ替えると結果が変わる点に注意してください。
  table_A       table_B
  customer_id   customer_id
  1             3
  2             4
  3             5
  4

BigQueryでは次のように記述します。
  SELECT
    customer_id
  FROM table_a
  EXCEPT DISTINCT
  SELECT
    customer_id
  FROM table_b;

customers と customer_ranks を使い、顧客マスタとランク登録テーブルの不一致（差分確認）を調べます。
  customer_id、customer_name：マスタに存在しない場合はNULL、prefecture：マスタに存在しない場合はNULL、difference_type：差分の種類
customersにありcustomer_ranksにない顧客IDとその逆パターンも抽出。difference_typeで前者は'rank_missing'を後者は'customer_missing'を付与。
2つの差分結果を UNION ALL で統合。customers と結合して顧客名と都道府県を取得する。マスタに存在しない顧客IDも結果に残す。
CTEを使用する。最終結果は difference_type ASC, customer_id ASC で並べる。
*/
WITH customers_only_id AS (
  SELECT
    customer_id
  FROM `resonant-tract-508812-p9.sql_training.customers`
  EXCEPT DISTINCT
  SELECT
    customer_id
  FROM `resonant-tract-508812-p9.sql_training.customer_ranks`
),
ranks_only_id AS (
  SELECT
    customer_id
  FROM `resonant-tract-508812-p9.sql_training.customer_ranks`
  EXCEPT DISTINCT
  SELECT
    customer_id
  FROM `resonant-tract-508812-p9.sql_training.customers`
),
union_bese AS (
  SELECT
    customer_id,
    'rank_missing' AS difference_type
  FROM customers_only_id
  UNION ALL
  SELECT
    customer_id,
    'customer_missing' AS difference_type
  FROM ranks_only_id
)
SELECT
  u.customer_id,
  c.customer_name,
  c.prefecture,
  u.difference_type
FROM union_bese AS u
LEFT OUTER JOIN `resonant-tract-508812-p9.sql_training.customers` AS c
  ON u.customer_id = c.customer_id
ORDER BY u.difference_type ASC, u.customer_id ASC;
/*追加の確認問題
今回の customers EXCEPT DISTINCT customer_ranks と、customer_ranks EXCEPT DISTINCT customers では、結果が異なります。
なぜ EXCEPT DISTINCT ではSELECTの左右を入れ替えると結果が変わるのでしょうか？

EXCEPT DISTINCT は、左側のSELECTに存在し、右側のSELECTには存在しない行を取得する集合演算「差集合」であるためです。
つまり、Oracle SQL（PL/SQL）における集合演算の MINUS と同じ動作をします。*/

/*
STEP 13-6｜集合演算の総合演習
今回は、これまでの JOIN、COUNTIF()、CASE、CTEも組み合わせた総合問題です。

customers と customer_ranks と orders を使い、顧客データの登録状況チェックです。
  customer_id、customer_name：マスタ未登録ならNULL、customer_rank：未登録ならNULL、completed_count：completed注文数
  registration_status：customersとcustomer_ranksの両方に存在 both_registered、customersのみ customer_only、customer_ranksのみ rank_only
completed注文数を COUNTIF() で集計して付与。注文がない顧客の completed_count は0とする。CTEを使用。最終結果は customer_id ASC で並べる。
*/
WITH both_registered AS (
  SELECT
    customer_id
  FROM `resonant-tract-508812-p9.sql_training.customers`
  INTERSECT DISTINCT
  SELECT
    customer_id
  FROM `resonant-tract-508812-p9.sql_training.customer_ranks`
),
customer_only AS (
  SELECT
    customer_id
  FROM `resonant-tract-508812-p9.sql_training.customers`
  EXCEPT DISTINCT
  SELECT
    customer_id
  FROM `resonant-tract-508812-p9.sql_training.customer_ranks`
),
rank_only AS (
  SELECT
    customer_id
  FROM `resonant-tract-508812-p9.sql_training.customer_ranks`
  EXCEPT DISTINCT
  SELECT
    customer_id
  FROM `resonant-tract-508812-p9.sql_training.customers`
),
union_base AS (
  SELECT
    customer_id,
    'both_registered' AS registration_status
  FROM both_registered
  UNION ALL
  SELECT
    customer_id,
    'customer_only' AS registration_status
  FROM customer_only
  UNION ALL
  SELECT
    customer_id,
    'rank_only' AS registration_status
  FROM rank_only
)
SELECT
  u.customer_id,
  c.customer_name,
  r.customer_rank,
  COUNTIF(o.status = 'completed') AS completed_count,
  u.registration_status
FROM union_base AS u
LEFT OUTER JOIN `resonant-tract-508812-p9.sql_training.customers` AS c
  ON u.customer_id = c.customer_id
LEFT OUTER JOIN `resonant-tract-508812-p9.sql_training.customer_ranks` AS r
  ON u.customer_id = r.customer_id
LEFT OUTER JOIN `resonant-tract-508812-p9.sql_training.orders` AS o
  ON u.customer_id = o.customer_id
GROUP BY u.customer_id, c.customer_name, r.customer_rank, u.registration_status
ORDER BY u.customer_id ASC;
/*追加の確認問題
今回の3つの集合、both_registered、customer_only、rank_only は互いに重複しません。
この3種類を UNION ALL で統合しても、同じ顧客IDが重複しないのはなぜでしょうか？

1. both_registered は 左側customersで右側customer_ranks の INTERSECT DISTINCT なので、両方の結果に共通する顧客IDだけ取得です。
2. customer_only は 左側customersで右側customer_ranks の EXCEPT DISTINCT なので、左側の結果にだけ存在する顧客IDだけ取得（重複除去を伴う）です。
3. rank_only は 左側customer_ranksで右側customers の EXCEPT DISTINCT なので、左側の結果にだけ存在する顧客IDだけ取得（重複除去を伴う）です。
これらの UNION ALL では、1[customersとcustomer_ranksの共通行] + 2[customersだけの行] + 3[customer_ranksだけの行] なので同じ顧客IDが重複しません。*/


-- STEP 14｜BigQueryのARRAY・STRUCT・UNNEST
/*
ここからは、これまで扱ってきた通常のリレーショナルテーブルとは少し異なる、BigQueryのネストされたデータ構造を学習します。
これらは、データエンジニアリングにおいて、JSON形式のデータやGA4のイベントデータなどを扱う際にも重要です。
*/

/*
STEP 14-1｜ARRAYの基本
これまでは、例えば次の顧客テーブルのように1つのセルに1つの値が入っていました。
  customer_id  customer_name  favorite_category
  1            Tanaka         electronics
  2            Sato           books

しかし、顧客が複数の商品カテゴリに興味を持っている場合はどうでしょうか。
ARRAY（アレイ：配列）を使うと1つの列に複数の値を保持でき、下記例の favorite_categories がARRAY型です。
  customer_id  customer_name  favorite_categories
  1            Tanaka         ['electronics', 'books']
  2            Sato           ['books', 'fashion', 'food']

1つのセルに複数の要素が格納されており、インデックス（要素の位置）は 0 から始まります。
  customer_id = 1
  offset0：electronics
  offset1：books

ARRAYの作成方法として、BigQueryでは角括弧 [] を使ってARRAYを作成でき、次のSQLは1行の中に2つのARRAY列を作成します。
  SELECT
    [10, 20, 30] AS array_col1,
    ['Tokyo', 'Kanagawa', 'Chiba'] AS array_col2;

また、ARRAY型を明示する場合は、次のように記述します。
次SQLの ARRAY<INT64> は、INT64型の配列を格納するARRAY（64ビット整数値を順番に格納できる可変長の配列データ構造）であることを意味します。
  SELECT
    ARRAY<INT64>[10, 20, 30] AS array_col1;

ARRAYの要素として使える主なデータ型の種類
  数値型
    ARRAY<INT64>：整数
    ARRAY<FLOAT64>：浮動小数点数
  文字列・バイナリ型
    ARRAY<STRING>：文字列
    ARRAY<BYTES>：バイト列
  日付・時間型
    ARRAY<DATE>：日付
    ARRAY<DATETIME>：日時
    ARRAY<TIME>：時刻
    ARRAY<TIMESTAMP>：タイムスタンプ
    ARRAY<INTERVAL>：時間間隔

ARRAYの要素を取得する場合、ARRAYには複数の要素が含まれるため、インデックスを指定して値を取得します。
  SELECT
    [10, 20, 30][OFFSET(0)] AS first_value,
    [10, 20, 30][OFFSET(1)] AS second_value;

  結果：
  first_value   second_value
  10             20

一方、ORDINAL（オーディナル）は、最初の要素が 1 から始まります。
             最初の要素	   2番目の要素
  OFFSET()	 OFFSET(0)	  OFFSET(1)
  ORDINAL()	 ORDINAL(1)   ORDINAL(2)

なお、存在しないインデックスを指定するとエラーになり、その場合は[SAFE_OFFSET()] や [SAFE_ORDINAL()] によって範囲外のインデックスに対してNULLを返せます。
下記例は存在しないインデックス(4)を指定してもエラーにならず NULL が返ります。
  SELECT
    ARRAY<STRING>['apple', 'banana', 'orange'][SAFE_OFFSET(4)] AS fruit;

ARRAY_LENGTH() は、ARRAYに含まれる「要素数」を取得する関数で下記例の結果は 3 となり、空のARRAYなら 0 でARRAY自体がNULLなら NULL を返します。
  SELECT
    ARRAY_LENGTH([10, 20, 30]) AS element_count;

演習問題として次のCTEを使用し、顧客別のARRAY情報を下記列によって取得、カテゴリが存在しない顧客も結果に残して customer_id ASC で並べる。
  customer_id、customer_name、category_count：好きなカテゴリの数、first_category：最初のカテゴリ、second_category：2番目のカテゴリで無ければ NULL
*/
WITH customer_preferences AS (
  SELECT
    1 AS customer_id,
    'Tanaka' AS customer_name,
    ARRAY<STRING>['electronics', 'books', 'food'] AS favorite_categories
  UNION ALL
  SELECT
    2,
    'Sato',
    ARRAY<STRING>['fashion', 'books']
  UNION ALL
  SELECT
    3,
    'Suzuki',
    ARRAY<STRING>['food']
  UNION ALL
  SELECT
    4,
    'Takahashi',
    ARRAY<STRING>[]
)
SELECT
  customer_id,
  customer_name,
  ARRAY_LENGTH(favorite_categories) AS category_count,
  favorite_categories[SAFE_OFFSET(0)] AS first_category,
  favorite_categories[SAFE_OFFSET(1)] AS second_category
FROM customer_preferences
ORDER BY customer_id ASC;
/*追加の確認問題
OFFSET() と SAFE_OFFSET() は、どちらもARRAYの要素を取得するために使用します。
今回のデータで favorite_categories[OFFSET(1)] を使用した場合、どの顧客で問題が発生し、なぜそのようになるでしょうか？
顧客ID[3, 4]はインデックス1の要素（配列内で2番目の要素）が存在しないためエラーとなります。*/

/*
STEP 14-2｜UNNEST：ARRAYを行に展開する
今回は、ARRAYに格納されているすべての要素を、個別の行として取り出す方法を学習します。

例えば、次のようなデータがあるとします。
  customer_id   favorite_categories
  1             ['electronics', 'books', 'food']
  2             ['fashion', 'books']

UNNEST() を使うと次のように展開でき、1つのARRAYに 3要素あれば3行 で 2要素あれば2行 に展開されます。
  customer_id = 1
  ['electronics', 'books', 'food']
    ↓
  'electronics'
  'books'
  'food'

UNNEST() の基本構文は次の通りです。
  SELECT
    customer_id,
    customer_name,
    category
  FROM customer_preferences
  CROSS JOIN UNNEST(favorite_categories) AS category;

UNNEST(favorite_categories) は配列の要素を行として展開し、AS category は展開した各要素の別名です。
CROSS JOIN では、元のテーブル customer_preferences の各行と、UNNEST で展開された要素の行を総当たりで結合します。
結果として、元のテーブルの他の列（IDやユーザー名など）の情報を保持したまま、配列の要素数分だけレコードが縦に増えます。
重要なのは空配列を CROSS JOIN UNNEST(…) AS … すると、その顧客の行は結果から消える点です。
これは「元のテーブルの行」と「展開後の要素」を掛け合わせるため、空配列（要素数 0）の場合、掛け算の結果が 0 になり、元のテーブルの行ごと結果から消えます。

空配列の顧客も保持したい場合は、LEFT OUTER JOIN UNNEST(…) AS … ON TRUE という書き方ができます。
空配列の行を消さずに要素を NULL として残したまま元のテーブルの行を保持するためのもので、次のような構文です。
なお、ON TRUE は通常のJOINのような「IDが一致したら」といった条件ではなく、「無条件で（常に正しいとして）結合する」という意味です。
これにより、実質的に CROSS JOIN と同じようにすべての要素を展開しつつ、LEFT JOIN の性質によって空配列の行も消さずに保持できます。
  SELECT
    customer_id,
    customer_name,
    category
  FROM customer_preferences
  LEFT OUTER JOIN UNNEST(favorite_categories) AS category
    ON TRUE;

また、ARRAYの要素の順序を取得したい場合には、WITH OFFSET を使用できます。
WITH OFFSET は、ARRAYをUNNESTする際に「その要素は元の配列におけるインデックスがいくつか」を 0 始まりの数値として一緒に取得できる機能です。
UNNESTの結果は元のARRAYの順序が保証されないため、元の配列でのインデックスを維持して集計や表示したい場合は WITH OFFSET を指定し ORDER BY で明示します。
  SELECT
    customer_id,
    customer_name,
    category,
    category_offset
  FROM customer_preferences
  CROSS JOIN UNNEST(favorite_categories) AS category
    WITH OFFSET AS category_offset
  ORDER BY customer_id ASC, category_offset ASC;

この LEFT OUTER JOIN UNNEST(…) AS … ON TRUE 版では、必ず AS … の直後に WITH OFFSET を記述して 次に ON TRUE を置き、最後にORDER BY で明示します。
  SELECT
    customer_id,
    customer_name,
    category,
    category_offset
  FROM customer_preferences
  LEFT OUTER JOIN UNNEST(favorite_categories) AS category
    WITH OFFSET AS category_offset
    ON TRUE
  ORDER BY customer_id ASC, category_offset ASC;


演習問題としてSTEP 14-1と同じCTEを使用し、顧客のカテゴリ情報を行に展開、次の列を取得してください。
  customer_id、customer_name、category、category_position：カテゴリの位置（1始まり）
空配列の顧客は結果に含めない。customer_id ASC, category_position ASC で並べる。
*/
WITH customer_preferences AS (
  SELECT
    1 AS customer_id,
    'Tanaka' AS customer_name,
    ARRAY<STRING>['electronics', 'books', 'food'] AS favorite_categories
  UNION ALL
  SELECT
    2,
    'Sato',
    ARRAY<STRING>['fashion', 'books']
  UNION ALL
  SELECT
    3,
    'Suzuki',
    ARRAY<STRING>['food']
  UNION ALL
  SELECT
    4,
    'Takahashi',
    ARRAY<STRING>[]
)
SELECT
  customer_id,
  customer_name,
  category,
  category_position + 1 AS category_position
FROM customer_preferences
CROSS JOIN UNNEST(favorite_categories) AS category
  WITH OFFSET AS category_position
ORDER BY customer_id ASC, category_position ASC;

-- 空配列の顧客も保持したい場合
WITH customer_preferences AS (
  SELECT
    1 AS customer_id,
    'Tanaka' AS customer_name,
    ARRAY<STRING>['electronics', 'books', 'food'] AS favorite_categories
  UNION ALL
  SELECT
    2,
    'Sato',
    ARRAY<STRING>['fashion', 'books']
  UNION ALL
  SELECT
    3,
    'Suzuki',
    ARRAY<STRING>['food']
  UNION ALL
  SELECT
    4,
    'Takahashi',
    ARRAY<STRING>[]
)
SELECT
  customer_id,
  customer_name,
  category,
  category_position + 1 AS category_position
FROM customer_preferences
LEFT OUTER JOIN UNNEST(favorite_categories) AS category
  WITH OFFSET AS category_position
  ON TRUE
ORDER BY customer_id ASC, category_position ASC;
/*追加の確認問題
今回のSQLで CROSS JOIN UNNEST() を LEFT OUTER JOIN UNNEST() ON TRUE に変更すると、顧客ID 4の行はどうなるでしょうか？
LEFT OUTER JOIN UNNEST(…) AS … WITH OFFSET AS … ON TRUE の場合、空配列である顧客ID4は要素をNULLとして残したまま元のテーブルの行が保持されます。*/


/*
STEP 14-3｜STRUCT：複数の項目を1つにまとめる
これまで学習したARRAYは、複数の値を1つの配列に格納する仕組みでした。
STRUCT（ストラクト：構造体）は、異なる意味や型を持つ複数の項目を、1つの構造体としてまとめる仕組みです。

例えば、次の顧客データがあるとします。
  customer_id  customer_name  prefecture  city
  1            Tanaka         Tokyo       Shibuya
  2            Sato           Kanagawa    Yokohama

例えば上記の prefecture と city を1つの住所情報としてまとめることができます。
  customer_id = 1
    address
    prefecture  Tokyo
    city        Shibuya

STRUCTの作成方法として構文は次の通りで、address は、prefecture と city という2つのフィールドを持つSTRUCT型になります。
  SELECT
    1 AS customer_id,
    STRUCT(
      'Tokyo' AS prefecture,
      'Shibuya' AS city
    ) AS address

また、型を明示して次のように記述することもできます。
  SELECT
    STRUCT<prefecture STRING, city STRING>(
      'Tokyo',
      'Shibuya'
    ) AS address

STRUCTは、ARRAYと異なりフィールドごとに異なるデータ型を持つこともでき、例えば STRING と INT64 を同じSTRUCT内に格納できます。
  SELECT
    STRUCT<area INT64, city STRING>(
      120,
      'Shibuya'
    ) AS address

STRUCTのフィールドを取得するには、ストラクト名.フィールド名 のドット記法でアクセスできます。
ARRAYのように [OFFSET(…)] や [SAFE_OFFSET(…)] で位置を指定するのではなく、フィールド名で値を取得することが基本です。
  SELECT
    address.area,
    address.city
  FROM customer_data;

演習問題として以下のCTEを使い、STRUCTのフィールド抽出と条件分岐として次の列を取得、全顧客を除外を出力して customer_id ASC で並べる。
  customer_id、customer_name、prefecture：STRUCT内の都道府県、city：STRUCT内の市区町村、postal_area_code：STRUCT内の郵便番号先頭3桁相当
  region_type：prefectureが Tokyo は tokyo_area、Kanagawa または Chiba は neighboring_area、それ以外は other_area
*/
WITH customer_data AS (
  SELECT
    1 AS customer_id,
    'Tanaka' AS customer_name,
    STRUCT<prefecture STRING, city STRING, postal_area_code INT64>(
      'Tokyo',
      'Shibuya',
      150
    ) AS address
  UNION ALL
  SELECT
    2,
    'Sato',
    STRUCT<prefecture STRING, city STRING, postal_area_code INT64>(
      'Kanagawa',
      'Yokohama',
      220
    )
  UNION ALL
  SELECT
    3,
    'Suzuki',
    STRUCT<prefecture STRING, city STRING, postal_area_code INT64>(
      'Tokyo',
      'Shinjuku',
      160
    )
  UNION ALL
  SELECT
    4,
    'Takahashi',
    STRUCT<prefecture STRING, city STRING, postal_area_code INT64>(
      'Chiba',
      'Chiba',
      260
    )
)
SELECT
  customer_id,
  customer_name,
  address.prefecture,
  address.city,
  address.postal_area_code,
  CASE
    WHEN address.prefecture = 'Tokyo' THEN 'tokyo_area'
    WHEN address.prefecture IN ('Kanagawa', 'Chiba') THEN 'neighboring_area'
    ELSE 'other_area'
  END AS region_type
FROM customer_data
ORDER BY customer_id ASC;
/*追加の確認問題
ARRAYとSTRUCTでは、内部の値へのアクセス方法にどのような違いがありますか？
ARRAY の場合、ARRAY[OFFSET(index)] や [ORDINAL(index)] もしくは [SAFE_OFFSET(index)] や [SAFE_ORDINAL(index)] で値を取得します。
STRUCT の場合、ストラクト名.フィールド名 のドット記法で値を取得します。*/

/*
STEP 14-4｜ARRAY<STRUCT>：構造体の配列
ARRAY<STRUCT<...>> は、複数のSTRUCT（構造体）をARRAY（配列）として保持するデータ型です。
これは、BigQueryでネストされたデータを扱う際に特に重要です。
  ARRAY：複数の要素を格納する
  STRUCT：複数のフィールドを1つにまとめる

例えば、1件の注文に複数の商品が含まれる場合を考えます。
通常のテーブルでは注文と商品を別々のテーブルで管理することがありますが、ARRAYとSTRUCTを組み合わせれば、1つの注文行の中に複数の商品情報を格納できます。
  order_id = 1001
  items（ARRAY）
    要素 0（STRUCT）
      product_name：Keyboard
      quantity：2
      unit_price：3000
    要素 1（STRUCT）
      product_name：Mouse
      quantity：1
      unit_price：1500

基本構文は次の通りで、この items は、3つのフィールドを持つSTRUCTのARRAYです。
  SELECT
    1001 AS order_id,
    [
      STRUCT('Keyboard' AS product_name, 2 AS quantity, 3000 AS unit_price),
      STRUCT('Mouse' AS product_name, 1 AS quantity, 1500 AS unit_price)
    ] AS items;

展開する場合、UNNEST(items) によって、ARRAY内のSTRUCTが1つずつ行として展開されます。
その後、item.product_name のようにドット記法でSTRUCT内のフィールドを取得できます。
つまり、UNNESTでARRAYを展開し、ドット記法でSTRUCTのフィールドを参照するという組み合わせです。
  SELECT
    order_id,
    item.product_name,
    item.quantity,
    item.unit_price
  FROM order_data
  CROSS JOIN UNNEST(items) AS item;

演習問題として次のCTEを使い、各注文に含まれる商品情報を展開して商品別の販売数量と売上合計を算出してください。
  product_name、total_quantity：商品ごとの販売数量合計、total_amount：商品ごとの売上合計、order_count：その商品が含まれる注文数
商品別に販売数量と売上金額を集計。売上金額は quantity * unit_price で計算。注文数は重複する注文IDを考慮して集計。売上合計の降順と商品名の昇順で並べる。
*/
WITH order_data AS (
  SELECT
    1001 AS order_id,
    1 AS customer_id,
    [
      STRUCT('Keyboard' AS product_name, 2 AS quantity, 3000 AS unit_price),
      STRUCT('Mouse' AS product_name, 1 AS quantity, 1500 AS unit_price)
    ] AS items
  UNION ALL
  SELECT
    1002,
    2,
    [
      STRUCT('Monitor' AS product_name, 1 AS quantity, 20000 AS unit_price),
      STRUCT('Cable' AS product_name, 3 AS quantity, 800 AS unit_price)
    ]
  UNION ALL
  SELECT
    1003,
    1,
    [
      STRUCT('Mouse' AS product_name, 2 AS quantity, 1500 AS unit_price)
    ]
  UNION ALL
  SELECT
    1004,
    3,
    ARRAY<STRUCT<product_name STRING, quantity INT64, unit_price INT64>>[]
)
SELECT
  items.product_name,
  SUM(items.quantity) AS total_quantity,
  SUM(items.quantity * items.unit_price) AS total_amount,
  COUNT(DISTINCT order_id) AS order_count
FROM order_data
CROSS JOIN UNNEST(items) AS items
GROUP BY items.product_name
ORDER BY total_amount DESC, items.product_name ASC;
/*追加の確認問題
今回のデータで、order_id = 1004 は空のARRAYを持っています。
商品別の売上集計において、CROSS JOIN UNNEST() の代わりに LEFT OUTER JOIN UNNEST() ON TRUE を使用した場合、どのような違いが生じるでしょうか？
LEFT OUTER JOIN UNNEST(…) AS … ON TURE の使用直後は、空配列である order_id = 1004 の行は保持され、展開したストラクト.フィールドの列はNULLです。
ただし GROUP BY … があるのでNULLの商品名を持つ行も1つのグループとして集計され、COUNT(DISTINCT order_id) は1004の注文IDが存在するため 1 となります。*/

/*
STEP 14-5｜UNNEST × JOIN：ネストデータとマスタの結合
次は、ネストされた商品明細を展開し、商品マスタと結合する演習です。
実務では、JSONやネストされたデータから商品IDを取り出し、別のマスタテーブルから商品名やカテゴリなどを付与することがありますが、その処理をBigQueryで実装します。

order_data：注文ID・顧客ID・商品明細のARRAY
  ↓
UNNEST(items)：商品明細を1商品1行に展開
  ↓
product_masterとのJOIN：商品名・カテゴリ・単価を取得
  ↓
商品カテゴリ別の集計：販売数量・売上・注文数を算出

次の2つのCTEを使用し、商品カテゴリ別の販売状況を集計してください。
  category、total_quantity：販売数量合計、total_amount：売上合計、order_count：注文数、unknown_product_count：商品マスタに存在しない明細の件数
UNNEST() で商品明細を展開。商品マスタと結合してカテゴリと単価を取得する。商品マスタに存在しない商品明細も保持。
カテゴリ別に集計。マスタ未登録の商品は category = 'unknown' と扱う。売上金額は quantity * unit_price とする。マスタ未登録商品の売上金額は0と扱う。
注文数は重複する注文IDを考慮する。unknown_product_count はマスタ未登録の明細行数を数える。最終結果は total_amount DESC, category ASC で並べる。
今回は、UNNEST()、LEFT OUTER JOIN、COUNTIF()、COUNT(DISTINCT ...)、IFNULL() など、これまでの学習内容を応用できます。
*/
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
  SELECT 101 AS product_id, 'Keyboard' AS product_name, 'electronics' AS category, 3000 AS unit_price
  UNION ALL
  SELECT 102, 'Mouse', 'electronics', 1500
  UNION ALL
  SELECT 103, 'Monitor', 'electronics', 20000
  UNION ALL
  SELECT 104, 'Cable', 'accessories', 800
  UNION ALL
  SELECT 105, 'Notebook', 'stationery', 500
),
base AS (
  SELECT
    o.order_id,
    i.product_id AS order_product_id,
    p.product_id AS master_product_id,
    i.quantity,
    p.category,
    p.unit_price
  FROM order_data AS o
  CROSS JOIN UNNEST(items) AS i
  LEFT OUTER JOIN product_master AS p
    ON i.product_id = p.product_id
)
SELECT
  IFNULL(category, 'unknown') AS category,
  SUM(quantity) AS total_quantity,
  IFNULL(SUM(quantity * unit_price), 0) AS total_amount,
  COUNT(DISTINCT order_id) AS order_count,
  COUNTIF(master_product_id IS NULL) AS unknown_product_count
FROM base
GROUP BY category
ORDER BY total_amount DESC, category ASC;
/*追加の確認問題
商品マスタとの結合を INNER JOIN に変更すると、今回の集計結果にどのような影響が出るでしょうか？
注文データと商品マスタでproduct_idが一致したものだけが集計され、例えば注文データに存在して商品マスタに存在しない product_id = 999 は除去されます。*/

/*
STEP 14-6｜ARRAY_AGG：複数行をARRAYに集約する
今回は、これまで学習した ARRAY（配列）STRUCT（構造体）UNNEST（展開）を踏まえて、ARRAY_AGG() による配列の生成を学習します。
これまで ARRAYに格納された商品明細を UNNEST() で複数行に展開しましたが、今回は逆に複数行の商品明細を注文単位にまとめてARRAYとして格納する処理を実装します。

ARRAY_AGG() は、複数行の値を1つのARRAYに集約する集約関数で、例えば次のような商品明細テーブルがあるとします。
  order_id  product_name
  1001      Keyboard
  1001      Mouse
  1002      Monitor
  1002      Cable

GROUP BY + ARRAY_AGG() を使うと、次のように注文単位にまとめられます。
ARRAY内の順序は、ARRAY_AGG内の ORDER BY で指定できます。
  1001 ｜ [Keyboard, Mouse]
  1002 ｜ [Cable, Monitor]

基本的な書き方は次のとおり GROUP BY を使う構文で、また ARRAY_AGG は他の集約関数（SUMやCOUNT等）と同時に使用できます。
  SELECT
    order_id,
    ARRAY_AGG(product_name ORDER BY product_name ASC) AS products
    COUNT(product_name)
  FROM order_items
  GROUP BY order_id;

今回の演習では、商品名だけでなく販売数量と単価もまとめてARRAYに格納するため、次のように ARRAY_AGG と STRUCT を組み合わせて書きます。
これにより各要素が3つのフィールドを持つSTRUCTで構成されたARRAY、つまり ARRAY<STRUCT<...>> 型のデータを作成できます。
  ARRAY_AGG(
    STRUCT(product_name, quantity, unit_price)
    ORDER BY product_name ASC
  )

演習問題として次のCTEを使い、商品明細を注文単位に集約（注文単位のARRAY構造を作成）し、以下の列を取得してください。
  order_id、customer_id、items：product_name と quantity と unit_price のフィールドを持つSTRUCTのARRAY
  total_quantity：注文内の販売数量合計、total_amount：注文内の売上合計
ARRAY内の商品は product_name ASC で並べる。注文単位で販売数量と売上金額を集計。売上金額は quantity * unit_price で計算。最終結果は order_id ASC に。
*/
WITH order_items AS (
  SELECT
    1001 AS order_id,
    1 AS customer_id,
    'Keyboard' AS product_name,
    2 AS quantity,
    3000 AS unit_price
  UNION ALL
  SELECT 1001, 1, 'Mouse', 1, 1500
  UNION ALL
  SELECT 1002, 2, 'Monitor', 1, 20000
  UNION ALL
  SELECT 1002, 2, 'Cable', 3, 800
  UNION ALL
  SELECT 1003, 1, 'Mouse', 2, 1500
  UNION ALL
  SELECT 1003, 1, 'Notebook', 1, 500
  UNION ALL
  SELECT 1004, 3, 'Keyboard', 1, 3000
)
SELECT
  order_id,
  customer_id,
  ARRAY_AGG(
    STRUCT(product_name, quantity, unit_price)
    ORDER BY product_name ASC
  ) AS items,
  SUM(quantity) AS total_quantity,
  SUM(quantity * unit_price) AS total_amount
FROM order_items
GROUP BY order_id, customer_id
ORDER BY order_id ASC;
/*追加の確認問題
ARRAY_AGG() の内部に指定する ORDER BY product_name ASC と、最終SELECTの末尾に指定する ORDER BY order_id ASC は、何の順序を制御しているのでしょうか？
ARRAY_AGG内の ORDER BY はARRAY内の順序を決めていて、最終SELECTの末尾に指定する ORDER BY は外側の行そのものにおける順序を決めています。*/

/*
STEP 14-7｜ARRAY・STRUCT・UNNEST・ARRAY_AGG 総合演習
これまで学習したネストデータの処理を組み合わせる演習です。
今回は、注文データに格納された商品明細を展開し、商品マスタと結合して集計した後、再びARRAYにまとめる処理に取り組みます。

今回の処理イメージ
  注文データ：ARRAY<STRUCT> 型の商品明細
    ↓
  UNNEST：商品明細を行に展開
    ↓
  商品マスタとJOIN：カテゴリと単価を取得
    ↓
  GROUP BY・ARRAY_AGG：注文単位に集計してARRAYを再生成
    ↓
  注文別の集計結果：商品情報のARRAY・数量・売上・未登録明細件数

次のCTEを使い、注文別の売上データを再構築する
  order_id、customer_id、items：product_id と product_name と quantity と unit_price のフィールドを持つSTRUCTのARRAY
  total_quantity：注文内の販売数量合計、total_amount：注文内の売上合計、unknown_product_count：商品マスタに登録されていない商品明細の件数
商品マスタに未登録の商品は product_name = 'unknown' で unit_price = 0 とする。商品マスタ未登録の商品明細も保持する。
注文単位の商品明細を再生成しARRAY内の要素は product_id ASC で並べる。最終結果は order_id ASC で並べる。
total_quantity は注文内の販売数量合計。total_amount は注文内の quantity * unit_price の合計で未登録商品の単価は0として計算。
unknown_product_count は商品マスタとの結合に一致しなかった商品明細の件数として販売数量ではなく該当する明細1件を1として数える。
*/
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
/*追加の確認問題
商品マスタとの結合を INNER JOIN に変更した場合、注文1004の items・total_quantity・total_amount・unknown_product_count はどう変化しますか？
商品マスタ未登録の商品ID999について、ARRAY内の4フィールドを持つSTRUCTのitemsが消え、total_quantityが1でunknown_product_countが0に変化します。*/










