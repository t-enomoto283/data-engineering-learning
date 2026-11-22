
# data-engineering-learning

SQL and Python learning projects for data engineering.

データエンジニアリングに必要なBigQuery SQL・Python・pandasの基礎知識と実装スキルを習得するための学習リポジトリです。

各演習で作成したSQL・Pythonコードを記録しています。

## 学習状況
| 学習分野 | 主な学習内容 |
|:---|:---|
| BigQuery SQL | データ抽出、結合、集計、CTE、ウィンドウ関数、ARRAY・STRUCT、データ操作 |
| Python・pandas | データ加工、品質検証、パイプライン設計、BigQuery連携、ETL/ELT | 

## BigQuery SQL
BigQueryを使用した、基本的なSQLから応用的なデータ操作。

### 主な学習内容
- 基本的なデータ抽出・条件指定・並び替え
- `GROUP BY`・集計関数
- `JOIN`・サブクエリ
- `CTE`（WITH句）
- 日付・時刻の操作
- ウィンドウ関数
- `UNION ALL`・`UNION DISTINCT`・`INTERSECT DISTINCT`・`EXCEPT DISTINCT`
- `ARRAY`・`STRUCT`・`UNNEST`
- DML系のデータ操作
- 複数のSQL技術を組み合わせた総合演習

演習コードは `bigquery/` ディレクトリに保存しています。

## Python・pandas
Python・pandasを使用したデータ処理から、BigQueryと連携するデータパイプラインの実装。

| 項目                   | 内容                         |
|:---------------------|:---------------------------|
| 1. Python基礎          | 関数、辞書、検証、例外処理、ファイル操作       |
| 2. pandas基礎          | DataFrame、CSV、抽出、結合、集計、欠損値 |
| 3. データ品質             | 重複、型、必須列、結合関係、品質レポート       |
| 4. パイプライン設計          | 関数化、ログ、設定管理、エラー処理、再実行      |
| 5. Python × BigQuery | 接続、SQL実行、データ取得、加工、書き込み     
| 6. ETL/ELT・自動化       | 増分処理、冪等性、スケジュール、監視         |
| 7. 総合演習              | データ取得から加工・保存・品質検証までの一連の実装  |

### STEP 7：総合演習
これまでの学習内容を組み合わせ、以下のデータパイプラインを実装しました。

| 演習 | 実装内容 |
|:---|:---|
| STEP 7-1 | CSVによるETL処理。データ品質検証、商品マスタ結合、売上集計、CSV出力 |
| STEP 7-2 | BigQueryによるELT処理。CSVロード、SQL集計、保存結果の検証 |
| STEP 7-3 | ウォーターマークによる増分処理。追加ロード、状態管理、再実行時のスキップ、JSONLログ |
| STEP 7-4 | 最終総合演習。データ品質検証、売上集計、BigQuery保存、結果検証、例外処理・JSONLログ |

演習コードは `python/` ディレクトリに保存しています。

## リポジトリ構成

```text
data-engineering-learning/
├── bigquery/
│   ├── SQL1-6.sql
│   ├── SQL7-8（JOINやサブクエリ）.sql
│   ├── SQL9-10（CTEや日付・時刻の扱い）.sql
│   ├── SQL11-12（ウィンドウ関数）.sql
│   ├── SQL13-14（UNION系やARRAY・STRUCT・UNNEST）.sql
│   ├── SQL15-16（DML系や総合演習）.sql
│   └── SQL17（日替わりSQL）.sql
├── python/
│   ├── 1_Python基礎の復習.py
│   ├── 2_pandas基礎.py
│   ├── 3_データ品質.py
│   ├── 4_パイプライン設計.py
│   ├── 5_Python×BigQuery.py
│   ├── 6_ETL／ELT・自動化.py
│   └── 7_総合演習.py
└── README.md
```

## 学習を通じて実装した主な処理
- SQLによるデータ抽出・結合・集計・分析
- CSVの読み込み・加工・集計
- 必須列・欠損値・重複・結合関係の検証
- PythonからBigQueryへのデータロードとSQL実行
- ETL・ELTパイプラインの構築
- ウォーターマークを使用した増分ロード
- 再実行時の処理制御
- 例外処理・JSONLログ出力・保存結果の検証

これらの演習を通じて、SQLによるデータ操作からPython・pandasを用いたデータ処理、BigQueryへの保存・品質検証までの基本的な実装を経験しました。
