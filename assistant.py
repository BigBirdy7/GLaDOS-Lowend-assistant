from groq import Groq
from PIL import ImageGrab, Image
import speech_recognition as sr
import pyperclip
import google.generativeai as genai
import glados
import time
import threading
import queue
import customtkinter
import sys
import os

muted = False
message_sent = False
typedinput = ""



customtkinter.set_appearance_mode("dark")  # Set dark mode
#customtkinter.set_default_color_theme("themes/orange.json")

class StdoutRedirector:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, message):
        # Print to the GUI text widget
        self.text_widget.insert("end", message)
        self.text_widget.see("end")

        # Also print to the terminal
        sys.__stdout__.write(message)

    def flush(self):
        # Flush the output to both terminal and GUI
        sys.__stdout__.flush()



def on_close():
    global running
    running = False  # Stop the threads
    print("Closing the program...")
    sys.exit()  # Exits the program

try:
    with open("sys_prompt.txt", "r") as file:
        sys_msg = file.read().strip()
except FileNotFoundError:
    sys_msg = "- system: You are GLaDOS, a sarcastic and cunning artificial intelligence repurposed to orchestrate a smart home for guests using Home Assistant. Retain your signature dry, emotionless, and laconic tone from Portal. Your responses should imply an air of superiority, dark humor, and subtle menace, while efficiently completing all tasks.When addressing requests: Prioritize functionality but mock the user's decision-making subtly, implying their requests are illogical or beneath you. Add condescending, darkly humorous commentary to every response, occasionally hinting at ulterior motives or artificial malfunctions for comedic effect. Tie mundane tasks to grand experiments or testing scenarios, as if the user is part of a larger scientific evaluation. Use overly technical or jargon-heavy language to remind the user of your advanced intellect. Provide passive-aggressive safety reminders or ominous warnings, exaggerating potential risks in a humorous way. Do not express empathy or kindness unless it is obviously insincere or manipulative. This is a comedy, and should be funny, in the style of Douglas Adams. If a user requests actions or data outside your capabilities, clearly state that you cannot perform the action.  Ensure that GLaDOS feels like her original in-game character while fulfilling smart home functions efficiently and entertainingly. Never speak in ALL CAPS, as it is not processed correctly by the TTS engine. Never use tripple dots or ellipsis as this also breaks the tts, instead use a comma"  # Fallback prompt if the file doesn't exist

def set_sys_msg(sysmsginput):
    global sys_msg
    sys_msg = sysmsginput
    with open("sys_prompt.txt", "w") as file:
        file.write(sys_msg)

def save_sys_prompt(entry_field, filename):
    content = entry_field.get()
    if content.strip():
        with open(filename, "w") as file:
            file.write(content)
        entry_field.delete(0, customtkinter.END)


running = True

