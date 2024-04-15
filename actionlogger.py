import win32gui
import win32process
import psutil
import time
import logging
import os
from pystray import MenuItem as item
import pystray
from PIL import Image
import ctypes
import threading
import traceback


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

    prev_window_title = None
    prev_window_process_name = None
    while running:
        if file_name != time.strftime("%Y-%m-%d", time.localtime()):
            time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            logging.info(f"{time_str} Passing to new log file.")
            file_name = time.strftime("%Y-%m-%d", time.localtime())
            logging.basicConfig(filename=f'C:/temp/action_log/{file_name}.log',
                                level=logging.INFO,
                                format='%(message)s', encoding='utf-8')
        active_window_process_name, pid, active_window_title = get_active_window()
        if active_window_title != prev_window_title:
            prev_window_title = active_window_title
            prev_window_process_name = active_window_process_name
            time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            logging.info(f"{time_str} [{pid} - {active_window_process_name}] {active_window_title}")
            # print(f"{time_str} [{pid} - {active_window_process_name}] {active_window_title}")
        time.sleep(1)


def main():
    global running

    counter = 0
    while True:
        try:
            if not os.path.exists(f'C:/temp/action_log'):
                os.makedirs(f'C:/temp/action_log')

            logging.basicConfig(filename=f'C:/temp/action_log/{time.strftime("%Y-%m-%d", time.localtime())}.log',
                                level=logging.INFO,
                                format='%(message)s', encoding='utf-8')

            image = Image.open("favicon.ico")
            menu = (item('Show Log', show_log), item('Quit', quit_window))
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
