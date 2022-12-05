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
    os.system(f'cd /mnt/disk; stress-ng --timeout {test_time}s --hdd 0 &')
    print(f'Тест начнётся в течение {test_time} секунд')
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
            f"smartctl -A /dev/{logic_disk_name} | grep 194").split(' ')[-3]
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
    # определение установленных дисков в платформу
    disks = get_console_output('ls -l /dev/disk/by-id')
    # определение логического имени жесткого диска
    logic_disk_name = get_logical_disk_name(disks)
    vendor_disk_name = (re.search(r'ata.*', disks).group(0).split(' ')
                        [0][4:29]).replace('_', ' ')  # определение названия вендора диска
    actual_date = datetime.datetime.now().strftime(
        '%d.%m.%Y')  # вывод актуальной даты проверки диска
    amount_of_disk_partition = how_many_partitions(
        logic_disk_name)  # подсчет разделов диска
    # Цикл в котором определяется надо форматировать диск или нет. Если диск новый или на нем установлена система freebsd, то его форматнут и сделает разметку ext4
    if amount_of_disk_partition <= 1:
        format_disk(logic_disk_name)
        amount_of_disk_partition = how_many_partitions(logic_disk_name)
    mount_disk()  # подключаем жесткий диск к LiveUSB
    # Указываем время теста
    test_time = input('Укажи время теста в секундах: ')
    # Запускаем стресс тест, в начале выполняется переход в директорию примонтированного диска, затем выполняется stress-ng в фоновом режиме
    start_stress_test(test_time)
    # Прараллельно тесту заполняется список с значениями температур жесткого диска
    temperature_values = temperature_list(
        time_calculator(test_time), logic_disk_name)
    # вычисляется максимальная температура нагрева диска в ходе теста
    max_temp = max(temperature_values)
    # создается или записывается в уже созданный файл значения: дата проверки, вендор диска, макс. температура
    file_write('disk_test.txt', actual_date + ' | ' +
               vendor_disk_name + ' | ' + str(max_temp) + '°C' + '\n')
    # выводится информация, записанная в файл, на экран оператора
    file_read('disk_test.txt')
    # print('Максимальная температура: ', max(
    #     temperature_values), '°C', sep='')
