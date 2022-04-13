import json
import os
import PIL
import datetime
from PIL import ImageOps
from PIL import ImageChops
from PIL import Image
from fpdf import FPDF

def SanitizeName(s):
	# convert role["name"] into the roleId used by the script tool (which is not equal to role["id"] ffs)
	s = s.lower()
	s = s.replace(' ', '_')
	s = s.replace("'","")
	if s == "mephit":
		s = "mezepheles"
	s = s.strip()
	return s

def SanitizeText(s):
	# remove non-pdf-able characters
	s = s.replace("“", "'")
	s = s.replace("”", "'")
	s = s.replace("’","'")
	s = s.replace("−","-")
	s.strip()
	return s
	

class ScriptPdf:
	def __init__(self, path):
		self.path = path
		with open(os.path.join(self.path, "official", "roles.json"), "r") as j:
			self.roles = json.load(j)
		with open(os.path.join(self.path, "official", "hatred.json"), "r") as j:
			self.hatred = json.load(j)
		self.iconDir = os.path.join(self.path, "official", "icons")
		
		self.rolesDict = {}
		for role in self.roles:
			name = SanitizeName(role["name"])
			self.rolesDict[name] = role
			self.rolesDict[name]["ability"] = SanitizeText(role["ability"])
			self.rolesDict[name]["firstNightReminder"] = SanitizeText(role["firstNightReminder"])
			self.rolesDict[name]["otherNightReminder"] = SanitizeText(role["otherNightReminder"])
		
		self.teamColors = {
			"townsfolk": (20,118,212),
			"outsider": (20,118,212),
			"minion": (149,18,36),
			"demon": (149,18,36),
			"traveler": (100,100,100),
		}
		
		self.pdf = None
		
	def FullScript(self, toolScript):
		# replace character names with full info from roles.json
		script = []
		roleNames = set() 
		firstNightOrder = []
		otherNightOrder = []
		jinxes = []
		for role in toolScript:
			if role["id"]=="_meta":
					continue
			for key in role.keys():
				if key != "id":
					script.append(role)
					continue
			script.append(self.rolesDict[role["id"]])
		
			
		# record the night reminders, in order
		for role in script:
			roleNames.add(role["name"])
			if role["firstNight"] > 0:
				firstNightOrder.append((role["firstNight"], role["name"], role["firstNightReminder"]))
			if role["otherNight"] > 0:
				otherNightOrder.append((role["otherNight"], role["name"], role["otherNightReminder"]))
		
		firstNightOrder = sorted(firstNightOrder, key=lambda x: x[0], reverse=True)
		otherNightOrder = sorted(otherNightOrder, key=lambda x: x[0], reverse=True)
		
		# record the jinxes
		for _jinx in self.hatred:
			role1 = _jinx["id"]
			for jinx in _jinx["hatred"]:
				role2 = jinx["id"]
				if role1 in roleNames and role2 in roleNames:
					jinxes.append((role1, role2, jinx["reason"]))
		
		return script, firstNightOrder, otherNightOrder, jinxes
		
	def MakePdf(self, toolScript, scriptName):		  
		script, firstNightOrder, otherNightOrder, jinxes = self.FullScript(toolScript)
		
		pdf = FPDF(format="A4", unit="mm", orientation="P") # 210 x 297
		pdf.add_page()
		pdf.set_margin(0)
		
		# title
		pdf.set_xy(0,10)
		pdf.set_font('Helvetica', 'B', 16)
		pdf.cell(w=210, h=0, align='C', txt=scriptName, border=0)

		pt = 0.36
		fontSize = 10
		fontName = 'Helvetica'
		pdf.set_font(fontName, '', fontSize)
		y = 20
		lMargin = 12
		colWidth = 95
		midMargin = 2
		imSize = 12
		x1 = lMargin
		x2 = lMargin + colWidth + midMargin
		x = x2

		teamColors = {
			"townsfolk": (20,118,212),
			"outsider": (20,118,212),
			"minion": (149,18,36),
			"demon": (149,18,36),
			"traveler": (100,100,100),
		}

		def AddRole(x, y, role):
			if role:
				imageFile = os.path.join(self.path, "official", "icons", role["id"]+".png")
				pdf.image(imageFile, x=x, y=y, w=imSize, h=imSize)
				pdf.set_xy(x+imSize,y)
				pdf.set_font(fontName, '', fontSize)
				pdf.multi_cell(w=colWidth-imSize, h=3.5, align='L', txt="**" + role["name"] + ":** " + role["ability"], border=0, markdown=True)
			y += fontSize*pt*5.5
			return y

		def AddTeamRect(y1,y2, teamName="TEAM"):
			w = lMargin/3
			h = y2-y1-fontSize*pt  
			pdf.rect(x=lMargin/3, y=y1-fontSize*pt/2, w=w, h=h)
			pdf.set_xy(lMargin/3, h+y1-fontSize*pt/2)
			with FPDF.rotation(pdf, angle=90, x=pdf.get_x(), y=pdf.get_y()):
				pdf.set_xy(pdf.get_x(),pdf.get_y()+lMargin/3/2+0.2)
				color = teamColors[teamName]
				pdf.set_text_color(*color)
				pdf.set_font(fontName, '', fontSize-1)
				pdf.cell(w=h,h=0,align="C",txt=teamName.upper())
				pdf.set_text_color(0,0,0)
				pdf.set_font(fontName, '', fontSize)

		prevTeam = "townsfolk"
		y1 = y
		y2 = None

		# roles & related margin 
		for role in script:
			if role["team"] != prevTeam:
				if x == x1:
					y = AddRole(x,y,None)
				x = x2
				y += fontSize*pt*0.75
				AddTeamRect(y1,y, prevTeam)
				prevTeam = role["team"]
				if role["team"] == "traveler":
					pdf.add_page()
					pdf.set_xy(0,10)
					y = 15
				y1 = y
			if x == x2:
				x = x1
				AddRole(x, y, role)
			else:
				x = x2
				y = AddRole(x, y, role)

		if x == x1:
			y = AddCharacter(x,y,None)
		if role["team"] == "traveler":
			AddTeamRect(y1,y, "traveler")
			y += fontSize*pt*3
		else:
			y += fontSize*pt*0.75
			AddTeamRect(y1,y, prevTeam)
			pdf.add_page()
			pdf.set_xy(0,10)
			y = 15

		x = x1
		y += fontSize*pt*3
		
		# jinxes
		if len(jinxes)>0:
			pdf.set_xy(x1+imSize, y)
			pdf.cell(w=colWidth, h=0, align='L', txt="**Jinxes**", border=0, markdown=True)
			y += fontSize*pt*2

			for role1,role2,jinx in jinxes:
				pdf.set_xy(x1+imSize,y)
				text = role1+" & "+role2+":\n"+jinx
				pdf.multi_cell(w=colWidth*2, h=3.5, align='L', txt=text, border=0, markdown=True)
				y += fontSize*pt*3
			y += fontSize*pt*2
		
		# first night order
		pdf.set_xy(x1+imSize, y)
		pdf.cell(w=colWidth, h=0, align='L', txt="**First Night**", border=0, markdown=True)
		y += fontSize*pt

		for _,name,reminder in firstNightOrder:
			y += fontSize*pt
			pdf.set_xy(x+imSize,y)
			pdf.cell(w=colWidth, h=0, align="L", txt=name, markdown=True)
			
		# other night order
		y += fontSize*pt*3
		pdf.set_xy(x1+imSize, y)
		pdf.cell(w=colWidth, h=0, align='L', txt="**Other Night**", border=0, markdown=True)
		y += fontSize*pt

		for _,name,reminder in otherNightOrder:
			y += fontSize*pt
			pdf.set_xy(x1+imSize,y)
			pdf.cell(w=colWidth, h=0, align="L", txt=name, markdown=True)
		
			
		today = datetime.datetime.now().strftime("%Y-%m-%d")		
		pdf.set_xy(x1+imSize, 297-15)
		pdf.set_text_color(150,150,150)
		pdf.cell(w=colWidth, h=0, align="L", txt=today)
		
		return pdf.output(dest='S')
