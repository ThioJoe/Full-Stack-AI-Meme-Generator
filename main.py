import openai
import json
import re
from base64 import b64decode
from PIL import Image, ImageDraw, ImageFont
import io
from datetime import datetime
import random
import string
import os

# Some Models:
# gpt-4
# gpt-3.5-turbo-16k

model = "gpt-4"
temperature = 1
basic_instructions = r'You will create funny memes.'
image_special_instructions = r'The images should be photographic.'

# Outputted file names will be based on this text. For example, 'meme' will create 'meme.png', 'meme-1.png', 'meme-2.png', etc.
base_file_name = "meme"
# Relative Output Folder
output_folder = "Outputs"
# The font to use for the meme text. Must be put in the current folder or in the default Windows font directory, and must be a TrueType font file (.ttf). You can find font files in the C:\Windows\Fonts folder on Windows.
font_file = "arial.ttf"

# ----------------------------------------------

format_instructions = f'You are a meme generator with the following formatting instructions. Each meme will consist of text that will appear at the top, and an image to go along with it. The user will send you a message with a general theme or concept on which you will base the meme. The user may choose to send you a text saying something like "anything" or "whatever you want", or even no text at all, which you should not take literally, but take to mean they wish for you to come up with something yourself.  In any case, you will respond with two things: First, the text of the meme that will be displayed in the final meme. Second, some text that will be used as an image prompt for an AI image generator to generate an image to also be used as part of the meme. You must respond only in the format as described next, because your response will be parsed, so it is important it conforms to the format. The first line of your response should be: "Meme Text: " followed by the meme text. The second line of your response should be: "Image Prompt: " followed by the image prompt text. --- Now here are additional instructions... '
basicInstructionAppend = f'Next are instructions for the overall approach you should take to creating the memes. Interpret as best as possible: {basic_instructions} | '
specialInstructionsAppend = f'Next are any special instructions for the image prompt. For example, if the instructions are "the images should be photographic style", your prompt may append ", photograph" at the end, or begin with "photograph of". It does not have to literally match the instruction but interpret as best as possible: {image_special_instructions}'
systemPrompt = format_instructions + basicInstructionAppend + specialInstructionsAppend

# Check for font file in current directory, then check for font file in Fonts folder, warn user and exit if not found
if not os.path.isfile(font_file):
    font_file = os.path.join(os.environ['WINDIR'], 'Fonts', font_file)
    if not os.path.isfile(font_file):
        print(f'\n  ERROR:  Font file "{font_file}" not found. Please add the font file to the same folder as this script. Or set the variable above to the name of a font file in the C:\\Windows\\Fonts folder.')
        input("\nPress Enter to exit...")
        exit()

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

# Sets the name and path of the file to be used
def set_file_path(baseName, outputFolder):
    def generate_random_string(length):
        # Define the characters to choose from
        characters = string.ascii_lowercase + string.digits
        # Generate a random string of specified length
        random_string = ''.join(random.choice(characters) for _ in range(length))
        return random_string

    # Generate random 3 digit number
    randString = generate_random_string(5)
    # Generate a timestamp string to append to the file name
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M")
    # Set the file name
    fileName = baseName + "_" + timestamp + "_" + randString + ".png"
    
    filePath = os.path.join(outputFolder, fileName)
    
    # If the output folder does not exist, create it
    if not os.path.exists(outputFolder):
        os.makedirs(outputFolder)
    
    return filePath
    
    

# Gets the meme text and image prompt from the message sent by the chat bot
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
    
# Sends the user message to the chat bot and returns the chat bot's response
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


def create_meme(image_path, top_text, filePath, fontFile, min_scale=0.06, buffer_scale=0.03, font_scale=1):
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
        fnt = ImageFont.truetype(fontFile, int(font_size))

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
    new_img.save(filePath)
    

# ----------------------------------------------

conversation = [{"role": "system", "content": systemPrompt}]

while True:
    userEnteredPrompt = input("\n Enter a meme subject or concept: ")
    if not userEnteredPrompt:
        userEnteredPrompt = "anything"
    if userEnteredPrompt:
        print("----------------------------------------------------------------------------------------------------")
        chatResponse = send_and_receive_message(userEnteredPrompt, conversation, temperature)
        break

# Take chat message and convert to dictionary with meme_text and image_prompt
memeDict = parse_meme(chatResponse)
image_prompt = memeDict['image_prompt']
meme_text = memeDict['meme_text']

# Print the meme text and image prompt
print("\n   Meme Text:  " + meme_text)
print("   Image Prompt:  " + image_prompt)

# Send image prompt to image generator and get image back (Using DALL·E API)
print("\nSending image creation request...")
image_response = openai.Image.create(prompt=image_prompt, n=1, size="512x512", response_format="b64_json")

# Convert image data to virtual file
image_data = b64decode(image_response["data"][0]["b64_json"])
virtual_image_file = io.BytesIO()
# Write the image data to the virtual file
virtual_image_file.write(image_data)

# Combine the meme text and image into a meme
filePath = set_file_path(base_file_name, output_folder)
create_meme(virtual_image_file, meme_text, filePath, fontFile=font_file)
