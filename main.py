from colorama import Fore
import sys
from PIL import Image
from createASCII import createASCII

if __name__ == '__main__':
    image = Image.open(sys.argv[1])
    ascii = createASCII(image, 150)
    f = open('wynik.txt', 'w')
    f.write(ascii)
    f.close()
    print(ascii)
    