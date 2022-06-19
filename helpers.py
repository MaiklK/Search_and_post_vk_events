import re
import operator


def month_in_russian(month):
    """Возвращает полное название месяца на русском языке по его номеру.

    :param month: цифра от 1 до 12
    """
    if type(month) is int:
        month = str(month)
    replace_values = {'1': 'января', '2': 'февраля', '3': 'марта', '4': 'апреля', '5': 'мая', '6': 'июня',
                      '7': 'июля', '8': 'августа', '9': 'сентября', '10': 'октября', '11': 'ноября',
                      '12': 'декабря'}
    for i, j in replace_values.items():
        month = month.replace(i, j)
    return month


def change_rus_letters(text):
    """Заменяет русские буквы на точные аналоги английских

    :param text: строка для преобразования
    """
    replace_values = {'А': 'A', 'а': 'a', 'В': 'B', 'Е': 'E', 'е': 'e', 'К': 'K',
                      'М': 'M', 'Н': 'H', 'О': 'O', 'о': 'o', 'Р': 'P', 'р': 'p',
                      'С': 'C', 'с': 'c', 'Т': 'T', 'у': 'y', 'Х': 'X', 'х': 'x'}
    for i, j in replace_values.items():
        text = text.replace(i, j)
    return text


def get_search_querys(datetime):
    """Выдает список поисковых запросов для поиска мероприятий в вк

    :param datetime: объект datetime.datetime для поисковых запросов по дате
    """
    return ["а", "б", "в", "г", "д", "е", "ж", "з", "и", "й", "к", "л", "м", "н", "о", "п", "р", "с", "т",
            "у", "ф", "х", "ш", "щ", "ы", "э", "ю", "я", "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k",
            "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", " ", "аа", "аб", "ав",
            "аг", "ад", "ае", "аё", "аж", "аз", "аи", "ай", "ак", "ал", "ам", "ан", "ао", "ап", "ар", "ас",
            "ат", "ау", "аш", "ащ", "аы", "аэ", "аю", "ая", "ва", "вб", "вв", "вг", "вд", "ве", "вё", "вж",
            "вз", "ви", "вй", "вк", "вл", "вм", "вн", "во", "вп", "вр", "вс", "вт", "ву", "вш", "вщ", "вы",
            "вэ", "вю", "вя", "иа", "иб", "ив", "иг", "ид", "ие", "иё", "иж", "из", "ии", "ий", "ик", "ил",
            "им", "ин", "ио", "ип", "ир", "ис", "ит", "иу", "иш", "ищ", "иы", "иэ", "ию", "ия", "ма", "мб",
            "мв", "мг", "мд", "ме", "мё", "мж", "мз", "ми", "мй", "мк", "мл", "мм", "мн", "мо", "мп", "мр",
            "мс", "мт", "му", "мш", "мщ", "мы", "мэ", "мю", "мя", "са", "сб", "св", "сг", "сд", "се", "сё",
            "сж", "сз", "си", "сй", "ск", "сл", "см", "сн", "со", "сп", "ср", "сс", "ст", "су", "сш", "сщ",
            "сы", "сэ", "сю", "ся", "ша", "шб", "шв", "шг", "шд", "ше", "шё", "шж", "шз", "ши", "шй", "шк",
            "шл", "шм", "шн", "шо", "шп", "шр", "шс", "шт", "шу", "шш", "шщ", "шы", "шэ", "шю", "шя", "батл",
            "sex", "секс", "rope", "сальса", "бачата", "урок", "мастеркласс", "хастл", "танцы", "обучение",
            "бдсм", "бондаж", "бал", "тренинг", "вальс", "танец", "танцы", datetime.strftime("%d.%m"),
            f'{datetime.strftime("%d")} {month_in_russian(datetime.month)}']


def just_leters_and_numbers(string: str):
    """Возвращает переданную строку удаляя все кроме букв и цифр

    :param string: текст
    """
    return re.sub(r'[^А-Яа-яЁёA-Za-z\d]', '', string)


