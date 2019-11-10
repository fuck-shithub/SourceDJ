import log_listener
import log_parser
import json
import gtts
import pyaudio
import subprocess
import wave
import io

try:
    with open("config.json") as f:
        config = json.load(f)
except FileNotFoundError:
    print("Config missing.")

loglistener = log_listener.LogListener(config["logfile"])
logparser = log_parser.LogParser(loglistener, chat_command_prefix=config["chat_command_prefix"])

p = pyaudio.PyAudio()

if config["loopback"]:
    def loopback_callback(in_data, frame_count, time_info, status):
        return in_data, pyaudio.paContinue


    loopback_stream = p.open(format=p.get_format_from_width(2),
                             channels=config["loopback_channels"],
                             rate=config["loopback_rate"],
                             input=True,
                             output=True,
                             stream_callback=loopback_callback,
                             input_device_index=config["loopback_input_device"],
                             output_device_index=config["loopback_output_device"])

    loopback_stream.start_stream()


tts_stream = None


@logparser.chat_command
def tts(event):
    tts_play(event.args)

    print(event.author, "->", event.command, event.args)


def tts_play(text):
    gtts.gTTS(text).save("tts.mp3")

    tts_audio = subprocess.Popen("ffmpeg -i tts.mp3 -loglevel panic -vn -f wav -c:a pcm_s16le pipe:1",
                                 stdout=subprocess.PIPE)

    wf = wave.open(io.BytesIO(tts_audio.stdout.read()))

    def tts_callback(in_data, frame_count, time_info, status):
        data = wf.readframes(frame_count)
        return data, pyaudio.paContinue

    global tts_stream
    tts_stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                        channels=wf.getnchannels(),
                        rate=wf.getframerate(),
                        output=True,
                        stream_callback=tts_callback,
                        output_device_index=config["output_device"])


logparser.start()
