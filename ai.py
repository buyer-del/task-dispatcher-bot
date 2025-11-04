# ============================================
#  🔊 Аудіо → Google Speech-to-Text (українська)
#  🖼️ Зображення → EasyOCR (українська)
# ============================================

from google.cloud import speech
from pydub import AudioSegment
import easyocr
from PIL import Image
import numpy as np
import io
import os

# --- Google Speech-to-Text ---
def transcribe_audio(file_path: str) -> str:
    """
    Розпізнає українську мову з аудіо через Google Speech-to-Text.
    Підтримує різні формати (.ogg, .mp3, .m4a, .wav тощо).
    """
    try:
        # 1. Конвертуємо будь-яке аудіо у WAV 16kHz mono
        wav_path = file_path + ".wav"
        sound = AudioSegment.from_file(file_path)
        sound = sound.set_frame_rate(16000).set_channels(1)
        sound.export(wav_path, format="wav")

        # 2. Завантажуємо аудіо у пам'ять
        with io.open(wav_path, "rb") as audio_file:
            content = audio_file.read()

        # 3. Налаштування клієнта Speech API
        client = speech.SpeechClient()
        audio = speech.RecognitionAudio(content=content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code="uk-UA",
            enable_automatic_punctuation=True,
        )

        # 4. Відправляємо запит до Google Speech-to-Text
        response = client.recognize(config=config, audio=audio)

        # 5. Отримуємо результат
        if not response.results:
            return "(мову не розпізнано)"

        text = " ".join([result.alternatives[0].transcript for result in response.results])
        return text.strip()

    except Exception as e:
        return f"Помилка транскрипції: {e}"


# --- EasyOCR (розпізнавання тексту з картинок) ---
_reader = easyocr.Reader(["uk"], gpu=False)

def extract_text_from_image(image_path: str) -> str:
    """
    Розпізнає текст українською з зображення (без Tesseract).
    """
    try:
        img = np.array(Image.open(image_path))
        results = _reader.readtext(img, detail=0)
        text = " ".join(results).strip()
        return text or "(текст не розпізнано)"
    except Exception as e:
        return f"Помилка OCR: {e}"
