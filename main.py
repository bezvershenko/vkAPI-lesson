from pprint import pprint
from random import shuffle, choice

import vk_api
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.utils import get_random_id
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType

from config import TOKEN, GROUP_ID, DATABASE_NAME
from database.SQLighter import SQLighter

RIGHT_ANSWERS = [
    'Правильно✅\n', 'Ты прав✅\n', 'Точно✅\n', 'Молодец, правильно✅\n'
]
WRONG_ANSWERS = [
    'Ты ошибся❌\nПравильный ответ: ',
    'А вот и нет❌\nПравильный ответ: ',
    'Ошибочка❌\nПравильный ответ: ',
    'Неееет❌\nПравильный ответ: ',
]

ADD = 1
users_data = {}


def genetateKeyboard(o1, o2):
    keyboard = VkKeyboard(one_time=True)

    keyboard.add_button(o1, color=VkKeyboardColor.DEFAULT)
    keyboard.add_button(o2, color=VkKeyboardColor.DEFAULT)
    keyboard.add_line()
    keyboard.add_button('Мой счет', color=VkKeyboardColor.POSITIVE)
    return keyboard


def send_next(vk, uid):
    try:
        current_task = next(users_data[uid]['all_tasks'])
        users_data[uid]['current_task'] = current_task

        vk.messages.send(user_id=uid, random_id=get_random_id(),
                         message=f'Где ставится ударение в слове {current_task[0]}?',
                         keyboard=genetateKeyboard(current_task[1], current_task[2]).get_keyboard())

    except StopIteration:
        pass


def answer_checking(vk, uid, msg):
    word, o1, o2, right_answer = users_data[uid]['current_task']
    answers = [o1, o2]
    add = ADD

    users_answer = msg.text
    db_worker = SQLighter(DATABASE_NAME)

    if users_answer == 'Мой счет':
        users_score = db_worker.select_user(uid)[0][2]
        vk.messages.send(user_id=uid, random_id=get_random_id(),
                         message=f'Твой счет: {users_score}', keyboard=genetateKeyboard(o1, o2).get_keyboard())

    elif users_answer == answers[right_answer]:
        vk.messages.send(user_id=uid, random_id=get_random_id(),
                         message=choice(RIGHT_ANSWERS) + f'Следует говорить: "{answers[right_answer]}"')
        db_worker.change_value_user(uid, add)

    else:
        vk.messages.send(user_id=uid, random_id=get_random_id(),
                         message=choice(WRONG_ANSWERS) + f'Правильный ответ: "{answers[right_answer]}"')
        db_worker.change_value_user(uid, -add)

    db_worker.close()
    if users_answer != 'Мой счет':
        send_next(vk, uid)


def main():
    vk_session = vk_api.VkApi(token=TOKEN)
    vk = vk_session.get_api()
    long_poll = VkBotLongPoll(vk_session, GROUP_ID)

    for event in long_poll.listen():
        if event.type == VkBotEventType.MESSAGE_NEW:
            pprint(users_data)
            msg = event.message
            uid = msg.from_id
            users_data[uid] = users_data.get(uid, {'state': 0})

            if users_data[uid]['state'] == 0:
                user = vk.users.get(user_ids=uid)[0]
                users_data[uid]['name'] = {'first_name': user['first_name'], 'last_name': user['last_name']}

                db_worker = SQLighter(DATABASE_NAME)
                all_tasks = db_worker.select_all('tasks')
                all_users = db_worker.select_all('users')

                shuffle(all_tasks)
                users_data[uid]['all_tasks'] = iter(all_tasks)

                is_registered = list(filter(lambda x: x[0] == uid, all_users))
                if not is_registered:
                    db_worker.add_user(uid, f"{users_data[uid]['name']['first_name']} "
                    f"{users_data[uid]['name']['last_name']}")

                db_worker.close()

                vk.messages.send(user_id=uid,
                                 message=f'Привет, {user["first_name"]} {user["last_name"]}! '
                                 f'начнем нашу викторину по ударениям!',
                                 random_id=get_random_id())
                users_data[uid]['state'] += 1
                send_next(vk, uid)

            elif users_data[uid]['state'] == 1:
                answer_checking(vk, uid, msg)


if __name__ == '__main__':
    main()
    # 1) поправить недочеты
    # 2) починить users_data ! (redis, pickle ...)
    # 3) рейтинг пользователей
    # 4) (по желанию) другая бд
    # 5) обработать конец очереди: что делать, когда все задания пройдены?
    # 6) реализовать logging
