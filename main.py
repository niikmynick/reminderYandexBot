import asyncio
import json
import logging
import logging.config

from aiogram import Bot, Dispatcher

from aiogram.enums import ParseMode
from aiogram.filters import Command, Filter
from aiogram.types import Message
from aiogram.utils.markdown import hbold
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import db
from properties import BOT_TOKEN
from utils import get_data, user_access


class TextFilter(Filter):
    def __init__(self, my_text: str) -> None:
        self.my_text = my_text

    async def __call__(self, message: Message) -> bool:
        return message.text == self.my_text


data = {}
users = {}
admins = {}


bot = Bot(BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()


@dp.message(Command('start'))
async def command_start_handler(message: Message) -> None:
    username = message.from_user.username

    logging.info(f'User {username} sent command /start')

    users[username] = {
        'chat_id': message.from_user.id,
        'status': 'need_login'
    }

    if user_access(username, data):
        name = data[username][0]["name"].split()[1]

        answer_text = (f'Привет, {hbold(name)}!\n'
                       '\nДобро пожаловавть в бот-помощник для сотрудников вашего отдела.\n'
                       'С моей помощью ты сможешь быстро узнавать свои задачи и дополнительную информацию по ним\n\n'
                       'Для начала работы введи свой логин в системе компании')

    elif username in admins.keys():
        answer_text = (f'Привет, {hbold(admins[username])}!\n'
                       '\nДобро пожаловавть в бот-помощник для сотрудников вашего отдела.\n'
                       'С моей помощью ты сможешь быстро узнавать свои задачи и дополнительную информацию по ним\n\n'
                       'Для начала работы введи свой логин в системе компании')

    else:
        name = message.from_user.full_name
        answer_text = (f'Привет, {hbold(name)}!\n'
                       '\nК сожалению, вам недоступно использование этого бота')
        users[username]['status'] = 'denied'

    await message.answer(answer_text)


@dp.message(TextFilter('Задачи'))
async def task_request_handler(message: Message) -> None:
    username = message.from_user.username

    if not (user_access(username, data) or username in admins or users[username]['status'] == 'logged_in'):
        return

    logging.info(f'User {username} asked for his tasks')
    await send_notification([username])


@dp.message(TextFilter('Отчет'))
async def report_request_handler(message: Message) -> None:
    username = message.from_user.username

    if not (user_access(username, data) or username in admins or users[username]['status'] == 'logged_in'):
        return

    logging.info(f'User {username} asked for report')
    await send_report(username)


@dp.message()
async def login_handler(message: Message) -> None:
    if users[message.from_user.username]['status'] != 'need_login':
        return

    username = message.from_user.username
    login = message.text
    db.insert_user(message.from_user.id, login, username)
    users[username]['status'] = 'logged_in'

    kb_builder = ReplyKeyboardBuilder()

    kb_builder.button(text=f"Задачи", callback_data=f"check:{username}")
    if username in admins.keys():
        kb_builder.button(text=f"Отчет", callback_data=f"total_info")

    logging.info(f'User {username} sent his login')
    await message.answer(
        'Отлично, теперь ты можешь пользоваться ботом',
        reply_markup=kb_builder.as_markup(resize_keyboard=True)
    )


def form_answer(beginning, lst):
    result = beginning
    for i in range(len(lst)):
        task = lst[i]
        result += (f'\n{hbold(str(i + 1) + ". " + task["company"])}\n'
                   f'{task["link"]}\n'
                   f'{hbold("Текущая стоимость:")} {task["price"]}\n'
                   f'{hbold("Дата завершения:")} {task["end_date"]}\n'
                   f'{hbold("Задача от куратора:")} {task["task"]}\n'
                   f'{hbold("Дедлайн:")} {task["deadline"]}\n')
    return result


def find_tasks(username):
    sprint_tasks = []
    done_tasks = []
    failed_tasks = []

    if username not in data.keys():
        return [sprint_tasks, done_tasks, failed_tasks]

    for task in data[username]:
        if task['status'] == 'В спринте':
            sprint_tasks.append(task)
        elif task['status'] == 'Выполнено':
            done_tasks.append(task)
        elif task['status'] == 'Не выполнено':
            failed_tasks.append(task)

    return [sprint_tasks, done_tasks, failed_tasks]


async def send_notification(require):
    global data
    data = get_data()

    for username in require:
        if username not in users.keys():
            continue

        sprint_tasks, done_tasks, failed_tasks = find_tasks(username)

        if sprint_tasks:
            answer = form_answer(f'Твои задачи {hbold("в спринте")}:\n', sprint_tasks)
            await bot.send_message(users[username]['chat_id'], answer)

        if done_tasks:
            answer = form_answer(f'Твои {hbold("выполненные задачи")}:\n', done_tasks)
            await bot.send_message(users[username]['chat_id'], answer)

        if failed_tasks:
            answer = form_answer(f'Твои {hbold("невыполненные задачи")}:\n', failed_tasks)
            await bot.send_message(users[username]['chat_id'], answer)

        if not (sprint_tasks or done_tasks or failed_tasks):
            await bot.send_message(users[username]['chat_id'], 'У вас нет задач')
            return

        logging.info(f'Sent tasks to user {username}')


async def send_report(username):
    global data
    data = get_data()

    answer_text = f'{hbold("Отчет по менеджерам:")}\n'

    i = 1
    for user in data.keys():
        sprint_tasks, done_tasks, failed_tasks = find_tasks(user)
        total_tasks = len(sprint_tasks) + len(done_tasks) + len(failed_tasks)

        name = data[user][0]['name']
        answer_text += f'{hbold(f"{i}. {name}")}\n'

        answer_text += f'Задач в спринте: '
        if len(sprint_tasks):
            answer_text += f'{len(sprint_tasks)} ({round(len(sprint_tasks) / (total_tasks / 100), 1)}%)\n'
        else:
            answer_text += '0\n'

        answer_text += f'Выполненных задач: '
        if len(done_tasks):
            answer_text += f'{len(done_tasks)} ({round(len(done_tasks) / (total_tasks / 100), 1)}%)\n'
        else:
            answer_text += '0\n'

        answer_text += f'Невыполненных задач: '
        if len(failed_tasks):
            answer_text += f'{len(failed_tasks)} ({round(len(failed_tasks) / (total_tasks / 100), 1)}%)\n'
        else:
            answer_text += '0\n'

        answer_text += f'Всего задач: {total_tasks}\n\n'

        i += 1

    await bot.send_message(users[username]['chat_id'], answer_text)
    logging.info(f'Sent report to user {username}')


def create_jobs(scheduler):
    scheduler.add_job(send_notification, "cron", day_of_week="mon", hour=10, minute=0, args=[data.keys()])
    scheduler.add_job(send_notification, "cron", day_of_week="wed", hour=10, minute=0, args=[data.keys()])
    scheduler.add_job(send_notification, "cron", day_of_week="fri", hour=10, minute=0, args=[data.keys()])

    scheduler.add_job(send_report, "cron", day_of_week="fri", hour=19, minute=0, args=[admins.keys()])


async def main():
    logging.debug('Connecting to database')
    db.connect()

    for i in db.get_users():
        users[i[1]] = {
            'chat_id': i[0],
            'status': 'logged_in'
        }

    logging.debug('Loading data from file')

    global data
    data = get_data()

    logging.debug('Configuring schedule')
    scheduler = AsyncIOScheduler()
    create_jobs(scheduler)
    scheduler.start()

    logging.debug('Starting bot')
    await dp.start_polling(bot)


if __name__ == "__main__":
    dict_config = json.load(open('logging.conf.json', 'r'))
    logging.config.dictConfig(
        config=dict_config
    )
    asyncio.run(main())
