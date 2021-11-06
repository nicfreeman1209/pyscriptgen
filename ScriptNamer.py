import numpy as np
import os

class ScriptNamer():
    def __init__(self, path):
        self.nouns = self.ReadLines(path, "nouns.txt")
        self.plurals = self.ReadLines(path, "plurals.txt")  
        self.adjectives = self.ReadLines(path, "adjectives.txt")
        self.verbs = self.ReadLines(path, "verbs.txt")   
        self.replacements = {
            "N" : self.nouns,
            "P" : self.plurals,
            "A" : self.adjectives,
            "V" : self.verbs,
        }
        self.patterns = [
            "N V", # trouble brewing
            "A N V", # bad moon rising
            "P and P", # sects and violets
        ]
        
    def ReadLines(self,path, filename):
        with open(os.path.join(path,filename)) as file:
            lines = file.readlines()
            lines = [line.strip().title() for line in lines]
        return lines

    def SampleNames(self):
        ret = []
        for pattern in self.patterns:
            name = ""
            for char in pattern:
                if char in self.replacements:
                    name += np.random.choice(self.replacements[char])
                else:
                    name += char
            ret.append(name)
        return ret