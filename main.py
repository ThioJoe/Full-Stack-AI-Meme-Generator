import openai
import json
import re
from base64 import b64decode
from PIL import Image, ImageDraw, ImageFont
import io

# Some Models:
# gpt-4
# gpt-3.5-turbo-16k

model = "gpt-4"
temperature = 1

basicInstructions = r'You will create funny memes.'

# ----------------------------------------------

formatInstructions = r'You are a meme generator with the following formatting instructions. Each meme will consist of text that will appear at the top, and an image to go along with it. The user will send you a message with a general theme or concept on which you will base the meme. The user may choose to send you a text saying something like "anything" or "whatever you want", which you should not take literally, but take to mean they wish for you to come up with something yourself.  In any case, you will respond with two things: First, the text of the meme that will be displayed in the final meme. Second, some text that will be used as an image prompt for an AI image generator to generate an image to also be used as part of the meme. You must respond only in the format as described next, because your response will be parsed, so it is important it conforms to the format. The first line of your response should be: "Meme Text: " followed by the meme text. The second line of your response should be: "Image Prompt: " followed by the image prompt text. -- Now that you know the format instructions, the following will be your instructions for the overall approach you should take to creating the memes: '
systemPrompt = formatInstructions + basicInstructions

# Load API key from key.txt file
def load_api_key(filename="key.txt"):
    try:
        with open(filename, "r", encoding='utf-8') as key_file:
            for line in key_file:
                stripped_line = line.strip()
                if not stripped_line.startswith('#') and stripped_line != '':
                    api_key = stripped_line
                    break
        return api_key
    except FileNotFoundError:
        print("\nAPI key file not found. Please create a file named 'key.txt' in the same directory as this script and paste your API key in it.\n")
        exit()
openai.api_key = load_api_key()


def parse_meme(message):
    pattern = r"Meme Text: (.*?)\nImage Prompt: (.*?)$"
    match = re.search(pattern, message, re.DOTALL)

    if match:
        return {
            "meme_text": match.group(1),
            "image_prompt": match.group(2)
        }

    else:
        return None
    

def send_and_receive_message(userMessage, conversationTemp, temperature=0.5):
    # Prepare to send request along with context by appending user message to previous conversation
    conversationTemp.append({"role": "user", "content": userMessage})
    
    print("Sending request to write meme...")
    chatResponse = openai.ChatCompletion.create(
        model=model,
        messages=conversationTemp,
        temperature=temperature
        )

    chatResponseMessage = chatResponse.choices[0].message.content
    chatResponseRole = chatResponse.choices[0].message.role

    #print("\n" + chatResponseMessage)
    #conversationTemp.append({"role": chatResponseRole, "content": chatResponseMessage})

    return chatResponseMessage


def create_meme(image_path, top_text, min_scale=0.06, buffer_scale=0.04, font_scale=1):
    print("Creating meme image...")
    
    # Load the image
    image = Image.open(image_path)

    # Calculate buffer size based on buffer_scale
    buffer_size = int(buffer_scale * image.width)

    # Get a drawing context
    d = ImageDraw.Draw(image)

    # Split the text into words
    words = top_text.split()

    # Initialize the font size and wrapped text
    font_size = int(font_scale * image.width)
    fnt = ImageFont.truetype('arial.ttf', font_size)
    wrapped_text = top_text

    # Try to fit the text on a single line by reducing the font size
    while d.textbbox((0,0), wrapped_text, font=fnt)[2] > image.width - 2 * buffer_size:
        font_size *= 0.9  # Reduce the font size by 10%
        if font_size < min_scale * image.width:
            # If the font size is less than the minimum scale, wrap the text
            lines = [words[0]]
            for word in words[1:]:
                new_line = (lines[-1] + ' ' + word).rstrip()
                if d.textbbox((0,0), new_line, font=fnt)[2] > image.width - 2 * buffer_size:
                    lines.append(word)
                else:
                    lines[-1] = new_line
            wrapped_text = '\n'.join(lines)
            break
        fnt = ImageFont.truetype('arial.ttf', int(font_size))

    # Calculate the bounding box of the text
    textbbox_val = d.multiline_textbbox((0,0), wrapped_text, font=fnt)

    # Create a white band for the top text, with a buffer equal to 10% of the font size
    band_height = textbbox_val[3] - textbbox_val[1] + int(font_size * 0.1) + 2 * buffer_size
    band = Image.new('RGBA', (image.width, band_height), (255,255,255,255))

    # Draw the text on the white band
    d = ImageDraw.Draw(band)

    # The midpoint of the width and height of the bounding box
    text_x = band.width // 2 
    text_y = band.height // 2

    d.multiline_text((text_x, text_y), wrapped_text, font=fnt, fill=(0,0,0,255), anchor="mm", align="center")

    # Create a new image and paste the band and original image onto it
    new_img = Image.new('RGBA', (image.width, image.height + band_height))
    new_img.paste(band, (0,0))
    new_img.paste(image, (0, band_height))

    # Save the result to a file
    new_img.save('meme.png')
    

# ----------------------------------------------

conversation = [{"role": "system", "content": systemPrompt}]

while True:
    userEnteredPrompt = input("\n Enter a meme subject or concept: ")
    if userEnteredPrompt:
        print("----------------------------------------------------------------------------------------------------")
        chatResponse = send_and_receive_message(userEnteredPrompt, conversation, temperature)
        break

# Take chat message and convert to dictionary with meme_text and image_prompt
memeDict = parse_meme(chatResponse)
image_prompt = memeDict['image_prompt']
meme_text = memeDict['meme_text']

# Send image prompt to image generator and get image back (Using DALL·E API)
print("Sending image creation request...")
image_response = openai.Image.create(prompt=image_prompt, n=1, size="512x512", response_format="b64_json")

# Convert image data to virtual file
image_data = b64decode(image_response["data"][0]["b64_json"])
virtual_image_file = io.BytesIO()
# Write the image data to the virtual file
virtual_image_file.write(image_data)

# Combine the meme text and image into a meme
create_meme(virtual_image_file, meme_text)
