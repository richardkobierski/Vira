import os
import asyncio
import discord
from dotenv import load_dotenv
from discord import app_commands, FFmpegPCMAudio, PCMVolumeTransformer
from pytube import YouTube
from pytube import Search

intents = discord.Intents.default()
client = discord.Client(intents=intents)
slash = app_commands.CommandTree(client)
load_dotenv()
songQueue = []
musicMessage = discord.Message
ffmpegSettings = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}


def checkIfSame(first, second):
    if first is second:
        return True
    return False


def isValidReaction(reaction, user):
    if user != client.user and reaction.message.id == musicMessage.id:
        return True
    return False


async def reactionFunctions(reaction, user, vc):
    if str(reaction.emoji) == '⏸️':
        await musicMessage.remove_reaction(reaction.emoji, user)
        vc.pause()
    elif str(reaction.emoji) == '▶️':
        await musicMessage.remove_reaction(reaction.emoji, user)
        vc.resume()
    elif str(reaction.emoji) == '⏩':
        await musicMessage.remove_reaction(reaction.emoji, user)
        vc.stop()
        await asyncio.sleep(5000)
        await currentSong(reaction.message, vc)


async def formatUI(msg, title, description):
    messageUI = discord.Embed(title=title, description=description)
    await msg.response.send_message(embed=messageUI, delete_after=10.0)


async def isValidUserVoiceChannel(msg, function, description):
    try:
        vc = msg.user.voice.channel
        return True
    except AttributeError:
        await formatUI(msg, function, description)
        return False


def clearQueue():
    if len(songQueue) > 0:
        songQueue.clear()


def isEmpty(botQueue):
    if len(botQueue) == 0:
        return True
    return False


async def addSong(song):
    song = await searchOrLink(song)
    songQueue.append(song)


async def createMusicUI(msg):
    global musicMessage
    musicUI = discord.Embed(title="Music Player", description=f'Current Song: {YouTube(songQueue[0]).title}')
    await msg.response.send_message(embed=musicUI)
    musicMessage = await msg.original_response()
    await addUIReactions(musicMessage)


async def updateMusicUI(msg):
    if len(songQueue) >= 2:
        print(songQueue)
        musicUIUpdate = discord.Embed(title="Music Player", description=f'Current Song: {YouTube(songQueue[1]).title}')
        await msg.edit_original_response(embed=musicUIUpdate)
    else:
        musicUIUpdate = discord.Embed(title="Music Player", description="Queue Finished")
        await musicMessage.clear_reactions()
        await msg.edit_original_response(embed=musicUIUpdate)


async def formatQueue(msg):
    songList = ""
    counter = 0
    for songs in songQueue:
        if counter == 0:
            songList += f'**NOW PLAYING:** {YouTube(songs).title}\n'
            counter += 1
        else:
            songList += f'**#{counter}:** {YouTube(songs).title}'
            songList += "\n"
            counter += 1
    await formatUI(msg, "Queue", songList)


async def searchOrLink(song):
    if "https://www.youtube.com/watch?v=" in song:
        return song
    else:
        searchName = Search(song)
        searchResult = searchName.results[0]
        searchLink = f'https://www.youtube.com/watch?v={searchResult.video_id}'
        return searchLink


async def currentSong(msg, vc):
    directory = os.getcwd() + "\\ffmpeg-n5.1-latest-win64-gpl-5.1\\bin\\ffmpeg.exe"
    print(directory)
    if isEmpty(songQueue):
        await vc.disconnect()
        return
    curSong = YouTube(songQueue[0])
    audio = curSong.streams.get_audio_only()
    player = FFmpegPCMAudio(
        executable=directory,
        source=audio.url, **ffmpegSettings)
    volumeAdjuster = PCMVolumeTransformer(player, volume=0.1)
    vc.play(volumeAdjuster)
    while vc.is_playing() or vc.is_paused():
        await asyncio.sleep(1)
    await updateMusicUI(msg)
    await nextSong(msg, vc)


async def nextSong(msg, vc):
    if songQueue is not None and not isEmpty(songQueue):
        songQueue.pop(0)
        await currentSong(msg, vc)
    await vc.disconnect()


async def addUIReactions(msg):
    await msg.add_reaction('⏸️')
    await msg.add_reaction('▶️')
    await msg.add_reaction('⏩')


@client.event
async def on_ready():
    await slash.sync()
    await client.change_presence(activity=discord.Streaming(name="music", url="https://github.com/richardkobierski"))
    print("Bot Started")


@client.event
async def on_reaction_add(reaction, user):
    botVC = reaction.message.guild.voice_client
    userVC = user.voice.channel
    if checkIfSame(botVC.channel, userVC) and isValidReaction(reaction, user):
        await reactionFunctions(reaction, user, botVC)
    elif not checkIfSame(botVC.channel, userVC):
        await musicMessage.remove_reaction(reaction.emoji, user)


@slash.command(name="ping", description="Check bot response")
async def ping(msg):
    await formatUI(msg, "Ping", f'pong! {round(client.latency * 1000)}ms')


