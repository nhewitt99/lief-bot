# This example requires the 'message_content' privileged intent to function.
import random
from discord.ext import commands
import discord

import utils
import buttons
import webcam_zmq


class Bot(commands.Bot):
    """
    Define a bot that keeps track of its own messages and cleans them up on close().
    All other commands get defined in main using decorators.
    """
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix=commands.when_mentioned_or('$'), intents=intents)
        self.my_messages = []

    async def on_ready(self):
        print(f'Logged in as {self.user} ({self.user.id})')

    async def on_message(self, message):
        # Keep track of my own messages to clean up later
        if message.author.id == self.application_id:
            self.my_messages.append(message)

        await super().on_message(message)

    async def close(self):
        for msg in self.my_messages:
            try:
                await msg.delete()
            except (discord.HTTPException, discord.Forbidden, discord.NotFound):
                pass
        await super().close()


class TestView(discord.ui.View):
    def __init__(self, capture):
        super().__init__()

        labels = [
            [None, "\u2191", None],
            ["\u21b6", "camera", "\u21b7"],
            [None, "\u2193", None],
        ]
        movement_dict = {
            "\u2191": "forward",
            "\u2193": "backward",
            "\u21b6": "ccw",
            "\u21b7": "cw",
        }

        view_buttons = buttons.parse_button_array(labels, movement_dict, capture)

        for b in view_buttons:
            self.add_item(b)


def main():
    bot = Bot()
    capture = webcam_zmq.CameraSubscriber()
    random_messages, random_weights = utils.parse_message_file("messages.txt")


    @bot.command()
    async def test(ctx: commands.Context):
        # Clean up the requester's message
        await ctx.message.delete()

        with open('test.png', 'rb') as f:
            default_file = discord.File(f)

        message_text = random.choices(random_messages, weights=random_weights, k=1)[0]
        await ctx.send(message_text, file=default_file, view=TestView(capture))

    @bot.command()
    async def shutdown(ctx: commands.Context):
        """
        Delete all messages the bot has sent and then disconnect
        """
        # Clean up the requester's message
        await ctx.message.delete()

        # Tell server we're shutting down
        await ctx.send('eepy time')
        await bot.close()
        print("Bot was shut down by request.")

    @bot.command()
    async def sus(ctx: commands.Context):
        await ctx.message.delete()
        with open('amogus.gif', 'rb') as f:
            file = discord.File(f, filename='amogus.gif')
        await ctx.send('when the imposter is SUS', file=file)

    try:
        with open('token.txt', 'r') as f:
            token = f.readline()
        bot.run(token)
    except KeyboardInterrupt:
        bot.close()
        print("Shutting down prematurely!")

    capture.cleanup()


if __name__=="__main__":
    main()

