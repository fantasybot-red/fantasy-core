import io
import random
import string
from sync_to_async import run
from PIL import Image, ImageDraw, ImageFont


# Generate a random CAPTCHA text
def generate_captcha_text(length=6):
    captcha_text = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))  # nosec
    return captcha_text

@run
def generate_captcha_image(captcha_text):
    # Image dimensions
    width, height = 5000, 2000

    # Create a blank image with a white background
    image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Set a font
    font = ImageFont.truetype('./unity/Arialn.ttf', size=400)

    # Calculate the bounding box of the CAPTCHA text
    text_bbox = draw.textbbox((0, 0), captcha_text, font=font)

    # Calculate the width and height of the CAPTCHA text
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    listall = [random.randint(100, 200) for _ in range(3)]  # nosec

    # Draw each letter of the CAPTCHA text at a random height

    def draw_letter(color, captcha_text, up):
        x = (width - text_width) / 5
        y = (height - text_height) / 2

        captcha_text = captcha_text.upper()

        # Store the starting point of the line
        start_x = 0
        start_y = 0

        for char in captcha_text:
            if up:
                char_height = y + random.randint(-500, -100)  # nosec
                up = False
            else:
                char_height = y + random.randint(100, 500)  # nosec
                up = True

            text_bbox = draw.textbbox((0, 0), char, font=font)
            char_text_width = text_bbox[2] - text_bbox[0]
            char_text_height = text_bbox[3] - text_bbox[1]
            char_start_x = x + random.randint(0, 100)  # nosec
            char_start_y = char_height + random.randint(0, 100)  # nosec
            char_end_x = x + char_text_width + random.randint(0, 100)  # nosec
            char_end_y = char_height + char_text_height + random.randint(0, 100)  # nosec
            draw.line([(char_start_x, char_start_y), (char_end_x, char_end_y)],
                      fill=(238, 75, 43), width=20)

            draw.text((x, char_height), char, fill=color, font=font)  # nosec
            char_text_width_center = x + char_text_width / 2 + random.randint(-50, 50)  # nosec
            char_text_height_center = char_height + (char_text_height + 20) / 2 + random.randint(20, 50)  # nosec
            if start_x != 0 and start_y != 0:
                draw.ellipse([(start_x - 20, start_y - 20), (start_x + 20, start_y + 20)], fill=color)
                draw.line([(start_x, start_y), (char_text_width_center, char_text_height_center)], fill=color, width=20)
            start_x = char_text_width_center
            start_y = char_text_height_center
            x += width / len(captcha_text) - 100
        draw.ellipse([(start_x - 20, start_y - 20), (start_x + 20, start_y + 20)], fill=color)

    up = [True, False]
    random.shuffle(up)

    font_spam = ImageFont.truetype('./unity/Arialn.ttf', size=200)
    for _ in range(50):
        text_bbox = draw.textbbox((0, 0), captcha_text, font=font_spam)
        char_text_width = text_bbox[2] - text_bbox[0]
        char_text_height = text_bbox[3] - text_bbox[1]
        x_random = random.randint(0 + char_text_width, width - char_text_width)  # nosec
        y_random = random.randint(0 + char_text_height, height - char_text_height)  # nosec
        char = random.choice(string.ascii_uppercase)  # nosec
        angle = random.randint(-10, 10)  # nosec
        draw.text((x_random, y_random), char, rotation=angle, fill=tuple(listall), font=font_spam)

    draw_letter(tuple(listall), generate_captcha_text(len(captcha_text)), up[0])

    draw_letter((238, 75, 43), captcha_text, up[1])

    for x in range(image.size[0]):
        for y in range(image.size[1]):
            r, g, b, a = image.getpixel((x, y))
            if a == 0:
                continue
            image.putpixel((x, y), (r, g, b, random.randint(170, 255)))  # nosec

    buf = io.BytesIO()
    image.show()
    image.save(buf, format='PNG')

    return buf.getvalue()

