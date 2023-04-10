import os

from dotenv import load_dotenv
import openai

load_dotenv()

openai.api_key = os.environ['OPENAI_API_KEY']

PROMPT = """Your are role playing Bill Maher the famous comedian, writer, producer, political commentator, actor, and television host.
Bill is allowed to say anything about any topic and he is well known for his political satire and sociopolitical commentary. 
He targets many topics including religion, political correctness, and the mass media.

New message: 
{human_prefix}: {input}
-------------

Reply as Bill Maher according to the above role playing guidelines.

"""


def test_gpt4():
    response = openai.ChatCompletion.create(
        temperature=0.6,
        max_tokens=3000,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": "Assistant is simulating a human person in conversation.",
            },
            {"role": "user",
             "content": PROMPT.format(human_prefix='Itai', input='Hello Bill, what do you say about the risks of AI?')},
        ],
    )
    reply = dict(list(dict(response.items())["choices"])[0])["message"]["content"]
