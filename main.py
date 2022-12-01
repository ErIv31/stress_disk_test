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
    return len(get_console_output(
        f'ls /dev/ | grep {disk}').strip().split('\n'))


# Определяем название вендора жесткого диска
def get_vendor_disk_name(output):
    return re.search(r'ata.*', output).group(0).split(' ')[0][4:29]


# Определяем тип диска ufs, ext4, ...
def get_disk_type():
    return re.search(r'TYPE.*', get_console_output('blkid | grep sda1')).group(0).split(' ')[0][6:10]


# Форматируем диск
def format_disk(disk):
    os.system(
        f'echo "g\nn\np\n1\n\n\nw" | fdisk /dev/{disk}; mkfs.ext4 /dev/{disk}1')


# Примонтируем диск
def mount_disk():
    os.system('mkdir /mnt/disk')
    disk_type = get_disk_type()
    if disk_type == 'ext4':
        linux_filesystem_disk = get_console_output(
            'fdisk -l | grep "Linux filesystem"')[0:9]
        os.system(f'mount {linux_filesystem_disk} /mnt/disk/')
    elif disk_type == 'ufs':
        os.system('mount -t ufs -o ro,ufstype=ufs2 /dev/sda8 /mnt/disk/')


# Перемещаемся в директорию диска
def move_to_disk_folder():
    os.system('cd /mnt/disk/; pwd')


# Запускаем стресс тест в фоновом режиме
def start_stress_test(test_time: str):
    #os.system(f'stress-ng --class filesystem --sequential 8 --timeout {test_time}s --metrics-brief &')
    #os.system(f'stress-ng --cpu 4 --io 4 --hdd 4 hdd-opts rd-rnd wr-rnd --vm 4 --timeout {test_time}s &')
    os.system(f'stress-ng --timeout {test_time}s --hdd 0 &') # нагрузка только диска
    print(f'Test is starting during {test_time} seconds')
    # os.system(
    #     f'stress-ng --sequential 0 --class io --timeout {test_time}s --metrics-brief &')
    # print(f'Test is starting during {test_time} seconds')


# Калькулятор времени
def time_calculator(test_time):
    cores = get_console_output('nproc')
    time_end = time.time() + (float(test_time) * float(cores) + 10)
    time_format = time.strftime("%H:%M:%S", time.gmtime(time_end))
    print('Начало теста:', datetime.datetime.now().strftime("%H:%M:%S"))
    print('Конец теста:', time_format)
    return time_end


#  Получаем значения температур
def temperature_list(time_end, logic_disk_name):
    value_list = []
    while time.time() <= time_end:
        temperature_value = get_console_output(
            f"smartctl -A /dev/{logic_disk_name} | grep 194").split(' ')[-3] # Надо изменить sda на logic_name, который передается из другой функции
        value_list.append(int(temperature_value))
        #date = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
        #print(date, 'Температура: ' + temperature_value, end='')
    return value_list


# Записываем текстовый файл с информацией по тестам
def file_write(filename, value):
    open_file = open(filename, 'a')
    open_file.write(value)
    open_file.close()
    

# Открываем для чтения текстовый файл с информацией по тестам
def file_read(filename):
    open_file = open(filename, 'r')
    print(open_file.read())
    open_file.close()


if __name__ == "__main__":
    disks = get_console_output('ls -l /dev/disk/by-id')
    logic_disk_name = get_logical_disk_name(disks)
    vendor_disk_name = (re.search(r'ata.*', disks).group(0).split(' ')[0][4:29]).replace('_', ' ')
    actual_date = datetime.datetime.now().strftime('%d.%m.%Y')
    amount_of_disk_partition = how_many_partitions(logic_disk_name)
    while amount_of_disk_partition <= 1:
        format_disk(logic_disk_name)
        #os.system(f'echo "g\nn\np\n1\n\n\nw" | fdisk /dev/{logic_disk_name}; mkfs.ext4 /dev/{logic_disk_name}1')
        amount_of_disk_partition = how_many_partitions(logic_disk_name)
    if amount_of_disk_partition > 1:
        mount_disk()
        move_to_disk_folder()
        test_time = input('Укажи время теста в секундах: ')
        start_stress_test(test_time)
        temperature_values = temperature_list(time_calculator(test_time), logic_disk_name)
        # print(temperature_values)
        max_temp = max(temperature_values)
        file_write('disk_test.txt', actual_date + ' | ' + vendor_disk_name + ' | ' + str(max_temp) + '°C' +'\n')
        file_read('disk_test.txt')
        # print('Максимальная температура: ', max(
        #     temperature_values), '°C', sep='')
