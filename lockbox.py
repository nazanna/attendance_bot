import re
import subprocess
from constants import DEBUG 

def get_lockbox_secret(secret_name: str):
    command = f'{"yc" if DEBUG else "/home/phys-bot/yandex-cloud/bin/yc"} lockbox payload get {secret_name}' # TODO: разобраться с путем к yc на машинке
    try:
        result = subprocess.run(command, shell=True, check=True, text=True, capture_output=True)
        command_output = result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error occurred: {e}")
        exit(1)

    match = re.search(r'text_value:\s*(\S+)', command_output)
    if match:
        value = match.group(1)
        return value
    else:
        print("Lockbox secret is empty!")
        exit(1)
