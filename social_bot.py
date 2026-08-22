import json
import os
from datetime import datetime, timezone

import requests

GRAPH_VERSION = "v26.0"

ACCESS_TOKEN = os.environ["META_ACCESS_TOKEN"]
INSTAGRAM_ID = os.environ["INSTAGRAM_ID"]
FACEBOOK_PAGE_ID = os.environ["FACEBOOK_PAGE_ID"]


def post_to_instagram(caption, image_url):
    create_url = (
        f"https://graph.facebook.com/{GRAPH_VERSION}/"
        f"{INSTAGRAM_ID}/media"
    )

    create_response = requests.post(
        create_url,
        data={
            "image_url": image_url,
            "caption": caption,
            "access_token": ACCESS_TOKEN,
        },
        timeout=30,
    )
    if not create_response.ok:
        print("Meta error:", create_response.text)
        create_response.raise_for_status()

    creation_id = create_response.json()["id"]

    publish_url = (
        f"https://graph.facebook.com/{GRAPH_VERSION}/"
        f"{INSTAGRAM_ID}/media_publish"
    )

    publish_response = requests.post(
        publish_url,
        data={
            "creation_id": creation_id,
            "access_token": ACCESS_TOKEN,
        },
        timeout=30,
    )
    publish_response.raise_for_status()

    return publish_response.json()


def post_to_facebook(caption, image_url):
    url = (
        f"https://graph.facebook.com/{GRAPH_VERSION}/"
        f"{FACEBOOK_PAGE_ID}/photos"
    )

    response = requests.post(
        url,
        data={
            "url": image_url,
            "caption": caption,
            "access_token": ACCESS_TOKEN,
        },
        timeout=30,
    )
    response.raise_for_status()

    return response.json()


with open("posts.json", "r", encoding="utf-8") as f:
    posts = json.load(f)

now = datetime.now(timezone.utc)
changed = False

for post in posts:
    if post.get("posted"):
        continue

    scheduled = datetime.fromisoformat(post["scheduled_at"])

    if scheduled.astimezone(timezone.utc) > now:
        continue

    caption = post["caption"]
    image_url = post["image_url"]

    print(f"Publishing {post['id']}...")

    if "instagram" in post["platforms"]:
        result = post_to_instagram(caption, image_url)
        print("Instagram:", result)

    if "facebook" in post["platforms"]:
        result = post_to_facebook(caption, image_url)
        print("Facebook:", result)

    post["posted"] = True
    post["posted_at"] = datetime.now(timezone.utc).isoformat()
    changed = True


if changed:
    with open("posts.json", "w", encoding="utf-8") as f:
        json.dump(posts, f, indent=2)
        f.write("\n")
else:
    print("No posts due.")
