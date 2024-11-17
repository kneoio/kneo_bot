import http.client
import json

conn = http.client.HTTPSConnection("api.piapi.ai")
payload = json.dumps({
   "model": "suno",
   "task_type": "generate_music",
   "input": {
      "gpt_description_prompt": "Autumn night breeze",
      "make_instrumental": True,
      "model_version": "chirp-v3-0"
   },
   "config": {
      "service_mode": "",
      "webhook_config": {
         "endpoint": "",
         "secret": ""
      }
   }
})
headers = {
   'x-api-key': '5192cb129f21becd6ed48e05c6868a7019bad8c1e32b581ad19ba7e44d453290',
   'Content-Type': 'application/json'
}
conn.request("POST", "/api/v1/task", payload, headers)
res = conn.getresponse()
data = res.read()
print(data.decode("utf-8"))