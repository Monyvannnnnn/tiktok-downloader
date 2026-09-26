import re
import json
import random
import httpx
import aiofiles
from fake_useragent import UserAgent
from bs4 import BeautifulSoup as bs
from services.logger import log_activity


async def get_content(
    url: str, output: str = "video.mp4", cookies: httpx.Cookies = None
):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0"
        )
    }
    async with httpx.AsyncClient(headers=headers, cookies=cookies, follow_redirects=True) as client:
        result = await client.get(url)
        async with aiofiles.open(output, "wb") as w:
            async for content in result.aiter_bytes(chunk_size=1024):
                await w.write(content)


async def musicaldown(url: str, output: str) -> bool:
    """
    url: tiktok video url
    output: output file name
    """
    try:
        try:
            ua = UserAgent().random
        except Exception:
            ua = (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/129.0.0.0 Safari/537.36"
            )
        headers = {"User-Agent": ua}
        async with httpx.AsyncClient(headers=headers, follow_redirects=True) as ses:
            res = await ses.get("https://musicaldown.com/en")
            parsing = bs(res.text, "html.parser")
            allInput = parsing.findAll("input")
            data = {}
            for i in allInput:
                name = i.get("name")
                if not name:
                    continue
                if i.get("id") == "link_url" or i.get("type") == "text":
                    data[name] = url
                else:
                    data[name] = i.get("value", "")

            res = await ses.post(
                "https://musicaldown.com/download", data=data
            )
            if res.text.find("Convert Video Now") >= 0:
                match_data = re.search(r"data: '(.*?)'", res.text)
                match_slider = re.search(r"url: '(.*?)'", res.text)
                if match_data and match_slider:
                    res = await ses.post(match_slider.group(1), data={"data": match_data.group(1)})
                    if res.text.find('"success":true') >= 0:
                        urlVideo = res.json()["url"]
                        await get_content(urlVideo, output)
                        return True
                return False

            parsing = bs(res.text, "html.parser")
            urls = parsing.findAll(
                "a", attrs={"class": "btn waves-effect waves-light orange download"}
            )
            if len(urls) <= 0:
                return False

            idx = random.randint(0, len(urls) - 1)
            urlVideo = urls[idx].get("href")
            if urlVideo:
                await get_content(urlVideo, output)
                return True
            return False

    except Exception as e:
        log_activity(f"musicaldown error : {e}")
        return False


async def get_video_detail(url: str):
    """
    url: str -> tiktok video url

    returns (video_id, author_id, author_username, video_url, images, cookies)
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0"
        ),
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
                log_activity(f"TikWM detail lookup notice: {e}")

            # Fallback to direct page scraping
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
                        raw_images = image_post.get("images") or []
                        cleaned_images = []
                        for img in raw_images:
                            if isinstance(img, str):
                                cleaned_images.append(img)
                            elif isinstance(img, dict):
                                u = img.get("imageURL", {}).get("urlList", [None])[0] or img.get("displayAddr")
                                if u:
                                    cleaned_images.append(u)
                        return (
                            video_id,
                            author.get("id"),
                            author.get("uniqueId"),
                            video.get("playAddr"),
                            cleaned_images if cleaned_images else None,
                            cookies,
                        )
                except Exception as e:
                    log_activity(f"Error parsing TikTok json: {e}")

            return None, None, None, None, None, cookies
    except Exception as e:
        log_activity(f"get_video_detail error: {e}")
        return None, None, None, None, None, None
