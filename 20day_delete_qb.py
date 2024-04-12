from qbittorrentapi import Client
import time
import schedule
from datetime import datetime

import configparser

config = configparser.ConfigParser()
config.read('config.ini')
qbittorrent_url = config['qBittorrent']['url']
qbittorrent_username = config['qBittorrent']['username']
qbittorrent_password = config['qBittorrent']['password']
days_threshold = int(config['Settings']['days_threshold'])
next_process_interval_minutes = int(config['Settings']['next_process_interval_minutes'])


def log_to_file(message):
    with open('log.txt', 'a', encoding='utf-8') as logfile:
        logfile.write(message + '\n')

def get_current_time():
    return time.strftime("%H:%M:%S", time.localtime())


def get_current_datetime():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

def convert_seconds_to_dhms(seconds):
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    return days, hours, minutes, seconds

def get_last_activity_torrents(qb_client):
    torrents = qb_client.torrents_info()
    last_delete_torrents = []
    last_activity_torrents = []

    # 获取当前时间戳减去20天的时间戳
    current_unix_timestamp = time.time()
    twenty_days_ago_timestamp = current_unix_timestamp - (days_threshold * 24 * 60 * 60)

    current_datetime = get_current_datetime()
    print("当前时间:", current_datetime)
    log_to_file("当前时间:"+current_datetime)
    for torrent in torrents:
        last_activity = torrent['last_activity']
        # 检查种子最后活动时间戳是否小于20天前的时间戳
        if last_activity < twenty_days_ago_timestamp:
            # 计算20天后的时间戳
            last_delete_torrents.append(torrent)
        else:
            last_activity_torrents.append(torrent)

    # 如果找到的种子大于5个，按最小的5个种子加上指定天数
    if len(last_activity_torrents) > 2:
        last_activity_torrents.sort(key=lambda x: x['last_activity'])
        for i in range(2):
            future_timestamp = last_activity_torrents[i]['last_activity'] + (days_threshold * 24 * 60 * 60)-int(time.time())

            days, hours, minutes, seconds = convert_seconds_to_dhms(future_timestamp)
            print(f"种子文件名: {last_activity_torrents[i]['name']}, 删除倒计时: {days}天 {hours}小时 {minutes}分钟 {seconds}秒")
            log_to_file(f"种子文件名: {last_activity_torrents[i]['name']}, 删除倒计时: {days}天 {hours}小时 {minutes}分钟 {seconds}秒")
    return last_delete_torrents



def find_duplicate_torrent(qb_client, torrent_name, torrent_size,torrent_hashes):
    torrents = qb_client.torrents_info()
    for torrent in torrents:
        if torrent['name'] == torrent_name and torrent['total_size'] == torrent_size and torrent['hash'] != torrent_hashes :
            return True
    return False

def delete_torrent(qb_client, torrent_hash, delete_files=False):
    qb_client.torrents_delete(torrent_hashes=torrent_hash, delete_files=delete_files)

def format_time(seconds):
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def countdown(seconds):
    for i in range(seconds, 0, -1):
        print(f"下一次处理任务将在 {format_time(i)} 后开始", end='\r')
        time.sleep(1)

def process_and_schedule():
    # Connect to qBittorrent
    print("连接到 qBittorrent...")
    log_to_file("连接到 qBittorrent...")
    qb_client = Client(host=qbittorrent_url, username=qbittorrent_username, password=qbittorrent_password)
    # Get torrents with last activity more than days_threshold days ago
    print(f"查找上传活动已经超过 {days_threshold} 天的种子...")
    log_to_file(f"查找上传活动已经超过 {days_threshold} 天的种子...")
    last_activity_torrents = get_last_activity_torrents(qb_client)
    torrents = qb_client.torrents_info()
    # 计算种子数量
    num_torrents = len(torrents)
    print(f"符合条件的种子数量:{len(last_activity_torrents)}/{num_torrents}")
    log_to_file(f"符合条件的种子数量:{len(last_activity_torrents)}/{num_torrents}")
    # Iterate over torrents and delete them if duplicates exist
    for torrent in last_activity_torrents:
        torrent_name = torrent['name']
        torrent_size = torrent['total_size']
        torrent_hashes=torrent['hash']
        print(f"检查种子是否有辅种: {torrent_name}")
        log_to_file(f"检查种子是否有辅种: {torrent_name}")
        if find_duplicate_torrent(qb_client, torrent_name, torrent_size,torrent_hashes):
            print(f"发现 {torrent_name} 的重复种子，删除任务...")
            log_to_file(f"发现 {torrent_name} 的重复种子，删除任务...")
            delete_torrent(qb_client, torrent['hash'])
        else:
            print(f"未找到 {torrent_name} 的重复种子，应当删除种子和文件。")
            log_to_file(f"未找到 {torrent_name} 的重复种子，应当删除种子和文件。")
            delete_torrent(qb_client, torrent['hash'], delete_files=True)

def main():
    process_and_schedule()
    next_process_seconds = next_process_interval_minutes * 60
    log_to_file(f"下一次处理任务将在 {format_time(next_process_seconds)} ,后开始")
    schedule.every(next_process_interval_minutes).minutes.do(process_and_schedule)
    while True:
        countdown(next_process_seconds)
        schedule.run_pending()
        print(" " * 50, end='\r')  # 清除上一次输出
        next_process_seconds = next_process_interval_minutes * 60

if __name__ == "__main__":
    main()
