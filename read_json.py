import json

file = open('dump.json',)
data = json.load(file)

for i in data:
    print(i)