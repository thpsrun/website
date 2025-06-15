import math
import time

import requests


def convert_time(secs):
    """Converts the time given into a string.

    Args:
        secs (float): The seconds of a speedrun time.

    Returns:
        final_time (str): The processed string format for a speedrun.
    """
    hours, remainder = divmod(secs, 3600)
    minutes, seconds = divmod(remainder, 60)
    seconds, milliseconds = divmod(round(seconds, 3) * 1000, 1000)

    if minutes >= 60:
        hours += math.floor(minutes / 60)
        minutes = minutes % 60

    if hours >= 1:
        final_time = f"{int(hours)}h "
    else:
        final_time = ""

    if minutes == 0:
        final_time += "0m "
    elif minutes < 10:
        final_time += f"{int(minutes)}m "
    else:
        final_time += f"{int(minutes)}m "

    if seconds < 10:
        final_time += f"0{int(seconds)}s "
    else:
        final_time += f"{int(seconds)}s "

    if milliseconds > 0:
        final_time += f"{int(milliseconds)}ms"
    else:
        final_time = final_time.rstrip(" ")

    return final_time


def src_api(url, paginate=False):
    """Processes a Speedrun.com API GET request to return values from any of its endpoints.

    This function is primarily used to connect to a Speedrun.com API endpoint via GET. However,
    this can be used if the API call returns valid HTTP Request Codes for `420: Enhance Your Calm`
    and `503: Service Unavailable` *and* returns data in JSON format with the "data" key value.

    Args:
        url (str): The complete URL of the API endpoint (usually Speedrun.com) being connected to.
        paginate (bool): False by default. Some use cases related to pagination *OR* to disable
            using the "data" key value lookup.

    Returns:
        response (dict): Dictionary/JSON object from the requested API.
    """
    response = requests.get(url)

    while response.status_code == 420 or response.status_code == 503:
        print("[DEBUG] Rate limit exceeded, waiting 60 seconds...")
        time.sleep(60)
        response = requests.get(url)

    if response.status_code != 200:
        response = response.status_code
        return response

    if paginate is False:
        response = response.json()["data"]
    else:
        response = response.json()

    return response


def points_formula(wr, run, max_points):
    """Processes points based on algorithmic formula

    Args:
        wr (float): The world record time (as a float).
        run (float): The personal best time (as a float).
        max_points (int): Maximum points of a speedrun

    Returns:
        int: Points awarded to the speedrun in comparison to world record.
    """
    return math.floor((0.008 * math.pow(math.e, (4.8284 * (wr / run)))) * max_points)


def time_conversion(time):
    """Processes the returned time values of a run entry in a string.

    Args:
        time (dict): Raw run dictionary from the Speedrun.com API.

    Returns:
        tuple: A tuple containing:
            - rta (str): The written format of real-time.
            - noloads (str): The written format of loads removed time (no loads).
            - igt (str): The written format of in-game.

    Called Functions:
        - `convert_time`
    """
    realtime = time["realtime_t"]
    realtime_nl = time["realtime_noloads_t"]
    ingame = time["ingame_t"]

    rta = convert_time(realtime) if realtime > 0 else 0
    noloads = convert_time(realtime_nl) if realtime_nl > 0 else 0
    igt = convert_time(ingame) if ingame > 0 else 0

    return rta, noloads, igt
