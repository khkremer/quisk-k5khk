import requests

def select_antenna(ant1=False, ant2=False, ant3=False):
    url = "http://nodered.local:1880/select_antenna"
    data = {"ant1": ant1, "ant2": ant2, "ant3": ant3}
    response = requests.post(url, json=data)
    response.raise_for_status()
    return response.text

# Select antenna 1
# print(select_antenna(ant1=True))

def on_antenna_button(antenna_name):
    print("in on_antenna_button: " + antenna_name)
    # 'antenna_name' is the string on the button (e.g., "Ant 1")
    if antenna_name == "Ant 1":
        select_antenna(ant1=True)
    elif antenna_name == "Ant 2":
        select_antenna(ant2=True)
    elif antenna_name == "Ant 3":
        select_antenna(ant3=True)
