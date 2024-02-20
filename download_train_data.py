from telethon import TelegramClient
import os
from config import *
# Replace with your own API ID, API HASH, and the phone number
api_id = api_id
api_hash = api_hash
name = '+31649726370'
dir_path = os.path.dirname(os.path.realpath(__file__))

# Replace with the channel username or link
channel_username = -1002016956419
# Path to the folder where files will be saved
download_path = 'downloads/'

with TelegramClient(name, api_id, api_hash) as client:
    async def download_files():
        # Get the channel entity
        entity = await client.get_entity(channel_username)

        # Get all messages in the channel
        async for message in client.iter_messages(entity):

            try:
                file_id = message.audio.id
                file_name = str(file_id)
            except AttributeError:
                try:
                    file_id = message.voice.id
                    file_name = str(file_id)
                except AttributeError:
                    try:
                        file_id = message.document.id
                        file_name = str(file_id)
                    except AttributeError:
                        # If no suitable attribute found, continue to the next message
                        continue

            # Download the audio file
            audio = await client.download_media(message,file=f'{dir_path}/train/{message.message}')
            final_audio = f'{dir_path}/train/{file_name}.wav'
            # if message.media:
            #     # Check if the message has a document
            #     if message.document:
            #         file = message.document
            #         # Access the attributes to get file name
            #         file_name = file.attributes[0].file_name
            #         # Download the file
            #         await client.download_media(message, file=download_path + file_name)

    client.loop.run_until_complete(download_files())
