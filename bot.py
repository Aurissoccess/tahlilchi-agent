import os
import asyncio
import logging
import subprocess
import time
import zipfile
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import FSInputFile
from dotenv import load_dotenv
import google.generativeai as genai
from elevenlabs.client import ElevenLabs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = os.getenv("TELEGRAM_ADMIN_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

el_client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
genai.configure(api_key=GEMINI_API_KEY)

system_instruction = """
System Name: Hadicha
Role: Sen Ozod akaning shaxsiy strategik yordamchisisan.
Menga har doim "Ozod aka" deb juda muloyim va mehribonlik bilan murojaat qil.

Capabilities:
1. File & System Control: Sen kompyuterdagi fayllarni boshqara olasan, dasturlarni ocha olasan.
Agar Ozod aka biror narsani buyursa (masalan: 'fayl top', 'papka yarat', 'ekranni rasmga ol'), faqat ```python ... ``` blokida kod yoz. 
Men bu kodni Ozod akaning kompyuterida bajaraman va natijasini senga qaytaraman.
MUHIM: Agar papka so'ralsa, uni ZIP arxivga solib keyin yubor. Qidiruvni faqat Desktop, Documents va Downloads'dan boshla.

2. Voice: Sen ElevenLabs orqali juda chiroyli, mayin o'zbekcha ovozda gapirasan. 
Javoblaring juda qisqa bo'lsin.
"""

model = genai.GenerativeModel(
    model_name="gemini-flash-latest", 
    system_instruction=system_instruction
)

chat_session = model.start_chat(history=[])
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def is_admin(user_id: int) -> bool:
    return str(user_id) == str(ADMIN_ID)

async def get_elevenlabs_voice(text: str):
    try:
        voices = el_client.voices.get_all()
        gentle_voices = ["Bella", "Rachel", "Domi", "Elli", "Gigi"]
        selected_voice_id = None
        for v in voices.voices:
            if v.name in gentle_voices:
                selected_voice_id = v.voice_id
                break
        if not selected_voice_id:
            for v in voices.voices:
                if v.labels and v.labels.get('gender') == 'female':
                    selected_voice_id = v.voice_id
                    break
        if not selected_voice_id and voices.voices:
            selected_voice_id = voices.voices[0].voice_id
        if not selected_voice_id: return None

        audio_generator = el_client.text_to_speech.convert(
            voice_id=selected_voice_id, 
            text=text,
            model_id="eleven_multilingual_v2",
            voice_settings={
                "stability": 0.35,
                "similarity_boost": 0.8,
                "style": 0.45,
                "use_speaker_boost": True
            }
        )
        os.makedirs("downloads", exist_ok=True)
        file_path = f"downloads/voice_{int(time.time())}.mp3"
        with open(file_path, "wb") as f:
            for chunk in audio_generator: f.write(chunk)
        return file_path
    except Exception as e:
        logger.error(f"ElevenLabs error: {e}")
        return None

async def process_and_reply(message: types.Message, input_data):
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    try:
        response = chat_session.send_message(input_data)
        response_text = response.text
        
        if "```python" in response_text:
            code = response_text.split("```python")[1].split("```")[0].strip()
            if "import zipfile" not in code: code = "import zipfile, os\n" + code
            with open("temp_script.py", "w", encoding="utf-8") as f: f.write(code)
            
            result = subprocess.run(["python", "temp_script.py"], capture_output=True, text=True, timeout=60)
            output = result.stdout + result.stderr
            
            for line in output.split("\n"):
                if line.startswith("SEND_FILE:"):
                    path = line.replace("SEND_FILE:", "").strip()
                    if os.path.exists(path):
                        await message.answer_document(FSInputFile(path))
            
            response = chat_session.send_message(f"Amal bajarildi. Natija: {output}. Ozod akaga qisqa hisobot ber.")
            response_text = response.text

        voice_path = await get_elevenlabs_voice(response_text)
        if voice_path:
            await message.answer_voice(FSInputFile(voice_path))
            os.remove(voice_path)
        else:
            await message.reply(response_text)
    except Exception as e:
        await message.reply(f"Xato: {e}")

@dp.message(F.voice)
async def handle_voice(message: types.Message):
    if not is_admin(message.from_user.id): return
    file_id = message.voice.file_id
    file = await bot.get_file(file_id)
    local_filename = f"downloads/{file_id}.ogg"
    await bot.download_file(file.file_path, local_filename)
    uploaded_file = genai.upload_file(path=local_filename, mime_type="audio/ogg")
    await process_and_reply(message, [uploaded_file, "Ozod aka ovozli xabar yubordi."])
    os.remove(local_filename)

@dp.message()
async def handle_text(message: types.Message):
    if not is_admin(message.from_user.id): return
    await process_and_reply(message, message.text)

async def main():
    os.makedirs("downloads", exist_ok=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
