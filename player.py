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
SECONDS_TO_BUFFER = 5

class Message(Enum):
    START = 'START'
    QUIT = 'QUIT'
    WAIT = 'WAIT'

def cls():
    os.system('cls' if os.name=='nt' else 'clear')

class Player:
    def __init__(self):
        self.frameQueue = Queue()
        self.asciiQueue = Queue()
        self.decodedAudio = Queue()
        self.messagesToDecoder = Queue()

        termSize = shutil.get_terminal_size()
        self.width = termSize.columns
        self.height = termSize.lines

    def play(self, src: str):
        decoder = Thread(target=self.decode, args=(src,))
        decoder.start()

        transformer = Thread(target=self.transform)
        transformer.start()

        displayer = Thread(target=self.display)
        displayer.start()

        audioPlayer = Thread(target=self.playAudio)
        audioPlayer.start()

        self.messagesToDecoder.put(Message.START)

        decoder.join()
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
            ascii = createASCII(imageData, self.width, self.height-1)
            self.asciiQueue.put((timeStamp, ascii))

    def display(self):
        if self.asciiQueue.get() != Message.START:
            return
        
        stop = time.time()
        printTime=0
        cls()
        while True:     
            message = self.asciiQueue.get()
            if message == Message.QUIT:
                break
            timeStamp, ascii = message
            # if (time.time() - self.timeZero) < timeStamp:
            #     time.sleep(max(timeStamp - (time.time()-self.timeZero) - printTime, 0))
            start = time.time()
            print(Cursor.POS(1,1) + ascii, flush=True)
            # print(Cursor.POS(1,1) + f"Frame time: {stop-start} FPS: {int(1.0/(stop-start))}")
            print(Cursor.POS(1,2) + str(round(timeStamp, 2)), flush=True)
            printTime = time.time()-start
            if (time.time() - self.timeZero) < timeStamp:
                time.sleep(max(timeStamp - (time.time()-self.timeZero), 0))


    def decode(self, src: str):
        video = av.open(src)

        vStream = video.streams.video[0]
        vStream.codec_context.skip_frame = "DEFAULT"
        vStream.thread_type = 'AUTO'
        timeBase = vStream.time_base
        self.averageFPS = vStream.average_rate

        aStream = video.streams.audio[0]
        self.sample_rate = aStream.sample_rate
        self.channels = aStream.channels
        self.frameSize = aStream.frame_size
        audioTimeBase = aStream.time_base

        if self.messagesToDecoder.get() != Message.START:
            self.frameQueue.put(Message.QUIT)
            self.decodedAudio.put(Message.QUIT)
            return

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
                
                if (time.time() - self.timeZero) < timeStamp:
                    time.sleep(max(timeStamp - (time.time() - self.timeZero), 0))
                audioQueue.put_nowait(audioFrame)
