
-- risingwave から ターゲットデータソースに publish する
CREATE SINK target_count_postgres_sink FROM target_count WITH (
    connector = 'jdbc',
    jdbc.url = 'jdbc:postgresql://postgres:5432/dev?user=admin&password=password',
    table.name = 'target_count',
    type = 'upsert', -- UPDATE、INSERT、DELETE
    primary_key = 'target_id'
);


registered_model_aliases




CREATE SOURCE pg_dev WITH (
    connector = 'postgres-cdc',
    hostname = 'postgres',
    port = '5432',
    username = 'admin',
    password = 'password',
    database.name = 'dev',
    auto.schema.change = 'false' -- true は有料版で使える
);




DESCRIBE pg_dev;

postgres で primarykey の確認をする
/d+ table_name


-- cdc では primarykey が必要
-- varchar は未サポート text にする
MATERIALIZED VIEW 

CREATE TABLE registered_model_aliases(alias text, version integer, name text, PRIMARY KEY(name, alias))
  INCLUDE timestamp AS modified_at
  INCLUDE DATABASE_NAME as db_name
  INCLUDE SCHEMA_NAME as schema_name
  INCLUDE table_name as table_name
  FROM pg_mydb TABLE 'mlflow_catalog.registered_model_aliases';


CREATE MATERIALIZED VIEW registered_model_aliases(alias, version, name)
  INCLUDE timestamp AS modified_at
  INCLUDE DATABASE_NAME as db_name
  INCLUDE SCHEMA_NAME as schema_name
  INCLUDE table_name as table_name
  FROM pg_mydb TABLE 'mlflow_catalog.registered_model_aliases';


CREATE SUBSCRIPTION sub_registered_model_aliases FROM registered_model_aliases WITH ();


declare cur subscription cursor for sub_registered_model_aliases;
fetch next from cur;



 alias | version |        name        |        table_name        |  schema_name   | db_name |        modified_at        |      op      | rw_timestamp
-------+---------+--------------------+--------------------------+----------------+---------+---------------------------+--------------+---------------
 dev   |       1 | your_model_pytorch | registered_model_aliases | mlflow_catalog | dev     | 1970-01-01 00:00:00+00:00 | UpdateDelete | 1740214437528


 alias | version |        name        |        table_name        |  schema_name   | db_name |          modified_at          |      op      | rw_timestamp
-------+---------+--------------------+--------------------------+----------------+---------+-------------------------------+--------------+---------------
 dev   |       2 | your_model_pytorch | registered_model_aliases | mlflow_catalog | dev     | 2025-02-22 08:53:57.825+00:00 | UpdateInsert | 1740214437528



