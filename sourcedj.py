import log_listener
import log_parser
import audio_queue
import json
import gtts
import pyaudio
import youtube_dl
import os
import traceback

try:
    with open("config.json") as f:
        config = json.load(f)
except FileNotFoundError:
    print("Config missing.")

loglistener = log_listener.LogListener(config["logfile"])
logparser = log_parser.LogParser(loglistener, chat_command_prefix=config["chat_command_prefix"])

pa = pyaudio.PyAudio()
tts_audio_queue = audio_queue.AudioQueue(pa, output_device=config["output_device"], frames_per_buffer=config["frames_per_buffer"], volume=config["tts_volume"])
ydl_audio_queue = audio_queue.AudioQueue(pa, output_device=config["output_device"], frames_per_buffer=config["frames_per_buffer"], volume=config["ydl_volume"])

if config["loopback"]:
    def loopback_callback(in_data, frame_count, time_info, status):
        return in_data, pyaudio.paContinue

    loopback_stream = pa.open(format=pa.get_format_from_width(2),
                              channels=config["loopback_channels"],
                              rate=config["loopback_rate"],
                              input=True,
                              output=True,
                              stream_callback=loopback_callback,
                              input_device_index=config["loopback_input_device"],
                              output_device_index=config["loopback_output_device"],
                              frames_per_buffer=config["loopback_frames_per_buffer"])

    loopback_stream.start_stream()


@logparser.chat_command
def tts(event):
    print(event.author, "->", event.command, event.args)

    try:
        gtts.gTTS(event.args).save("tts.mp3")
    except AssertionError:
        pass
    except Exception:
        traceback.print_exc()
    else:
        tts_audio_queue.add_to_queue("tts.mp3")


@logparser.chat_command
def play(event):
    print(event.author, "->", event.command, event.args)

    ydl = youtube_dl.YoutubeDL(config["youtube_dl_options"])
    with ydl:
        video_info = ydl.extract_info(event.args, download=True)
        try:
            if video_info["_type"] == "playlist":
                filename = os.path.join("youtube-dl", video_info["entries"][0]["id"])
            else:
                filename = os.path.join("youtube-dl", video_info["id"])
        except KeyError:
            filename = os.path.join("youtube-dl", video_info["id"])

    ydl_audio_queue.add_to_queue(filename)


logparser.start()
