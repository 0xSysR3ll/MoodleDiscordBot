import discord
from discord.ext import tasks
from modules.config import Config
from modules.framagenda import *
from ics import Calendar
import arrow
from collections import defaultdict
from modules.logger_config import setup_logger

# Set up the logger
logger = setup_logger()

# Load the configuration
config = Config('config/config.yml')
config.load()

# Get discord and calendar details from the config
discord_token = config.get_config('discord', 'token')
discord_channels = config.get_config('discord', 'channels')
discord_guilds = config.get_config('discord', 'guilds')
calendar_url = config.get_config('calendar', 'url')

# Initialize the bot
logger.info("Initializing bot...")
try:
    bot = discord.Bot(guild_ids=discord_guilds)
except Exception as e:
    logger.error(f"Error initializing bot: {e}")

# Define a daily task that sends events for the week or for today

@tasks.loop(hours=24)
async def daily_task():
    current_date = arrow.now()
    today = arrow.now().format('YYYY-MM-DD')
    week = arrow.now().shift(days=+7).format('YYYY-MM-DD')

    for discord_channel in discord_channels:
        channel = bot.get_channel(discord_channel)
        if current_date.weekday() == 0 and current_date.hour == 8:
            await send_events(None, channel, today, week, "pour cette semaine")
        elif current_date.weekday() != 0 and current_date.hour == 8:
            await send_events(None, channel, today, today, 'pour aujourd\'hui')

# Define the bot's behavior when it's ready


@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user}!")
    logger.info("Downloading calendar...")
    try:
        download_calendar(calendar_url)
    except Exception as e:
        logger.error(f"Error downloading calendar: {e}")
    logger.info("Syncing commands...")
    await bot.sync_commands(force=True)
    logger.info("Starting daily task...")
    try:
        daily_task.start()
    except Exception as e:
        logger.error(f"Error starting daily task: {e}")

# Define a ping command that sends the bot's latency
@bot.command(name='ping', description="Sends the bot's latency.")
async def ping_command(ctx):
    logger.info(f"Received command 'ping' from {ctx.author} in {ctx.channel}!")
    latency = round(bot.latency * 1000)
    await ctx.respond(f"Pong! ({latency}ms)")


# This function is used to send a list of events to a Discord channel
async def send_events(ctx, channel, start_date, end_date, time_range):
    # Parse the calendar events between the start and end dates
    events = parse_calendar(start_date, end_date)

    # Create a set of all unique words in event names for checking presence of certain words later
    event_name_words = set(
        word for event in events for word in event.name.split())

    # Check for presence of "DISTANCIEL" and "PRESENTIEL" in event names and store them in event_mode
    event_mode = []
    if "DISTANCIEL" in event_name_words:
        logger.debug("DISTANCIEL found in event names!")
        event_mode.append("DISTANCIEL")
    if "PRESENTIEL" in event_name_words:
        logger.debug("PRESENTIEL found in event names!")
        event_mode.append("PRESENTIEL")

    # If there are no events, create an embed message saying no courses are planned
    if len(events) == 0:
        logger.debug("No events found!")
        embed_title = f"📅 Agenda {time_range}"
        embed_description = f"Bonjour ! Il n'y a pas de cours prévu {time_range} !"
        embed = discord.Embed(
            title=embed_title, description=embed_description, color=discord.Color.blue())
    else:
        # If there are events, group them by day
        events_by_day = defaultdict(list)
        for event in events:
            events_by_day[event.begin.format('YYYY-MM-DD')].append(event)

        # Create an embed message to display the events
        embed_title = f"📅 Agenda {time_range}"
        if event_mode:
            embed_title += f" ({', '.join(event_mode)})"
        embed = discord.Embed(title=embed_title, color=discord.Color.orange())

        # For each day, add a field to the embed message with the events for that day
        for day, events in sorted(events_by_day.items(), key=lambda item: arrow.get(item[0], 'YYYY-MM-DD')):
            events_str = ""
            for event in sorted(events, key=lambda e: e.begin):
                if "DISTANCIEL" in event.name or "PRESENTIEL" in event.name:
                    continue
                description = f"Description: {event.description}\n" if event.description else ""
                location = f"Lieu: {event.location}\n" if event.location else ""
                events_str += f"\n**{event.name}**\nDe {event.begin.format('HH:mm')} à {event.end.format('HH:mm')}\n{description}{location}"
            embed.add_field(name=arrow.get(day, 'YYYY-MM-DD').format('dddd D MMMM YYYY',
                            locale='fr').capitalize(), value=events_str, inline=True)

    # If this is a Discord interaction, respond to the interaction with the embed message
    if ctx is not None and isinstance(ctx, discord.Interaction):
        logger.info(f"Sending response to {ctx.author} in {ctx.channel.name}!")
        try:
            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error sending response: {e}")
    else:
        logger.info(f"Sending message to {channel}!")
        # Otherwise, send the embed message to the provided channel
        try:
            await channel.send(embed=embed)
        except Exception as e:
            logger.error(f"Error sending message: {e}")


