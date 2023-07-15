# AI Meme Generator
# Creates start-to-finish memes using various AI service APIs. OpenAI's chatGPT to generate the meme text and image prompt, and several optional image generators for the meme picture. Then combines the meme text and image into a meme using Pillow.
# Author: ThioJoe - https://github.com/ThioJoe

# Import installed libraries
import openai
from stability_sdk import client
import stability_sdk.interfaces.gooseai.generation.generation_pb2 as generation

# Import standard libraries
import requests
import warnings
import re
from base64 import b64decode
from PIL import Image, ImageDraw, ImageFont
from collections import namedtuple
import io
from datetime import datetime
import random
import string
import os
import textwrap
import sys
import argparse
import configparser
import platform


# ----------------------------------------- Settings -----------------------------------------

# Settings for OpenAI API to generate text to be used as the meme text and image prompt
text_model = "gpt-4" # Some model examples: "gpt-4", "gpt-3.5-turbo-16k"
temperature = 1.5 # Controls randomness. Lowering results in less random completions. Higher temperature results in more random completions.

# Image Platform settings
image_platform = "clipdrop" # Possible options: "openai", "stability", "clipdrop"

# This is NOT the individual meme image prompt. Here you can change this to tell it the general style or qualities to apply to all memes, such as using dark humor, surreal humor, wholesome, etc. 
basic_instructions = r'You will create funny memes that are clever and original, and not cliche or lame.'
# You can use this to tell it how to generate the image itself. You can specify a style such as being a photograph, drawing, etc, or something more specific such as always use cats in the pictures.
image_special_instructions = r'The images should be photographic.' 

# Outputted file names will be based on this text. For example, 'meme' will create 'meme.png', 'meme-1.png', 'meme-2.png', etc.
base_file_name = "meme"
# Relative Output Folder
output_folder = "Outputs"
# The font to use for the meme text. Must be put in the current folder or in the default Windows font directory, and must be a TrueType font file (.ttf). You can find font files in the C:\Windows\Fonts folder on Windows.
font_file = "arial.ttf"


# ==============================================================================================

# Construct the system prompt for the chat bot
def construct_system_prompt(basic_instructions, image_special_instructions):
    format_instructions = f'You are a meme generator with the following formatting instructions. Each meme will consist of text that will appear at the top, and an image to go along with it. The user will send you a message with a general theme or concept on which you will base the meme. The user may choose to send you a text saying something like "anything" or "whatever you want", or even no text at all, which you should not take literally, but take to mean they wish for you to come up with something yourself.  The memes don\'t necessarily need to start with "when", but they can. In any case, you will respond with two things: First, the text of the meme that will be displayed in the final meme. Second, some text that will be used as an image prompt for an AI image generator to generate an image to also be used as part of the meme. You must respond only in the format as described next, because your response will be parsed, so it is important it conforms to the format. The first line of your response should be: "Meme Text: " followed by the meme text. The second line of your response should be: "Image Prompt: " followed by the image prompt text.  --- Now here are additional instructions... '
    basicInstructionAppend = f'Next are instructions for the overall approach you should take to creating the memes. Interpret as best as possible: {basic_instructions} | '
    specialInstructionsAppend = f'Next are any special instructions for the image prompt. For example, if the instructions are "the images should be photographic style", your prompt may append ", photograph" at the end, or begin with "photograph of". It does not have to literally match the instruction but interpret as best as possible: {image_special_instructions}'
    systemPrompt = format_instructions + basicInstructionAppend + specialInstructionsAppend
    
    return systemPrompt

