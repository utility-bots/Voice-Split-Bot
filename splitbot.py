from telethon.sync import TelegramClient, events
import os
import logging
import psycopg2
from config import *
import datetime
from pydub import AudioSegment
from pydub.utils import make_chunks
from time import time


dir_path = os.path.dirname(os.path.realpath(__file__))
user_activity = {}

client = TelegramClient(f'{dir_path}/audio_splitter.session', api_id, api_hash)

log_file_path = dir_path + '/split.log'

logging.basicConfig(
    # filename=log_file_path,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)


@client.on(events.NewMessage(func=lambda event: event.audio or event.voice or event.document))
async def handle_audio(event):
    user_id = event.chat_id
    if not (check_premium_time(user_id)):
        return await client.send_message(user_id,
                                         'شارژ اکانت شما به اتمام رسیده است برای شارژ به @MyTelegramBotsSupport پیام بدید.')
    current_time = time()
    LIMIT =1
    TIMEFRAME = 45

    if user_id not in user_activity:
        user_activity[user_id] = [current_time]
    else:
        user_activity[user_id].append(current_time)

        user_activity[user_id] = [t for t in user_activity[user_id] if
                                            current_time - t < TIMEFRAME]

        if len(user_activity[user_id]) > LIMIT:
            await client.send_message(user_id,"لطفا 1 دقیقه صبر کنید و فایل ها رو یکی یکی بعد از تکمیل پردازش بفرستید.")
            return
    try:
        file_id = event.message.audio.id
        file_name = event.message.audio.attributes[-1].file_name

    except AttributeError:
        try:
            file_id = event.message.voice.id
            file_name = str(file_id)
        except AttributeError:
            file_id = event.message.document.id
            file_name = str(file_id)

    await client.send_message(user_id, 'در حال پردازش لطفا چند دقیقه صبر کنید...')
    audio = await event.download_media(file=f'{dir_path}/audio_files/{user_id}/{file_id}', )

    format_types = ['mp3', 'ogg', 'm4a', 'aac', 'mav', 'flac', 'wma', 'amr', 'aiff', 'ape', 'oga']

    file_type = find_matching_string(file_name, format_types)
    audio_clip = AudioSegment.from_file(audio, format=file_type)

    segment_size = 10 * 60 * 1000

    audio_parts = make_chunks(audio_clip, segment_size)
    output_dir = os.path.join(dir_path, "audio_files", str(user_id))
    os.makedirs(output_dir, exist_ok=True)

    for i, part in enumerate(audio_parts):
        segment_file = f'{file_id}_{i}.mp3'
        segment_path = os.path.join(output_dir, segment_file)
        part.export(segment_path, format="mp3")
        await client.send_file(user_id, segment_path)
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


def find_matching_string(target_string, string_list):
    target_string = target_string.lower()
    for string in string_list:
        if string.lower() in target_string:
            return string
    return None


def remove_files_starting_with(directory, file_name):
    files = os.listdir(directory)

    for filename in files:
        if filename.startswith(file_name):
            file_path = os.path.join(directory, filename)
            try:
                os.remove(file_path)
            except OSError as e:
                pass


if __name__ == '__main__':
    client.start()
    client.run_until_disconnected()
