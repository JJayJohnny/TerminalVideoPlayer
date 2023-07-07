import sys
from PIL import Image
from createASCII import createASCII
import shutil
import player

if __name__ == '__main__':
    # image = Image.open(sys.argv[1])
    # termSize = shutil.get_terminal_size()
    # ascii = createASCII(image, termSize.columns, termSize.lines)
    # f = open('wynik.txt', 'w')
    # f.write(ascii)
    # f.close()
    # print(ascii)
    player.play(sys.argv[1])
    