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

    :param days_delta: разница часов
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


def search_all_event_by_city(search_querys: list, city_id: int, country_id: int):
    """Находит id всех предстоящих мероприятий Вконтекте согласно поисковым
    запросам из списка

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


def sort_group_by_date(all_id_groups: list, dt, hours_delta):
    """Фильтрует мероприятия которые случаться со сдвигом по времени
    остальные отбрасывает + удаляет дубли мероприятий

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


def up_fields_for_events(all_id_groups: list, field: str, events: list):
    """Добавляет ключи и их значения (информация из api Вконтакте)
    к словарю мероприятий

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


def up_all_fields(fields: list, events: list):
    """Массовое добавление ключей и значений (информация из api Вконтакте)
    к словарю мероприятий

    :param fields: список полей

    :param events: словарь мероприятий
    """
    for field in fields:
        ids = th.ids_from_list_events(events)
        events = up_fields_for_events(ids, field, events)
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


login = password = app_id = client_secret = id_country = city_name = id_city = hours_delta = id_group = ''
# взятие конфига из файла settings.ini
if check_file('settings.ini'):
    config = configparser.ConfigParser()
    config.read('settings.ini', encoding="utf-8")
    login = config['vk']['login']  # логин от аккаунта VK
    password = config['vk']['password']  # пароль
    app_id = config['vk']['app_id']  # id приложения
    client_secret = config['vk']['client_secret']  # секретный ключ приложения
    id_country = config['vk']['id_country']  # id страны в которой будем искать события
    id_city = config['vk']['id_city']  # id города для которого будем искать события
    id_group = config['vk']['id_group']  # id группы в которую будем постить
    # дальше идут необязательные параметры
    city_name = config['vk']['city_name']  # имя города для которого будем искать события
    hours_delta = config['vk']['hours_delta']  # разница в часах от московского времени
    interesting_path = config['vk']['interesting_path']  # путь к белому списку мероприятий
    not_interesting_path = config['vk']['not_interesting_path']  # путь к черному списку мероприятий
else:
    error("Не найден файл конфигурации 'settings.ini'")
vk_session = authorization_vk(login, password, app_id, client_secret)
