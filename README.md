# Vira
Vira is a lightweight Discord music bot that plays music on YouTube.
# Commands
* /join - Joins the user's voice channel.
* /leave - Leaves the user's voice channel.
* /play - Plays a song in the voice channel.
* /pause - Pauses music at the current time.
* /resume - Resumes playing music at paused time.
* /queue - Shows the user's queue.
# Features
1. Discord bots can create a lot of chat clutter when users constantly execute commands. Vira helps reduce chat clutter by automatically removing non-critical messages after a few seconds. 
2. Other music bots take up a lot of local storage because they download the songs before playing them. Vira does not; it streams the music directly from YouTube itself!
3. Each time users create a new session, Vira creates a music controller inside the channel, allowing users to use reactions to pause, play, or skip a song!
<img width="442" alt="Music Controller" src="https://github.com/richardkobierski/Vira/assets/160172357/4534a502-17ef-4cc1-aa10-9377a551ddeb">

# Requirements
Vira requires two things to run, which are listed below.
* FFMPEG - This is the bot's audio player. (https://ffmpeg.org/)
* Discord.py[voice] - This is required for the bot to play music through the voice channel. (https://discordpy.readthedocs.io/en/latest/intro.html)
