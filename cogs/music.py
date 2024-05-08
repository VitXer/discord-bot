import asyncio
import os
import shutil
from datetime import datetime
from os.path import exists
from random import shuffle

import discord
import spotipy
import yt_dlp
from discord.ext import commands
from ffmpeg.asyncio import FFmpeg
from pydub import AudioSegment
from spotipy.oauth2 import SpotifyClientCredentials
from yt_dlp import YoutubeDL

deltime = 20


def get_spotify_playlist_tracks(playlist_or_album_or_track_url):
    client_id = os.getenv("SPOTIFY")
    client_secret = os.getenv("SPOTIFY_SECRET")

    client_credentials_manager = SpotifyClientCredentials(client_id, client_secret)
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

    if "playlist" in playlist_or_album_or_track_url:
        playlist_id = playlist_or_album_or_track_url.split('/')[-1].split('?')[0]
        results = sp.playlist_tracks(playlist_id)
        tracks_list = []
        for track in results['items']:
            track_info = track['track']
            artist = track_info['artists'][0]['name']
            title = track_info['name']
            tracks_list.append(f"{artist} - {title}")
        return tracks_list

    elif "album" in playlist_or_album_or_track_url:
        album_id = playlist_or_album_or_track_url.split('/')[-1].split('?')[0]
        results = sp.album_tracks(album_id)
    elif "track" in playlist_or_album_or_track_url:
        track_id = playlist_or_album_or_track_url.split('/')[-1].split('?')[0]
        track_info = sp.track(track_id)
        artist = track_info['artists'][0]['name']
        title = track_info['name']
        return [f"{artist} - {title}"]
    else:
        print("Niepoprawny link. Wprowadź link do playlisty, albumu lub pojedynczego utworu.")
        return []

    tracks_list = []

    for track in results['items']:
        artist = track['artists'][0]['name']
        title = track['name']
        tracks_list.append(f"{artist} - {title}")

    return tracks_list


