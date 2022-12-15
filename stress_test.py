#!/usr/bin/python3
import os
import re
import time
import datetime
import config


from subprocess import Popen, PIPE


# Получаем результат выполнения системной команды
def get_console_output(val):
    return Popen(val, stdout=PIPE, stderr=PIPE, shell=True, universal_newlines=True).communicate()[0]


# Получаем логическое имя диска
def get_logical_disk_name(output):
    return re.search(r'ata.*', output).group(0).split(' ')[2][-3:]


# Определяем название вендора жесткого диска
def get_vendor_disk_name(output):
    return re.search(r'ata.*', output).group(0).split(' ')[0][4:29].replace('_', ' ')


# Определяем тип диска ufs, ext4, ...
def get_disk_type(logic_disk_name):
    return re.search(r'TYPE.*', get_console_output(f'blkid | grep {logic_disk_name}')).group(0).split(' ')[0][6:10]


# Форматируем диск
def format_disk(disk):
    os.system(
        f'echo "g\nn\np\n1\n\n\nw" | fdisk /dev/{disk}; mkfs.ext4 /dev/{disk}1')


# Примонтируем диск
def mount_disk():
    if os.path.exists('/mnt/disk'):
        linux_filesystem_disk = get_console_output(
            'fdisk -l | grep "Linux filesystem"')[0:9]
        os.system(f'mount {linux_filesystem_disk} /mnt/disk/')
    else:
        os.system('mkdir /mnt/disk')
        linux_filesystem_disk = get_console_output(
            'fdisk -l | grep "Linux filesystem"')[0:9]
        os.system(f'mount {linux_filesystem_disk} /mnt/disk/')


# Запускаем стресс тест в фоновом режиме
def start_stress_test(test_time: str):
    #os.system(f'stress-ng --class filesystem --sequential 8 --timeout {test_time}s --metrics-brief &')
    #os.system(f'stress-ng --cpu 4 --io 4 --hdd 4 hdd-opts rd-rnd wr-rnd --vm 4 --timeout {test_time}s &')
    # нагрузка только диска
    cmd = f'cd /mnt/disk; stress-ng --timeout {test_time}s --hdd 0 &'
    if config.DEBUG:
        print(cmd)
    else:
        os.system(cmd)
    # os.system(
    #     f'stress-ng --sequential 0 --class io --timeout {test_time}s --metrics-brief &')


def time_format(source_time):
    return time.strftime("%H:%M:%S", time.gmtime(source_time))


# Калькулятор времени
def time_calculator():
    cores = get_console_output('nproc')
    start = time.time()
    time_end = start + float(config.TEST_TIME)
    actual_test_time = float(config.TEST_TIME) 
    print('Начало теста:', time_format(start))
    print('Конец теста:', time_format(time_end))
    return actual_test_time, time_end


#  Получаем значения температур
def temperature_list(time_end, logic_disk_name):
    value_list = []
    while time.time() <= time_end + 1.0:
        temperature_value = get_console_output(
            f"hddtemp /dev/{logic_disk_name}").split(' ')[-1]
        try:
            value_list.append(int(temperature_value))
        except:
            value_list.append(None)
        if config.DEBUG:
            print('time time', time_format(time.time()))
            print('time end', time_format(time_end))
            print(datetime.datetime.now().strftime(
                '%H:%M:%S'), 'Температура: ' + temperature_value, end='' '\n')
        time.sleep(config.RESOLUTION)
    os.system('umount /mnt/disk')
    return value_list


# Записываем текстовый файл с информацией по тестам
def file_write(filename, actual_date, vendor_disk_name, max_temp):
    with open(filename, 'a') as f:
        value = f'{actual_date} | {vendor_disk_name} | {max_temp} °C \n'
        f.write(value)


# Открываем для чтения текстовый файл с информацией по тестам
def show_maximum(filename):
    with open(filename, 'r') as f:
        print(f.read())
