import random
import websocket
import uuid
import json
import urllib.request
import urllib.parse
from PIL import Image
import io
import time
import socket


with open('workflows/e-commerce-api.json', encoding='utf-8') as f:
    prompt_text = f.read()

prompt_save = json.loads(prompt_text)


def swap(url_image_human, url_image_outfit, user_prompt):
    server_address = "localhost:20218"    

    prompt = prompt_save

    image_seed = random.randint(1, 1125899906)
    image_seed_2 = random.randint(1, 1125899906)

    prompt["31"]["inputs"]["seed"] = image_seed
    prompt["243"]["inputs"]["seed"] = image_seed_2

    prompt["248"]["inputs"]["text"] = user_prompt
    
    prompt["265"]["inputs"]["Url"] = url_image_human
    prompt["266"]["inputs"]["Url"] = url_image_outfit

    client_id = str(uuid.uuid4())

    def queue_prompt(prompt):
        p = {"prompt": prompt, "client_id": client_id}
        data = json.dumps(p).encode('utf-8')
        req = urllib.request.Request("http://{}/prompt".format(server_address), data=data)
        return json.loads(urllib.request.urlopen(req).read())

    def get_image(filename, subfolder, folder_type):
        data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
        url_values = urllib.parse.urlencode(data)
        with urllib.request.urlopen("http://{}/view?{}".format(server_address, url_values)) as response:
            return response.read()

    def get_history(prompt_id):
        with urllib.request.urlopen("http://{}/history/{}".format(server_address, prompt_id)) as response:
            return json.loads(response.read())

    def get_images(ws, prompt):
        prompt_id = queue_prompt(prompt)['prompt_id']
        output_images = {}
        try:
            while True:
                try:
                    out = ws.recv()
                except TimeoutError:
                    print("Timeout occurred, no data received from the server.")
                    return []

                if isinstance(out, str):
                    message = json.loads(out)
                    if message['type'] == 'executing':
                        data = message['data']
                        if data['node'] is None and data['prompt_id'] == prompt_id:
                            break
                else:
                    continue

            history = get_history(prompt_id)[prompt_id]
            for o in history['outputs']:
                for node_id in history['outputs']:
                    node_output = history['outputs'][node_id]
                    if 'images' in node_output:
                        images_output = []
                        for image in node_output['images']:
                            image_data = get_image(image['filename'], image['subfolder'], image['type'])
                            images_output.append(image_data)
                        output_images[node_id] = images_output

        finally:
            ws.close()

        return output_images

    try:
        ws = websocket.WebSocket()
        ws.connect("ws://{}/ws?clientId={}".format(server_address, client_id))
        ws.settimeout(300000)
        images = get_images(ws, prompt)
    except ConnectionRefusedError:
        raise ConnectionError(f"ComfyUI server at {server_address} refused connection. Please check if the server is running and accessible.")
    except Exception as e:
        raise ConnectionError(f"Failed to connect to ComfyUI server: {str(e)}")

    result = []

    for node_id in images:
        for image_data in images[node_id]:
            imageResult = Image.open(io.BytesIO(image_data))
            if imageResult.mode != 'RGB':
                imageResult = imageResult.convert('RGB')

            result.append(imageResult)
        
    return result
