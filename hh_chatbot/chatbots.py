from openai import OpenAI
import time
import re
import os
import requests
from PIL import Image
import base64
import numpy as np

def crop_white_area(img_path, threshold=240):
    # Open the image
    img = Image.open(img_path).convert("RGBA")
    # to numpy array
    img_array = np.array(img)
    b1 = np.all(np.all(img_array[:, :, :3] > threshold, axis=2), axis=1)
    b2 = np.all(np.all(img_array[:, :, :3] > threshold, axis=2), axis=0)
    mask_array = np.ones_like(img_array)
    mask_array[:, :, :3] = img_array[:, :, :3]
    # find the bounding box
    bbox = [np.where(~b2)[0].min(), np.where(~b1)[0].min(), np.where(~b2)[0].max(), np.where(~b1)[0].max()]
    # crop the image
    cropped_img = img.crop(bbox)
    # convert to jpg
    cropped_img = cropped_img.convert("RGB")
    return cropped_img

def get_chatbot_dict():
    return {
        'null_chatbot': NullChatbot,
        'ohmygpt': OhMyGPT,
        'grok': Grok
    }
def call_chatbot(name, arg_dict={
        "model": "gpt-3.5.-turbo",
        "key": "",
        "temperature": 0.7,
        "top_p": 0.95
    }):
    return get_chatbot_dict()[name](arg_dict)

# chatbot interface
class Chatbot_Interface:
    def __init__(self):
        pass

    def ask(self, text, clear_message=False, img_path=None, is_crop=True, img_size=0, wait_time=1):
        pass

class OhMyGPT(Chatbot_Interface):
    def __init__(self, arg):
        self.current_timestamp = 0
        self.url = "https://api.ohmygpt.com/v1/chat/completions"
        try:
            self.headers = {
                "Content-Type": "application/json",
                "Authorization": "Bearer " + arg["key"],
            }
        except KeyError("Error: API key is missing."):
            exit()
        self.arg = arg
        if 'model' in arg:
            self.model = arg['model']
        else:
            self.model = "gpt-3.5-turbo"
        if not 'temperature' in self.arg.keys():
            self.arg['temperature'] = 0.7
        if not 'top_p' in self.arg.keys():
            self.arg['top_p'] = 0.95
        if not 'previous' in self.arg.keys():
            self.previous = []
        else:
            self.previous = self.arg['previous']
        print("Chatbot connected")

    def call_ohmygpt(self, message):
        url = self.url
        headers = self.headers
        payload = {
            "model": self.model,
            "messages": message,
            "temperature": self.arg['temperature'],
            "top_p": self.arg['top_p'],
        }
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        response_data =  response.json()
        # Extract the assistant's reply
        assistant_reply = response_data["choices"][0]["message"]["content"]
        # Extract the prompt tokens count
        prompt_tokens = response_data["usage"]["prompt_tokens"]
        # Extract the completion tokens count
        completion_tokens = response_data["usage"]["completion_tokens"]
        # Extract the total tokens count
        total_tokens = response_data["usage"]["total_tokens"]
        return assistant_reply, prompt_tokens, completion_tokens, total_tokens

    def ask(self, message, clear_message=False, img_path=None, is_crop=True, img_size=250000, wait_time=5):
        # If user put in string as a message
        if isinstance(message, str):
            # If user put in an image path
            if not img_path is None:
                if is_crop:
                    img = crop_white_area(img_path)
                else:
                    img = Image.open(img_path)

                # resize the images to a total of 250000, keeping the original aspect ratio
                # check the size of the image first
                if img.size[0] * img.size[1] > img_size:
                    img_height = img.size[1]
                    img_width = img.size[0]
                    ratio_img = img_size / (img_height * img_width)
                    img = img.resize((int(ratio_img * img_width), int(ratio_img * img_height)))

                detail = "high"
                if img_size <= 250000:
                    detail = "low"

                # img = img.resize((500, 500))
                # save resized image as jpg
                # convert img to jpg
                img.save("temp.jpg")
                encoded_image = base64.b64encode(open("temp.jpg", 'rb').read()).decode('ascii')
                msg = {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": message
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{encoded_image}",
                                "detail": detail
                            }
                        }
                    ]
                }

            # If user did not put in an image path
            else:
                msg = {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": message
                        }
                    ]
                }

            # Need to handle previous message
            if not clear_message:
                self.previous.append(msg)
                if len(self.previous) > 10:
                    self.previous = self.previous[1:]
            else:
                del self.previous
                self.previous = []
                self.previous.append(msg)

        # If user put in string as a list
        elif isinstance(message, list):
            # Image processing is not supported when message is a list
            if not img_path is None:
                raise TypeError("Image processing is not supported when the message is a list.")

            del self.previous
            self.previous = message
        else:
            print("Error: message is not a string or list")
            raise

        while self.current_timestamp + wait_time > time.time():
            time.sleep(wait_time)
        self.current_timestamp = time.time()

        response_message, _, _, _ = self.call_ohmygpt(self.previous)
        self.current_timestamp = time.time()

        if not isinstance(message, list):
            temp = {}
            temp["role"] = 'system'
            temp["content"] = response_message
            self.previous.append(temp)
        return response_message

class Grok(Chatbot_Interface):
    def __init__(self, arg):
        self.current_timestamp = 0
        self.arg = arg
        try:
            self.key = self.arg["key"]
        except KeyError("Error: API key is missing."):
            exit()
        if 'model' in self.arg.keys():
            self.model = self.arg["model"]
        else:
            self.model = "grok-3-mini"
        if not 'temperature' in self.arg.keys():
            self.arg['temperature'] = 0.7
        if not 'top_p' in self.arg.keys():
            self.arg['top_p'] = 0.95
        if not 'previous' in self.arg.keys():
            self.previous = []
        else:
            self.previous = self.arg['previous']
        print("Chatbot connected")

    def ask(self, message, clear_message=False, img_path=None, is_crop=True, img_size=0, wait_time=5):
        # If user put in string as a message
        if not img_path is None:
            raise TypeError("Image processing is not supported for grok.")
        if isinstance(message, str):
            msg = {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": message
                    }
                ]
            }
            # Need to handle previous message
            if not clear_message:
                self.previous.append(msg)
                if len(self.previous) > 10:
                    self.previous = self.previous[1:]
            else:
                del self.previous
                self.previous = []
                self.previous.append(msg)

        # If user put in list as a message
        elif isinstance(message, list):
            del self.previous
            self.previous = message
        else:
            print("Error: message is not a string or list")
            raise

        while self.current_timestamp + wait_time > time.time():
            time.sleep(wait_time)
        self.current_timestamp = time.time()

        # Initiate the OpenAI client
        client = OpenAI(
            api_key=self.arg["key"],
            base_url="https://api.x.ai/v1"
        )
        # Send a request to the LLM with prespecified message and parameters
        response = client.chat.completions.create(
            model=self.model,
            messages=self.previous,
            temperature=self.arg['temperature'],
            top_p=self.arg['top_p'],
        )
        # Extract the reply of the model
        response_message = response.choices[0].message.content
        # If type of message is not list
        if not isinstance(message, list):
            temp = {}
            temp["role"] = 'system'
            temp["content"] = response_message
            self.previous.append(temp)
        return response_message

class NullChatbot(Chatbot_Interface):
    def __init__(self, arg={}):
        self.model_name = "NullChatbot"

    def ask(self, message, clear_message=False, img_path=None, is_crop=True, img_size=0, wait_time=5):
        return "This is your message: " + message