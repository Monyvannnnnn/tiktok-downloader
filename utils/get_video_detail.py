import httpx
import json
import re
from bs4 import BeautifulSoup as bs
from pathlib import Path
from tiktok_downloader.get_content import get_content


async def get_video_detail(url: str):
    """
    url: str -> tiktok video url

    returns (video_id, author_id, author_username, video_url, images, cookies)
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0",
        "Accept-Language": "en-US,en;q=0.9",
    }
    cookies = None
    try:
        async with httpx.AsyncClient(headers=headers, follow_redirects=True) as ses:
            # First try TikWM API for reliable detail extraction
            try:
                r = await ses.post("https://www.tikwm.com/api/", data={"url": url})
                res_json = r.json()
                if res_json.get("code") == 0 and "data" in res_json:
                    data = res_json["data"]
                    v_id = str(data.get("id")) if data.get("id") else None
                    a_id = str(data.get("author", {}).get("id")) if data.get("author", {}).get("id") else None
                    a_user = data.get("author", {}).get("unique_id")
                    v_url = data.get("play")
                    images = data.get("images")
                    return v_id, a_id, a_user, v_url, images, ses.cookies
            except Exception as e:
                print(f"TikWM detail lookup error: {e}")

            # Fallback to direct page scraping
            clean_url = url.split("?")[0]
            match = re.search(r"/video/(\d+)", url)
            post_id = match.group(1) if match else None

            if not post_id:
                res = await ses.get(url)
                cookies = res.cookies
                final_url = str(res.url)
                match = re.search(r"/video/(\d+)", final_url) or re.search(r"(\d{15,})", final_url)
                if match:
                    post_id = match.group(1)
            
            target_url = f"https://www.tiktok.com/@i/video/{post_id}" if post_id else url
            result = await ses.get(target_url)
            cookies = result.cookies

            parser = bs(result.text, "html.parser")
            infotag = (
                parser.find("script", attrs={"id": "__UNIVERSAL_DATA_FOR_REHYDRATION__"})
                or parser.find("script", attrs={"id": "SIGI_STATE"})
                or parser.find("script", attrs={"id": "__FRONTEND_DATA__"})
            )
            if infotag and infotag.text.strip():
                try:
                    infoload = json.loads(infotag.text)
                    video_detail = infoload.get("__DEFAULT_SCOPE__", {}).get("webapp.video-detail", {})
                    item = video_detail.get("itemInfo", {}).get("itemStruct", {})
                    if item:
                        video_id = item.get("id")
                        author = item.get("author", {})
                        video = item.get("video", {})
                        image_post = item.get("imagePost", {})
                        return (
                            video_id,
                            author.get("id"),
                            author.get("uniqueId"),
                            video.get("playAddr"),
                            image_post.get("images"),
                            cookies,
                        )
                except Exception as e:
                    print(f"Error parsing TikTok json: {e}")

            return None, None, None, None, None, cookies
    except Exception as e:
        print(f"get_video_detail error: {e}")
        return None, None, None, None, None, None
