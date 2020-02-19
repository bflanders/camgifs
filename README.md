# camgifs
Capture and send camera snippets to my phone. Look ma! It's all free!

* Listen on network
* Find JPG ending bytes
* Convert frame to numpy
* Start background subtraction
* Allow a burn in period
* Detect frame diffs by measuring mask delta
* If diffing goes over a threshold value, start recording
* Convert recording to GIF
* Load GIF to S3
* Make SMS with S3 GIF media link embeded
* Send SMS (twilio)
