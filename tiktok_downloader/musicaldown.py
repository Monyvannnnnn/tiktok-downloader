import httpx
import re
import random
from fake_useragent import UserAgent
from bs4 import BeautifulSoup as bs
from .get_content import get_content


async def musicaldown(url: str, output: str):
    """
    url: tiktok video url
    output: output file name
    """
    try:
        try:
            ua = UserAgent().random
        except Exception:
            ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
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
        print(f"musicaldown error : {e}")
        return False
