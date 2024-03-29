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

from ScriptSampler import Data, Script
from ScriptPdf import ScriptPdf
dataPath = "public"
inputData = Data(dataPath)
scriptPdf = ScriptPdf(dataPath)

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
		s += '\gen  :  Generates a new script. Optional arguments specify team sizes (default 13-4-4-4) and roles to be required/omitted. Example: _\\gen 13-4-4-1 pithag cannibal -butler_\n'
		s += '\data  :  Uploads the heatmap and SAO distribution of the input data.\n'
		s += '\explain  :  Gives a short description of the script generation algorithm.\n'
		s += '\help  : Sends this message.\n'
		s += '\n'
		s += 'Development: <https://github.com/nicfreeman1209/pyscriptgen>\n'
		s += 'Invite someone to the bots own server: <https://discord.gg/53UwcFKrd8>\n'
		s += 'Add the bot to your server: <https://discord.com/api/oauth2/authorize?client_id=906466718325559307&permissions=34816&scope=bot>\n'
		s += "The bot will only respond to commands in channels where the channel name includes 'scriptmonger', and DMs.\n"
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
    - To each off-script role, put together the (sorted) vector of heatmap values of this role with the current on-script roles.
	- Assign that role a weight that is the 10th percentile of that vector.
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
	omittedRoles = []
	tokens = m.split()
	alpha = 0.0
	beta = 1.0
	gamma = 0.1
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
				if token[:6] == "alpha=":
					alpha = float(token[6:])
					alpha = float("%.1f" % alpha)
				elif token[:5] == "beta=":
					beta = float(token[5:])
					beta = float("%.1f" % beta)
				elif token[:5] == "gamma=":
					gamma = int(token[5:])
					gamma = float("%.1f" % gamma)
				elif token.startswith("-"):
					omittedRoles.append(token[1:])
				else:
					requiredRoles.append(token)	
		except:
			await message.channel.send("Invalid parameter '%s'" % token)
			return

	seed = np.random.randint(10**4,10**5)
	steps = np.random.randint(500,700)
	scriptNames = scriptNamer.SampleNames()
	script = Script(inputData, teamSizes, seed=seed, steps=steps,  alpha=alpha, beta=beta, gamma=gamma, requiredRoles=requiredRoles, omittedRoles=omittedRoles)
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
		logging.info("Timeout %s for %s in %s" % (script.ID(), message.author.display_name, message.guild.name if message.guild else "DM"))
		return
		
	toolScript = script.ToolScript()
	toolScript.append({
		"id": "_meta",
		"name": scriptName,
		"logo": "https://raw.githubusercontent.com/nicfreeman1209/pyscriptgen/main/logo.png"
		})
	pdfFile = io.BytesIO(scriptPdf.PdfAsBytes(toolScript, scriptName))
	await message.channel.send(content=contentMsg, file=discord.File(fp=pdfFile, filename=scriptName+".pdf"))	
	jsonFile = io.StringIO(json.dumps(toolScript))
	await message.channel.send(content="", file=discord.File(fp=jsonFile, filename=scriptName+".json"))
	
	logging.info("Created %s for %s in %s, %s" % (script.ID(), message.author.display_name, message.guild.name if message.guild else "DM", scriptName))

@bot.event
async def close():
	pass

bot.run(os.getenv('DISCORD_TOKEN'))