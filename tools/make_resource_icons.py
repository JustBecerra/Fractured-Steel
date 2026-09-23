"""32px icons for the resource panel: power, alloy beam, personnel.

Run from the repository root:

    python3 tools/make_resource_icons.py
"""
from PIL import Image, ImageDraw

OUT = "mods/fracturedsteel/chrome/assets/resource-icons.png"
SIZE = 32


def icon():
	return Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))


def power():
	img = icon()
	draw = ImageDraw.Draw(img)
	bolt = [(18, 1), (7, 15), (14, 15), (8, 31), (26, 13), (17, 13), (27, 1)]
	draw.polygon(bolt, fill=(255, 196, 48, 255), outline=(90, 58, 8, 255))
	return img


def alloy():
	img = icon()
	draw = ImageDraw.Draw(img)
	# Horizontal I-beam.
	draw.rectangle((3, 9, 28, 13), fill=(168, 176, 186, 255))
	draw.rectangle((3, 19, 28, 23), fill=(168, 176, 186, 255))
	draw.rectangle((13, 9, 18, 23), fill=(148, 156, 166, 255))
	draw.line((3, 9, 28, 9), fill=(230, 236, 242, 255))
	draw.line((3, 19, 28, 19), fill=(230, 236, 242, 255))
	draw.line((3, 13, 28, 13), fill=(70, 76, 84, 255))
	draw.line((3, 23, 28, 23), fill=(70, 76, 84, 255))
	return img


def crew():
	img = icon()
	draw = ImageDraw.Draw(img)
	draw.ellipse((11, 3, 21, 13), fill=(226, 232, 238, 255), outline=(40, 48, 58, 255))
	draw.polygon([(6, 29), (9, 16), (23, 16), (26, 29)], fill=(226, 232, 238, 255), outline=(40, 48, 58, 255))
	return img


def main():
	# Sheets must be power-of-two. Three 32px icons sit in a 128x32 sheet.
	sheet = Image.new("RGBA", (128, SIZE), (0, 0, 0, 0))
	sheet.paste(power(), (0, 0), power())
	sheet.paste(alloy(), (SIZE, 0), alloy())
	sheet.paste(crew(), (SIZE * 2, 0), crew())
	sheet.save(OUT)
	print(f"wrote {OUT} {sheet.size}")


if __name__ == "__main__":
	main()
