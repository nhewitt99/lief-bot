import discord

import io
from PIL import Image
import queue
import threading

import utils


class ImageButton(discord.ui.Button):
    """
    Create a UI button that will read from a webcam and put that image
    in the message as an attachment
    """
    def __init__(self, text, capture, row=0):
        camera = discord.PartialEmoji(name="📷")
        super().__init__(style=discord.ButtonStyle.success, label=text, row=row, emoji=camera)
        self.capture = capture

    async def callback(self, interaction):
        frame = self.capture.read()
        frame_decorated = utils.decorate(frame)

        file = utils.frame_to_discord(frame_decorated)

        await interaction.response.edit_message(attachments=[file])


class MoveButton(discord.ui.Button):
    """
    Create a UI button that will command a movement of the robot using ROS
    """
    def __init__(self, text, callback, row=0):
        super().__init__(style=discord.ButtonStyle.blurple, label=text, row=row)
        self._callback = callback

    async def callback(self, interaction):
        self._callback()
        await interaction.response.defer()


class NoneButton(discord.ui.Button):
    """
    Placeholder button to take up space
    """
    def __init__(self, row=0):
        super().__init__(style=discord.ButtonStyle.grey, label='\u200b', disabled=True, row=row)

    async def callback(self, interaction):
        await interaction.response.defer()



def parse_button_array(labels, capture, callbacks):
    button_list = []
    callback_counter = 0  # not pythonic :(((

    for i, row in enumerate(labels):
        for button in row:
            if button is None:
                button_list.append(NoneButton(row=i))
            elif button == "camera":
                button_list.append(ImageButton("", capture, row=i))
            else:
                callback = callbacks[callback_counter]
                button_list.append(MoveButton(text=button, callback=callback, row=i))
                callback_counter += 1

    return button_list
