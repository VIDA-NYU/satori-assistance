# Test Print Pipeline

# Before conducting the test, please ensure the PipelineSever is running and a print-pipeline is registered.
import ptgctl
import requests
import json
import time
import time

# Change PTG_URL to the correct URL
PTG_URI = "://argus-api.hsrn.nyu.edu"


uri = "://argus-api.hsrn.nyu.edu"


# Log in the PTG server

TEST_CONTENT = "TEST CONTENT 1295478"

r = requests.post(url=f'https{uri}/token',data={'username':'test', 'password':'test'})
token = r.json()['access_token']
header = {"Authorization":"Bearer "+token}


# Sending a message request to the print-pipeline
current_timestamp = int(time.time())
r = requests.post("https" + uri + "/data/chat:user:message_channel2", files={'entries': "{}|{}".format(TEST_CONTENT, current_timestamp)}, headers=header)
print("PUSH Feedback:", r.content)

# Wait for sometime so the server can respond
time.sleep(5)

r = requests.get("http" + uri + "/data/chat:assistant:message_channel2", headers=header)
print(r.content)

r_content = r.content.decode("utf-8").split("|")[0]
print(r_content)
print()
if r_content == "Print: " + TEST_CONTENT:
    print("Test OK")
else:
    print("Test Failed")
