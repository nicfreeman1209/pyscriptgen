import os
import sys
import random
import numpy as np
import io
import json

import logging
loggingMode = logging.INFO
logging.basicConfig(filename='logging.log', 
					format='%(asctime)s %(name)-16s %(levelname)-8s %(message)s',
					datefmt='%m-%d %H:%M:%S',
					filemode='a',
					level=loggingMode)
console = logging.StreamHandler()
console.setLevel(loggingMode)
console.setFormatter(logging.Formatter('%(levelname)-8s %(message)s'))
logging.getLogger('').addHandler(console)
		
def ExceptionHook(excType, excValue, traceback, logging=logging):
    logging.error("Uncaught exception",
                 exc_info=(excType, excValue, traceback))
sys.excepthook = ExceptionHook

from dotenv import load_dotenv
load_dotenv()

from Script import Data, Script
dataPath = "public"
inputData = Data(dataPath)

from ScriptNamer import ScriptNamer
scriptNamer = ScriptNamer("english")

defaultTeamSizes = {
	"townsfolk" : 13,
	"outsider" : 4,
	"minion" : 4,
	"demon" : 4,
}

import discord
from discord.ext.commands import Bot
from discord.ext import commands
intents = discord.Intents.default()
intents.members = True
bot = Bot("\\", intents=intents) 

@bot.event
async def on_ready():
	logging.info('Logged in as {0.user}'.format(bot))
	for guild in bot.guilds:
		logging.info('Present in guild %s' % guild.name)

@bot.event
async def on_guild_join(guild):
	logging.info('Joined guild %s' % guild.name)	

@bot.event
async def on_guild_remove(guild):
	logging.info('Removed guild %s' % guild.name)	

@bot.event
async def on_message(message):
	if message.author == bot.user:
		return
	
	isDM = isinstance(message.channel, discord.channel.DMChannel)
	isBotChannel = 'scriptmonger' in str(message.channel).lower()
	if not isBotChannel and not isDM:
		return

	m = message.content.lower()
		
	if m.startswith('\help'):
		s = ''
		s += 'Available commands:\n'
		s += '\gen  :  Generates a new script. Optional arguments specify team sizes (default 13-4-4-4) and required roles. Example: _\\gen 13-4-4-1 pithag vigor crier_\n'
		s += '\data  :  Uploads the heatmap and SAO distribution of the input data.\n'
		s += '\explain  :  Gives a short description of the script generation algorithm.\n'
		s += '\n'
		s += "This bot will only respond to commands in channels where the channel name is or includes 'scriptmonger', and DMs.\n"
		s += 'Development: <https://github.com/nicfreeman1209/pyscriptgen>\n'
		s += 'Add to a server: <https://discord.com/api/oauth2/authorize?client_id=906466718325559307&permissions=34816&scope=bot>\n'
		await message.channel.send(s)
		return
	elif m.startswith('\data'):
		statsPath = os.path.join(dataPath, "stats")
		await message.channel.send(content="heatmap of pairwise role frequencies", file=discord.File(fp=os.path.join(statsPath, "heatmap.png")))					
		await message.channel.send(content="heatmap.xlsx (with role names)", file=discord.File(fp=os.path.join(statsPath, "heatmap.xlsx")))					
		await message.channel.send(content="distribution of Standard Amy Order", file=discord.File(fp=os.path.join(statsPath, "sao.png")))	
		logging.info("Sent stats data to %s in %s" % (message.author.display_name, message.guild.name if message.guild else "DM"))
		return
	elif m.startswith('\explain'):
		s = """
The input data is a (large) collection of existing scripts.
If you type \data you will see:
  - A heatmap of how often each pair of roles are found on the same script.
  - The distribution of Standard Amy Order (SAO) amongst townsfolk on these scripts.  	
		
To generate a new script, we start with a "completely" random script.
Then repeat the following:
  1) Choose a random slot on the current script.
  2) Remove the role in that slot.
  3) Based on the remaining on-script roles, estimate how likely each (off-script) role would be to fill this empty slot:
    - To each role, give a weight that is a sum of its heatmap values when paired with the current on-script roles.
    - Ignore any roles that aren't on the right team (townsfolk/outsider/etc). 
    - Additionally, if we are looking for a townsfolk, use the SAO distribution to sample which SAO class we want; ignore any roles that don't fit into this SAO class.
	- Don't allow more than 5 jinxes at once.
  4) Sample a role using the weights above, put it in the empty slot.
Stop after a few hundred iterations.
"""
		await message.channel.send(s)	
		return		
	elif not m.startswith('\gen'):
		return
	
	teamSizes = defaultTeamSizes.copy()
	requiredRoles = []
	tokens = m.split()
	for token in tokens[1:]:
		try:
			token = token.lower()
			if token.count('-') == 3:
				t = token.split('-')
				teamSizes['townsfolk'] = int(t[0])
				teamSizes['outsider'] = int(t[1])
				teamSizes['minion'] = int(t[2])
				teamSizes['demon'] = int(t[3])
			else:
				requiredRoles.append(token)				
		except:
			return
		
	seed = np.random.randint(10**4,10**5)
	steps = np.random.randint(500,700)
	script = Script(inputData, teamSizes, seed=seed, steps=steps,  alpha=0, beta=1, requiredRoles=requiredRoles)
	scriptNames = scriptNamer.SampleNames()
	nameStr = "**Suggested names** (please choose one):"
	for i in range(len(scriptNames)):
		nameStr += "\n(%d) %s" % (i+1, scriptNames[i])
			
	sentMessage = await message.channel.send(script.__repr__() + "\n" + nameStr)
	
	emojis = ["%d\u20E3"%(i+1) for i in range(len(scriptNames))] + ["\U00002754"]
	for emoji in emojis:
		await sentMessage.add_reaction(emoji)	

	try:	
		def reaction_check(reaction, user):
			return sentMessage==reaction.message and message.author==user	
		reaction, user = await bot.wait_for('reaction_add', check=reaction_check, timeout=300)
		if reaction.emoji == "\U00002754":
			scriptName = np.random.choice(scriptNamer.SampleNames())
			contentMsg = ""		
		else:
			scriptName = scriptNames[emojis.index(reaction.emoji)]
			contentMsg = ""
	except:
		scriptName = np.random.choice(scriptNamer.SampleNames())
		contentMsg = "Timeout for %s, a name will be chosen at random:" % script.ID()
		
	toolScript = script.ToolScript()
	toolScript.append({
		"id": "_meta",
		"name": scriptName,
		"logo": "https://raw.githubusercontent.com/nicfreeman1209/pyscriptgen/main/logo.png"
		})
	f = io.StringIO(json.dumps(toolScript))
	await message.channel.send(content=contentMsg, file=discord.File(fp=f, filename=scriptName+".json"))
	
	logging.info("Created %s for %s in %s, %s" % (script.ID(), message.author.display_name, message.guild.name if message.guild else "DM", scriptName))

@bot.event
async def close():
	pass

bot.run(os.getenv('DISCORD_TOKEN'))