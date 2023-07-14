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
from enum import Enum

FPS = True
SYNNCHRONIZE_EVERY = 10

class Message(Enum):
    START = 'START'
    QUIT = 'QUIT'

class Player:
    def __init__(self, src: str):
        self.frameQueue = Queue()
        self.asciiQueue = Queue()
        self.decodedAudio = Queue()
        self.synchronizationQueue = Queue()

        decoder = Thread(target=self.decode, args=(src,))
        decoder.start()

        transformers = [Thread(target=self.transform) for i in range(1)]
        for transformer in transformers:
            transformer.start()

        displayer = Thread(target=self.display)
        displayer.start()

        audioPlayer = Thread(target=self.playAudio)
        audioPlayer.start()

        decoder.join()
        for transformer in transformers:
            transformer.join()
        displayer.join()
        audioPlayer.join()


    def transform(self):   
        while True:
            message = self.frameQueue.get()
            if message == Message.QUIT:
                self.asciiQueue.put(message)
                break
            timeStamp, imageData = message
            termSize = shutil.get_terminal_size()
            ascii = createASCII(imageData, termSize.columns, termSize.lines-1)
            self.asciiQueue.put((timeStamp, ascii))

    def display(self):
        if self.asciiQueue.get() != Message.START:
            return
        
        stop = time.time()
        os.system('clear')
        frameCounter = 0
        while True:
            message = self.asciiQueue.get()
            if message == Message.QUIT:
                break
            if FPS:
                start = time.time()
            timeStamp, ascii = message
            if (time.time() - self.timeZero) < timeStamp:
                time.sleep(max(timeStamp - (time.time()-self.timeZero), 0))
            print(Cursor.POS(1,1) + ascii)
            if frameCounter%SYNNCHRONIZE_EVERY == 0:
                self.synchronizationQueue.put(timeStamp)
            if FPS:
                stop = time.time()
            print(Cursor.POS(1,1) + f"Frame time: {stop-start} FPS: {int(1.0/(stop-start))}")
            print(Cursor.POS(1,2) + str(round(timeStamp, 2)))
            frameCounter += 1


    def decode(self, src: str):
        video = av.open(src)

        vStream = video.streams.video[0]
        vStream.codec_context.skip_frame = "DEFAULT"
        vStream.thread_type = 'AUTO'
        timeBase = vStream.time_base

        aStream = video.streams.audio[0]
        self.sample_rate = aStream.sample_rate
        self.channels = aStream.channels
        self.frameSize = aStream.frame_size
        audioTimeBase = aStream.time_base

        self.timeZero = time.time()
        self.asciiQueue.put(Message.START)
        self.decodedAudio.put(Message.START)
                   
        for packet in video.demux(vStream, aStream):
            if packet.dts is None:
                continue

            type = packet.stream.type
            for frame in packet.decode():
                if type == 'video':
                    self.frameQueue.put((float(frame.pts*timeBase), frame.to_image()))
                if type == 'audio':
                    self.decodedAudio.put((float(frame.pts*audioTimeBase), frame.to_ndarray().T))
        self.frameQueue.put(Message.QUIT)
        self.decodedAudio.put(Message.QUIT)
                
    def playAudio(self):
        audioQueue = Queue()
        correctionTime = 0.0

        if self.decodedAudio.get() != Message.START:
            return
        
        def callback(outdata, frames, time, status):
            if status:
                print(status)
            try:
                data = audioQueue.get_nowait()
                outdata[:] = data
            except Empty as e:
                data = np.zeros((self.frameSize, self.channels), dtype=np.float32)
                outdata[:] = data

        
        with sd.OutputStream(samplerate=self.sample_rate, channels=self.channels, callback=callback, blocksize=self.frameSize):
            while True:
                message = self.decodedAudio.get()
                if message == Message.QUIT:
                    break
                timeStamp, audioFrame = message
                try:
                    videoTimeStamp = self.synchronizationQueue.get_nowait()
                except Empty:
                    videoTimeStamp = timeStamp
                correctionTime += timeStamp-videoTimeStamp
                if (time.time() - self.timeZero - correctionTime) < timeStamp:
                    time.sleep(max(timeStamp - (time.time() - self.timeZero - correctionTime), 0))
                audioQueue.put_nowait(audioFrame)