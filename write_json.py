import json

file = open('dump.json', 'w+')
data = { "tilin": "ete sech", "numero": 4444 }

json.dump(data, file)
dump = json.dumps(data)

print(dump)