**Search and post vk events** 

Поиск и публикация событий (мероприятий ) ВКонтакте при помощи модуля vk_api

События сортируются по времени, к посту прикрепляются аватарки первых 10 мероприятий,
есть опция фильтрации на интересные и неинтересные события

Мой первый скрипт...

Для работы надо скопировать репризиторий, установить модуль vk_api

```
python3 -m pip install vk_api
```

создать в папке файл setting.ini следующего содержания:
```
[vk]
login = python@vk.com
password = vk_passvord
app_id = app_id 
client_secret = client_secret
country_id = 1
city_id = 1
group_id = 1

[settings]
city_name = Москва
hours_delta = 0
days_delta = 0
interesting_path = interesting.txt
not_interesting_path = not_interesting.txt
```

app_id получить можно [тут](https://dev.vk.com/) client_secret [там же](https://dev.vk.com/) инструкция [тут](https://help-ru.tilda.cc/vk-app-id)

country_id получить можно в [базе ВК](https://dev.vk.com/method/database.getCountries) city_id получить тоже в [базе](https://dev.vk.com/method/database.getCities) 1 и 1 это Россия и Москва соотвественно

group_id - это id группы в которую постить, важно **аккаунт которым вы используете должен иметь права постинга в данной группе**

city_name - название города

hours_delta - разница в часах, серверное время московское. Например Владивосток hours_delta = 7

days_delta - разница в днях, сегодня days_delta = 0, завтра days_delta = 1...

interesting_path - список белых ключей (интересных событий)

not_interesting_path - список черных ключей (неинтересных событий)


