import ctypes
import logging
import os
import re
import threading
import time
import traceback
from typing import Optional

import psutil
import pystray
import win11toast
import win32gui
import win32process
from PIL import Image
from win11toast import toast, notify, update_progress, clear_toast

win11toast.DEFAULT_APP_ID = "ActionLogger"

focus_mode = False

running = None
icon: Optional[pystray.Icon] = None

# regex for process name and window title. If both match, consider it as a time-wasting app
blacklist = [
    # 微信 : nproc = WeChat.exe and title any
    (r"WeChat\.exe", r".*"),
    # 小红书 : nproc = firefox.exe and title contains "小红书"
    (r"firefox\.exe", r".*小红书.*"),
    # 知乎 : nproc = firefox.exe and title contains "知乎"
    (r"firefox\.exe", r".*知乎.*"),
    # QQ : nproc = QQ.exe and title any
    (r"QQ\.exe", r".*"),
    # CS2 : nproc = cs2.exe and title any
    (r"cs2\.exe", r".*"),
]

ignorelist = [
]


def quit_window(icon, item):
    icon.stop()


def show_log(icon, item):
    os.system(f'code C:/temp/action_log/{time.strftime("%Y-%m-%d", time.localtime())}.log')


def get_active_window():
    while True:
        try:
            window = win32gui.GetForegroundWindow()
            title = win32gui.GetWindowText(window)
            pid = win32process.GetWindowThreadProcessId(window)[1]
            process = psutil.Process(pid)
        except:
            time.sleep(1)
            continue
        return process.name(), pid, title