def clean_name(name: str, dt):
    """Очищает название мероприятия от мусора

    :param name: имя мероприятия
    :param dt: datetime
    """
    replace_list = [f'{dt.day} {month_in_russian(dt.month)}', dt.strftime('%d%m%Y'), dt.strftime('%d%m%y'),
                    dt.strftime('%d.%m.%Y'), dt.strftime('%d.%m.%y'), dt.strftime('%d.%m'), dt.strftime("%d %m"),
                    f'{dt.day}.f{dt.strftime("%m")}', f'{dt.strftime("%Y")} г', dt.strftime('%d%m'),
                    f'{dt.strftime("%Y")}г', f'{dt.strftime("%Y")}года', f'{dt.strftime("%Y")}год',
                    f'{dt.strftime("%y")} г', f'{dt.strftime("%y")}г', dt.strftime("%Y"), dt.strftime("%d/%m"),
                    'января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября',
                    'ноября', 'декабря', '@', '(', ')']
    for string in replace_list:
        name = name.replace(string, '')
    replace_values = {'  ': ' ', '	': ' ', '"AHAVA" Jewish Sp': 'AHAVA', '"AHAVA" Москва': 'AHAVA',
                      '"AHAVA" Moscow': 'AHAVA', '"AHAVA"': 'AHAVA', ' - - ': ' - '}
    for i, j in replace_values.items():
        name = name.replace(i, j)
    name = name.strip(r'.-+= ,"|\/[]()').lower()
    name = change_rus_letters(name)
    return name


def prepare_to_check(text):
    """Обрабатывает текст и оставляет только буквы и цифры
    плюс меняет аналогичные русские буквы на английские и приводит в нижний регистр

    :param text: текст для обработки
    """
    text = just_leters_and_numbers(text).lower()
    return change_rus_letters(text)


def ids_from_list_events(events: list):
    """Пробегается по списку из словарей и возвращает список из значений ключа 'id'

    :param events: словарь с мероприятиями
    """
    ids = []
    for event in events:
        ids.append(event['id'])
    return ids


def sort_events_by_keys(events: list, list_keys: list):
    """Отсортировывает события по списку ключей

    :param events: список мероприятий
    :param list_keys: список ключей
    """
    sorted_events = []
    for event in events:
        check_event = event.get('name', '') + event.get('screen_name', '') + \
                      event.get('description', '').replace('\\n', '') + \
                      event.get('site', '') + event.get('status', '')
        check_event = prepare_to_check(check_event)
        for check in list_keys:
            check = prepare_to_check(check)
            if check in check_event:
                sorted_events.append(event)
                break
    return sorted_events


def minus_events(from_events: list, other_events: list):
    """Вычитает из основного списка мероприятий другой список мероприятий

    :param from_events: список основных мероприятий
    :param other_events: список вычитаемых мероприятий
    """
    help_list = []
    for from_event in from_events:
        check = 0
        for other_event in other_events:
            if from_event['id'] == other_event['id']:
                check += 1
        if check == 0:
            help_list.append(from_event)
    return help_list


def create_dict_from_events_by_startdate(events: list):
    """Создает словарь вида id: start_date из списка мероприятий
    в порядке возрастания по start_date

    :param events: список мероприятий
    """
    event_id = {}
    for event in events:
        event_id[event['id']] = event['start_date']
    sorted_tuples = sorted(event_id.items(), key=operator.itemgetter(1))
    date_id = {k: v for k, v in sorted_tuples}
    return date_id


def sort_events_by_date(events: list):
    """Сортирует список мероприятий по стартовой дате
    в порядке возрастания
    :param events: список мероприятий
    """
    check_dict = create_dict_from_events_by_startdate(events)
    events_by_date = []
    for id_event in check_dict:
        for event in events:
            if id_event == event['id']:
                events_by_date.append(event)
                break
    return events_by_date
