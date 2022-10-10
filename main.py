#!/usr/bin/python3
import os
import re
import time
import datetime

from subprocess import Popen, PIPE


# Получаем результат выполнения системной команды
def get_console_output(val):
    return Popen(val, stdout=PIPE, stderr=PIPE, shell=True, universal_newlines=True).communicate()[0]


# Получаем логическое имя диска
def get_logical_disk_name(output):
    return re.search(r'ata.*', output).group(0).split(' ')[2][-3:]


# Определяем сколько разделов на диске
def how_many_partitions(disk):
    return len(partition = get_console_output(
        f'ls /dev/ | grep {disk}').strip().split('\n'))


# Форматируем диск
def format_disk(disk):
    os.system(
        f'echo "g\nn\np\n1\n\n\nw" | fdisk /dev/{disk}; mkfs.ext4 /dev/{disk}1')


# Примонтируем диск
# def mount_disk(disk):
#     os.system(f'mount /dev/{disk}1 /mnt/disk/')


# Перемещаемся в директорию диска
# def move_to_disk_folder():
#     os.system('cd /mnt/disk/; pwd')


# Запускаем стресс тест в фоновом режиме
def start_stress_test(test_time: str):
    #os.system(f'stress-ng --class filesystem --sequential 8 --timeout {test_time}s --metrics-brief &')
    #os.system(f'stress-ng --cpu 4 --io 4 --hdd 4 hdd-opts rd-rnd wr-rnd --vm 4 --timeout {test_time}s &')
    os.system(f'stress-ng --sequential 0 --class io --timeout {test_time}s --metrics-brief &')
    print(f'Test is starting during {test_time} seconds')


#  Получаем значения температур
def temperature_list(test_time):
    value_list = []
    cores = get_console_output('nproc')
    time_end = time.time() + (float(test_time) * float(cores) + 10)
    time_format = time.strftime("%H:%M:%S", time.gmtime(time_end))
    print('Начало теста:', datetime.datetime.now().strftime("%H:%M:%S"))
    print('Конец теста:', time_format)
    while time.time() <= time_end:
        temperature_value = get_console_output(
            "smartctl -A /dev/sda | grep Temperature | awk '{print $10}'")
        value_list.append(int(temperature_value))
        #date = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
        #print(date, 'Температура: ' + temperature_value, end='')
    return value_list


if __name__ == "__main__":
    disks = get_console_output('ls -l /dev/disk/by-id')
    logic_disk_name = get_disk_logical_name(disks)
    amount_of_disk_partition = disk_amount(logic_disk_name)
    if amount_of_disk_partition <= 1:
        os.system(f'echo "g\nn\np\n1\n\n\nw" | fdisk /dev/{logic_disk_name}; mkfs.ext4 /dev/{logic_disk_name}1')
    else:
        mount_disk(logic_disk_name)
        move_to_disk_folder()
        print('Укажи время теста в секундах')
        test_time = input()
        start_stress_test(test_time)
        temperature_values = temperature_list(test_time)
        #print(temperature_values)
        print('Минимальная температура: ', min(
            temperature_values), '°C', sep='')
        print('Максимальная температура: ', max(
            temperature_values), '°C', sep='')
