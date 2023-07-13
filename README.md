# Full Stack AI Meme Generator

Allows you to automatically generate meme images from start to finish using AI. It will generate the text for the meme (optionally based on a user-provided concept), create a related image, and combine the two into a final image file.
----------------------
<p align="center"><img src="https://github.com/ThioJoe/Full-Stack-AI-Meme-Generator/assets/12518330/9beefed6-1efa-4eba-b87f-ad3ae16c9809" width=35%></p>

## Features

- Uses OpenAI's GPT-4 to generate the text and image prompt for the meme.
- Allows customization of the meme generation process through various settings.
- Generates memes with a user-provided subject or concept, or you can let the AI decide.
- Logs meme generation details for future reference.

## Usage

1. Clone the repository.
2. Install the necessary Python packages.
3. Obtain at least an OpenAI API key, but it is recommended to also use APIs from Clipdrop or Stability AI (DreamStudio) for the image generation stage.
4. Edit the settings variables in the script.
5. Run the script and enter a meme subject or concept when prompted (optional).

## Settings

Various settings for the meme generation process can be customized:

- OpenAI API settings: Choose the text model and temperature for generating the meme text and image prompt.
- Image platform settings: Choose the platform for generating the meme image. Options include OpenAI's DALLE2, StabilityAI's DreamStudio, and ClipDrop.
- Basic Meme Instructions: You can tell the AI about the general style or qualities to apply to all memes, such as using dark humor, surreal humor, wholesome, etc. 
- Special Image Instructions: You can tell the AI how to generate the image itself (more specifically,  how to write the image prompt). You can specify a style such as being a photograph, drawing, etc, or something more specific such as always using cats in the pictures.

## Example Image Output With Log
<p align="center"><img src="https://github.com/ThioJoe/Full-Stack-AI-Meme-Generator/assets/12518330/28e82079-4244-463e-9370-b5665c5fedd7" width="400"></p>

```
Meme File Name: meme_2023-07-13-15-34_ZYKCV.png
AI Basic Instructions: You will create funny memes.
AI Special Image Instructions: The images should be photographic.
User Prompt: 'cats'
Chat Bot Meme Text: "When you finally find the perfect napping spot... on the laptop."
Chat Bot Image Prompt: "A photograph of a cat laying down on an open laptop."
Image Generation Platform: clipdrop
```