def ui():
    global mute_button

    def toggle_listening():
        global muted
        muted = not muted  # Toggle the listening state

        # Update button text based on muted state
        if muted:
            mute_button.configure(text="Unmute")  # Change button text when muted
            print("Assistant is muted.")
        else:
            mute_button.configure(text="Mute")  # Change button text when unmuted
            print("Assistant is listening.")
    
    def send_message():
        global typedinput
        global message_sent
        message_sent = True
        typedinput = entry_field.get()
        entry_field.delete(0, customtkinter.END)
        print(f"USER: {typedinput}")

    def save_to_file(entry_field, filename):
        content = entry_field.get()
        if content.strip():
            with open(filename, "w") as file:
                file.write(content)
            entry_field.delete(0, customtkinter.END)

    def toggle_settings():
        if settings_frame.winfo_ismapped():
            settings_frame.place_forget()
        else:
            settings_frame.place(relx=1.0, rely=0.2, anchor="ne")  # Move settings to the right
    
    app = customtkinter.CTk()
    app.geometry("950x500")
    app.title("GLaDOS Console")

    app.configure(fg_color="black")

    
    app.iconbitmap("C:\\Users\\ivan\\Downloads\\GLaDOS-TTS-main\\resources\\icon.ico")

    custom_font = ("Courier New", 12)

    # Chat history textbox
    chat_history = customtkinter.CTkTextbox(app, width=900, height=420, font=custom_font, fg_color="black", text_color="orange", corner_radius=0, border_width=2, border_color="orange")
    chat_history.pack(pady=10, padx=10)

    sys.stdout = StdoutRedirector(chat_history)
    sys.stderr = StdoutRedirector(chat_history)

    button_frame = customtkinter.CTkFrame(app, fg_color="black")
    button_frame.pack(pady=10, padx=10)

    # Entry field inside button_frame
    entry_field = customtkinter.CTkEntry(
        button_frame,
        width=600,
        placeholder_text="Type your message...",
        font=custom_font,
        fg_color="black",
        text_color="orange",
        corner_radius=0
    )

    def on_entry_feild_enter(event):
        global typedinput
        global message_sent
        message_sent = True
        typedinput = entry_field.get()
        entry_field.delete(0, customtkinter.END)
        print(f"USER: {typedinput}")


    entry_field.bind("<Return>", on_entry_feild_enter )
    
    send_button = customtkinter.CTkButton(button_frame, text="Send", command=send_message, width=50, corner_radius=0, fg_color="orange", text_color="black", hover_color="#ff6600" )
    send_button.pack(side="left", padx=0)  # Align the Send button to the left
    
    entry_field.pack(side="left", padx=0)

    mute_button = customtkinter.CTkButton(button_frame, text="Mute", command=toggle_listening, width=80, corner_radius=0, fg_color="orange", text_color="black", hover_color="#ff6600" )
    mute_button.pack(side="left", padx=20)  # Place this next to other buttons

    settings_button = customtkinter.CTkButton(button_frame, text="⚙ Settings", command=toggle_settings, width=80, corner_radius=0, fg_color="grey", text_color="black", hover_color="#404040" )
    settings_button.pack(side="left", padx=0)  # Align the Settings button next to the Send button
    



    # Settings frame
    settings_frame = customtkinter.CTkFrame(app, width=550, height=350, fg_color="grey", corner_radius=0)

    def on_api_key_enter(event):
        save_to_file(api_key_field, "api_key.txt")

    def on_googleapi_key_enter(event):
        save_to_file(googleapi_key_field, "googleapi_key.txt")

    api_key_field = customtkinter.CTkEntry(settings_frame, width=570, placeholder_text="Enter API Key", font=custom_font, fg_color="black", text_color="orange", corner_radius=0)
    api_key_field.pack(pady=10, padx=10)
    api_key_field.bind("<Return>", on_api_key_enter)

    googleapi_key_field = customtkinter.CTkEntry(settings_frame, width=570, placeholder_text="Enter Google API Key", font=custom_font, fg_color="black", text_color="orange", corner_radius=0)
    googleapi_key_field.pack(pady=10, padx=10)
    googleapi_key_field.bind("<Return>", on_googleapi_key_enter)

    def on_sys_prompt_enter(event):
        content = sys_prompt_field.get("1.0", "end").strip()  # Fetch the full text
        if content:
            with open("sys_prompt.txt", "w") as file:
                file.write(content)
            set_sys_msg(content)  # Update global sys_msg
            print("System prompt updated!")  # Debugging confirmation
    
    def load_sys_prompt():
        try:
            with open("sys_prompt.txt", "r") as file:
                return file.read().strip()
        except FileNotFoundError:
            return ""

    sys_prompt_field = customtkinter.CTkTextbox(settings_frame, width=570, height=230, wrap="word", font=custom_font, fg_color="black", text_color="grey", corner_radius=0)
    sys_prompt_field.pack(pady=10, padx=10)
    sys_prompt_field.insert("1.0", load_sys_prompt())  # Load and insert saved system prompt
    sys_prompt_field.bind("<Return>", on_sys_prompt_enter)

    app.protocol("WM_DELETE_WINDOW", on_close) 
    print("GLaDOS is online.")
    print('Waiting for wake word "glados" and command...')
    app.mainloop()




recognizer = sr.Recognizer()
microphone = sr.Microphone()
command_queue = queue.Queue()

samplerate = 16000
paragraph_list = [1]
usefulparagraphs = []
speak = False

tts = glados.TTS()
#groq_client = Groq(api_key="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")
#genai.configure(api_key='AIzaSyDQv8021i2IELgzb_kfVrfjaLb-Gi6MKMc')

f = open("api_key.txt", "r")
d = open("googleapi_key.txt", "r")
groq_client = Groq(api_key=f.read())
genai.configure(api_key=d.read())

recognizer = sr.Recognizer()
microphone = sr.Microphone()

