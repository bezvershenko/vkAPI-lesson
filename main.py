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
users_data = {}


def send_next(vk, uid):
    try:
        current_task = next(users_data[uid]['all_tasks'])
        users_data[uid]['current_task'] = current_task

        keyboard = VkKeyboard(one_time=True)

        keyboard.add_button(current_task[1], color=VkKeyboardColor.DEFAULT)
        keyboard.add_button(current_task[2], color=VkKeyboardColor.DEFAULT)
        keyboard.add_line()
        keyboard.add_button('Мой счет', color=VkKeyboardColor.POSITIVE)

        vk.messages.send(user_id=uid, random_id=get_random_id(),
                         message=f'Где ставится ударение в слове {current_task[0]}?',
                         keyboard=keyboard.get_keyboard())
        return users_data

    except StopIteration:
        pass


def answer_checking_big_quiz(vk, uid, msg):
    word, o1, o2, right_answer = users_data[uid]['current_task']
    answers = [o1, o2]

    user_answer = msg.text

    db_worker = SQLighter(DATABASE_NAME)

    if user_answer == 'Мой счет':
        db_worker = SQLighter(DATABASE_NAME)
        user_score = db_worker.select_user(uid)[0][2]
        vk.messages.send(user_id=uid, random_id=get_random_id(),
                         message=f'Твой счет: {user_score}')

    elif user_answer == answers[right_answer]:

        vk.messages.send(user_id=uid, random_id=get_random_id(),
                         message=choice(RIGHT_ANSWERS) + f'Следует говорить "{answers[right_answer]}"')
        add = 1

        db_worker.change_value_user(uid, add)

    else:
        vk.messages.send(user_id=uid, random_id=get_random_id(), message=choice(WRONG_ANSWERS) + answers[right_answer])
        db_worker.change_value_user(uid, -1)

    db_worker.close()
    send_next(vk, uid)


def main():
    vk_session = vk_api.VkApi(token=TOKEN)
    vk = vk_session.get_api()

    long_poll = VkBotLongPoll(vk_session, GROUP_ID)

    for event in long_poll.listen():

        if event.type == VkBotEventType.MESSAGE_NEW:
            print(event)

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
                    db_worker.add_user(uid, users_data[uid]['name']['first_name'] + ' ' + users_data[uid]['name'][
                        'last_name'])

                db_worker.close()

                vk.messages.send(user_id=uid, random_id=get_random_id(),
                                 message=f"Привет, {user['first_name']} {user['last_name']}! "
                                 f"Начнем нашу викторину по ударениям!")
                send_next(vk, uid)
                users_data[uid]['state'] += 1

            elif users_data[uid]['state'] == 1:
                answer_checking_big_quiz(vk, uid, msg)


if __name__ == '__main__':
    main()
