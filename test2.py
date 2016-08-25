import codejail.jail_code
from codejail.languages import python3
codejail.jail_code.configure('python', '/home/denis/university/python/BattleGround/sandbox_virtualenv/bin/python', lang=python3)
import codejail.safe_exec
dict1 = {"result":None}
codejail.safe_exec.safe_exec("import os\nos.system('ls /etc')\nresult = 5", dict1)
print(dict1)
