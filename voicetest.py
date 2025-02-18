import onnxruntime as ort
import numpy as np
import sounddevice as sd

# Load the pre-trained ONNX model
model_path = "glados.onnx"
session = ort.InferenceSession(model_path)

def synthesize_speech(text):

    for input_meta in session.get_inputs():
        print(f"Input name: {input_meta.name}, Shape: {input_meta.shape}, Type: {input_meta.type}")
    # Preprocess the input (depending on your model's expected format)
    input_data = np.array([ord(c) for c in text], dtype=np.float32).reshape(1, -1)

    # Run the model
    outputs = session.run(None, {"input_text": input_data})

    # Convert output to audio (assuming model outputs waveform data)
    audio = np.array(outputs[0], dtype=np.float32)

    # Play audio
    sd.play(audio, samplerate=22050)  # Adjust sample rate as needed
    sd.wait()

# Example usage
synthesize_speech("Hello. This is a test of the GLaDOS voice assistant.")