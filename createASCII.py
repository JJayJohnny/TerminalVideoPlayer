from PIL import Image, ImageEnhance
from colorama import Fore, Style
import math
from concurrent.futures import ThreadPoolExecutor
from functools import partial

CHARS_BY_DENSITY = ' .`-_\':,;^=+/"|)\\<>)iv%xclrs{*}I?!][1taeo7zjLunT#JCwfy325Fp6mqSghVd4EgXPGZbYkOA&8U$@KHDBWNMR0Q'

COLORS = {
    (0, 0, 0): Fore.BLACK,
    (0, 0, 1): Fore.BLUE,
    (0, 1, 0): Fore.GREEN,
    (1, 0, 0): Fore.RED,
    (1, 0, 1): Fore.MAGENTA,
    (0, 1, 1): Fore.CYAN,
    (1, 1, 0): Fore.YELLOW,
    (1, 1, 1): Fore.WHITE,
}

STYLES = [Style.DIM, Style.NORMAL, Style.BRIGHT]

MIN_DISTANCE = math.sqrt(255**2 * 3)

def createASCII(image: Image, columns: int = 100, rows: int = 50) -> str:
    image.thumbnail((columns, rows))
    width, height = image.size
    image = ImageEnhance.Contrast(image).enhance(1.5)
    image = ImageEnhance.Sharpness(image).enhance(1.5)
    grayScale = image.convert("L")
    ascii = []

    # with ThreadPoolExecutor(10) as executor:
    #      futures = [executor.submit(processLine, image, grayScale, width, h) for h in range(height)]
    #      for future in futures:
    #           line, h = future.result()
    #           ascii[h] = line
    for h in range(height):
        line = ''
        for w in range(width):
            brightness = grayScale.getpixel((w, h)) / 255.0
            pixel = image.getpixel((w, h))
            char = CHARS_BY_DENSITY[int(brightness*(len(CHARS_BY_DENSITY)-1))]
            color = findColor(pixel)
            final = color + char + char
            line += final
        ascii.append(line)
    
    return '\n'.join(ascii) + Style.RESET_ALL

def findColor(pixel):
    color = (int(pixel[0]/128), int(pixel[1]/128), int(pixel[2]/128))
    return COLORS[color]

def distance(c1, c2):
    return math.sqrt((c1[0] - c2[0])**2 + (c1[1] - c2[1])**2 + (c1[2] - c2[2])**2)

def processLine(image, grayScale, width, h):
    line = ''
    for w in range(width):
            brightness = grayScale.getpixel((w, h)) / 255.0
            pixel = image.getpixel((w, h))
            char = CHARS_BY_DENSITY[int(brightness*(len(CHARS_BY_DENSITY)-1))]
            color = findColor(pixel)
            final = color + char + char
            line += final
    return line, h