# =============================================== Argument Parser ================================================
# Parse the arguments at the start of the script
parser = argparse.ArgumentParser()
parser.add_argument("--openaikey", help="OpenAI API key")
parser.add_argument("--clipdropkey", help="ClipDrop API key")
parser.add_argument("--stabilitykey", help="Stability AI API key")
parser.add_argument("--userprompt", help="A meme subject or concept to send to the chat bot. If not specified, the user will be prompted to enter a subject or concept.")
parser.add_argument("--memecount", help="The number of memes to create. If using arguments and not specified, the default is 1.")
parser.add_argument("--imageplatform", help="The image platform to use. If using arguments and not specified, the default is 'clipdrop'. Possible options: 'openai', 'stability', 'clipdrop'")
parser.add_argument("--temperature", help="The temperature to use for the chat bot. If using arguments and not specified, the default is 0.7")
parser.add_argument("--basicinstructions", help=f"The basic instructions to use for the chat bot. If using arguments and not specified, the default is '{basic_instructions}'")
parser.add_argument("--imagespecialinstructions", help=f"The image special instructions to use for the chat bot. If using arguments and not specified, the default is '{image_special_instructions}'")
args = parser.parse_args()

# Create a namedtuple classes
ApiKeysTupleClass = namedtuple('ApiKeysTupleClass', ['openai_key', 'clipdrop_key', 'stability_key'])

# =============================================== Run Checks and Import Configs  ===============================================

# Check for font file in current directory, then check for font file in Fonts folder, warn user and exit if not found
def check_font(font_file):
    # Check for font file in current directory
    if not os.path.isfile(font_file):
        if platform.system() == "Windows":
            # Check for font file in Fonts folder (Windows)
            font_file = os.path.join(os.environ['WINDIR'], 'Fonts', font_file)
        elif platform.system() == "Linux":
            # Check for font file in font directories (Linux)
            font_directories = ["/usr/share/fonts", "~/.fonts"]
            for dir in font_directories:
                potential_font_file = os.path.join(dir, font_file)
                if os.path.isfile(potential_font_file):
                    font_file = potential_font_file
                    break
        # Warn user and exit if not found
        if not os.path.isfile(font_file):
            print(f'\n  ERROR:  Font file "{font_file}" not found. Please add the font file to the same folder as this script. Or set the variable above to the name of a font file in the system font folder.')
            input("\nPress Enter to exit...")
            exit()
    # Return the font file path
    return font_file

# Returns a dictionary of the config file
def get_config(config_file_path):
    config_raw = configparser.ConfigParser()
    config_raw.optionxform = lambda option: option  # This must be included otherwise the config file will be read in all lowercase
    config_raw.read(config_file_path)

    # Go through all the config files, convert to dictionary
    config = {}
    for section in config_raw.sections():
        for key in config_raw[section]:
            config[key] = config_raw[section][key]  # Do not use parseConfigSetting() here or else it will convert all values to lowercase

    return config

# Get API key constants from config file or command line arguments
def get_api_keys(config_file="api_keys.ini", args=None):
    # Default values
    openai_key, clipdrop_key, stability_key = '', '', ''

    # Try to read keys from config file. Default value of '' will be used if not found
    try:
        keys_dict = get_config(config_file)
        openai_key = keys_dict.get('OpenAI', '')
        clipdrop_key = keys_dict.get('ClipDrop', '')
        stability_key = keys_dict.get('StabilityAI', '')
    except FileNotFoundError:
        print("Config not found, checking for command line arguments.")  # Could not read from config file, will try command-line arguments next

    # Checks if any arguments are not None, and uses those values if so
    if not all(value is None for value in vars(args).values()):
        openai_key = args.openaikey if args.openaikey else openai_key
        clipdrop_key = args.clipdropkey if args.clipdropkey else clipdrop_key
        stability_key = args.stabilitykey if args.stabilitykey else stability_key

    return ApiKeysTupleClass(openai_key, clipdrop_key, stability_key)

# ------------ VALIDATION ------------

