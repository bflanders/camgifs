#%% Imports
from array2gif import write_gif
import boto
from boto.s3.key import Key
import cv2
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
import requests
from time import sleep, time as timer
from twilio.rest import Client

#%% Helper functions
def streaming():
    stream = requests.get('<network stream>', stream=True)
    while True:
        yield stream.raw.read(1024)
        
def get_frame():
    streamer = streaming()
    bytes = b''
    while True:
        bytes += next(streamer)
        a = bytes.find(b'\xff\xd8')
        b = bytes.find(b'\xff\xd9')
        if a != -1 and b != -1:
            jpg = bytes[a:b+2]
            bytes = bytes[b+2:]
            frame = np.frombuffer(jpg, dtype=np.uint8)
            return frame

#%% Main
sub = cv2.createBackgroundSubtractorMOG2()
recording = False
rec_start = 0
rec_timed_out = False
frames = 0
fps = 0
images = []
burning_in = True
start_time = timer()
while (not recording) or (recording and not rec_timed_out):
    frame = get_frame()
    img = cv2.imdecode(frame, cv2.IMREAD_COLOR)
    mask = sub.apply(img)
    diff = int(1000*np.sum(mask>0)/mask.size)
    if burning_in:
        if (timer() - start_time) > 5:
            burning_in = False
        continue
    if not recording and diff > 98:
        recording = True
        rec_start = timer()
    if recording:
        images.append(img)
        frames += 1
        rec_time = timer() - rec_start
        rec_timed_out = rec_time > 5
        fps = frames/max(1,rec_time)
    print(f'diff: {diff:5d}, rec: {recording}, fps: {fps:0.1f}', end='\r')

# Write in out ti GIF
gif_file = datetime.now().strftime('%Y%m%d_%H%M%S')+'.gif'
pils = [Image.fromarray(images[i][:,:,0]) for i in range(len(images))]
pils[0].save(gif_file, save_all=True, append_images=pils)

s3_secret_access_key = '<secret access key>' # NOT A GOOD IDEA
s3_access_key = '<access key>'
region = 'us-east-1'
bucket_name = 'camgifs'

# Upload to S3
conn = boto.connect_s3(s3_access_key, s3_secret_access_key)
bucket = conn.get_bucket(bucket_name, validate=True)
k = Key(bucket)
k.key = gif_file
sent = k.set_contents_from_file(open(gif_file,'rb'))
k.set_acl('public-read')

# Send out sms with media embed
account_sid = '<account sid>'
auth_token = '<auth token>'
client = Client(account_sid, auth_token)

message = client.messages \
    .create(
         body="cam trigger"
         ,media_url=[f'https://camgifs.s3.amazonaws.com/{gif_file}']
         ,from_='+<twilio phone>'
         ,to='+<my phone>'
     )

print(message.sid)