import os
PTG_USERNAME = "test"
PTG_PASSWORD = "test"
PTG_URL = os.getenv("PTG_URL") or "http://192.168.50.223:7890"
import json

script_dir = os.path.dirname(os.path.abspath(__file__))
config_dir = os.path.join(script_dir, "configs")


class StreamServerConfig():
    def __init__(self, url, username, password):
        self.url = url
        self.username = username
        self.password = password
    
                
def read_config(config_name="default"):
    with open(os.path.join(config_dir, f"{config_name}.json"), "r") as f:
        config_json = json.load(f)
        return StreamServerConfig(config_json["url"], config_json["username"], config_json["password"]) 
    
    
    