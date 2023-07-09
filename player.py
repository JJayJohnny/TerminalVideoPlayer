import av
from createASCII import createASCII
import shutil
import time
from threading import Thread
from queue import Queue

FPS = True

def play(src: str):
    frameQueue = Queue()
    asciiQueue = Queue()

    decoder = Thread(target=decode, args=(src, frameQueue))
    decoder.start()

    transformer = Thread(target=transform, args=(frameQueue, asciiQueue))
    transformer.start()

    displayer = Thread(target=display, args=(asciiQueue,))
    displayer.start()

    decoder.join()
    transformer.join()
    displayer.join()


def transform(frameQueue: Queue, asciiQueue: Queue):
    while True:
        imageData = frameQueue.get()
        termSize = shutil.get_terminal_size()
        ascii = createASCII(imageData, termSize.columns, termSize.lines)
        asciiQueue.put(ascii)

def display(asciiQueue: Queue):
    while True:
        if FPS:
            start = time.time()
        ascii = asciiQueue.get()
        print('ESC [ 1;1 H')
        print(ascii)
        if FPS:
            stop = time.time()
        print(f"Frame time: {stop-start} FPS: {1.0/(stop-start)}")


def decode(src: str, frameQueue: Queue):
    video = av.open(src)

    vStream = video.streams.video[0]
    vStream.codec_context.skip_frame = "DEFAULT"
    # vStream.thread_count = 10

    for packet in video.demux(vStream):
        if packet.dts is None:
            continue

        type = packet.stream.type

        for frame in packet.decode():
            if type == 'video':
                frameQueue.put(frame.to_image())
             
    # for frame in container.decode(video=0):
    #     frame.to_image().save("frame.jpg", quality=50)