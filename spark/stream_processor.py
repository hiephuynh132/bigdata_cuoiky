from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    udf, from_json, col, from_unixtime, current_timestamp
)

from pyspark.sql.types import (
    StringType, StructType, StructField, IntegerType, BooleanType, FloatType
)

import uuid
import requests


# ============================================================
# SENTIMENT API CALL
# ============================================================
def analyze_sentiment(text: str) -> float:
    try:
        url = "http://my-api:36000/predict"
        payload = {"text": text}
        response = requests.post(url, json=payload, timeout=2)
        return float(response.json().get('prediction', 0))
    except:
        return 0.0


# ============================================================
# UUID UDF
# ============================================================
uuid_udf = udf(lambda: str(uuid.uuid1()), StringType())


# ============================================================
# SCHEMA
# ============================================================
comment_schema = StructType([
    StructField("id", StringType(), True),
    StructField("name", StringType(), True),
    StructField("author", StringType(), True),
    StructField("body", StringType(), True),
    StructField("subreddit", StringType(), True),
    StructField("upvotes", IntegerType(), True),
    StructField("downvotes", IntegerType(), True),
    StructField("over_18", BooleanType(), True),
    StructField("timestamp", FloatType(), True),
    StructField("permalink", StringType(), True),
])


# ============================================================
# SPARK SESSION
# ============================================================
spark: SparkSession = SparkSession.builder \
    .appName("StreamProcessor") \
    .config('spark.cassandra.connection.host', 'cassandra') \
    .config('spark.cassandra.connection.port', '9042') \
    .config('spark.cassandra.output.consistency.level', 'ONE') \
    .getOrCreate()


# ============================================================
# READ KAFKA
# ============================================================
df = spark.readStream.format("kafka") \
    .option("kafka.bootstrap.servers", "kafkaservice:9092") \
    .option("subscribe", "redditcomments") \
    .load()


# ============================================================
# PARSE JSON
# ============================================================
parsed_df = df.withColumn(
    "comment_json",
    from_json(col("value").cast("string"), comment_schema)
)

output_df = parsed_df.select(
    "comment_json.*"
).withColumn(
    "uuid", uuid_udf()
).withColumn(
    "api_timestamp", from_unixtime(col("timestamp").cast(FloatType()))
).withColumn(
    "ingest_timestamp", current_timestamp()
).drop("timestamp")


# ============================================================
# FOREACHBATCH: SENTIMENT 0/1 cho từng comment
# ============================================================
def process_comments(batch_df, batch_id):

    rows = batch_df.collect()
    results = []

    for row in rows:
        sentiment = analyze_sentiment(row.body)
        r = row.asDict()
        r["sentiment_score"] = sentiment  # GIỮ NGUYÊN 0 hoặc 1
        results.append(r)

    if not results:
        return

    df_with_sentiment = spark.createDataFrame(results)

    df_with_sentiment.write \
        .format("org.apache.spark.sql.cassandra") \
        .options(table="comments", keyspace="reddit") \
        .mode("append") \
        .save()


# ============================================================
# START STREAM (CHỈ COMMENTS, KHÔNG SUMMARY)
# ============================================================
output_df.writeStream \
    .foreachBatch(process_comments) \
    .option("checkpointLocation", "/tmp/check_point_comments/") \
    .start()


spark.streams.awaitAnyTermination()
