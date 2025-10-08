## Image Summarization

Analyze one or more image uploads and produce a summarization for the given prompt using OpenAI GPT-4 Omni vision capabilities. T*his implementation uses OpenAI’s GPT-4o model documented [here](https://openai.com/index/hello-gpt-4o).


Invoke the [/images/summarize](https://aiopsproxy.cluster.us-east-1.prod.cloud.netflix.net/docs#/default/summarize_images_images_summarize_post) Metatron endpoint. Sample call:

```
metatron curl -a aiopsproxy -X 'POST' \
'https://aiopsproxy.cluster.us-east-1.prod.cloud.netflix.net/images/summarize" -d 
'{
 "prompt": "Summarize the images",
  "files": [{
    "name": "nflx_logo",
    "content_type": "image/png",
    "base64_data": "i..........CC"
  },{
    "name": "emoji",
    "content_type": "image/png",
    "base64_data": "i......5CYII="
  }
]}'
```

Would output:

```
{
 "summary": "1. The first image is the Netflix logo, which features a red capital 'N' on a white background.\n2. The second image is a red icon with a white horizontal line in the center, often used to represent a \"Do Not Enter\" or \"No Entry\" sign.",
 "sources": [
   "nflx_logo",
   "emoji"
 ]
}```
