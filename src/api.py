import shutil
from typing import Optional

import requests

from model import Stage, Schedule

API_LEAGUE = "league"
API_RANKED = "gachi"
API_REGULAR = "regular"

data_url = "https://splatoon2.ink/data/schedules.json"
img_base = "https://splatoon2.ink/assets/splatnet"


def request_schedule(mode: str, request_time: float) -> Optional[Schedule]:
    schedules: dict = requests.get(data_url).json()

    for schedule in schedules.get(mode, []):
        start_time = schedule["start_time"]
        end_time = schedule["end_time"]

        if start_time <= request_time <= end_time:
            return Schedule(start_time, end_time, schedule["rule"]["name"],
                            [create_stage(schedule["stage_a"]),
                             create_stage(schedule["stage_b"])]
                            )
    return None


def download_image(url: str, file_name):
    response = requests.get(url, stream=True)
    with open(file_name, "wb") as out_file:
        shutil.copyfileobj(response.raw, out_file)
    del response


def create_stage(stage_dict: dict) -> Stage:
    return Stage(stage_dict["name"], img_base + stage_dict["image"])
