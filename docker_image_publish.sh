# This is a helper script to build and publish docker images
# used in the repository to docker hub
# echo "=> Logging into docker hub"

echo "=> Building and pushing docker images"
echo "=> Reddit Producer"
cd reddit_producer
docker build -t local/reddit_producer:latest .
# docker push local/reddit_producer:latest

echo "=> Spark Stream Processor"
cd ../spark
docker build -t local/spark_stream_processor:latest .
# docker push local/spark_stream_processor:latest

echo "=> Cassandra"
cd ../cassandra
docker build -t local/cassandra:latest .
# docker push local/cassandra:latest

echo "=> Grafana"
cd ../grafana
docker build -t local/grafana:latest .
# docker push local/grafana:latest