import json
from hh_chatbot.chatbots import *
import time
import signal
from functools import wraps
from dotenv import load_dotenv

script_dir = os.path.dirname(__file__)
env_path = os.path.join(script_dir, '.env')

def test():
    print("test, wow it is updated")

def timeout(seconds=10, error_message='Function call timed out'):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            def raise_timeout(*args):
                raise TimeoutError(error_message)

            original_handler = signal.signal(signal.SIGALRM, raise_timeout)
            signal.alarm(seconds)
            try:
                result = func(*args, **kwargs)
            finally:
                signal.signal(signal.SIGALRM, original_handler)
                signal.alarm(0)
            return result

        return wrapper

    return decorator

@timeout(seconds=240, error_message='GPT took too long to call')
def get_answers_llm(prompt, sample_json, img_path = None, model = 'grok-3-mini', required_type=None, trial = 3, prompt2 = None, temperature=None):
    def get_json(response):
        if "<think>" in response and "</think>" in response:
            json_match = re.search(r"{.*}", response, re.DOTALL)
            if json_match:
                response_json = json_match.group(0)
                # Parse the JSON
            else:
                raise
        elif '```json' in response and '```' in response:
            response_json = response[response.rfind('```json') + 6:response.rfind('```')]
            response_json = response_json[response_json.index('{'):response_json.rfind('}') + 1]
        else:
            response_json = response[response.index('{'):response.rfind('}') + 1]
        r_json = json.loads(response_json)
        return r_json


    if required_type is None:
        required_type = [f for f in sample_json if not f in ['...']]
    if prompt2 is None:
        prompt2 = "These features are missing or too short or not right. Please correct the response and output a new json with all features.\n\n"

    # print(prompt)
    r_json = {}
    response = ""
    response2 = ""
    if temperature is None:
        temperature = 0.2

    if model == 'gpt-4o-mini':
        load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))  # Load variables from .env file
        api_key = os.getenv("ohmygpt_API_KEY")
        chatbot = call_chatbot('ohmygpt', {'key': api_key, 'temperature':temperature, 'model':model})
    elif model == 'grok-3-mini':
        load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
        api_key = os.getenv("grok_API_KEY")
        chatbot = call_chatbot('grok', {'key': api_key, 'temperature':temperature, 'model':model})
    else:
        return {}, "", ""

    for _ in range(trial):
        try:
            response = chatbot.ask(message=prompt, img_path=img_path, clear_message=True)
            # response = get_answers_gpt3(prompt, model, temperature=0.2)
            # get the JSON response
            r_json = get_json(response)
            # Check if the JSON response has all the required keys
            prompt_check = ""
            array_missing = [key for key in required_type if
                             key not in r_json
                             or '...' in str(r_json[key])]
            if len(array_missing) > 0:
                raise
            else:
                break
            #     array = []
            #     array.append(prompt)
            #     array.append(response)
            #     for key in array_missing:
            #         prompt2 += f"{key}: \n"
            #     array.append(prompt2)
            #     response2 = get_answers_gpt3(array, model)
            #     r_json = get_json(response2)
            #     array_missing2 = [key for key in required_type if
            #                      key not in r_json
            #                      or '...' in r_json[key]
            #                      or len(r_json[key]) == 0]
            #     if len(array_missing2) > 0:
            #         response2 = ""
            #         continue
            #     # if '```json' in response2 and '```' in response2:
            #     #     response_json2 = response2[response2.rfind('```json') + 6:response2.rfind('```')]
            #     #     response_json2 = response_json2[response_json2.index('{'):response_json2.rfind('}') + 1]
            #     # else:
            #     #     response_json2 = response2[response2.index('{'):response2.rfind('}') + 1]
            #     # # response_json2 = response2[response2.rfind('```json') + 6:response2.rfind('```')]
            #     # # response_json2 = response_json2[response_json2.index('{'):response_json2.rfind('}') + 1]
            #     # r_json = json.loads(response_json2)
            # else:
            #     response_json2 = ""
            # break
        except:
            time.sleep(5)
            r_json = {}
            response = "Error in response, retrying failed."
            response2 = ""
            continue
    return r_json, response, response2

@timeout(seconds=240, error_message='GPT took too long to call')
def get_py(prompt, img_path = None, model = 'grok-3-mini', trial = 3, prompt2 = None, temperature=None):
    """Prompt grok to generate a python script"""
    def check_py(response):
        if "<think>" in response and "</think>" in response:
            py_match = re.search(r"{.*}", response, re.DOTALL)
            if py_match:
                response_py = py_match.group(0)
                # Parse the JSON
            else:
                raise
        elif '```python' in response and '```' in response:
            start_pos = response.index('```python')+9
            stop_pos = response[start_pos:].index('```') + start_pos
            response_py = response[start_pos:stop_pos]
            # response_py = response[response.rfind('```python') + 9:response.rfind('```')]
        else:
            print("The response is not in the correct format.")
        return response_py

    if temperature is None:
        temperature = 0.2

    if model == 'gpt-4o-mini':
        load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))  # Load variables from .env file
        api_key = os.getenv("ohmygpt_API_KEY")
        chatbot = call_chatbot('ohmygpt', {'key': api_key, 'temperature': temperature, 'model': model})
    elif model == 'grok-3-mini':
        load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
        api_key = os.getenv("grok_API_KEY")
        chatbot = call_chatbot('grok', {'key': api_key, 'temperature': temperature, 'model': model})
    else:
        return "", "", ""

    for _ in range(trial):
        try:
            response = chatbot.ask(message=prompt, img_path=img_path, clear_message=True)
            # Get code
            code = check_py(response)
            response2 = ""
            break
        except:
            time.sleep(5)
            code = ""
            response = "Error in response, retrying failed."
            response2 = ""
    return code, response, response2

