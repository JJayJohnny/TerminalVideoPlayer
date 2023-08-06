import sys
from player import Player
from pynput.keyboard import Key, Listener, Controller

player = Player()
keyboard = Controller()

def onPress(key):
    pass

def onRelease(key):
    if key == Key.space:
        player.pause()
    elif key == Key.esc:
        player.quit()
        return False

if __name__ == '__main__':
    with Listener(on_press=onPress, on_release=onRelease) as listener:
        player.play(sys.argv[1])
        keyboard.press(Key.esc)
        keyboard.release(Key.esc)
        listener.join()

    