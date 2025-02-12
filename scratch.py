zaruba_dict = {}

zaruba_dict["lordmitrii"] = True
zaruba_dict["3lii"] = True
responce = ""

for key, value in zaruba_dict.items():
    if value:
        responce += "@" + key

print(responce)