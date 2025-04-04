######################################################################################################################################################
### File Name: srl/m_tasks.py
### Author: ThePackle
### Description: Includes functions (mini tasks) that are called throughout other tasks.py or views.py files.
### Dependencies: None.
######################################################################################################################################################
import time,math,requests

### convert_time is used a few times through the project, mainly to take integer seconds and convert them to a string to call on the website.
### For example: time_secs of a run is 69.420; this will take the float and convert it to say "1m 09s 420ms"
def convert_time(secs):
    hours, remainder = divmod(secs, 3600)
    minutes, seconds = divmod(remainder, 60)
    seconds, milliseconds = divmod(round(seconds, 3) * 1000, 1000)

    if minutes >= 60:
        hours += math.floor(minutes / 60)
        minutes = minutes % 60

    if hours >= 1: final_time = f"{int(hours)}h "
    else: final_time = ""

    if minutes == 0: final_time += "0m "
    elif minutes < 10: final_time += f"{int(minutes)}m "
    else: final_time += f"{int(minutes)}m "

    if seconds < 10: final_time += f"0{int(seconds)}s "
    else: final_time += f"{int(seconds)}s "

    if milliseconds > 0: final_time += f"{int(milliseconds)}ms"
    else: final_time = final_time.rstrip(" ")

    return final_time

### src_api is a custom function that is called a LOT through the project.
### Since this project currently uses the v1 endpoint and not a library like speedruncompy, this just provides a consistent function.
### If a 402 or 503 status code is given, then it is rate limited and will need to wait.
def src_api(url,paginate=False):
    response = requests.get(url)

    while response.status_code == 420 or response.status_code == 503:
        print("Rate limit exceeded, waiting 60 seconds...")
        time.sleep(60)
        response = requests.get(url)
    
    if response.status_code != 200:
        print(f"Error: {response}")

        response = response.status_code
        return response
    
    if paginate == False:
        response = response.json()["data"]
    else:
        response = response.json()

    return response

### points_formula is the formula used to determine the points for a run.
### It is used a couple of times throughout the app, so this is to consolidate it in one place to make it easier to modify.
def points_formula(wr,run,max_points):
    return math.floor((0.008 * math.pow(math.e, (4.8284 * (wr / run)))) * max_points)