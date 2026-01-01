import pymongo
import os
from datetime import datetime, time
from dotenv import load_dotenv

load_dotenv()


class MongoConn:
    db_conn = os.getenv("MONGO_CONN")
    db = os.getenv("MONGO_DB")

    def __init__(self, collection):
        self.myclient = pymongo.MongoClient(f"mongodb://{self.db_conn}")
        self.mydb = self.myclient[self.db]
        self.collection = self.mydb[collection]

    def save(self, data: dict):
        result = self.collection.insert_one(data)

    def close(self):
        self.myclient.close()

    def read_all(self, filter: dict) -> list:
        return self.collection.find(filter)

    def read_by_datetime(self, filtered_date: datetime, chat_id) -> list:
        start = datetime.combine(filtered_date.date(), time.min)
        end = datetime.combine(filtered_date.date(), time.max)
        print(f"Searching between {start} and {end} in group {chat_id}")
        return self.read_by_daterange(start_day=start, end_day=end, chat_id=chat_id)

    def read_by_daterange(
        self, start_day: datetime, end_day: datetime, chat_id
    ) -> list:
        return self.read_all(
            {"message_time": {"$lte": end_day, "$gte": start_day}, "chat_id": chat_id}
        )

    def get_msg_by_hour(self, day: datetime, chat_id) -> list:
        start = datetime.combine(day.date(), time.min)
        end = datetime.combine(day.date(), time.max)

        return self.collection.aggregate(
            [
                {
                    "$match": {
                        "message_time": {"$lte": end, "$gte": start},
                        "chat_id": chat_id,
                    }
                },
                {"$project": {"hour": {"$hour": "$message_time"}}},
                {"$group": {"_id": "$hour", "count": {"$sum": 1}}},
                {"$sort": {"_id": 1}},
            ]
        )

    def get_msg_by_user(self, day: datetime, chat_id) -> list:
        start = datetime.combine(day.date(), time.min)
        end = datetime.combine(day.date(), time.max)

        return self.collection.aggregate(
            [
                {
                    "$match": {
                        "message_time": {"$lte": end, "$gte": start},
                        "chat_id": chat_id,
                    }
                },
                {
                    "$group": {
                        "_id": "$user_id",
                        "username": {"$first": "$username"},
                        "count": {"$sum": 1},
                    }
                },
                {"$sort": {"count": -1}},
            ]
        )

    def get_message_by_hour_and_person(self, day: datetime, user_id, chat_id) -> list:
        start = datetime.combine(day.date(), time.min)
        end = datetime.combine(day.date(), time.max)

        return self.collection.aggregate(
            [
                {
                    "$match": {
                        "message_time": {"$lte": end, "$gte": start},
                        "chat_id": chat_id,
                        "user_id": user_id,
                    }
                },
                {"$project": {"hour": {"$hour": "$message_time"}}},
                {"$group": {"_id": "$hour", "count": {"$sum": 1}}},
                {"$sort": {"_id": 1}},
            ]
        )
