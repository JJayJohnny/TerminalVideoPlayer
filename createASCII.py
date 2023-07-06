from PIL import Image, ImageEnhance
from colorama import Fore, Style
import math

CHARS_BY_DENSITY = ' .`-_\':,;^=+/"|)\\<>)iv%xclrs{*}I?!][1taeo7zjLunT#JCwfy325Fp6mqSghVd4EgXPGZbYkOA&8U$@KHDBWNMR0Q'

# CHARS_BY_DENSITY = "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft\|()1[]?-_+~i!lI;:,\"^`. "

COLORS = [
    [(0, 0, 0), Fore.BLACK],
    [(0, 0, 255), Fore.BLUE],
    [(0, 255, 0), Fore.GREEN],
    [(255, 0, 0), Fore.RED],
    [(255, 0, 255), Fore.MAGENTA],
    [(0, 255, 255), Fore.CYAN],
    [(255, 255, 0), Fore.YELLOW],
    [(255, 255, 255), Fore.WHITE],
]

STYLES = [Style.DIM, Style.NORMAL, Style.BRIGHT]

MIN_DISTANCE = math.sqrt(255**2 * 3)

def createASCII(image: Image, columns: int = 100) -> str:
    image = ImageEnhance.Contrast(image).enhance(1.5)
    image = ImageEnhance.Sharpness(image).enhance(1.5)
    image.thumbnail((columns, columns))
    width, height = image.size
    print(f'Width: {width} height: {height}')
    grayScale = image.convert("L")
    grayScale.save('gray.jpg')
    ascii = []

    for h in range(height):
        line = ''
        for w in range(width):
            brightness = grayScale.getpixel((w, h)) / 255
            pixel = image.getpixel((w, h))

            char = CHARS_BY_DENSITY[int(brightness*(len(CHARS_BY_DENSITY)-1))]
            color = findColor(pixel)
            # style = STYLES[int(brightness*(len(STYLES)-1))]
            final = color + char + Style.RESET_ALL
            line += final
        ascii.append(line)
    
    return '\n'.join(ascii)

def findColor(pixel):
    minDist = MIN_DISTANCE
    index = 0

    for c in COLORS:
        d = distance(pixel, c[0])
        if d < minDist:
            minDist = d
            index = COLORS.index(c)
    return COLORS[index][1]

def distance(c1, c2):
    return math.sqrt((c1[0] - c2[0])**2 + (c1[1] - c2[1])**2 + (c1[2] - c2[2])**2)