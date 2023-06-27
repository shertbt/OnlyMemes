# *OnlyMemes*
### мемы по подписке
## Обзор
Сервис разделен на два:

- website
- imageserver

Первый сервис website, где пользователи могут создавать/просматривать текстовые посты или картинки по подписке. В приложении можно создать свой профиль, редактировать информацию о себе, с разным доступом (видно всем, подписчикам, только для себя). Каждый пост имеет собственную страницу, которую можно просматривать (если есть доступ) по id. В посте можно писать заголовок описание, имеется информация об авторе и дате создания. 

- Подписка на пользователя осуществяется с помощью ввода его токена доступа. Персональный токен выдается всем пользователям при регистрации и входе.

- Имеется возможность поиска пользователей по имени и сортировка результата по имени или дате регистрации.

Второй сервис imageserver - файловый сервер, в котором хранятся картинки, загружаемые в посты.

### Flag Store 1 - текстовые посты
Флаги хранятся в текстовом виде в постах в явном виде, либо в скрытом с помощью brainfuck

### Flag Store 2 - картинки в постах
Флаги в виде картинке, на котором написано сорержание флага

### Flag Store 3 - 'о себе' пользователя
Флаги в описании (about me) с доступом только для себя

## Уязвимости
1.  Генерация персонального токена зависит от имени пользователя
    - Можно легко вычислить токен пользователя, подписаться на него и увидеть его посты
2.  Blind SQL injection in ORDER BY для SQLAlchemy versions [,1.2.18) в поиске
    - Можно подобрать символы токена и узнать персональный токен пользователя
3. Вход с любым паролем
    - Bcrypt может хэшировать только 56 байт данных, любые следующие за ними отбрасываются. Если не изменить pepper на более короткий, пользователь сможет войти по первому символу пароля
4. SSFR атака на файловый сервер
    - Возможно получение картинки по id поста с помощью подделки запроса к файловому серверу
5. Отсутствие проверки аутентификации при просмотре постов по id
    - Возможность просмотра постов по id без проверки подписки на автора


#### + ***вывод всех пользователей по пустому запросу в поиск***
- Дает возможность более простого перебора пользователей при атаках

## Патчи
1. Изменение генерации токена на случаную строку
2. Изменение запроса к БД, без ввода, напр. через формы
3. Изменение библиотеки для хэширования паролей или удаление/сокращение значения pepper
4. Добавить аутентификацию на внутренний сервер с картинками (например,с помощью ключа) 
5. Проверка подписки перед показом поста по id

# Сборка
## Сервис
## Чекер