def search_and_get_link(search_query):
    ydl_opts = {
        'extract_flat': True,
        'force_generic_extractor': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            search_results = ydl.extract_info(f"ytsearch:{search_query}", download=False)
            if 'entries' in search_results:
                first_result = search_results['entries'][0]
                video_url = f"https://www.youtube.com/watch?v={first_result['id']}"
                return video_url
        except Exception as e:
            print("Wystąpił błąd podczas wyszukiwania:", e)
            return None


def get_links(playlist_url):
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'force_generic_extractor': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            result = ydl.extract_info(playlist_url, download=False)
            videos = result.get('entries', []) if 'entries' in result else []
            video_links = [video['url'] for video in videos]
            return video_links
        except yt_dlp.DownloadError as e:
            print(f"Nie można pobrać informacji z playlisty: {e}")
            return []


async def queue_add(ctx, task_id):
    id = ctx.guild.id

    for i in range(1000):
        if not exists(f'servers/{id}/song{i + 1}.mp3'):
            os.rename(f'servers/{id}/song{task_id}.mp3', f'servers/{id}/song{i + 1}.mp3')
            return f'servers/{id}/song{i + 1}.mp3'


async def queue_hop(ctx):
    id = ctx.guild.id
    if exists(f'servers/{id}/song1.mp3'):
        os.remove(f'servers/{id}/song1.mp3')

    for i in range(1000):
        # print(i + 1)
        try:
            os.rename(f'servers/{id}/song{i + 2}.mp3', f'servers/{id}/song{i + 1}.mp3')
        except:
            ass = 0
            # print("XD")
    await play(ctx)


async def play(ctx):
    id = ctx.guild.id
    channel = ctx.author.voice.channel
    try:
        vc = await channel.connect()
    except:
        voice_client = ctx.guild.voice_client
        await voice_client.disconnect()
        vc = await channel.connect()
    if not exists(f'servers/{id}/song1.mp3'):
        voice_client = ctx.guild.voice_client
        await voice_client.disconnect()
        return
    vc.play(discord.FFmpegPCMAudio(f'servers/{id}/song1.mp3'))
    await ctx.guild.change_voice_state(channel=channel, self_mute=False, self_deaf=True)

    await ctx.send(f'Started playing next item in queue.', delete_after=deltime)
    while vc.is_playing():
        await asyncio.sleep(1)
    await queue_hop(ctx)


async def change_speed(input_path, output_path, speed_factor):
    # Load the MP3 file
    audio = AudioSegment.from_file(input_path, format="mp3")

    # Apply speed change
    audio_with_altered_speed = audio._spawn(audio.raw_data, overrides={
        "frame_rate": int(audio.frame_rate * speed_factor)
    }).set_frame_rate(audio.frame_rate)

    # Export the modified audio to the output path
    audio_with_altered_speed.export(output_path, format="mp3")


async def player(ctx, link, speed):
    ID = ctx.guild.id
    await ctx.respond("# Loading...", delete_after=deltime)
    await download_video(link, ctx, ID, speed)


async def is_short_video(link):
    durmin = 120
    dursec = durmin * 60

    ydl_opts = {'quiet': True}
    with YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(link, download=False)
        duration = info_dict.get('duration', 0)
        return duration < dursec  # 10 minutes in seconds


async def download_video(links, ctx, id, speed):
    if not speed:
        for link in links:
            if not await is_short_video(link):
                await ctx.respond(f"The video is too long. {link} Please provide a link to a video shorter than limit.",
                                  delete_after=deltime)
                return

            dt = datetime.now()

            task_id = datetime.timestamp(dt)

            output_path = f"servers/{id}/song{task_id}.mp3"

            filename = output_path  # f"servers/{id}/tempo{task_id}.webm"
            args = {'default_search': 'ytsearch',
                    'ignoreerrors': True,
                    'outtmpl': filename,
                    # 'format': 'bestaudio/worstvideo'
                    'format': 'bestaudio/best'
                    # ,'ratelimit': 10000000
                    }

            with YoutubeDL(args) as ydl:
                ydl.download(link)

            if speed and 0.1 <= speed <= 10000:
                os.rename(f'servers/{id}/song{task_id}.mp3', f'servers/{id}/songplay{task_id}.mp3')
                await change_speed(f'servers/{id}/songplay{task_id}.mp3', f'servers/{id}/song{task_id}.mp3', speed)
                os.remove(f'servers/{id}/songplay{task_id}.mp3')

            name = await queue_add(ctx, task_id)

            if name == f'servers/{id}/song1.mp3':
                taskmaster = asyncio.create_task(play(ctx))

            await ctx.send(f"{link} has been added to queue.", delete_after=deltime)
            print("Done!", "process finished")
    else:
        for link in links:
            if not await is_short_video(link):
                await ctx.respond(f"The video is too long. {link} Please provide a link to a video shorter than limit.",
                                  delete_after=deltime)
                return

            dt = datetime.now()

            task_id = datetime.timestamp(dt)

            output_path = f"servers/{id}/song{task_id}.mp3"

            filename = f"servers/{id}/tempo{task_id}.webm"
            args = {'default_search': 'ytsearch',
                    'ignoreerrors': True,
                    'outtmpl': filename,
                    'format': 'bestaudio/worstvideo'
                    # ,'ratelimit': 10000000
                    }

            with YoutubeDL(args) as ydl:
                ydl.download(link)

            await ctx.respond("# Applying speed. It might take some time.", delete_after=deltime)

            try:

                input_path = f"servers/{id}/tempo{task_id}.webm.mkv"

                if output_path.endswith(".webm"):
                    os.rename(input_path, output_path)
                else:
                    ffmpeg = FFmpeg().input(input_path).output(output_path, y='-y')
                    task = asyncio.create_task(ffmpeg.execute())
                    # os.system(f'ffmpeg -y -i "{input_path}" "{output_path}"')
                    await task
                    os.remove(input_path)
            except Exception as e:
                print(e)
                input_path = f"servers/{id}/tempo{task_id}.webm"
                if output_path.endswith(".webm"):
                    os.rename(input_path, output_path)
                else:
                    ffmpeg = FFmpeg().input(input_path).output(output_path, y='-y')
                    task = asyncio.create_task(ffmpeg.execute())
                    # os.system(f'ffmpeg -y -i "{input_path}" "{output_path}"')
                    await task
                    os.remove(input_path)

            if speed and 0.1 <= speed <= 10000:
                os.rename(f'servers/{id}/song{task_id}.mp3', f'servers/{id}/songplay{task_id}.mp3')
                await change_speed(f'servers/{id}/songplay{task_id}.mp3', f'servers/{id}/song{task_id}.mp3', speed)
                os.remove(f'servers/{id}/songplay{task_id}.mp3')

            name = await queue_add(ctx, task_id)

            if name == f'servers/{id}/song1.mp3':
                taskmaster = asyncio.create_task(play(ctx))

            await ctx.send(f"{link} has been added to queue.", delete_after=deltime)
            print("Done!", "process finished")


class music(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print('music active')

    @commands.slash_command(name="resume")
    async def resume(self, ctx):
        await ctx.respond("Resumed", delete_after=deltime)

    @commands.slash_command(name="stop", description="stops the player")
    async def stop(self, ctx):
        id = ctx.guild.id
        shutil.rmtree(f'servers/{id}')
        await ctx.respond("Stopped.", delete_after=deltime)
        voice_client = ctx.guild.voice_client
        await voice_client.disconnect()

    @commands.slash_command(name="skip", description="skips to the next item in player queue")
    async def skip(self, ctx):
        id = ctx.guild.id
        voice_client = ctx.guild.voice_client
        await voice_client.disconnect()
        await ctx.respond("Skipped.", delete_after=deltime)

    @commands.slash_command(name="play", description="plays music on VC from YT")
    async def play(self, ctx, search: str, speed: float = None, randomise_playlist: bool = False,
                   invert_playlist: bool = False, amount: int = 1):

        if search == "klasyczek":
            search = "https://open.spotify.com/playlist/6N5FdKiShxXMk7Z1TXE7od?si=21795ba34e8b42da"

        if "https://open.spotify.com/playlist/" in search or "https://open.spotify.com/album/" in search or "https://open.spotify.com/track/" in search:
            linke = get_spotify_playlist_tracks(search)
        else:
            linke = [search]

        if randomise_playlist:
            shuffle(linke)

        if len(linke) >= 20:
            linke = linke[:20]
            await ctx.respond("Eat shit idiot.", delete_after=3)

        for link in linke:

            if link == "mighty":
                link = 'https://www.youtube.com/playlist?list=PLrUKOTaX534A4BXCrLjEn578ZbAXKQS21'

            if link == "haxar":
                link = 'https://www.youtube.com/playlist?list=PLhCswEbgn5CCe9FI7aCVTYQS0u9RNc8YL'

            if "https://www.youtube.com/watch?v=" in link:
                links = [link]
            elif "https://youtu.be/" in link:
                links = [link]
            elif "https://www.youtube.com/playlist?list=" in link:
                links = get_links(link)
            else:
                links = [search_and_get_link(link)]

            id = ctx.guild.id

            if amount and (10 < amount or amount < 1):
                await ctx.respond("The amount range is 1 - 10")
                return
            for i in range(amount):

                ts = datetime.timestamp(datetime.now())

                if speed and (0.1 > speed or speed > 10000):
                    await ctx.respond("The speed range is 0.1 - 10000.")
                    return

                if randomise_playlist:
                    shuffle(links)

                if invert_playlist:
                    links.reverse()

                task = asyncio.create_task(player(ctx, links, speed))

                await task


def setup(bot):
    bot.add_cog(music(bot))
