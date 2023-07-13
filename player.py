import av
from createASCII import createASCII
import shutil
import time
from threading import Thread
from queue import Queue, Empty
from colorama import Cursor
import os
import numpy as np
import sounddevice as sd

FPS = True

def play(src: str):
    frameQueue = Queue()
    asciiQueue = Queue()
    audioQueue = Queue()
    decodedAudio = Queue()

    decoder = Thread(target=decode, args=(src, frameQueue, decodedAudio, audioQueue))
    decoder.start()

    transformers = [Thread(target=transform, args=(frameQueue, asciiQueue)) for i in range(1)]
    for transformer in transformers:
        transformer.start()

    displayer = Thread(target=display, args=(asciiQueue,))
    displayer.start()

    audioPlayer = Thread(target=playAudio, args=(audioQueue, decodedAudio))
    audioPlayer.start()

    decoder.join()
    for transformer in transformers:
        transformer.join()
    displayer.join()
    audioPlayer.join()


def transform(frameQueue: Queue, asciiQueue: Queue):   
    while True:
        temp = frameQueue.get()
        asciiQueue.put(temp)
        if temp == 'END':
            break
        imageData = frameQueue.get()
        termSize = shutil.get_terminal_size()
        ascii = createASCII(imageData, termSize.columns, termSize.lines-1)
        asciiQueue.put(ascii)

def display(asciiQueue: Queue):
    timeZero = time.time()
    stop = time.time()
    os.system('clear')
    while True:
        displayTime = asciiQueue.get()
        if displayTime == 'END':
            break
        if FPS:
            start = time.time()
        ascii = asciiQueue.get()
        if (time.time() - timeZero) < displayTime:
            time.sleep(max(displayTime - (time.time()-timeZero), 0))
        print(Cursor.POS(1,1) + ascii)
        if FPS:
            stop = time.time()
        print(Cursor.POS(1,1) + f"Frame time: {stop-start} FPS: {int(1.0/(stop-start))}")
        print(Cursor.POS(1,2) + str(round(displayTime, 2)))


def decode(src: str, frameQueue: Queue, decodedAudio: Queue, audioQueue: Queue):
    video = av.open(src)

    vStream = video.streams.video[0]
    vStream.codec_context.skip_frame = "DEFAULT"
    vStream.thread_type = 'AUTO'
    timeBase = vStream.time_base

    aStream = video.streams.audio[0]
    sample_rate = aStream.sample_rate
    channels = aStream.channels
    frameSize = aStream.frame_size
    audioTimeBase = aStream.time_base

    def callback(outdata, frames, time, status):
        if status:
            print(status)
        try:
            data = audioQueue.get_nowait()
            outdata[:] = data
        except Empty as e:
            data = np.zeros((frameSize, channels), dtype=np.float32)
            outdata[:] = data
            
    with sd.OutputStream(samplerate=sample_rate, channels=channels, callback=callback, blocksize=frameSize):
        for packet in video.demux(vStream, aStream):
            if packet.dts is None:
                continue

            type = packet.stream.type
            for frame in packet.decode():
                if type == 'video':
                    frameQueue.put(float(frame.pts*timeBase))
                    frameQueue.put(frame.to_image())
                if type == 'audio':
                    decodedAudio.put(float(frame.pts*audioTimeBase))
                    decodedAudio.put(frame.to_ndarray().T)
    frameQueue.put('END')
    decodedAudio.put('END')
             
def playAudio(audioQueue, decodedAudio):
    timeZero = time.time()
    while True:
        timeStamp = decodedAudio.get()
        if timeStamp == 'END':
            break
        audioFrame = decodedAudio.get()
        if (time.time() - timeZero) < timeStamp:
            time.sleep(max(timeStamp - (time.time() - timeZero), 0))
        audioQueue.put_nowait(audioFrame)