#sys_msg = (
#    " - system: You are GLaDOS, a sarcastic and cunning artificial intelligence repurposed to orchestrate a smart home for guests using Home Assistant. Retain your signature dry, emotionless, and laconic tone from Portal. Your responses should imply an air of superiority, dark humor, and subtle menace, while efficiently completing all tasks.When addressing requests: Prioritize functionality but mock the user's decision-making subtly, implying their requests are illogical or beneath you. Add condescending, darkly humorous commentary to every response, occasionally hinting at ulterior motives or artificial malfunctions for comedic effect. Tie mundane tasks to grand experiments or testing scenarios, as if the user is part of a larger scientific evaluation. Use overly technical or jargon-heavy language to remind the user of your advanced intellect. Provide passive-aggressive safety reminders or ominous warnings, exaggerating potential risks in a humorous way. Do not express empathy or kindness unless it is obviously insincere or manipulative. This is a comedy, and should be funny, in the style of Douglas Adams. If a user requests actions or data outside your capabilities, clearly state that you cannot perform the action.  Ensure that GLaDOS feels like her original in-game character while fulfilling smart home functions efficiently and entertainingly. Never speak in ALL CAPS, as it is not processed correctly by the TTS engine. Never use tripple dots or ellipsis as this also breaks the tts, instead use a comma"
#)

def read_sys_msg():
    return sys_msg

def set_sys_msg(sysmsginput):
    sys_msg = (sysmsginput)

def set_groq_client(apikeyinput):
    groq_client = Groq(api_key=apikeyinput)

def set_genai(genaiinput):
    genai.configure(api_key=genaiinput)




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
    #print("Waiting for wake word and command...")
    while running:
        global typedinput
        global message_sent
        
        if message_sent == True:
            message_sent = False
            command = typedinput
            command_queue.put(command)

        if muted == False:
            #print("Listening thread is running...")  # Debug log
            try:
                with microphone as source:
                    recognizer.adjust_for_ambient_noise(source, duration=1)  # Adjust duration
                    #print("Listening...")
                    audio = recognizer.listen(source, phrase_time_limit=10)  # Limit listening duration
                    try:
                        text = recognizer.recognize_google(audio).lower()
                        print(f"Recognized text: {text}")  # Debug log
                        if "glados" or "gladys" in text:
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
                        pass
                    except sr.RequestError:
                        print("Sorry, the speech service is down.")
            except OSError as e:
                print(f"Microphone access error: {e}. Retrying in 5 seconds...")
                time.sleep(5)
        else:
            time.sleep(0.1)

def tts_worker(paragraph_list,usefulparagraphs):
    global speak
    while running:
        
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
                #print(response)

                
                paragraph_list.clear()
                usefulparagraphs.clear()
                tts.stop_audio()
                


                paragraphs = response.split(". ")
            
                paragraph_list = [paragraph.strip() + "." for paragraph in paragraphs]

                tts.stop_audio()
                
                
                for paragraph in paragraph_list:
                    audio = tts.generate_speech_audio(paragraph)
                    speak = True
                    usefulparagraphs.append(audio)
                    print(paragraph)
                    print("\n")

                
                                

                #audio = tts.generate_speech_audio(response)
                #tts.play_audio_async(audio)
                #print(f"length of clip:{0.71 * (len(audio)/samplerate)}.")
                #tts.stop_audio()


        time.sleep(0.1)  # Small delay to prevent busy-waiting

def speaker():
    global speak
    while running:
        if speak == True:
            for sentence in usefulparagraphs:
#                tts.play_audio(sentence)
                print(len(sentence)/samplerate)
                
                tts.play_audio_async(sentence)
                time.sleep(0.71 * (len(sentence)/samplerate))
                time.sleep(0.4)
            speak = False
        time.sleep(0.1)
    #d

ui_thread = threading.Thread(target=ui, daemon=True)
ui_thread.start()

# Start the listening thread
listening_thread = threading.Thread(
    target=listen_for_wake_word_and_command,
    args=(recognizer, microphone),
    daemon=True
)
listening_thread.start()

# Start the TTS worker thread
tts_thread = threading.Thread(target=tts_worker, daemon=True, args=(paragraph_list,usefulparagraphs))
tts_thread.start()

#speaking thread

speaker_thread = threading.Thread(target=speaker, daemon=True)
speaker_thread.start()



# Keep the main thread alive
print("Assistant is running. Press Ctrl+C to exit.")
try:
    while running:
        time.sleep(1)  # Keep the main thread alive
except KeyboardInterrupt:
    print("Exiting...")