def validate_api_keys(apiKeys, image_platform):
    if not apiKeys.openai_key:
        print("\n  ERROR:  No OpenAI API key found. OpenAI API key is required - In order to generate text for the meme text and image prompt. Please add your OpenAI API key to the api_keys.ini file.")
        input("\nPress Enter to exit...")
        exit()

    valid_image_platforms = ["openai", "stability", "clipdrop"]
    image_platform = image_platform.lower()

    if image_platform in valid_image_platforms:
        if image_platform == "stability" and not apiKeys.stability_key:
            print("\n  ERROR:  Stability AI was set as the image platform, but no Stability AI API key was found in the api_keys.ini file.")
            input("\nPress Enter to exit...")
            exit()
        if image_platform == "clipdrop" and not apiKeys.clipdrop_key:
            print("\n  ERROR:  ClipDrop was set as the image platform, but no ClipDrop API key was found in the api_keys.ini file.")
            input("\nPress Enter to exit...")
            exit()
    else:
        print(f'\n  ERROR:  Invalid image platform "{image_platform}". Valid image platforms are: {valid_image_platforms}')
        input("\nPress Enter to exit...")
        exit()

def initialize_api_clients(apiKeys):
    if apiKeys.openai_key:
        openai.api_key = apiKeys.openai_key

    if apiKeys.stability_key:
        stability_api = client.StabilityInference(
            key=apiKeys.stability_key, # API Key reference.
            verbose=True, # Print debug messages.
            engine="stable-diffusion-xl-1024-v0-9", # Set the engine to use for generation.
            # Available engines: stable-diffusion-xl-1024-v0-9 stable-diffusion-v1 stable-diffusion-v1-5 stable-diffusion-512-v2-0 stable-diffusion-768-v2-0
            # stable-diffusion-512-v2-1 stable-diffusion-768-v2-1 stable-diffusion-xl-beta-v2-2-2 stable-inpainting-v1-0 stable-inpainting-512-v2-0
        )
    else:
        stability_api = None
    
    # Only need to return stability_api because openai.api_key has global scope
    return stability_api


# =============================================== Functions ================================================

# Sets the name and path of the file to be used
def set_file_path(baseName, outputFolder):
    def generate_random_string(length):
        # Define the characters to choose from
        characters = string.ascii_uppercase
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
    
# Write or append log file containing the user user message, chat bot meme text, and chat bot image prompt for each meme
def write_log_file(userPrompt, AiMemeDict, filePath, logFolder=output_folder, basic=basic_instructions, special=image_special_instructions, platform=image_platform):
    # Get file name from path
    memeFileName = os.path.basename(filePath)
    with open(os.path.join(logFolder, "log.txt"), "a", encoding='utf-8') as log_file:
        log_file.write(textwrap.dedent(f"""
                       Meme File Name: {memeFileName}
                       AI Basic Instructions: {basic}
                       AI Special Image Instructions: {special}
                       User Prompt: '{userPrompt}'
                       Chat Bot Meme Text: {AiMemeDict['meme_text']}
                       Chat Bot Image Prompt: {AiMemeDict['image_prompt']}
                       Image Generation Platform: {platform}
                       \n"""))

# Gets the meme text and image prompt from the message sent by the chat bot
def parse_meme(message):
    # The regex pattern to match
    pattern = r'Meme Text: (\"(.*?)\"|(.*?))\n*\s*Image Prompt: (.*?)$'

    match = re.search(pattern, message, re.DOTALL)

    if match:
        # If meme text is enclosed in quotes it will be in group 2, otherwise, it will be in group 3.
        meme_text = match.group(2) if match.group(2) is not None else match.group(3)
        
        return {
            "meme_text": meme_text,
            "image_prompt": match.group(4)
        }
    else:
        return None
    
