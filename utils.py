from datetime import datetime
import requests
from openpyxl import load_workbook
import logging


month_name = {
    1: 'Января',
    2: 'Февраля',
    3: 'Марта',
    4: 'Апреля',
    5: 'Мая',
    6: 'Июня',
    7: 'Июля',
    8: 'Августа',
    9: 'Сентября',
    10: 'Октября',
    11: 'Ноября',
    12: 'Декабря'
}


def processed_sheet(source):
    dt = {}

    row = 2
    try:
        while source[f'A{row}'].value is not None:
            username = source[f'A{row}'].value
            name = source[f'D{row}'].value
            company = source[f'F{row}'].value

            end_date = source[f'G{row}'].value
            day = end_date.day
            month = month_name[end_date.month]

            link = source[f'H{row}'].value

            price = source[f'I{row}'].value
            try:
                price = round(int(price), 2)
            except Exception:
                pass

            task = source[f'O{row}'].value

            dead_day = 'day'
            dead_month = 'month'
            try:
                deadline = datetime.strptime(source[f'P{row}'].value, '%Y-%d-%m %H:%M:%S')
                dead_day = deadline.day
                dead_month = month_name[deadline.month]
            except TypeError:
                pass

            status = source[f'Q{row}'].value

            temp = {
                    'name': name,
                    'company': company,
                    'end_date': f'{day} {month}',
                    'link': link,
                    'price': price,
                    'task': task,
                    'deadline': f'{dead_day} {dead_month}',
                    'status': status
                }

            if username in dt.keys():
                dt[username].append(temp)
            else:
                dt[username] = [temp]

            row += 1
    except ValueError as e:
        logging.error(f'While processing the Excel sheet an error occured\nInfo: {e}')

    logging.info('Data was successfully loaded from Excel sheet')
    return dt


def get_data():
    download_file()
    try:
        book = load_workbook('table.xlsx')
        sheet = book.get_sheet_by_name('Продления')

        # book = xw.Book('table.xlsx')
        # sheet = book.sheets['Продления']

        return processed_sheet(sheet)

    except FileNotFoundError:
        logging.error('File table.xlsx not found')


def user_access(username, data):
    return username in data.keys()


def download_file():
    url = "<path to google sheets>"
    filename = "table.xlsx"

    response = requests.get(url)
    with open(filename, "wb") as file:
        file.write(response.content)
