import json
import os
from datetime import datetime, timezone

import requests

GRAPH_VERSION = "v26.0"

ACCESS_TOKEN = os.environ["META_ACCESS_TOKEN"]
INSTAGRAM_ID = os.environ["INSTAGRAM_ID"]
FACEBOOK_PAGE_ID = os.environ["FACEBOOK_PAGE_ID"]


def post_to_instagram(caption, image_url):
    import time

    # Step 1: Create the media container
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
        print("Meta create error:", create_response.text)
        create_response.raise_for_status()

    creation_id = create_response.json()["id"]
    print("Created Instagram container:", creation_id)

    # Step 2: Wait for Instagram to finish processing it
    status_url = (
        f"https://graph.facebook.com/{GRAPH_VERSION}/"
        f"{creation_id}"
    )

    for attempt in range(12):
        status_response = requests.get(
            status_url,
            params={
                "fields": "status_code",
                "access_token": ACCESS_TOKEN,
            },
            timeout=30,
        )

        if not status_response.ok:
            print("Meta status error:", status_response.text)
            status_response.raise_for_status()

        status_code = status_response.json().get("status_code")
        print(f"Container status: {status_code}")

        if status_code == "FINISHED":
            break

        if status_code == "ERROR":
            raise RuntimeError(
                f"Instagram container processing failed: "
                f"{status_response.text}"
            )

        time.sleep(5)

    else:
        raise RuntimeError(
            "Instagram container did not finish processing within 60 seconds."
        )

    # Step 3: Publish the finished container
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

    if not publish_response.ok:
        print("Meta publish error:", publish_response.text)
        publish_response.raise_for_status()

    print("Instagram post published:", publish_response.json())

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
