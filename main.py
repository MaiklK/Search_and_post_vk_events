#!/usr/bin/python
# -*- coding: UTF-8 -*-
import datetime
import os
import traceback
import vk_api
import configparser
import log
import helpers as th


def error(message):
    """Действия после критической ошибки

    :param message: сообщение показываемое пользователю
    """
    print(message)
    input("Введите 'Enter' для завершения сеанса")
    exit()


def check_file(file_path):
    """Проверяет существование файла
    :param file_path: путь к файлу
    """
    return os.path.exists(file_path)


def get_start_dt(days_delta: int, hours_delta: int):
    """Возвращает дату со смещением на дни и часы

    :param days_delta: разница дней
    :param hours_delta: разница часов
    """
    return datetime.datetime.now() + datetime.timedelta(days=days_delta, hours=hours_delta)


def list_from_file(file_path):
    """Создает список из файла

    :param file_path: путь к файлу
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        filelist = file.read().splitlines()
    return filelist


def authorization_vk(login: str, password: str, app_id, client_secret: str, api_version='5.131'):
    """Авторизация Вконтакте. При успешной авторизации создается файл с токеном и куками,
    из которых в последствии берутся данные

    :param login: логин от аккаунта Вконтакте
    :param password: пароль от аккаунта Вконтакте
    :param app_id: id Standalone-приложения
    :param client_secret: сервисный ключ из настроек приложения
    :param api_version: Версия API
    """
    vk_session = vk_api.VkApi(login=login, password=password, app_id=app_id, client_secret=client_secret,
                              api_version=api_version)
    try:
        vk_session.auth(token_only=True)
        return vk_session
    except Exception:
        log.log(traceback.format_exc())
        error('Ошибка авторизации подробности в логе')


def search_all_event_by_city(vk_session, search_querys: list, city_id: int, country_id: int):
    """Находит id всех предстоящих мероприятий Вконтекте согласно поисковым
    запросам из списка

    :param vk_session: объект vk_api
    :param search_querys: лист с поисковыми запросами
    :param city_id: id города
    :param country_id: id страны
    """
    search_events = {}
    with vk_api.VkRequestsPool(vk_session) as pool:
        for query in search_querys:
            search_events[query] = pool.method('groups.search', {
                'q': query, 'fields': 'photo', 'type': 'event',
                'country_id': country_id, 'city_id': city_id, 'future': 1,
                'count': 1000
            })
    # получение ответа Вконтакте
    all_events = [value.result['items'] for value in search_events.values()]
    # выдергивание только id мероприятий
    all_id_groups = [event['id'] for events in all_events for event in events]
    return list(set(all_id_groups))


def unix_to_datetime(timestamp):
    """Преобразует UnixTime в формат datetime

    :param timestamp: время Unix
    """
    return datetime.datetime.fromtimestamp(int(timestamp))


def sort_group_by_date(vk_session, all_id_groups: list, dt, hours_delta):
    """Фильтрует мероприятия которые случаться со сдвигом по времени
    остальные отбрасывает + удаляет дубли мероприятий

    :param vk_session: объект vk_api
    :param all_id_groups: список id всех предстоящих мероприятий
    :param dt: datetime.now
    :param hours_delta: размер сдвига по дням
    """
    sort_events = []
    name_events = []
    while len(all_id_groups) != 0:
        ids = ''
        for i in range(499):
            if len(all_id_groups) != 0:
                ids += f"{all_id_groups.pop(0)},"
        even_not_sort = vk_api.VkApi.method(vk_session, method='groups.getById',
                                            values={'fields': 'start_date', 'group_ids': ids})
        for event in even_not_sort:
            if event['is_closed'] == 1 and event['type'] == 'group' and event.get('start_date', -1) == -1:
                continue
            if event.get('start_date') < 0:
                event['start_date'] *= -1
            if unix_to_datetime(event['start_date'] + hours_delta * 3600).strftime('%d.%m.%y') == dt.strftime(
                    '%d.%m.%y'):
                # проверка на дубли мероприятий (в поиске куча мероприятий с одинаковыми названиями, но разными id)
                event_name = th.just_leters_and_numbers(th.clean_name(event['name'], dt))
                check_name_event = event_name
                if check_name_event not in name_events:
                    name_events.append(check_name_event)
                    sort_events.append({"id": event['id'],
                                        "name": event['name'],
                                        "screen_name": event['screen_name'],
                                        "start_date": event['start_date'] + hours_delta * 3600})
    return sort_events


def up_fields_for_events(vk_session, all_id_groups: list, field: str, events: list):
    """Добавляет ключи и их значения (информация из api Вконтакте)
    к словарю мероприятий

    :param vk_session: объект vk_api
    :param all_id_groups: id мероприятий
    :param field: название поля
    :param events: словарь мероприятий
    """
    ids = ''
    while len(all_id_groups) != 0:
        if len(ids) > 499:
            break
        ids += f"{all_id_groups.pop(0)},"
    events_fields = vk_api.VkApi.method(vk_session, method='groups.getById',
                                        values={'fields': field, 'group_ids': ids})
    for i in range(len(events)):
        for events_field in events_fields:
            if events[i]['id'] == events_field['id']:
                events[i][field] = events_field.get(field, 0)
    return events


def up_all_fields(vk_session, fields: list, events: list):
    """Массовое добавление ключей и значений (информация из api Вконтакте)
    к словарю мероприятий

    :param vk_session: объект vk_api
    :param fields: список полей
    :param events: словарь мероприятий
    """
    for field in fields:
        ids = th.ids_from_list_events(events)
        events = up_fields_for_events(vk_session, ids, field, events)
    return events


def normal_date(start_date: int, hours_delta: int):
    """Приводит дату начала или окончания мероприятия из utctime
    в нормальный вид и смещает на количество часов из hours_delta

    :param start_date: дата в utctime
    :param hours_delta: разница в часах
    """
    start_date = unix_to_datetime(start_date)
    start_date += datetime.timedelta(hours=-hours_delta)
    return start_date.strftime("%d.%m %H:%M")


def generate_block_text_events(events: list, hours_delta: int, dt):
    """Генерирует основной блок с мероприятиями для постинга

    :param events: список мероприятий
    :param hours_delta: разница в часах
    :param dt: datetime
    """
    i = 1
    text_block_events = ''
    for event in events:
        event_name = th.clean_name(event['name'], dt).upper()
        start_date = normal_date(event['start_date'], hours_delta)
        if event.get('finish_date', 0) == 0:
            text_block_events += f"\n⌚ {start_date}⌚\n{i}.📢@club{event['id']}({event_name})"
        else:
            finish_date = normal_date(event['finish_date'], hours_delta)
            text_block_events += f'\n⌚ {start_date} - {finish_date}⌚\n{i}.📢@club{event["id"]}({event_name})'
        i += 1
    return text_block_events


def generate_trash_block(events: list, hours_delta: int, dt):
    """Генерирует блок с мусорными мероприятиями для постинга

    :param events: список мероприятий
    :param hours_delta: разница в часах
    :param dt: datetime
    """
    text_block_events = ''
    i = 1
    for event in events:
        event_name = th.clean_name(event['name'], dt).lower()
        start_date = normal_date(event["start_date"], hours_delta)
        text_block_events += f'{i}. {start_date} @club{event["id"]}({event_name})\n'
        i += 1
    return text_block_events


def get_photo_events(events: list, photo_list: list):
    """Добавляет photo для постинга из первых 10 фото мероприятий

    :param events: список мероприятий
    :param photo_list: список фото для постинга
    """
    for event in events:
        if len(photo_list) == 10:
            return photo_list
        if event.get('has_photo', 0) == 1:
            if event['crop_photo'] == 0:
                continue
            photo_list.append(
                f"photo{str(event['crop_photo']['photo']['owner_id'])}_{str(event['crop_photo']['photo']['id'])}")
    return photo_list


def photo_to_post(events1: list, events2: list):
    """Возвращает 10 первых фото из 2 списков мероприятий

    :param events1: список мероприятий 1
    :param events2: список мероприятий 2
    """
    photos = ''
    photo_list = []
    photo_list = get_photo_events(events1, photo_list)
    photo_list = get_photo_events(events2, photo_list)
    for photo in photo_list:
        photos += f'{photo},'
    return photos


def post_events_in_vk(vk_session, post_interest, post_other, post_not_interest, id_group, city_name, dt, photos):
    """Постинг мероприятий в указанной группе

    :param post_interest: текст интересных событий
    :param post_other: текст неопознанных(по ключам) событий
    :param post_not_interest: текст не интересных событий
    :param id_group: id группы для постинга (аккаунта должен быть админом)
    :param city_name: имя города
    :param dt: datetime
    :param photos: список фотографий
    """
    text_to_post = f'ВСЕ СОБЫТИЯ|МЕРОПРИЯТИЯ ВКОНТАКТЕ {city_name.upper()} НА {dt.strftime("%d.%m.%Y")}\n'
    if len(post_interest) > 0:
        text_to_post += f'\nПОХОДУ ТУТ БУДЕТ ИНТЕРЕСНО:\n{post_interest}\n'
    if len(post_other) > 0:
        text_to_post += f'\nНЕОПОЗНАННЫЕ СОБЫТИЯ:\n{post_other}\n'
    if len(post_not_interest) > 0:
        text_to_post += f'\nЭТИ МОЖНО НЕ СМОТРЕТЬ:\n\n{post_not_interest}'
    text_to_post = {'owner_id': f'-{id_group}', 'message': text_to_post, 'attachments': photos}
    return vk_api.VkApi.method(vk_session, 'wall.post', text_to_post)


def post_nothing(vk_session, id_group, city_name, dt):
    """Постинг в случае отсутствия событий на нужную дату

    :param id_group: id группы для постинга (аккаунта должен быть админом)
    :param city_name: имя города
    :param dt: datetime
    """
    text_to_post = f'ВСЕ СОБЫТИЯ|МЕРОПРИЯТИЯ ВКОНТАКТЕ {city_name} НА {dt.strftime("%d.%m.%Y")}\n\n' \
                   f'А СОБЫТИЙ ТО И НЕТУ'
    text_to_post = {'owner_id': f'-{id_group}', 'message': text_to_post}
    return vk_api.VkApi.method(vk_session, 'wall.post', text_to_post)


def main(login: str, password: str, app_id: str, client_secret: str, id_country: str, id_city: str,
         id_group: str, city_name: str, hours_delta: int, days_delta: int,
         interesting_path: str, not_interesting_path: str):
    """Тело основной функции, ищет и публикует мероприятия на желаемую дату задается параметром 'days_delta',
    желаемой страны параметр 'id_country' и города 'id_city', при этом фильтруя на интересные 'interesting_path'
    и неинтересные 'not_interesting_path'

    :param login: логин от аккаунта VK
    :param password: пароль от аккаунта VK
    :param app_id: id приложения
    :param client_secret:  секретный ключ приложения
    :param id_country: id страны в которой будем искать события
    :param id_city: id города для которого будем искать события
    :param id_group: id группы в которую будем постить
    :param city_name: имя города для которого будем искать события
    :param hours_delta: разница в часах от московского времени
    :param days_delta: разница в днях 0 => сегодня
    :param interesting_path: путь к белому списку мероприятий
    :param not_interesting_path: путь к черному списку мероприятий
    """
    da_ta = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
    print(f"{da_ta}: Начало работы")
    dt = get_start_dt(int(days_delta), int(hours_delta))
    vk_session = authorization_vk(login, password, app_id, client_secret)
    search_querys = th.get_search_querys(datetime.datetime.now())
    all_ids_events = search_all_event_by_city(vk_session, search_querys, int(id_city), int(id_country))
    events = sort_group_by_date(vk_session, all_ids_events, dt, hours_delta)
    if len(events) == 0:
        post_nothing(vk_session, id_group, city_name, dt)
        da_ta = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
        print(f'{da_ta}: Нету событий для {city_name} на {dt.strftime("%d.%m.%Y %H:%M")}')
    fields = ['description', 'finish_date', 'status', 'has_photo', 'crop_photo', 'site']
    events = up_all_fields(vk_session, fields, events)
    events = th.sort_events_by_date(events)
    interesting_events = []
    not_interesting_events = []
    if check_file(interesting_path):
        interesting = list_from_file(interesting_path)
        interesting_events = th.sort_events_by_keys(events, interesting)
        events = th.minus_events(events, interesting_events)
    if check_file(not_interesting_path):
        not_interesting = list_from_file(not_interesting_path)
        not_interesting_events = th.sort_events_by_keys(events, not_interesting)
        events = th.minus_events(events, not_interesting_events)
    text_interesting_events = generate_block_text_events(interesting_events, hours_delta, dt)
    text_others_events = generate_block_text_events(events, hours_delta, dt)
    text_not_interesting_events = generate_trash_block(not_interesting_events, hours_delta, dt)
    photos = photo_to_post(interesting_events, events)
    req = post_events_in_vk(vk_session, text_interesting_events, text_others_events,
                            text_not_interesting_events, id_group, city_name, dt, photos)
    if 'post_id' in req:
        da_ta = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
        print(f"{da_ta}: события успешно опубликованы")
    else:
        error('Что-то пошло не так')



login = password = app_id = client_secret = id_country = id_city = id_group = city_name = hours_delta = \
    days_delta = interesting_path = not_interesting_path = ''
# взятие конфига из файла settings.ini
if check_file('settings.ini'):
    config = configparser.ConfigParser()
    config.read('settings.ini', encoding="utf-8")
    login = config['vk']['login']  # логин от аккаунта VK
    password = config['vk']['password']  # пароль от аккаунта VK
    app_id = config['vk']['app_id']  # id приложения
    client_secret = config['vk']['client_secret']  # секретный ключ приложения
    id_country = config['vk']['id_country']  # id страны в которой будем искать события
    id_city = config['vk']['id_city']  # id города для которого будем искать события
    id_group = config['vk']['id_group']  # id группы в которую будем постить
    # дальше идут необязательные параметры
    city_name = config['settings']['city_name']  # имя города для которого будем искать события
    hours_delta = config['settings']['hours_delta']  # разница в часах от московского времени
    days_delta = config['settings']['days_delta']  # разница в днях 0 сегодня 1 завтра и т.д.
    interesting_path = config['settings']['interesting_path']  # путь к белому списку мероприятий
    not_interesting_path = config['settings']['not_interesting_path']  # путь к черному списку мероприятий
else:
    error("Не найден файл конфигурации 'settings.ini'")

try:
    main(login, password, app_id, client_secret, id_country, id_city, id_group, city_name, int(hours_delta),
         int(days_delta), interesting_path, not_interesting_path)
except Exception:
    log.log(traceback.format_exc())
    error('Что-то пошло не так, подробности в логе')
