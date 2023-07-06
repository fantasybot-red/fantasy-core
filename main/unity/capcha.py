import io
from PIL import Image, ImageDraw, ImageFont
import random
import string

# Generate a random CAPTCHA text
def generate_captcha_text(length=6):
    captcha_text = ''.join(random.choices(string.ascii_uppercase+string.digits, k=length))
    return captcha_text

# Generate a random CAPTCHA image with red text and random letter heights
def generate_captcha_image(captcha_text):
    # Image dimensions
    width, height = 5000, 2000

    # Create a blank image with a white background
    image = Image.new('RGBA', (width, height), (0,0,0,0))
    draw = ImageDraw.Draw(image)

    # Set a font
    font = ImageFont.truetype('arial.ttf', size=400)

    # Calculate the bounding box of the CAPTCHA text
    text_bbox = draw.textbbox((0, 0), captcha_text, font=font)

    # Calculate the width and height of the CAPTCHA text
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    listall = [random.randint(100, 200) for _ in range(3)]

    # Draw each letter of the CAPTCHA text at a random height


    def draw_letter(color, captcha_text, up):
        x = (width - text_width) / 5
        y = (height - text_height) / 2

        # Store the starting point of the line
        start_x = 0
        start_y = 0

        for char in captcha_text:
            if up:
                char_height = y + random.randint(-500, -100)
                up = False
            else:
                char_height = y + random.randint(100, 500)
                up = True

            text_bbox = draw.textbbox((0, 0), char, font=font)
            char_text_width = text_bbox[2] - text_bbox[0]
            char_text_height = text_bbox[3] - text_bbox[1]
            char_start_x = x + random.randint(0, 100)
            char_start_y = char_height + random.randint(0, 100)
            char_end_x = x + char_text_width + random.randint(0, 100)
            char_end_y = char_height + char_text_height + random.randint(0, 100)
            draw.line([(char_start_x, char_start_y), (char_end_x, char_end_y)], fill=tuple([random.randint(0, 100) for _ in range(3)]), width=20)

            draw.text((x, char_height), char, fill=color, font=font)
            char_text_width_center = x + char_text_width / 2 + random.randint(-50, 50)
            char_text_height_center = char_height + (char_text_height + 20 ) / 2 + random.randint(20, 50)
            if start_x != 0 and start_y != 0:
                draw.ellipse([(start_x - 20, start_y  - 20), (start_x + 20, start_y + 20)], fill=color)
                draw.line([(start_x, start_y), (char_text_width_center, char_text_height_center)], fill=color, width=20)
            start_x = char_text_width_center
            start_y = char_text_height_center
            x += width / len(captcha_text) - 100
        draw.ellipse([(start_x - 20, start_y - 20), (start_x + 20, start_y + 20)], fill=color)

    up = [True, False]
    random.shuffle(up)

    font_spam = ImageFont.truetype('arial.ttf', size=200)
    for _ in range(5):
        text_bbox = draw.textbbox((0, 0), captcha_text, font=font_spam)
        char_text_width = text_bbox[2] - text_bbox[0]
        char_text_height = text_bbox[3] - text_bbox[1]
        x_random = random.randint(0+char_text_width, width-char_text_width)
        y_random = random.randint(0+char_text_height, height-char_text_height)
        char = random.choice(string.ascii_uppercase)
        angle = random.randint(-10, 10)
        draw.text((x_random, y_random), char, rotation=angle, fill=tuple(listall), font=font_spam)

    draw_letter(tuple(listall), generate_captcha_text(), up[0])

    draw_letter("red", captcha_text, up[1])

    buf = io.BytesIO()
    image.save(buf, format='PNG')

    return buf.getvalue()