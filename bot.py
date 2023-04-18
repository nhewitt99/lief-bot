# This example requires the 'message_content' privileged intent to function.
import sys
import random
from discord.ext import commands
import discord

import utils
import buttons
import webcam_zmq
import standalone_ros2


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


class DirectionalView(discord.ui.View):
    def __init__(self, capture, callbacks):
        super().__init__()

        labels = [
            [None, "\u2191", None],
#            ["\u21b6", None, "\u21b7"],
            ["\u21b6", "camera", "\u21b7"],
            [None, "\u2193", None],
        ]

        view_buttons = buttons.parse_button_array(labels, capture, callbacks)

        for b in view_buttons:
            self.add_item(b)


def main():
    # This spins up a ROS 2 node to send velocity commands
    ros_pub = standalone_ros2.VelocityInterface()

    # This talks to Discord
    bot = Bot()

    # Connect to a camera stream
    address = "127.0.0.1"
    if len(sys.argv) > 1:
        address = sys.argv[1]
    capture = webcam_zmq.CameraSubscriber(address=address)

    # Open the file of welcome messages
    random_messages, random_weights = utils.parse_message_file("messages.txt")

    # In order of appearance on button pad: up left right down
    callbacks = [
        lambda: ros_pub.pub_velocity(0.306, 0.0),
        lambda: ros_pub.pub_velocity(0.0, 0.7),
        lambda: ros_pub.pub_velocity(0.0, -0.7),
        lambda: ros_pub.pub_velocity(-0.153, 0.0),
    ]

    @bot.command()
    async def test(ctx: commands.Context):
        # Clean up the requester's message
        await ctx.message.delete()

        # Default image
        with open('test.png', 'rb') as f:
            default_file = discord.File(f)

        # Pick a random welcome message and set up UI
        message_text = random.choices(random_messages, weights=random_weights, k=1)[0]
        message_view = DirectionalView(capture, callbacks=callbacks)

        await ctx.send(message_text, file=default_file, view=message_view)

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
        # Clean up requester's message
        await ctx.message.delete()

        with open('amogus.gif', 'rb') as f:
            file = discord.File(f, filename='amogus.gif')

        await ctx.send('when the imposter is SUS', file=file)

    # Start the bot using auth token and wait for interrupt
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

