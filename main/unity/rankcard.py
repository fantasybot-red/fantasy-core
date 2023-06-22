import io
import aiohttp
from PIL import Image, ImageDraw, ImageFont

def truncate_str(str, max_len=30):
  if len(str) <= max_len:
    return str
  else:
    return str[:max_len - 3] + "..."

async def rank_card(username, avatar, level, rank, current_xp, xp_color, next_level_xp):
    custom_background = "#36393f"

    # create backdrop
    img = Image.new('RGB', (1034, 282), color=custom_background)
    async with aiohttp.ClientSession() as session:
        async with session.get(avatar) as resp:
            img_avatar = io.BytesIO(await resp.content.read())
    
    img_avatar = Image.open(img_avatar)
    
    mask = Image.new('L', img_avatar.size)
    mask_draw = ImageDraw.Draw(mask)
    width, height = img_avatar.size
    mask_draw.ellipse((0, 0, width, height), fill=255)
        
    img_avatar = img_avatar.resize((210, 210))
    
    mask = mask.resize((210, 210))        

    img.paste(img_avatar, (30, 30), mask=mask)
    d = ImageDraw.Draw(img)
    d = drawProgressBar(d, 260, 180, 700, 40, current_xp/next_level_xp, bg="#484B4E", fg = xp_color) # create progress bar

    font = ImageFont.truetype(font=f"./unity/Ubuntu-Regular.ttf", size=50)
    font2 = ImageFont.truetype(font=f"./unity/Ubuntu-Regular.ttf", size=25)

    ufont = ImageFont.truetype(font=f"./unity/Ubuntu-Regular.ttf", size=45)
    
    d.text((260, 100), truncate_str(username, max_len=15), font=ufont, fill=(255, 255, 255, 128))
    d.text((890, 130), f"{current_xp}/{next_level_xp} XP", font=font2, fill=(255, 255, 255, 128))
    x_df = 800
    if len(f"LEVEL {level}") > 8:
        x_df -= (len(f"LEVEL {level}") - 8) * 20
    d.text((x_df, 50), f"LEVEL {level}", font=font, fill=(255, 255, 255, 128))
    d.text((260, 50), f"RANK #{rank}", font=font2, fill=(255, 255, 255, 128))

    buf = io.BytesIO()
    img.save(buf, format='PNG')

    return buf.getvalue()


def drawProgressBar(d, x, y, w, h, progress, bg="black", fg="red"):
    d.ellipse((x+w, y, x+h+w, y+h), fill=bg)
    d.ellipse((x, y, x+h, y+h), fill=bg)
    d.rectangle((x+(h/2), y, x+w+(h/2), y+h), fill=bg)

    # draw progress bar
    w *= progress
    d.ellipse((x+w, y, x+h+w, y+h), fill=fg)
    d.ellipse((x, y, x+h, y+h), fill=fg)
    d.rectangle((x+(h/2), y, x+w+(h/2), y+h), fill=fg)

    return d