# Sends the user message to the chat bot and returns the chat bot's response
def send_and_receive_message(text_model, userMessage, conversationTemp, temperature=0.5):
    # Prepare to send request along with context by appending user message to previous conversation
    conversationTemp.append({"role": "user", "content": userMessage})
    
    print("Sending request to write meme...")
    chatResponse = openai.ChatCompletion.create(
        model=text_model,
        messages=conversationTemp,
        temperature=temperature
        )

    chatResponseMessage = chatResponse.choices[0].message.content
    chatResponseRole = chatResponse.choices[0].message.role

    #print("\n" + chatResponseMessage)
    #conversationTemp.append({"role": chatResponseRole, "content": chatResponseMessage})

    return chatResponseMessage


def create_meme(image_path, top_text, filePath, fontFile, min_scale=0.05, buffer_scale=0.03, font_scale=1):
    print("Creating meme image...")
    
    # Load the image. Can be a path or a file-like object such as IO.BytesIO virtual file
    image = Image.open(image_path)

    # Calculate buffer size based on buffer_scale
    buffer_size = int(buffer_scale * image.width)

    # Get a drawing context
    d = ImageDraw.Draw(image)

    # Split the text into words
    words = top_text.split()

    # Initialize the font size and wrapped text
    font_size = int(font_scale * image.width)
    fnt = ImageFont.truetype(fontFile, font_size)
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

def image_generation_request(apiKeys, image_prompt, platform, stability_api=None):
    if platform == "openai":
        openai_response = openai.Image.create(prompt=image_prompt, n=1, size="512x512", response_format="b64_json")
        # Convert image data to virtual file
        image_data = b64decode(openai_response["data"][0]["b64_json"])
        virtual_image_file = io.BytesIO()
        # Write the image data to the virtual file
        virtual_image_file.write(image_data)
    
    if platform == "stability" and stability_api:
        # Set up our initial generation parameters.
        stability_response = stability_api.generate(
            prompt=image_prompt,
            #seed=992446758, # If a seed is provided, the resulting generated image will be deterministic.
            steps=30,       # Amount of inference steps performed on image generation. Defaults to 30.
            cfg_scale=7.0,  # Influences how strongly your generation is guided to match your prompt. Setting this value higher increases the strength in which it tries to match your prompt. Defaults to 7.0 if not specified.
            width=1024, # Generation width, if not included defaults to 512 or 1024 depending on the engine.
            height=1024, # Generation height, if not included defaults to 512 or 1024 depending on the engine.
            samples=1, # Number of images to generate, defaults to 1 if not included.
            sampler=generation.SAMPLER_K_DPMPP_2M   # Choose which sampler we want to denoise our generation with. Defaults to k_dpmpp_2m if not specified. Clip Guidance only supports ancestral samplers.
                                                    # (Available Samplers: ddim, plms, k_euler, k_euler_ancestral, k_heun, k_dpm_2, k_dpm_2_ancestral, k_dpmpp_2s_ancestral, k_lms, k_dpmpp_2m, k_dpmpp_sde)
        )

        # Set up our warning to print to the console if the adult content classifier is tripped. If adult content classifier is not tripped, save generated images.
        for resp in stability_response:
            for artifact in resp.artifacts:
                if artifact.finish_reason == generation.FILTER:
                    warnings.warn(
                        "Your request activated the API's safety filters and could not be processed."
                        "Please modify the prompt and try again.")
                if artifact.type == generation.ARTIFACT_IMAGE:
                    #img = Image.open(io.BytesIO(artifact.binary))
                    #img.save(str(artifact.seed)+ ".png") # Save our generated images with their seed number as the filename.
                    virtual_image_file = io.BytesIO(artifact.binary)

    if platform == "clipdrop":
        r = requests.post('https://clipdrop-api.co/text-to-image/v1',
            files = {
                'prompt': (None, image_prompt, 'text/plain')
            },
            headers = { 'x-api-key': apiKeys.clipdrop_key}
        )
        if (r.ok):
            virtual_image_file = io.BytesIO(r.content) # r.content contains the bytes of the returned image
        else:
            r.raise_for_status()

    return virtual_image_file

# ==================== RUN ====================

