#!/usr/bin/env python
import openai
from elevenlabs import set_api_key, generate
import itertools
from dotenv import load_dotenv
from pprint import pprint
from urllib.parse import urlparse
from newsplease import NewsPlease
from typing import List
import fire
import os
import io
import re
import json
import glob
from pydub import AudioSegment
from pathlib import Path
load_dotenv()

OPENAI_API_KEY = os.environ['OPENAI_API_KEY']
openai.api_key = OPENAI_API_KEY
set_api_key(os.environ['IIELEVENLABS_API_KEY'])

def is_good_url(url:str):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False
    
    
def slugify(s):
  s = s.lower().strip()
  s = re.sub(r'[^\w\s-]', '', s)
  s = re.sub(r'[\s_-]+', '-', s)
  s = re.sub(r'^-+|-+$', '', s)
  return s  


def get_article_summary(article: NewsPlease) -> str:
    messages = [{"role": "system", "content": "You are a helpful assistant that summarize technology articles."}, 
                {"role": "user", "content": """
                 Here's a text I want you to summarize to between 150 and 300 words and also change the tone to provide a text that will be read out loud. 
                 Read out loud the summary should ressemble a news summary, short, informative, friendly.
                 The output is read at the third person (as a narrator). 
                 The summary should only talk about the news article. 
                 Here's the article : """ + article.maintext}, 
            ]
    response = openai.ChatCompletion.create(model="gpt-4", messages=messages)
    return response["choices"][0]["message"]["content"]



def save_articles_to_json_file(articles:List[NewsPlease]) -> None:
    with open("./articles.json", "w") as f:
        f.write(json.dumps(articles, indent=4, separators=(',', ': '),  sort_keys=True, default=str))

def join_podcasts() -> None:
    path = "final/"
    Path(path).mkdir(exist_ok=True)
    files_list = sorted(glob.glob(path+"*.mp3"))
    combined_wav = AudioSegment.empty()
    silence = AudioSegment.silent(duration=2000)
    for pod in files_list:
        podcast = AudioSegment.from_file(pod)
        combined_wav += silence + podcast
    byte_array = generate(
        text = "This podcast is brought to you by Flint. s h, Tech consulting company, made with the help of OpenAI and Elevenlabs.",
        model="eleven_monolingual_v1",
        voice = "oWAxZDx7w5VEj9dCyTzz"
    )
    s = AudioSegment.from_file_using_temporary_files(io.BytesIO(byte_array))
    combined_wav += silence + s
    combined_wav.export("final/podcast_final.mp3", format="mp3")


def save_transcript(transcript:str) -> None:
    with open("./final/transcript.txt", "w") as f:
        f.write(transcript)

def create_podcast() -> None:
    with open('articles.json') as articles:
        articles = json.loads(articles.read())
        
    voice = itertools.cycle(['oWAxZDx7w5VEj9dCyTzz', 'flq6f7yk4E4fJM5XTYuZ'])
    transcript = ""
    for idx, article in enumerate(articles):
        byte_array = generate(
                            text = article["maintext"],
                            model="eleven_monolingual_v1",
                            voice = next(voice)
                        )
        s = AudioSegment.from_file_using_temporary_files(io.BytesIO(byte_array))
        s.export("final/"+str(idx)+".mp3", format="mp3")
        source = "N/A"
        if article["url"]:
            source = article["url"]
        transcript += "\n\n---\n" + article["maintext"] + "\n\nSource => " + source
    join_podcasts()
    save_transcript(transcript)

def main(*args):
    articles = []
    for url in args:
        if is_good_url(url):
            article = NewsPlease.from_url(url)
            article.maintext = get_article_summary(article)
            articles.append(article.get_dict())
        else:
            print(f"L'URL {url} n'est pas valide.")

    save_articles_to_json_file(articles)
    
if __name__ == '__main__':
    fire.Fire({
      '--url': main,
      '--create_podcasts': create_podcast,
      '--join_podcasts': join_podcasts,
  })

    
    