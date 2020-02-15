import subprocess
import pyaudio
import soundfile as sf
import numpy as np
import io


class AudioQueue:
    def __init__(self, pa, output_device, samplerate=44100, channels=1, format=pyaudio.paFloat32, frames_per_buffer=1024, volume=1):
        self.pa = pa
        self.output_device = output_device
        self.samplerate = samplerate
        self.channels = channels
        self.format = format
        self.frames_per_buffer = frames_per_buffer
        self.volume = volume

        self._audiodata = np.zeros(shape=0)
        self._stream = self.pa.open(format=self.format,
                                    channels=self.channels,
                                    rate=self.samplerate,
                                    output=True,
                                    stream_callback=self._callback,
                                    output_device_index=self.output_device,
                                    frames_per_buffer=self.frames_per_buffer)
        self._empty_audio_array = np.zeros(shape=self.frames_per_buffer)

    def add_to_queue(self, file):
        audio = subprocess.Popen(["ffmpeg", "-i", file, "-loglevel", "panic", "-vn", "-f", "wav", "-c:a", "pcm_s16le", "-ar", str(self.samplerate), "pipe:1"],
                                 stdout=subprocess.PIPE)

        audiofile = sf.SoundFile(io.BytesIO(audio.stdout.read()))
        self._audiodata = np.concatenate((self._audiodata, audiofile.read(dtype="int16")))

        if not self._stream.is_active():
            self._stream.start_stream()

    def _callback(self, in_data, frame_count, time_info, status):
        size = frame_count
        data = self._audiodata[:size]
        self._audiodata = self._audiodata[size:]

        #for i in range(len(data)):
        #    chunk = np.fromstring(data[i], np.int16)
        #    chunk = chunk * self.volume
        #    data[i] = chunk.astype(np.int16)

        if len(data) == 0:
            data = self._empty_audio_array
        return data, pyaudio.paContinue
