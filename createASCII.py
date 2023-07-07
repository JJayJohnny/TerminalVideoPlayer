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

COLORS = [
    [[(v/255.0) ** 2.2 for v in color[0]], color[1]]for color in COLORS
]

STYLES = [Style.DIM, Style.NORMAL, Style.BRIGHT]

MIN_DISTANCE = math.sqrt(255**2 * 3)

def createASCII(image: Image, columns: int = 100, rows: int = 50) -> str:
    # image = ImageEnhance.Contrast(image).enhance(1.5)
    # image = ImageEnhance.Sharpness(image).enhance(1.5)
    image.thumbnail((columns, rows))
    width, height = image.size
    # print(f'Width: {width} height: {height}')
    grayScale = image.convert("L")
    # grayScale.save('gray.jpg')
    ascii = []

    for h in range(height):
        line = ''
        for w in range(width):
            brightness = grayScale.getpixel((w, h)) / 255.0
            pixel = image.getpixel((w, h))
            srgb = [(v/255.0)**2.2 for v in pixel]
            char = CHARS_BY_DENSITY[int(brightness*(len(CHARS_BY_DENSITY)-1))]
            color = findColor(srgb, brightness)
            # style = STYLES[int(brightness*(len(STYLES)-1))]
            final = color + char + char
            line += final
        ascii.append(line)
    
    return '\n'.join(ascii)

def findColor(pixel, brightness):
    minDist = 2.0
    index = 0

    for c in COLORS:
        temp = [v * brightness for v in c[0]]
        d = distance(pixel, temp)
        if d < minDist:
            minDist = d
            index = COLORS.index(c)
    # if minDist < 0.2:
    #     return COLORS[index][1] + Style.BRIGHT
    # if minDist > 0.8:
    #     return COLORS[index][1] + Style.DIM
    return COLORS[index][1]

def distance(c1, c2):
    return math.sqrt((c1[0] - c2[0])**2 + (c1[1] - c2[1])**2 + (c1[2] - c2[2])**2)