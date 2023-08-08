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

MIN_HEIGHT = 4
MIN_WIDTH = 4

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
        self.height = termSize.lines-1
        self.playing = False

    def play(self, src: str):
        if self.height < MIN_HEIGHT or self.width < MIN_WIDTH:
            return
        decoder = Thread(target=self.decode, args=(src,))
        decoder.start()

        transformer = Thread(target=self.transform)
        transformer.start()

        displayer = Thread(target=self.display)
        displayer.start()

        audioPlayer = Thread(target=self.playAudio)
        audioPlayer.start()

        self.messagesToDecoder.put(Message.START)
        self.playing = True

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
            ascii = createASCII(imageData, self.width-1, self.height-1)
            self.asciiQueue.put((timeStamp, ascii))

    def display(self):
        if self.asciiQueue.get() != Message.START:
            return
        
        cls()
        self.printTopBar()
        while True:
            while self.playing == False:
                time.sleep(0.5)     
            message = self.asciiQueue.get()
            if message == Message.QUIT:
                break
            timeStamp, ascii = message
            print(Cursor.POS(1,2) + ascii, flush=True)
            print(Cursor.POS(1,2) + str(int(timeStamp)), flush=True)
            if (time.time() - self.timeZero) <= timeStamp:
                time.sleep(max(timeStamp - (time.time()-self.timeZero), 0))
            else:
                self.timeZero += (time.time() - self.timeZero) - timeStamp


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
            try:
                message = self.messagesToDecoder.get_nowait()
                if message == Message.QUIT:
                    return
            except Empty:
                pass

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
                while self.playing == False:
                    time.sleep(0.5)
                message = self.decodedAudio.get()
                if message == Message.QUIT:
                    break
                timeStamp, audioFrame = message
                
                if (time.time() - self.timeZero) < timeStamp:
                    time.sleep(max(timeStamp - (time.time() - self.timeZero), 0))
                audioQueue.put_nowait(audioFrame)

    def pause(self):
        self.playing = not self.playing
        self.printTopBar()

    def quit(self):
        self.playing = True
        self.messagesToDecoder.put(Message.QUIT)
        self.asciiQueue = Queue()
        self.asciiQueue.put(Message.QUIT)
        self.frameQueue = Queue()
        self.frameQueue.put(Message.QUIT)
        self.decodedAudio = Queue()
        self.decodedAudio.put(Message.QUIT)
    
    def printTopBar(self):
        controls = "ESC - quit | Space - pause"
        if self.width >= len(controls):
            print(Cursor.POS(1,1)+ controls)
        if not self.playing:
            print(Cursor.POS(self.width-7, 1) + "PAUSED")
        else:
            print(Cursor.POS(self.width-7, 1) + "      ")

