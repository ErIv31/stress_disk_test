import config

from stress_test import *


def main():
    disks = get_console_output('ls -l /dev/disk/by-id')
    # определение логического имени жесткого диска
    logic_disk_name = get_logical_disk_name(disks)
    # определение названия вендора диска
    vendor_disk_name = get_vendor_disk_name(disks)
    disk_type = get_disk_type(logic_disk_name)
    if disk_type != 'ext4': 
        format_disk(logic_disk_name)
    mount_disk()  # подключаем жесткий диск к LiveUSB
    actual, end = time_calculator()
    # Запускаем стресс тест, в начале выполняется переход в директорию
    # примонтированного диска, затем выполняется stress-ng
    # в фоновом режиме
    if config.DEBUG:
        print(actual)
    start_stress_test(actual)
    # Прараллельно тесту заполняется список с значениями температур
    # жесткого диска

    temperature_values = temperature_list(
        end,
        logic_disk_name,
    )
    # вычисляется максимальная температура нагрева диска в ходе теста
    max_temp = max(temperature_values)
    # создается или записывается в уже созданный файл значения: дата
    # проверки, вендор диска, макс. температура
    actual_date = datetime.datetime.now().strftime(
        '%d.%m.%Y')
    file_write('disk_test.txt', actual_date, vendor_disk_name, max_temp)
    # выводится информация, записанная в файл, на экран оператора
    show_maximum('disk_test.txt')
    # print('Максимальная температура: ', max(
    #     temperature_values), '°C', sep='')


if __name__ == "__main__":
    main()