# logging thread
def logging_thread():
    global running
    time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    logging.info(f"{time_str} Application started.")

    file_name = time.strftime("%Y-%m-%d", time.localtime())

    # Every 60min, toast the user to update the timetable
    last_timetable_update = time.time() - 60 * 28
    # If the user stays on the same window (of time-wasting app) for 2 min, check if to-do has been set
    # If not, toast the user to set a to-do
    # If the user sets a to-do , remind the user to work on the to-do every 5 min
    # For focus mode, kill the time-wasting app after staying for 90 sec (warning in 20 sec)
    last_window_change = time.time()
    # Every 30 min, remind the user to set a to-do for the next 30 min
    last_todo_set = time.time() - 60 * 25
    todo_task = "小目标"
    progress_bar_displayed = False
    # Last blacklisted reminder
    last_blacklist_reminder = None
    last_blacklist_start = None

    prev_window_title = None
    prev_window_process_name = None
    active_window_process_name, pid, active_window_title = get_active_window()

    while running:
        if file_name != time.strftime("%Y-%m-%d", time.localtime()):
            time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            logging.info(f"{time_str} Passing to new log file.")
            file_name = time.strftime("%Y-%m-%d", time.localtime())
            logging.basicConfig(filename=f'C:/temp/action_log/{file_name}.log',
                                level=logging.INFO,
                                format='%(message)s', encoding='utf-8', force=True)

        # 5 minute before the every 30 minute to-do request, remind the user to update the timetable
        if time.time() - last_todo_set > 25 * 60 and time.time() - last_timetable_update > 60 * 30:
            # 25s timeout
            clear_toast(group='timetable')
            result = toast('记录 时间表', '记录 做了什么 在做什么', buttons=['推迟 (2m)', '记录好了'], duration='long',
                           audio={'silent': 'true'}, group='timetable')
            if 'arguments' in result and '记录好了' in result['arguments']:
                # User has updated the timetable
                last_timetable_update = time.time()
            elif 'arguments' in result and result['arguments'] == 'http:':
                # User accidentally clicked the notification
                last_timetable_update = time.time() - 60 * 30
            else:
                # User delayed the notification
                last_timetable_update = time.time() - 60 * 28

        # Every 30 min, remind the user to set a to-do for the next 30 min
        if time.time() - last_todo_set > 60 * 30:
            result = toast('想要 做什么', '决定 接下来30分钟 待办事项', buttons=['推迟 (2m)', '我会加油'],
                           input='小目标', duration='long', audio={'silent': 'true'})
            if 'arguments' in result and '我会加油' in result['arguments'] and 'user_input' in result and \
                    result['user_input']['小目标']:
                last_todo_set = time.time()
                todo_task = result['user_input']['小目标']
            elif 'arguments' in result and result['arguments'] == 'http:':
                last_todo_set = time.time() - 60 * 30
            else:
                last_todo_set = time.time() - 60 * 28


        prev_window_title = active_window_title
        prev_window_process_name = active_window_process_name

        # Get the active window
        active_window_process_name, pid, active_window_title = get_active_window()

        if active_window_title != prev_window_title or active_window_process_name != prev_window_process_name:
            # Window has changed
            time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            logging.info(f"{time_str} [{pid} - {active_window_process_name}] {active_window_title}")

            last_window_change = time.time()

            time_wasting_app = False
            for nproc, title in blacklist:
                if re.match(nproc, active_window_process_name) and re.match(title, active_window_title):
                    time_wasting_app = True
                    break
            if not time_wasting_app:
                # The switched app is not a time-wasting app
                last_blacklist_reminder = None
                last_blacklist_start = None
                # Clear the kill warning
                if progress_bar_displayed:
                    clear_toast()
                    progress_bar_displayed = False
            else:
                if last_blacklist_start is None:
                    last_blacklist_start = time.time()

        # User is still on the same window

        # Check if the active window is a time-wasting app
        for nproc, title in blacklist:
            if re.match(nproc, active_window_process_name) and re.match(title, active_window_title):
                break
        else:
            # User is not on a time-wasting app
            last_blacklist_reminder = None
            time.sleep(1)
            continue

        # User has been on the same time-wasting app for 2 min
        if focus_mode:
            # Focus mode is enabled
            # Kill the time-wasting app after 90 sec

            if time.time() - last_blacklist_start > 95:
                # Already killed, stay for another 5 sec, then clear the warning
                clear_toast()
                progress_bar_displayed = False
            elif time.time() - last_blacklist_start > 90 and not killed:
                # Kill the time-wasting app
                assert progress_bar_displayed is not None
                update_progress({'status': '杀掉了！', 'value': '1', 'valueStringOverride': '0 sec'})
                try:
                    os.system(f'taskkill /f /pid {pid}')
                    killed = True
                except:
                    pass
            elif time.time() - last_blacklist_start > 20:
                killed = False
                # Display the warning
                sec_passed = time.time() - last_blacklist_start - 20
                if not progress_bar_displayed or (active_window_process_name != prev_window_process_name):
                    progress_bar_displayed = True
                    clear_toast()
                    notify('分心啦！', f'马上 帮你专注 做 {todo_task}', progress={
                        'title': f'{active_window_process_name}',
                        'status': '即将 杀掉...',
                        'value': str(sec_passed / 70),
                        'valueStringOverride': f'{int(70 - sec_passed)} sec'
                    }, scenario='incomingCall', tag='focus_killer')
                else:
                    update_progress(
                        {'value': str(sec_passed / 70), 'valueStringOverride': f'{int(70 - sec_passed)} sec'}, tag='focus_killer')

        else:
            # Focus mode is disabled
            # Remind the user to do the to-do after 2 min of no switching, and every 5 min after the first reminder
            if last_blacklist_reminder is None and time.time() - last_blacklist_start > 23:
                last_blacklist_reminder = time.time()
                notify('你在 做什么', f'还在为 {todo_task} 努力吗？', duration='long', audio={'silent': 'true'}, tag='focus_reminder')
            elif last_blacklist_reminder is not None and time.time() - last_blacklist_reminder > 180:
                last_blacklist_reminder = time.time()
                notify('你在 做什么', f'还在为 {todo_task} 努力吗？', duration='long', audio={'silent': 'true'}, tag='focus_reminder')

        time.sleep(1)



def switch_focus_mode(icon, item):
    global focus_mode
    focus_mode = not item.checked
    time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    logging.info(f"{time_str} Focus Mode {'Enabled' if focus_mode else 'Disabled'}")


def main():
    global running
    global icon

    counter = 0
    while True:
        try:
            if not os.path.exists(f'C:/temp/action_log'):
                os.makedirs(f'C:/temp/action_log')

            logging.basicConfig(filename=f'C:/temp/action_log/{time.strftime("%Y-%m-%d", time.localtime())}.log',
                                level=logging.INFO,
                                format='%(message)s',
                                encoding='utf-8')

            image = Image.open("favicon.ico")
            menu = (pystray.MenuItem("Focus Mode", action=switch_focus_mode, checked=lambda i: focus_mode),
                    pystray.MenuItem('Show Log', show_log), pystray.MenuItem('Quit', quit_window))
            icon = pystray.Icon("ActionLogger", image, "Tray Icon", menu)

            break

        except:
            counter += 1
            # exception detail
            ctypes.windll.user32.MessageBoxW(0,
                                             f"ActionLogger start failed. [attempt #{counter}/3]\n\n{traceback.format_exc()}",
                                             "ActionLogger start failed", 1)
            if counter >= 3:
                return
            time.sleep(1)

    running = True

    # run logging thread
    threading.Thread(target=logging_thread).start()

    icon.run()

    running = False

    time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    logging.info(f"{time_str} Application quit gracefully.")


if __name__ == '__main__':
    main()
