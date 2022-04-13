import requests
import os
import json

roles = "https://raw.githubusercontent.com/bra1n/townsquare/develop/src/roles.json"
hatred = "https://raw.githubusercontent.com/bra1n/townsquare/develop/src/hatred.json"
iconDir = "https://raw.githubusercontent.com/bra1n/townsquare/develop/src/assets/icons/"

def DownloadToDir(url, dir):
	r = requests.get(url, allow_redirects=True)
	filename = url.split("/")[-1]
	path = os.path.join(dir, filename)
	open(path, 'wb').write(r.content)

DownloadToDir(roles, ".")
DownloadToDir(hatred, ".")

with open("roles.json", "r") as rolesFile:
	roles = json.load(rolesFile)
	for role in roles:
		id = role["id"]
		url = iconDir + id + ".png"
		DownloadToDir(url, "icons")
		
