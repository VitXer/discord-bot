import requests
from discord.ext import commands
from googletrans import Translator

history = [{'role': 'system', 'content': 'You are Ai-chan. You are female. You are a helpful assistant.'}]


class aitext(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.url = "http://127.0.0.1:5000/v1/chat/completions"
        self.headers = {
            "Content-Type": "application/json"
        }

    @commands.Cog.listener()
    async def on_ready(self):
        print('aitext active')

    @commands.slash_command(name="askai", description="Ask AI about a topic")
    async def askai(self, ctx, user_message: str):
        trans = Translator()
        trans = trans.translate(user_message, dest="en")
        lang = trans.src

        if trans.src == "en":
            history.append({"role": "user", "content": user_message})
            print("not translating")
        else:
            history.append({"role": "user", "content": trans.text})
            print("translating")

        await ctx.respond(f"Generating response to {user_message} in lang {trans.src}")

        data = {
            "mode": "chat",
            "character": "Example",
            "messages": history
        }

        response = requests.post(self.url, headers=self.headers, json=data, verify=False)
        assistant_message = response.json()['choices'][0]['message']['content']
        history.append({"role": "assistant", "content": assistant_message})

        print(history)
        if trans.src == "en":
            await ctx.respond(assistant_message)
        else:
            await ctx.respond(Translator().translate(assistant_message, dest=lang).text)

    @commands.slash_command(name="forget", description="forgets ai conversation")
    async def forget(self, ctx):
        global history
        history = [{'role': 'system', 'content': 'You are Ai-chan. You are female. You are a helpful assistant.'}]
        await ctx.respond("Forgor")


def setup(bot):
    bot.add_cog(aitext(bot))
