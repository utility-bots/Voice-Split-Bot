from telethon.sync import TelegramClient, events
import os
import logging
import psycopg2
from config import *
import datetime
from time import time
from ffmpeg.asyncio import FFmpeg
import audiosegment
import asyncio

# Get the directory path of the current file
dir_path = os.path.dirname(os.path.realpath(__file__))

# Dictionary to track user activity, latter using it for antiflood system.
user_activity = {}

# Initialize a Telegram client, obtain your api_id and api_hash from https://my.telegram.org/
client = TelegramClient(f'{dir_path}/support_account.session', api_id, api_hash)

# Define the path for the log file
log_file_path = dir_path + '/split.log'

# Configure logging settings
logging.basicConfig(
    filename=log_file_path,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)


async def ffmpeg_convert(audio, final_audio):
    ffmpeg = (FFmpeg().input(audio).output(final_audio))

    await ffmpeg.execute()


# Define a handler for handling incoming audio messages
@client.on(events.NewMessage(func=lambda event: event.audio or event.voice or event.document))
async def handle_audio(event):
    user_id = event.chat_id
    # Check if the user has premium time remaining, or you can skip this part and use it as free for all.
    if not (check_premium_time(user_id)):
        return await client.send_message(user_id,
                                         'شارژ اکانت شما به اتمام رسیده است برای شارژ به @MyTelegramBotsSupport پیام بدید.')

    # Record user activity for antiflood system, you can change LIMIT and TIMEFRAME as your needs.
    current_time = time()
    LIMIT = 1
    TIMEFRAME = 1

    if user_id not in user_activity:
        user_activity[user_id] = [current_time]
    else:
        user_activity[user_id].append(current_time)

        user_activity[user_id] = [t for t in user_activity[user_id] if
                                  current_time - t < TIMEFRAME]

        if len(user_activity[user_id]) > LIMIT:
            await client.send_message(user_id,
                                      "لطفا 1 دقیقه صبر کنید و فایل ها رو یکی یکی بعد از تکمیل پردازش بفرستید.")
            return
    try:
        file_id = event.message.audio.id
        # file_name = event.message.audio.attributes[-1].file_name
        file_name =str(file_id)
    except AttributeError:
        try:
            file_id = event.message.voice.id
            file_name = str(file_id)
        except AttributeError:
            file_id = event.message.document.id
            file_name = str(file_id)

    await client.send_message(user_id, 'در حال پردازش لطفا چند دقیقه صبر کنید...')

    # Download the audio file
    audio = await event.download_media(file=f'{dir_path}/audio_files/{user_id}/{file_name}', )
    final_audio = f'{dir_path}/audio_files/{user_id}/{file_name}.wav'
    #
    format_types = ['mp3', 'ogg', 'm4a', 'aac', 'mav', 'flac', 'wma', 'amr', 'aiff', 'ape', 'oga','wav']

    file_type = find_matching_string(file_name, format_types)


    try:
        await asyncio.wait_for(ffmpeg_convert(audio, final_audio), timeout=50)

    except Exception as e:
        print(f"Error processing audio: {e}")
        pass

    segment_duration = 10 * 60
    offset = 0
    segment_index = 0
    segment_paths = []
    audio = audiosegment.from_file(final_audio)
    audio_duration = audio.seg.duration_seconds
    while offset < audio_duration:
        segment_duration = min(segment_duration, audio_duration - offset)
        segment_end = min(offset + segment_duration, audio_duration)

        segment = audio[round(offset * 1000):round(segment_end * 1000)]

        segment_file = f"{file_name}_{segment_index}.mp3"
        segment_path = os.path.join(dir_path, "audio_files", str(user_id), segment_file)

        segment.export(segment_path, format="mp3")
        segment_paths.append(segment_path)
        segment_index += 1
        offset = segment_end
        await client.send_file(user_id, segment_path)

    output_dir = os.path.join(dir_path, "audio_files", str(user_id))
    os.makedirs(output_dir, exist_ok=True)

    remove_files_starting_with(f'{dir_path}/audio_files/{user_id}/', file_name)


def check_premium_time(user_id):
    con = psycopg2.connect(host=PGHOST, user=PGUSER, password=PGPASSWORD, database=PGDATABASE)
    cur = con.cursor()

    cur.execute('SELECT remaining_time FROM customers WHERE user_id = %s;', (user_id,))
    remaining_time = cur.fetchone()

    con.close()

    if remaining_time is not None:
        remain_time = remaining_time[0]
        if remain_time:
            current_date = datetime.datetime.today()
            if current_date <= remain_time:
                return True

    return False


# Function to find a matching string from a list in a target string for finding file format
def find_matching_string(target_string, string_list):
    target_string = target_string.lower()
    for string in string_list:
        if string.lower() in target_string:
            return string
    return None


# Function to remove files starting with a certain name in a directory
def remove_files_starting_with(directory, file_name):
    files = os.listdir(directory)

    for filename in files:
        if filename.startswith(file_name):
            file_path = os.path.join(directory, filename)
            try:
                os.remove(file_path)
            except OSError as e:
                pass


# Start the Telegram client
if __name__ == '__main__':
    client.start()
    client.run_until_disconnected()