@slash.command(name="join", description="Joins voice channel")
async def join(msg):
    vc = msg.guild.voice_client
    validUserVoice = await isValidUserVoiceChannel(msg, "Join", "Unable to connect: user not in a voice channel")
    if not validUserVoice:
        return
    userVC = msg.user.voice.channel
    if vc is None:
        await formatUI(msg, "Join", "Connected")
        await userVC.connect()
    elif vc is not None:
        await formatUI(msg, "Join", "Unable to connect: already connected")


@slash.command(name="leave", description="Leaves voice channel")
async def leave(msg):
    vc = msg.guild.voice_client
    validUserVoice = await isValidUserVoiceChannel(msg, "Leave", "Unable to disconnect: user not in channel")
    if not validUserVoice:
        return
    userVC = msg.user.voice.channel
    if vc is None:
        await formatUI(msg, "Leave", "Unable to disconnect: already disconnected")
    elif checkIfSame(vc.channel, userVC):
        clearQueue()
        await formatUI(msg, "Leave", "Disconnected")
        await vc.disconnect()
    else:
        await formatUI(msg, "Leave", "Unable to disconnect: wrong channel")


@slash.command(name="play", description="Play a video from youtube!")
async def play(msg, song: str):
    vc = msg.guild.voice_client
    validUserVoice = await isValidUserVoiceChannel(msg, "Play", "Unable to play: user not in channel")
    if not validUserVoice:
        return
    userVC = msg.user.voice.channel
    if isEmpty(songQueue) and vc is None:
        vc = await userVC.connect()
        await addSong(song)
        await createMusicUI(msg)
        await currentSong(msg, vc)
    elif not checkIfSame(vc.channel, userVC):
        await formatUI(msg, "Play", "Unable to play: wrong voice channel")
    else:
        await addSong(song)
        await formatUI(msg, "Music Player",
                       f'Added {YouTube(songQueue[len(songQueue) - 1]).title} to the queue, position #' + str(
                           len(songQueue) - 1))


@slash.command(name="skip", description="Skips current song")
async def skip(msg):
    vc = msg.guild.voice_client
    validUserVoice = await isValidUserVoiceChannel(msg, "Skip", "Unable to skip: user not in a voice channel")
    if not validUserVoice:
        return
    userVC = msg.user.voice.channel
    if vc is None:
        await formatUI(msg, "Skip", "Unable to skip: bot not in a voice channel")
    elif not checkIfSame(vc.channel, userVC):
        await formatUI(msg, "Skip", "Unable to skip: wrong voice channel")
    elif not isEmpty(songQueue):
        await formatUI(msg, "Skip", "Skipping song")
        vc.stop()
        await asyncio.sleep(5000)
        await currentSong(msg, vc)
    else:
        await formatUI(msg, "Skip", "Unable to skip: no song playing")


@slash.command(name="pause", description="Pauses current song")
async def pause(msg):
    vc = msg.guild.voice_client
    validUserVoice = await isValidUserVoiceChannel(msg, "Pause", "Unable to pause: user not in a voice channel")
    if not validUserVoice:
        return
    userVC = msg.user.voice.channel
    if vc is None:
        await formatUI(msg, "Pause", "Unable to pause: bot not in voice channel")
    elif not checkIfSame(vc.channel, userVC):
        await formatUI(msg, "Pause", "Unable to pause: wrong voice channel")
    elif not isEmpty(songQueue):
        await formatUI(msg, "Pause", "Pausing song")
        vc.pause()
    else:
        await formatUI(msg, "Pause", "Unable to pause: no song playing")


@slash.command(name="resume", description="Resumes current song")
async def resume(msg):
    vc = msg.guild.voice_client
    validUserVoice = await isValidUserVoiceChannel(msg, "Resume", "Unable to pause: user not in a voice channel")
    if not validUserVoice:
        return
    userVC = msg.user.voice.channel
    if vc is None:
        await formatUI(msg, "Resume", "Unable to resume: bot not in voice channel")
    elif not checkIfSame(vc.channel, userVC):
        await formatUI(msg, "Resume", "Unable to resume: wrong voice channel")
    elif not isEmpty(songQueue):
        await formatUI(msg, "Resume", "Resuming song")
        vc.resume()
    else:
        await formatUI(msg, "Resume", "Unable to resume: no song playing")


@slash.command(name="queue", description="Shows song queue")
async def queue(msg):
    vc = msg.guild.voice_client
    validUserVoice = await isValidUserVoiceChannel(msg, "Queue", "Unable to pause: user not in a voice channel")
    if not validUserVoice:
        return
    userVC = msg.user.voice.channel
    if vc is None:
        await formatUI(msg, "Queue", "Unable to show queue: bot not in voice channel")
    elif not checkIfSame(vc.channel, userVC):
        await formatUI(msg, "Queue", "Unable to show queue: wrong voice channel")
    elif not isEmpty(songQueue):
        await formatQueue(msg)
    else:
        await formatUI(msg, "Queue", "Unable to show queue: no queue")


client.run(os.getenv('BOT_TOKEN'))
