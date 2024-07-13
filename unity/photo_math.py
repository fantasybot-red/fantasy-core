import io
import re
import aiohttp
import markdownify
import urllib.parse
from pylatexenc.latex2text import LatexNodes2Text

headers_real = {"User-Agent": "Mozilla/5.0 (compatible; FantasyBot/0.1; +https://fantasybot.xyz/support)"}

def format_data_html(data):
    out = re.findall(r"(<span><img class=\"math-equation\" src=\"(.*?)\"></span>)", data)
    for full, url in out:
        from_k = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)["from"][0]
        data_latex = LatexNodes2Text().latex_to_text(from_k)
        data = data.replace(full, data_latex)
    out = re.findall(r"<img src=\".*?\" alt=\".*?\" />", data)
    for full in out:
        data = data.replace(full, "")
    markdown_text = markdownify.markdownify(data)
    while "\n\n" in markdown_text:
        markdown_text = markdown_text.replace("\n\n", "\n")
    return markdown_text


async def get_answer(bytes_data):
    async with aiohttp.ClientSession(headers=headers_real) as s:
        async with s.post(
                "https://identitytoolkit.googleapis.com/v1/accounts:signUp?key=AIzaSyDvmQBkox_MZkYss__mFXDTgoA5XAonSwA",
                json={"returnSecureToken": True}) as r:
            token = (await r.json())["idToken"]
        headers = {
            'authorization': f'Bearer {token}',
            'origin': 'https://dicamon.vn',
            'referer': 'https://dicamon.vn/',
        }
        async with s.post('https://search-hive.giainhanh.io/api/v2/search-image', headers=headers,
                          data={'file': io.BytesIO(bytes_data)}) as r:
            if (not r.ok) or ("json" not in r.content_type):
                return
            data = (await r.json()).get("data", [])
        return_data = []
        for i in data:
            question_answer_obj = {}
            question_answer_obj["question"] = {}
            question_answer_obj["answer"] = {}
            question = i["question"]
            question_text = None
            question_img = None
            if question["type"] == "html":
                question_text = format_data_html(question["content"])
            elif question["type"] == "text":
                question_text = question["content"]
            elif question["type"] == "text_link":
                question_text = question["content"]
                question_img = question["extra_data"]["links"][0]
            question_answer_obj["question"]["text"] = question_text.strip()
            question_answer_obj["question"]["img"] = question_img
            answer = i["best_answer"]
            answer_text = None
            answer_img = None
            if answer["type"] == "html":
                answer_text = format_data_html(answer["content"])
            elif answer["type"] == "text":
                answer_text = answer["content"]
            elif answer["type"] == "text_link":
                answer_text = answer["content"]
                answer_img = answer["extra_data"]["links"][0]
            question_answer_obj["answer"]["text"] = answer_text.strip()
            question_answer_obj["answer"]["img"] = answer_img
            return_data.append(question_answer_obj)
    return return_data[:4]