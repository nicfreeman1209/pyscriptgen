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

	m = message.content.lower()
	if not m.startswith('\scriptmonger'):
		return
		
	tokens = m.split()
	for token in tokens:
		token = token.strip()
		print(token, token=="data")
		try:
			if token == "data":
				statsPath = os.path.join(path, "stats")
				await message.channel.send(content="heatmap.png", file=discord.File(fp=os.path.join(statsPath, "heatmap.png")))					
				await message.channel.send(content="heatmap.xlsx", file=discord.File(fp=os.path.join(statsPath, "heatmap.xlsx")))					
				await message.channel.send(content="sao.png", file=discord.File(fp=os.path.join(statsPath, "sao.png")))	
				return
		
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
	
	f = io.StringIO(script.ToolScript().__repr__())
	await message.channel.send(content="", file=discord.File(fp=f, filename="script_"+script.ID()+".json"))		

client.run(os.getenv('DISCORD_TOKEN'))