# Set default values for parameters to those at top of script, but can be overridden by command line arguments or by being set when called from another script
def generate(
    text_model=text_model, 
    temperature=temperature, 
    basic_instructions=basic_instructions, 
    image_special_instructions=image_special_instructions, 
    image_platform=image_platform, 
    font_file=font_file, 
    base_file_name=base_file_name, 
    output_folder=output_folder
):
    # Parse the arguments
    args = parser.parse_args()
    
    # Get api keys and put into tuple
    apiKeys = get_api_keys(args=args)
    # Validate api keys
    validate_api_keys(apiKeys, image_platform)
    # Initialize api clients. Only get stability_api object back because openai.api_key has global scope
    stability_api = initialize_api_clients(apiKeys)

    # Check if any settings arguments, and replace the default values with the args if so. To run automated from command line, specify at least 1 argument.
    if args.imageplatform:
        image_platform = args.imageplatform
    if args.temperature:
        temperature = float(args.temperature)
    if args.basicinstructions:
        basic_instructions = args.basicinstructions
    if args.imagespecialinstructions:
        image_special_instructions = args.imagespecialinstructions

    systemPrompt = construct_system_prompt(basic_instructions, image_special_instructions)
    conversation = [{"role": "system", "content": systemPrompt}]
    userEnteredPrompt = ""

    # Get full path of font file from font file name
    font_file = check_font(font_file)

    # ---------- Start User Input -----------

    # If any arguments are being used, skip the user input
    if all(value is None for value in vars(args).values()):
        print("\nEnter a meme subject or concept (Or just hit enter to let the AI decide)")
        userEnteredPrompt = input(" >  ")
        if not userEnteredPrompt:
            userEnteredPrompt = "anything"
            
        # Set the number of memes to create
        meme_count = 1
        print("\nEnter the number of memes to create (Or just hit Enter for 1): ")
        userEnteredCount = input(" >  ")
        if userEnteredCount:
            meme_count = int(userEnteredCount)

    else:
        if args.userprompt:
            userEnteredPrompt = args.userprompt
        else:
            userEnteredPrompt = "anything"

        meme_count = 1
        if args.memecount:
            meme_count = int(args.memecount)


    def single_meme_generation_loop():
        # Send request to chat bot to generate meme text and image prompt
        chatResponse = send_and_receive_message(text_model, userEnteredPrompt, conversation, temperature)

        # Take chat message and convert to dictionary with meme_text and image_prompt
        memeDict = parse_meme(chatResponse)
        image_prompt = memeDict['image_prompt']
        meme_text = memeDict['meme_text']

        # Print the meme text and image prompt
        print("\n   Meme Text:  " + meme_text)
        print("   Image Prompt:  " + image_prompt)

        # Send image prompt to image generator and get image back (Using DALL·E API)
        print("\nSending image creation request...")
        virtual_image_file = image_generation_request(apiKeys, image_prompt, image_platform, stability_api)

        # Combine the meme text and image into a meme
        filePath = set_file_path(base_file_name, output_folder)
        create_meme(virtual_image_file, meme_text, filePath, fontFile=font_file)
        write_log_file(userEnteredPrompt, memeDict, filePath)
        
        absoluteFilePath = os.path.abspath(filePath)
        
        return {"meme_text": meme_text, "image_prompt": image_prompt, "file_path": absoluteFilePath}

    # Create list of dictionaries to hold the results of each meme so that they can be returned by main() if called from command line
    memeResultsDictsList = []

    for i in range(meme_count):
        print("\n----------------------------------------------------------------------------------------------------")
        print(f"Generating meme {i+1} of {meme_count}...")
        memeInfoDict = single_meme_generation_loop()

        # Add meme info dict to list of meme results
        memeResultsDictsList.append(memeInfoDict)
    
    # If called from command line, will return the list of meme results
    return memeResultsDictsList

if __name__ == "__main__":
    generate()
