import requests
import os
import json
from PIL import Image
import glob
import numpy as np
import math
from tqdm import tqdm

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
	for role in tqdm(roles):
		id = role["id"]
		url = iconDir + id + ".png"
		#DownloadToDir(url, "icons_raw")
		
def FetchFilledPartOfImage(im):
    # crop the non-blank part (of a mask)
    im = im.convert("RGBA")
    data = np.asarray(im)
    alphas = data[:,:,3]
    nzRows = np.where(data.any(axis=0))[0]
    nzCols = np.where(data.any(axis=1))[0]
    l,r = nzRows[0], nzRows[-1]
    b,t = nzCols[0], nzCols[-1]
    o_x = (l+r)/2
    o_y = (t+b)/2
    o = max(r-l, t-b)/2
    o *= 1.25 # padding
    im = im.crop((o_x-o, o_y-o, o_x+o, o_y+o))
    return im
	
for imageFile in tqdm(glob.glob("./icons_raw/*.png")):
	filename = os.path.basename(imageFile)
	image = Image.open(imageFile)
	image = FetchFilledPartOfImage(image)
	image = image.resize((90,90), Image.ANTIALIAS)
	image.save(os.path.join(".", "icons", filename))