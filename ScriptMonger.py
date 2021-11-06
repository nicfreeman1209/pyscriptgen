# invite link:
# https://discord.com/api/oauth2/authorize?client_id=906466718325559307&permissions=34816&scope=bot

import os
import random
import numpy as np
import discord
import io

from dotenv import load_dotenv
load_dotenv()

from Script import Data, Script
path = "public"
inputData = Data(path)

teamSizes = {
	"townsfolk" : 13,
	"outsider" : 4,
	"minion" : 4,
	"demon" : 4,
}

client = discord.Client()

@client.event
async def on_ready():
	print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
	if message.author == client.user:
		return
	
	if not 'scriptmonger' in str(message.channel).lower():
		return

	m = message.content.lower()
		
	if m.startswith('\help'):
		s = ''
		s += 'Available commands:\n'
		s += '\gen  :  Generates a new script. Optional a-b-c-d argument to specify team sizes, default 13-4-4-4.\n'
		s += '\data  :  Uploads the heatmap and SAO distribution of the input data.\n'
		s += '\explain  :  Gives a short description of the script generation algorithm.\n'
		s += '\n'
		s += "This bot will only respond to commands in channels where the channel name is or includes 'scriptmonger'.\n"
		await message.channel.send(s)
		return
	elif m.startswith('\data'):
		statsPath = os.path.join(path, "stats")
		await message.channel.send(content="heatmap of pairwise role frequencies", file=discord.File(fp=os.path.join(statsPath, "heatmap.png")))					
		await message.channel.send(content="heatmap.xlsx (with role names)", file=discord.File(fp=os.path.join(statsPath, "heatmap.xlsx")))					
		await message.channel.send(content="distribution of Standard Amy Order", file=discord.File(fp=os.path.join(statsPath, "sao.png")))	
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
  3) Based on the remaining roles, estimate how likely each role would be to fill this empty slot:
    - To each role, give a weight that is a sum of its heatmap values when paired with currently selected roles.
    - Ignore any roles that aren't on the right team (townsfolk/outsider/etc). 
    - Additionally, if we are looking for a townsfolk, use the SAO distribution to sample which SAO class we want; ignore any roles that don't fit into this SAO class.
  4) Sample a role using the weights above, put it in the empty slot.
Stop after a few hundred iterations.
"""
		await message.channel.send(s)	
		return		
	elif not m.startswith('\gen'):
		return
		
	tokens = m.split()
	for token in tokens:
		try:		
			if token.count('-') == 3:
				t = token.split('-')
				teamSizes['townsfolk'] = int(t[0])
				teamSizes['outsider'] = int(t[1])
				teamSizes['minion'] = int(t[2])
				teamSizes['demon'] = int(t[3])
		except Exception as e:
			print(e)
		
	script = Script(inputData, teamSizes, seed=np.random.randint(10**3,10**4), steps=500,  alpha=0, beta=1)
	
	await message.channel.send(script.__repr__())
	
	f = io.StringIO(script.ToolScript())
	await message.channel.send(content="", file=discord.File(fp=f, filename="script_"+script.ID()+".json"))		

client.run(os.getenv('DISCORD_TOKEN'))