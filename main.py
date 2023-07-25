import sys
from player import Player

if __name__ == '__main__':
    player = Player()
    player.play(sys.argv[1])
    