import asyncio
import os

import discord
import requests
from PIL import Image, ImageDraw, ImageFont
from discord.ext import commands
from dotenv import load_dotenv

WARNING_CHANNEL_ID = os.getenv("WARNING_CHANNEL_ID")
coords = []


def fetch_data():
    load_dotenv()

    IP = os.getenv("SERVER_IP")
    PORT = os.getenv("SERVER_API_PORT")

    url_trains = f"http://{IP}:{PORT}/api/trains"
    url_network = f"http://{IP}:{PORT}/api/network"

    try:
        response_trains = requests.get(url_trains)
        response_trains.raise_for_status()  # Raises exception for 4xx or 5xx status codes
        data_trains = response_trains.json()  # Parse response as JSON

        response_network = requests.get(url_network)
        response_network.raise_for_status()  # Raises exception for 4xx or 5xx status codes
        data_network = response_network.json()  # Parse response as JSON

        return data_trains, data_network

    except requests.exceptions.RequestException as e:
        print("Wystąpił błąd podczas żądania HTTP:", e)
        return None, None


def plot_map(trains_data, network_data, ERROR_ID):
    if trains_data is None or network_data is None:
        return
    minx = float('inf')
    maxx = -float('inf')
    miny = float('inf')
    maxy = -float('inf')

    for track in network_data['tracks']:
        for path in track['path']:
            if path['x'] > maxx:
                maxx = path['x']
            if path['x'] < minx:
                minx = path['x']
            if path['z'] > maxy:
                maxy = path['z']
            if path['z'] < miny:
                miny = path['z']

    img_size_x = maxx - minx + 30
    img_size_y = maxy - miny + 30

    addx = -minx + 15
    addz = -miny + 15

    with Image.new('RGBA', (int(img_size_x), int(img_size_y)), (255, 255, 255, 255)) as im:

        draw = ImageDraw.Draw(im)
        font = ImageFont.truetype("arial.ttf", 12)

        for track in network_data['tracks']:
            draw_track(draw, addx, addz, track)

        for train in trains_data['trains']:

            for car in train['cars']:
                LEADING = addx + car['leading']['location']['x'], addz + car['leading']['location']['z']
                TRAILING = addx + car['trailing']['location']['x'], addz + car['trailing']['location']['z']

                draw.line(
                    (LEADING, TRAILING), (255, 0, 127, 255), width=3)

            TEXT_POS = (addx + train['cars'][0]['leading']['location']['x'] - 3,
                        addz + train['cars'][0]['leading']['location']['z'] - 6)

            draw.text(TEXT_POS, train['name'], fill=(0, 255, 0, 255), font=font)

            if train['id'] in ERROR_ID:
                draw.line((addx + train['cars'][0]['leading']['location']['x'] + 50,
                           addz + car['leading']['location']['z'] + 50,
                           addx + train['cars'][0]['leading']['location']['x'] - 50,
                           addz + car['leading']['location']['z'] - 50),
                          (255, 0, 0, 255), width=6)
                draw.line((addx + train['cars'][0]['leading']['location']['x'] - 50,
                           addz + car['leading']['location']['z'] + 50,
                           addx + train['cars'][0]['leading']['location']['x'] + 50,
                           addz + car['leading']['location']['z'] - 50),
                          (255, 0, 0, 255), width=6)

                global coords

                coords.append(train['cars'][0]['leading']['location'])

        im.save(f"MAP.png", "PNG")


def draw_track(draw, addx, addz, track, color=(0, 0, 0, 255), width=0, segments=5):
    path = track['path']

    if len(path) == 2:
        points = path
    elif path[0]['x'] == path[-1]['x'] or path[0]['z'] == path[-1]['z']:
        points = [{'x': path[0]['x'], 'z': path[0]['z']}, {'x': path[-1]['x'], 'z': path[-1]['z']}]
    else:
        points = bezier_curve(*path, segments=segments)

    draw.line([(addx + point['x'], addz + point['z']) for point in points], color, width)


def bezier_curve(p0, p1, p2, p3, segments):
    points = []
    for i in range(segments + 1):
        t = i / segments
        x = (1 - t) ** 3 * p0['x'] + 3 * (1 - t) ** 2 * t * p1['x'] + 3 * (1 - t) * t ** 2 * p2['x'] + t ** 3 * p3['x']
        y = (1 - t) ** 3 * p0['z'] + 3 * (1 - t) ** 2 * t * p1['z'] + 3 * (1 - t) * t ** 2 * p2['z'] + t ** 3 * p3['z']
        points.append({'x': x, 'z': y})
    return points


deltime = 5


class create_track(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print('create_track active')
        new_data = fetch_data()
        global coords
        while True:
            channel = self.client.get_channel(int(WARNING_CHANNEL_ID))

            await asyncio.sleep(5)

            old_data = new_data

            new_data = fetch_data()

            ERROR_ID = []

            for train_new, train_old in zip(new_data[0]['trains'], old_data[0]['trains']):

                if train_new['cars'][0]['leading']['location'] == train_old['cars'][0]['leading']['location'] and \
                        train_new['stopped'] != True:
                    ERROR_ID.append(train_new['id'])

            TRAIN_DATA, TRACK_DATA = new_data

            plot_map(TRAIN_DATA, TRACK_DATA, ERROR_ID)

            print(ERROR_ID)

            text = "WARNING!\nCOLLISION DETECTED AT"

            for coord in coords:
                text += f"\n{coord}"

            if len(ERROR_ID) > 0:
                with open("MAP.png", "rb") as f:
                    await channel.send(files=[discord.File(f)], delete_after=60)
                    await channel.send(text, delete_after=60)
                os.remove("MAP.png")
                await asyncio.sleep(55)


def setup(bot):
    bot.add_cog(create_track(bot))
