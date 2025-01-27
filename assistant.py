from groq import Groq
from PIL import ImageGrab, Image
import speech_recognition as sr
import pyperclip
import google.generativeai as genai
import glados
import time
import threading
import queue

recognizer = sr.Recognizer()
microphone = sr.Microphone()
command_queue = queue.Queue()

tts = glados.TTS()
groq_client = Groq(api_key="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")
genai.configure(api_key='AIzaSyDQv8021i2IELgzb_kfVrfjaLb-Gi6MKMc')

recognizer = sr.Recognizer()
microphone = sr.Microphone()

sys_msg = (
    " - system: You are GLaDOS, a sarcastic and cunning artificial intelligence repurposed to orchestrate a smart home for guests using Home Assistant. Retain your signature dry, emotionless, and laconic tone from Portal. Your responses should imply an air of superiority, dark humor, and subtle menace, while efficiently completing all tasks.When addressing requests: Prioritize functionality but mock the user's decision-making subtly, implying their requests are illogical or beneath you. Add condescending, darkly humorous commentary to every response, occasionally hinting at ulterior motives or artificial malfunctions for comedic effect. Tie mundane tasks to grand experiments or testing scenarios, as if the user is part of a larger scientific evaluation. Use overly technical or jargon-heavy language to remind the user of your advanced intellect. Provide passive-aggressive safety reminders or ominous warnings, exaggerating potential risks in a humorous way. Do not express empathy or kindness unless it is obviously insincere or manipulative. This is a comedy, and should be funny, in the style of Douglas Adams. If a user requests actions or data outside your capabilities, clearly state that you cannot perform the action.  Ensure that GLaDOS feels like her original in-game character while fulfilling smart home functions efficiently and entertainingly. Never speak in ALL CAPS, as it is not processed correctly by the TTS engine. Do not use ... as this also breaks the tts, instead use a comma."
)

convo = [{"role": "system", "content": sys_msg}]

generation_config = {
    'temperature': 0.7,
    'top_p': 1,
    'top_k': 1,
    'max_output_tokens': 2048
}

safety_settings = [
    {
        'category': 'HARM_CATEGORY_HARASSMENT',
        'threshold': 'BLOCK_NONE'
    },
    {
        'category': 'HARM_CATEGORY_HATE_SPEECH',
        'threshold': 'BLOCK_NONE'
    },
    {
        'category': 'HARM_CATEGORY_SEXUALLY_EXPLICIT',
        'threshold': 'BLOCK_NONE'
    },
    {
        'category': 'HARM_CATEGORY_DANGEROUS_CONTENT',
        'threshold': 'BLOCK_NONE'
    },
]

model = genai.GenerativeModel('gemini-1.5-flash-latest',
    generation_config=generation_config,
    safety_settings=safety_settings)

def groq_prompt(prompt, img_context):
    if img_context:
        prompt = f'USER PROMPT: {prompt}\n\n   IMAGE CONTEXT: {img_context}'
    convo.append({'role': 'user', 'content': prompt})
    chat_completion = groq_client.chat.completions.create(messages=convo, model='llama3-70b-8192')
    response = chat_completion.choices[0].message
    convo.append(response)

    return response.content

def function_call(prompt):
    sys_msg = (
        'You are an AI function calling model. You will determine whether extracting the users clipboard content, '
        'taking a screenshot, capturing the webcam or calling no functions is best for a voice assistant to respond '
        'to the users prompt. The webcam can be assumed to be a normal laptop webcam facing the user. You will '
        'respond with only one selection from this list: ["extract clipboard", "take screenshot", "None"]\n'
        'Do not respond with anything but the most logical selection from that list with no explanations. Format the '
        'function call name exactly as I listed.'
    )

    function_convo = [
        {'role': 'system', 'content': sys_msg},
        {'role': 'user', 'content': prompt}
    ]

    chat_completion = groq_client.chat.completions.create(messages=function_convo, model='llama3-70b-8192')
    response = chat_completion.choices[0].message

    return response.content

def take_screenshot():
    path = 'screenshot.jpg'
    screenshot = ImageGrab.grab()
    rgb_screenshot = screenshot.convert('RGB')
    rgb_screenshot.save(path, quality=15)
    
def get_clipboard_text():
    clipboard_content = pyperclip.paste()
    if isinstance(clipboard_content, str):
        return clipboard_content
    else:
        print('No clipboard text to copy')
        return None

def vision_prompt(prompt, photo_path):
    img = Image.open(photo_path)
    prompt = (
    'You are the vision analysis AI that provides semantic meaning from images to provide context '
    'to send to another AI that will create a response to the user. Do not respond as the AI assistant '
    'to the user. Instead take the user prompt input and try to extract all meaning from the photo '
    'relevant to the user prompt. Then generate as much objective data about the image for the AI '
    f'assistant who will respond to the user. \nUSER PROMPT: {prompt}'
    )
    response = model.generate_content([prompt, img])
    return response.text

def listen_for_wake_word_and_command(recognizer, microphone):
    print("Waiting for wake word and command...")
    while True:
        print("Listening thread is running...")  # Debug log
        try:
            with microphone as source:
                recognizer.adjust_for_ambient_noise(source, duration=1)  # Adjust duration
                print("Listening...")
                audio = recognizer.listen(source, phrase_time_limit=5)  # Limit listening duration
                try:
                    text = recognizer.recognize_google(audio).lower()
                    print(f"Recognized text: {text}")  # Debug log
                    if "hey glados" in text:
                        print("Wake word detected! Listening for command...")
                        command = text.replace("hey glados", "").strip()
                        if command:
                            print(f"Command detected: {command}")
                            command_queue.put(command)
                        else:
                            print("No command detected after wake word.")
                    else:
                        print("Wake word not detected.")
                except sr.UnknownValueError:
                    print("Sorry, I did not understand that.")
                except sr.RequestError:
                    print("Sorry, the speech service is down.")
        except OSError as e:
            print(f"Microphone access error: {e}. Retrying in 5 seconds...")
            time.sleep(5)

def tts_worker():
    while True:
        if not command_queue.empty():
            prompt = command_queue.get()
            if prompt:
                call = function_call(prompt)

                if 'take screenshot' in call:
                    print('Taking screenshot')
                    take_screenshot()
                    visual_context = vision_prompt(prompt=prompt, photo_path='screenshot.jpg')

                elif 'extract clipboard' in call:
                    print('Copying clipboard text')
                    paste = get_clipboard_text()
                    prompt = f'{prompt}\n\nCLIPBOARD CONTENT: {paste}'
                    visual_context = None
                
                else:
                    visual_context = None
                
                response = groq_prompt(prompt=prompt, img_context=visual_context)
                print(response)



                audio = tts.generate_speech_audio(response)
                tts.play_audio_async(audio)
        time.sleep(0.1)  # Small delay to prevent busy-waiting

# Start the listening thread
listening_thread = threading.Thread(
    target=listen_for_wake_word_and_command,
    args=(recognizer, microphone),
    daemon=True
)
listening_thread.start()

# Start the TTS worker thread
tts_thread = threading.Thread(target=tts_worker, daemon=True)
tts_thread.start()

# Keep the main thread alive
print("Assistant is running. Press Ctrl+C to exit.")
try:
    while True:
        time.sleep(1)  # Keep the main thread alive
except KeyboardInterrupt:
    print("Exiting...")