# This function is a command that sends today's events to the Discord channel
@bot.command(name='today', description="Sends today's events.")
async def today_command(ctx):
    logger.info(f"Received command 'today' from {ctx.author} in {ctx.channel}!")
    # Defer the interaction to ensure the command doesn't time out
    await ctx.defer(ephemeral=True)

    # Get the current date in YYYY-MM-DD format
    today = arrow.now().format('YYYY-MM-DD')

    # Set the time range string for today
    time_range = "pour aujourd'hui"

    # Send a response to indicate processing is underway
    try:
        await ctx.respond('Traitement de la demande en cours... :hourglass_flowing_sand:')
    except Exception as e:
        logger.error(f"Error sending response: {e}")

    # Call the send_events function to fetch and send the events for today
    try:
        await send_events(ctx, ctx.channel, today, today, time_range)
    except Exception as e:
        logger.error(f"Error sending events: {e}")


# This function is a command that sends tomorrow's events to the Discord channel
@bot.command(name='tomorrow', description="Sends tomorrow's events.")
async def tomorrow_command(ctx):
    logger.info(f"Received command 'tomorrow' from {ctx.author} in {ctx.channel}!")
    # Defer the interaction to ensure the command doesn't time out
    await ctx.defer(ephemeral=True)

    # Get the date for tomorrow in YYYY-MM-DD format
    tomorrow = arrow.now().shift(days=+1).format('YYYY-MM-DD')

    # Set the time range string for tomorrow
    time_range = "pour demain"

    # Send a response to indicate processing is underway
    try:
        await ctx.respond('Traitement de la demande en cours... :hourglass_flowing_sand:')
    except Exception as e:
        logger.error(f"Error sending response: {e}")

    # Call the send_events function to fetch and send the events for tomorrow
    try:
        await send_events(ctx, ctx.channel, tomorrow, tomorrow, time_range)
    except Exception as e:
        logger.error(f"Error sending events: {e}")


# This function is a command that sends the events for the next 3 days to the Discord channel
@bot.command(name='3days', description="Sends the events for the next 3 days.")
async def threedays_command(ctx):
    logger.info(f"Received command '3days' from {ctx.author} in {ctx.channel}!")
    # Defer the interaction to ensure the command doesn't time out
    await ctx.defer(ephemeral=True)

    # Get the current date in YYYY-MM-DD format
    today = arrow.now().format('YYYY-MM-DD')

    # Get the date for three days from now in YYYY-MM-DD format
    threedays = arrow.now().shift(days=+3).format('YYYY-MM-DD')

    # Set the time range string for the next three days
    time_range = "pour les 3 prochains jours"

    # Send a response to indicate processing is underway
    try:
        await ctx.respond('Traitement de la demande en cours... :hourglass_flowing_sand:')
    except Exception as e:
        logger.error(f"Error sending response: {e}")

    # Call the send_events function to fetch and send the events for the next three days
    try:
        await send_events(ctx, ctx.channel, today, threedays, time_range)
    except Exception as e:
        logger.error(f"Error sending events: {e}")


# This function is a command that sends the events for the current week to the Discord channel
@bot.command(name='week', description="Sends this week's events.")
async def week_command(ctx):
    logger.info(f"Received command 'week' from {ctx.author} in {ctx.channel}!")
    # Defer the interaction to ensure the command doesn't time out
    await ctx.defer(ephemeral=True)

    # Get the current date in YYYY-MM-DD format
    today = arrow.now().format('YYYY-MM-DD')

    # Get the date for one week from now in YYYY-MM-DD format
    week = arrow.now().shift(days=+7).format('YYYY-MM-DD')

    # Set the time range string for the current week
    time_range = "pour cette semaine"

    # Send a response to indicate processing is underway
    try:
        await ctx.respond('Traitement de la demande en cours... :hourglass_flowing_sand:')
    except Exception as e:
        logger.error(f"Error sending response: {e}")

    # Call the send_events function to fetch and send the events for the current week
    await send_events(ctx, ctx.channel, today, week, time_range)

logger.info("Starting bot...")
try:
    bot.run(discord_token)
except Exception as e:
    logger.error(f"Error starting bot: {e}")
