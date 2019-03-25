import os.path as path

import itchat

from api import request_schedule, API_LEAGUE, API_RANKED, API_REGULAR, \
    request_next_salmon_run, request_salmon_run
from model import Item
from translation import TIME, BATTLES, STAGES, WEAPONS, CN_LEAGUE, \
    CN_RANKED, CN_REGULAR, CN_SALMON_RUN
from util import download_img, combine_imgs, RES_DIR, IMG_EXT

CMD_QR = True

KEYWORDS_LEAGUE = [CN_LEAGUE, "双排", "四排", "排排", "pp", "wyx"]
KEYWORDS_RANKED = [CN_RANKED, "真格", "伤身体"]
KEYWORDS_REGULAR = [CN_REGULAR, "涂地", "常规"]
KEYWORDS_SALMON_RUN = [CN_SALMON_RUN, "dg", "工"]

MODES = {API_LEAGUE: CN_LEAGUE,
         API_RANKED: CN_RANKED,
         API_REGULAR: CN_REGULAR}

UNKNOWN_MESSAGE = "你怎么辣么可爱 本宝宝听不懂你在说什么\n" \
                  "格式: 查询 (当前/下个/X小时后) 组排/单排/涂地/打工"

MINUTES_EPOCH = 60
HOURS_EPOCH = 60 * MINUTES_EPOCH

COMBINED_IMAGE = RES_DIR + "combined" + IMG_EXT


@itchat.msg_register(itchat.content.TEXT)
def reply(msg):
    request_input: str = msg.text
    request_time = msg.createTime
    requester = msg.user
    if not request_input.startswith("查询"):
        return

    def any_in(keywords: [str]) -> bool:
        return any(keyword in request_input for keyword in keywords)

    if any_in(KEYWORDS_SALMON_RUN):
        reply_salmon_run(requester, request_time, request_input)
    else:
        mode = None
        if any_in(KEYWORDS_LEAGUE):
            mode = API_LEAGUE
        elif any_in(KEYWORDS_RANKED):
            mode = API_RANKED
        elif any_in(KEYWORDS_REGULAR):
            mode = API_REGULAR
        if mode is None:
            requester.send_msg(UNKNOWN_MESSAGE)
        else:
            reply_battle(requester, mode, request_time, request_input)


def reply_salmon_run(requester, request_time: float, request_input: str):
    if "下" in request_input:
        run = request_next_salmon_run()
    else:
        run = request_salmon_run(request_time)

    if run is None:
        requester.send_msg("木有找到打工信息")
    else:
        if run.start_time <= request_time <= run.end_time:
            remain_message = "剩余{}小时结束".format(
                diff_hours(request_time, run.end_time))
        else:
            remain_message = "还有{}小时开始".format(
                diff_hours(request_time, run.start_time))
        requester.send_msg("{remaining}, " "地图:{stage}, "
                           "武器: {weapon}".format(
            remaining=remain_message,
            stage=STAGES.get(run.stage.name, run.stage.name),
            weapon=" ".join(str(s) for s in list(map(
                lambda w: WEAPONS.get(w.name, w.name), run.weapons)))))

        stage_img = cache_img([run.stage])[0]
        if path.isfile(stage_img):
            requester.send_image(stage_img)
        if combine_imgs(cache_img(run.weapons), COMBINED_IMAGE,
                        vertical=False) and path.isfile(COMBINED_IMAGE):
            requester.send_image(COMBINED_IMAGE)


def reply_battle(requester, mode: str, msg_time: float, request_input: str):
    global query_time
    if "下" in request_input:
        query_time = msg_time + 2 * HOURS_EPOCH
    elif "小时后" in request_input:
        index = request_input.index("小时后") - 1
        num_char = request_input[index]
        try:
            parsed = int(num_char)
        except ValueError:
            parsed = TIME.get(request_input[index], 0)
        query_time = msg_time + parsed * HOURS_EPOCH

    schedule = request_schedule(mode, query_time)
    if schedule is None:
        requester.send_msg("木有找到模式信息")
        return

    if schedule.start_time <= msg_time <= schedule.end_time:
        remain_message = " (剩余{}分钟结束) ".format(
            diff_minutes(msg_time, schedule.end_time))
    else:
        remain_message = " (还有{}分钟开始) ".format(
            diff_minutes(msg_time, schedule.start_time))
    requester.send_msg("{mode}: {type}模式{remaining}, 地图: {stage}".format(
        mode=MODES.get(mode, mode),
        type=BATTLES.get(schedule.mode, schedule.mode),
        remaining=remain_message,
        stage=" ".join(str(s) for s in
                       list(map(lambda s: STAGES.get(s.name, s.name),
                                schedule.stages)))))
    if combine_imgs(cache_img(schedule.stages), COMBINED_IMAGE):
        requester.send_image(COMBINED_IMAGE)


def diff_minutes(epoch1: float, epoch2: float) -> int:
    return int(abs(epoch1 - epoch2) / MINUTES_EPOCH)


def diff_hours(epoch1: float, epoch2: float) -> int:
    return int(abs(epoch1 - epoch2) / HOURS_EPOCH)


def cache_img(items: [Item]) -> [str]:
    files = []
    for item in items:
        file_name = RES_DIR + item.name + IMG_EXT
        files.append(file_name)
        if not path.isfile(file_name):  # sequential download
            download_img(item.img_url, file_name)
    return files


if __name__ == "__main__":
    if CMD_QR:
        itchat.auto_login(enableCmdQR=2)
    else:
        itchat.auto_login()
    itchat.run()
