import numpy as np
from Script import Data, Script

steps = 500 #np.random.randint(10**3,10**4)
seed = np.random.randint(10**3,10**4)
alpha = 0 # increase this to make the popularity of individual characters be *less* important - range [0,1]
beta = 1 # increase this to make the pairwise correlations between characters be *more* important - suggested range [0,2]

teamSizes = {
    "townsfolk" : 13,
    "outsider" : 4,
    "minion" : 4,
    "demon" : 4,
}

inputData = Data("public")

script = Script(inputData, teamSizes, seed=seed, steps=steps,  alpha=alpha, beta=beta)

print(script)