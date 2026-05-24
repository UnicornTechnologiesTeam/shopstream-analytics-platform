import json
import gzip
import uuid
import random
import argparse
import os
from datetime import datetime, timedelta, date

BUCKET      = "shopstream-raw-data-dg"
TOTAL_DAILY = 500_000

PRODUCTS = [
    {"product_id": f"P{i:04d}",
     "category": random.choice(["electronics", "clothing", "books", "home", "sports", "beauty"]),
     "price": round(random.uniform(5.99, 899.99), 2)}
    for i in range(1, 1001)
]

PAGE_TYPES    = ["home", "category", "product", "cart", "checkout", "search", "blog"]
DEVICE_TYPES  = ["mobile", "desktop", "tablet"]
COUNTRIES     = ["US", "CO", "BR", "MX", "AR", "ES", "DE", "FR", "CA", "JP"]
REFERRERS     = ["https://google.com", "https://bing.com", "https://facebook.com",
                 "https://instagram.com", "https://twitter.com", "", ""]
ELEMENT_TYPES = ["button", "link", "image", "banner", "product_card"]
SEARCH_QUERIES = ["laptop", "headphones", "shoes", "t-shirt", "book", "phone case",
                  "watch", "backpack", "camera", "keyboard", "mouse", "monitor"]

EVENT_TYPES   = ["page_view", "click", "search", "product_view", "cart_event"]
EVENT_WEIGHTS = [0.40,        0.25,   0.10,    0.15,            0.10]

USER_POOL = [str(uuid.uuid4())[:8] for _ in range(5000)]


def random_ts(day):
    hour   = random.choices(range(24), weights=[1,1,1,1,1,2,3,4,5,6,7,8,9,10,10,10,9,9,8,7,6,5,4,2])[0]
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    return datetime(day.year, day.month, day.day, hour, minute, second).isoformat()


def gen_page_view(user_id, session_id, day):
    page = random.choice(PAGE_TYPES)
    return {"event_type": "page_view", "user_id": user_id, "session_id": session_id,
            "page_url": f"/{page}/{random.choice(['best-sellers','new-arrivals','sale',page])}",
            "page_type": page, "timestamp": random_ts(day),
            "time_on_page_seconds": int(random.expovariate(1/90)),
            "referrer": random.choice(REFERRERS),
            "device_type": random.choice(DEVICE_TYPES),
            "country": random.choices(COUNTRIES, weights=[30,15,10,10,8,6,5,5,6,5])[0]}

def gen_click(user_id, session_id, day):
    page = random.choice(PAGE_TYPES)
    return {"event_type": "click", "user_id": user_id, "session_id": session_id,
            "element_id": str(uuid.uuid4())[:8], "element_type": random.choice(ELEMENT_TYPES),
            "page_url": f"/{page}/detail", "timestamp": random_ts(day),
            "x_position": random.randint(0, 1920), "y_position": random.randint(0, 1080)}

def gen_search(user_id, session_id, day):
    return {"event_type": "search", "user_id": user_id, "session_id": session_id,
            "query": random.choice(SEARCH_QUERIES),
            "results_count": max(0, int(abs(random.gauss(50, 40)))),
            "timestamp": random_ts(day)}

def gen_product_view(user_id, session_id, day):
    prod = random.choice(PRODUCTS)
    return {"event_type": "product_view", "user_id": user_id, "session_id": session_id,
            "product_id": prod["product_id"], "category": prod["category"],
            "price": prod["price"], "timestamp": random_ts(day),
            "time_on_page_seconds": int(random.expovariate(1/45))}

def gen_cart_event(user_id, session_id, day):
    prod = random.choice(PRODUCTS)
    return {"event_type": "cart_event", "user_id": user_id, "session_id": session_id,
            "product_id": prod["product_id"],
            "action": random.choices(["add", "remove"], weights=[75, 25])[0],
            "timestamp": random_ts(day)}

GENERATORS = {
    "page_view": gen_page_view, "click": gen_click, "search": gen_search,
    "product_view": gen_product_view, "cart_event": gen_cart_event,
}


def generate_day(target_date, total=TOTAL_DAILY):
    events = []
    while len(events) < total:
        user_id    = random.choice(USER_POOL)
        session_id = str(uuid.uuid4())[:12]
        n = max(1, int(random.expovariate(1/5)))
        for _ in range(n):
            etype = random.choices(EVENT_TYPES, weights=EVENT_WEIGHTS)[0]
            events.append(GENERATORS[etype](user_id, session_id, target_date))
            if len(events) >= total:
                break
    return events[:total]


def upload_s3(events, target_date, bucket):
    import boto3
    s3  = boto3.client("s3")
    y, m, d = target_date.year, target_date.month, target_date.day
    key = f"raw/year={y}/month={m:02d}/day={d:02d}/events.json.gz"
    payload = "\n".join(json.dumps(e) for e in events).encode("utf-8")
    s3.put_object(Bucket=bucket, Key=key, Body=gzip.compress(payload),
                  ContentType="application/gzip")
    return f"s3://{bucket}/{key}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date",   default=None)
    parser.add_argument("--days",   type=int, default=1)
    parser.add_argument("--total",  type=int, default=TOTAL_DAILY)
    parser.add_argument("--local",  action="store_true")
    parser.add_argument("--bucket", default=BUCKET)
    args = parser.parse_args()

    start = date.fromisoformat(args.date) if args.date else date.today()
    dates = [start - timedelta(days=i) for i in range(args.days - 1, -1, -1)]

    for d in dates:
        print(f"[{d}] Generando {args.total:,} eventos...", end=" ", flush=True)
        events = generate_day(d, args.total)
        if args.local:
            path = f"./data/year={d.year}/month={d.month:02d}/day={d.day:02d}"
            os.makedirs(path, exist_ok=True)
            with gzip.open(f"{path}/events.json.gz", "wb") as f:
                f.write("\n".join(json.dumps(e) for e in events).encode())
            print(f"guardado en {path}/events.json.gz")
        else:
            s3_path = upload_s3(events, d, args.bucket)
            print(f"subido a {s3_path}")

    print("Listo!")

if __name__ == "__main__":
    main()
