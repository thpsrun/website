import math
import time
from typing import TypedDict

import requests

from srl.srcom.schema.src import SrcRunsTimes


def convert_time(
    secs: float,
) -> str:
    """Converts the time given into a string.

    Arguments:
        secs (float): The seconds of a speedrun time.

    Returns:
        final_time (str): The processed string format for a speedrun.
    """
    hours, remainder = divmod(secs, 3600)
    minutes, seconds = divmod(remainder, 60)
    seconds, milliseconds = divmod(round(seconds, 3) * 1000, 1000)
    milliseconds = str(int(milliseconds)).zfill(3)

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

    if milliseconds != "000":
        final_time += f"{milliseconds}ms"
    else:
        final_time = final_time.rstrip(" ")

    return final_time


def src_api(
    url: str,
    paginate: bool = False,
) -> dict:
    """Processes a Speedrun.com API GET request to return values from any of its endpoints.

    This function is primarily used to connect to a Speedrun.com API endpoint via GET. However,
    this can be used if the API call returns valid HTTP Request Codes for `420: Enhance Your Calm`
    and `503: Service Unavailable` *and* returns data in JSON format with the "data" key value.

    Arguments:
        url (str): The complete URL of the API endpoint (usually Speedrun.com) being connected to.
        paginate (bool): False by default. Some use cases related to pagination *OR* to disable
            using the "data" key value lookup.

    Returns:
        response (dict): Dictionary/JSON object from the requested API.
    """
    response = requests.get(
        url,
        headers={
            "User-Agent": "thps.run/4.0 (https://thps.run; automation@thps.run)",
        },
    )

    while response.status_code == 420 or response.status_code == 503:
        print("[DEBUG] Rate limit exceeded, waiting 60 seconds...")
        time.sleep(60)
        response = requests.get(url)

    if response.status_code != 200:
        raise ValueError(
            f"SRC API request failed with statuscode {response.status_code}"
        )

    if paginate is False:
        response = response.json()["data"]
    else:
        response = response.json()

    return response


def points_formula(
    wr: float,
    run: float,
    max_points: int,
) -> int:
    """Processes points based on algorithmic formula

    Arguments:
        wr (float): The world record time (as a float).
        run (float): The personal best time (as a float).
        max_points (int): Maximum points of a speedrun

    Returns:
        int: Points awarded to the speedrun in comparison to world record.
    """
    return math.floor((0.008 * math.pow(math.e, (4.8284 * (wr / run)))) * max_points)


class TimeDict(TypedDict):
    realtime_t: int
    realtime_noloads_t: int
    ingame_t: int


def time_conversion(
    time: SrcRunsTimes,
) -> tuple[str, str, str]:
    """Processes the returned time values of a run entry in a string.

    Arguments:
        time (SrcRunsTimes): Time data from a speedrun.

    Returns:
        tuple: A tuple containing:
            - rta (str): The written format of real-time.
            - noloads (str): The written format of loads removed time (no loads).
            - igt (str): The written format of in-game.

    Called Functions:
        - `convert_time`
    """

    rta = convert_time(time.realtime_t) if time.realtime_t > 0 else "0"
    noloads = (
        convert_time(time.realtime_noloads_t) if time.realtime_noloads_t > 0 else "0"
    )
    igt = convert_time(time.ingame_t) if time.ingame_t > 0 else "0"

    return rta, noloads, igt
