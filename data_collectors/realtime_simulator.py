import os
import time
import random
from datetime import datetime


class RealtimeSimulator:

    def __init__(self):
        self.templates = [
            "URGENT: {disaster} in {location}. {count} {victims} need {need}.",
            "Emergency {need} required in {location}. {disaster} has affected {count} {victims}.",
            "{count} {victims} stranded in {location} due to {disaster}. Need {need} urgently.",
            "Breaking: {disaster} hits {location}. {count} {victims} require immediate {need}.",
            "SOS: {disaster} in {location} area. Approximately {count} {victims} desperately need {need}.",
            "{location} crisis: {disaster} leaves {count} {victims} without {need}. Help needed now!",
            "Disaster alert - {disaster} in {location}. {count} {victims} require urgent {need} assistance.",
            "Critical situation: {count} {victims} affected by {disaster} in {location}. {need} needed ASAP.",
        ]
        self.disasters = [
            "Flood", "Earthquake", "Building collapse", "Fire", "Landslide",
            "Cyclone", "Heavy rain", "Gas leak", "Bridge collapse"
        ]
        self.locations = [
            "Andheri East", "Bandra West", "Kurla Station", "Dadar", "Thane",
            "Borivali", "Powai", "Worli", "Colaba", "Malad"
        ]
        self.needs = [
            "food and water", "medical supplies", "shelter", "rescue",
            "blankets", "first aid", "evacuation", "ambulance services",
            "clean water", "emergency medicine"
        ]
        self.victims = [
            "families", "people", "individuals", "residents", "citizens",
            "children", "elderly persons", "workers", "commuters"
        ]

    def generate_post(self) -> str:
        return random.choice(self.templates).format(
            disaster=random.choice(self.disasters),
            location=random.choice(self.locations),
            count=random.choice([15, 20, 30, 40, 50, 75, 100, 150, 200]),
            victims=random.choice(self.victims),
            need=random.choice(self.needs)
        )

    def generate_batch(self, count: int = 20) -> list:
        return [self.generate_post() for _ in range(count)]

    def save_batch_to_file(self, count: int = 20,
                           filename: str = 'data/sample_posts.txt') -> list:
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        posts = self.generate_batch(count)
        with open(filename, 'w', encoding='utf-8') as f:
            for post in posts:
                f.write(post + '\n')
        print(f"✅ Generated {len(posts)} posts → {filename}")
        return posts

    def stream_to_file(self, duration_seconds: int = 30,
                       posts_per_minute: int = 4,
                       filename: str = 'data/sample_posts.txt') -> list:
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        interval = 60 / posts_per_minute
        end_time = time.time() + duration_seconds
        posts, count = [], 0

        print(f"🔴 LIVE: Streaming for {duration_seconds}s at {posts_per_minute} posts/min\n")

        while time.time() < end_time:
            post = self.generate_post()
            posts.append(post)
            count += 1
            ts = datetime.now().strftime("%H:%M:%S")
            print(f"[{ts}] 📥 #{count}: {post[:70]}...")
            time.sleep(interval)

        with open(filename, 'w', encoding='utf-8') as f:
            for post in posts:
                f.write(post + '\n')

        print(f"\n✅ Captured {len(posts)} posts → {filename}")
        print("▶️  Run: python main.py")
        return posts


if __name__ == "__main__":
    simulator = RealtimeSimulator()
    simulator.save_batch_to_file(count=20)
    # For live streaming demo use:
    # simulator.stream_to_file(duration_seconds=30, posts_per_minute=4)