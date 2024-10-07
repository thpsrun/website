import time,math,requests

def convert_time(secs):
    hours, remainder = divmod(secs, 3600)
    minutes, seconds = divmod(remainder, 60)
    seconds, milliseconds = divmod(round(seconds, 3) * 1000, 1000)

    if minutes >= 60:
        hours += math.floor(minutes / 60)
        minutes = minutes % 60

    if hours >= 1: final_time = f"{int(hours)}h "
    else: final_time = ""

    if minutes < 10: final_time += f"0{int(minutes)}m "
    else: final_time += f"{int(minutes)}m "

    if seconds < 10: final_time += f"0{int(seconds)}s "
    else: final_time += f"{int(seconds)}s "

    if milliseconds > 0: final_time += f"{int(milliseconds)}ms"
    else: final_time = final_time.rstrip(" ")

    return final_time

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