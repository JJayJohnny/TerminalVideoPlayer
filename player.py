import av
from createASCII import createASCII
import shutil
import time
from threading import Thread
from queue import Queue
from colorama import Cursor
import os

FPS = True

maxFPS = 30

def play(src: str):
    frameQueue = Queue()
    asciiQueue = Queue()

    decoder = Thread(target=decode, args=(src, frameQueue))
    decoder.start()

    transformers = [Thread(target=transform, args=(frameQueue, asciiQueue)) for i in range(10)]
    for transformer in transformers:
        transformer.start()

    time.sleep(2)
    displayer = Thread(target=display, args=(asciiQueue,))
    displayer.start()

    decoder.join()
    for transformer in transformers:
        transformer.join()
    displayer.join()


def transform(frameQueue: Queue, asciiQueue: Queue):
    asciiQueue.put(frameQueue.get())
    while True:
        imageData = frameQueue.get()
        termSize = shutil.get_terminal_size()
        ascii = createASCII(imageData, termSize.columns, termSize.lines-1)
        asciiQueue.put(ascii)

def display(asciiQueue: Queue):
    maxFPS = asciiQueue.get()
    frameTime = 1.0/maxFPS
    stop = time.time()
    os.system('clear')
    while True:
        if FPS:
            start = time.time()
        ascii = asciiQueue.get()
        if (time.time() - stop) < frameTime:
            time.sleep(max(frameTime - (time.time()-stop), 0))
        print(Cursor.POS(1,1))
        print(ascii)
        if FPS:
            stop = time.time()
        print(Cursor.POS(1,1) + f"Frame time: {stop-start} FPS: {1.0/(stop-start)}")


def decode(src: str, frameQueue: Queue):
    video = av.open(src)

    vStream = video.streams.video[0]
    vStream.codec_context.skip_frame = "DEFAULT"
    vStream.thread_count = 5
    maxFPS = vStream.average_rate
    print(maxFPS)
    frameQueue.put(maxFPS)

    for packet in video.demux(vStream):
        if packet.dts is None:
            continue

        type = packet.stream.type

        for frame in packet.decode():
            if type == 'video':
                frameQueue.put(frame.to_image())
             
    # for frame in container.decode(video=0):
    #     frame.to_image().save("frame.jpg", quality=50)