import base64

def test_encode_audio_file_to_base64():
    file_path = r"C:\Users\justa\IdeaProjects\KneoBroadcaster\Echoes_of_the_Lost.mp3"
    try:
        # Read the binary content of the file
        with open(file_path, "rb") as audio_file:
            audio_data = audio_file.read()

        # Encode the binary content in Base64
        encoded_audio = base64.b64encode(audio_data).decode("utf-8")

        # Print or return the encoded string for verification
        print("Encoded Base64 Audio:", encoded_audio)
        return encoded_audio

    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except Exception as e:
        print(f"Error encoding file: {e}")

# Run the test
encoded_audio = test_encode_audio_file_to_base64()

with open("encoded_audio.txt", "w") as f:
    f.write(encoded_audio)
