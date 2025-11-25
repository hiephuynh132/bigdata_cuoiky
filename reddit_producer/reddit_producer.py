# TODO: add logs and error handling
from json import dumps
from kafka import KafkaProducer
import configparser
import praw
import threading
import csv
import os
import time

threads = []


class RedditProducer:

    def __init__(self, subreddit_list, cred_file="secrets/credentials.cfg", sample_file="data/sample_comments.csv"):
        self.subreddit_list = subreddit_list
        self.sample_file = sample_file
        self.sample_data = self.load_sample_data(sample_file)

        # Reddit client
        self.reddit = self.__get_reddit_client__(cred_file)

        # Kafka producer
        self.producer = KafkaProducer(
            bootstrap_servers=['kafkaservice:9092'],
            value_serializer=lambda x: dumps(x).encode('utf-8')
        )

    # ==========================
    #       LOAD SAMPLE
    # ==========================

    def load_sample_data(self, file_path):
        if not os.path.exists(file_path):
            print(f"[WARN] Sample CSV not found: {file_path}")
            return []

        result = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    row["upvotes"] = int(row.get("upvotes", 0))
                    row["timestamp"] = float(row.get("timestamp", time.time()))
                    result.append(row)
            print(
                f"[INFO] Loaded {len(result)} sample events from {file_path}")
        except Exception as e:
            print(f"[ERROR] Failed to read sample CSV: {e}")

        return result

    # ==========================
    #      SEND SAMPLE FIRST
    # ==========================

    def run_startup_sample(self):
        print("[INFO] Sending startup sample test data...")

        for row in self.sample_data:
            try:
                self.producer.send("redditcomments", value=row)
                print(f"[SAMPLE] Sent: {row}")
                time.sleep(0.2)
            except Exception as e:
                print("[ERROR] Kafka sample send failed:", e)

        print("[INFO] Finished sending sample test data.")
        time.sleep(1)

    # ==========================
    #      REDDIT STREAM
    # ==========================

    def __get_reddit_client__(self, cred_file):
        config = configparser.ConfigParser()
        config.read_file(open(cred_file))

        return praw.Reddit(
            user_agent=config.get("reddit", "user_agent"),
            client_id=config.get("reddit", "client_id"),
            client_secret=config.get("reddit", "client_secret")
        )

    def start_stream(self, subreddit_name):
        subreddit = self.reddit.subreddit(subreddit_name)
        for comment in subreddit.stream.comments(skip_existing=True):
            try:
                payload = {
                    "id": comment.id,
                    "name": comment.name,
                    "author": comment.author.name if comment.author else None,
                    "body": comment.body,
                    "subreddit": comment.subreddit.display_name,
                    "upvotes": comment.ups,
                    "timestamp": comment.created_utc,
                }
                self.producer.send("redditcomments", value=payload)
                print(f"[LIVE] {subreddit_name}: {payload}")

            except Exception as e:
                print("[ERROR] Reddit stream failed:", e)

    def start_streaming_threads(self):
        print("[INFO] Starting live Reddit streaming threads...")

        for subreddit_name in self.subreddit_list:
            thread = threading.Thread(
                target=self.start_stream, args=(subreddit_name,))
            thread.start()
            threads.append(thread)

        for t in threads:
            t.join()


# ==========================
#           MAIN
# ==========================
if __name__ == "__main__":
    reddit_producer = RedditProducer(
        subreddit_list=['AskReddit', 'funny', 'gaming'],
        sample_file="data/sample_comments.csv"
    )

    # 1) Chạy sample test khi khởi động
    reddit_producer.run_startup_sample()

    # 2) Sau đó chạy Reddit thật
    reddit_producer.start_streaming_threads()
