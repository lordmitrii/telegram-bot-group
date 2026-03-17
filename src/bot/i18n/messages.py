"""Localized messages for the bot."""

MESSAGES = {
    "start": "Пем бравл старс невероятно крутые. /help для просмотра команд.",
    "help": """
🤖 *Доступные команды:*

📌 *Основные команды:*
/start - Начать работу с ботом
/help - Показать список команд
/list - Показать список зарегистрированных бойцов

🔥 *Команды Зарубы:*
/zaruba <время> - Создать новую зарубу
/reg <время (необязательно)> - Зарегистрироваться на зарубу
/unreg - Слиться с зарубы
/cancel - Отменить текущую зарубу
/botinok <@пользователь> - Снять ауру нубику
/stats <@пользователь> - Показать статистику по зарубам

⚽ *Футбольные Команды:*
/subscribe - Подписаться на дневные уведомления
/unsubscribe - Отписаться от дневных уведомлений


⚠ *Дополнительно:*
Неизвестные команды будут проигнорированы.
    """,
    "unknown": "❌ Неизвестная команда. Попробуйте /zaruba, /reg, /list, /cancel, /unreg или /botinok.",

    "zaruba_no_username": "❌ Не удалось определить ваше имя пользователя.",
    "zaruba_no_time": "❌ Укажите время зарубы. Пример: /zaruba 18:00",
    "no_zaruba": "❌ Нет активной зарубы. Сначала создайте её командой /zaruba <время>.",
    "zaruba_created": "🏆 Заруба назначена на {time}. Запишитесь с помощью /reg",
    "zaruba_button_reg": "✅ Рег",
    "zaruba_button_unreg": "🚫 Анрег",
    "zaruba_button_cancel": "🛑 Отмена",
    "cancel_success": "🚫 Заруба отменена.",
    "reg_already_registered": "❌ @{user}, вы уже зарегистрированы на зарубу.",
    "unreg_creator_forbidden": "❌ @{user}, создатель зарубы не может сняться, только отменить ее.",

    "list_reg_yes": "✅ @{user} - на {time}\n",
    "list_reg_no": "❌ @{user} не зарегистрирован\n",

    "list_stats": "📜 *Статистика о @{user}:*\n\n✨ Аура: {aura}\n✅ Заруб начал: {initiated}\n✅ Регистраций на зурубы: {regnuto}\n❌ Заруб отменил: {canceled}\n❌ Слился с заруб: {unregnuto}",
    "stats_good": "*Вердикт*: ✅ респектабельный\n*Шанс подвести друзей*: {chance}%",
    "stats_bad": "*Вердикт*: ❌ вафлежуй\n*Шанс подвести друзей*: {chance}%",
    "stats_good_label": "✅ респектабельный",
    "stats_bad_label": "❌ вафлежуй",
    "stats_aura_negative": "*Вердикт*: негативная аура",
    "stats_aura_positive": "*Вердикт*: позитивная аура",
    "stats_aura_incredible": "*Вердикт*: Невероятная аура",
    "stats_aura_negative_label": "негативная аура",
    "stats_aura_positive_label": "позитивная аура",
    "stats_aura_incredible_label": "Невероятная аура",
    "stats_verdict_combined": "*Вердикт*: {reliability}, {aura}\n*Шанс подвести друзей*: {chance}%",
    "stats_not_found": "Нет статистики о пользователе @{user}",
    "stats_user_invalid": "Пользователь указан неправильно. Используйте формат /stats <@пользователь>",

    "reg_success": "✅ @{user}, вы зарегистрированы на {time}!",
    "unreg_success": "🚫 @{user}, вы отменили регистрацию на зарубу.",
    "unreg_not_found": "❌ @{user}, вы не были зарегистрированы.",
    "zaruba_action_only_creator_cancel": "❌ Отменить зарубу может только тот, кто ее создал.",
    "zaruba_action_only_registered_unreg": "❌ Сняться может только уже зарегистрированный игрок.",
    "zaruba_action_only_unregistered_reg": "❌ Вы уже зарегистрированы на эту зарубу.",
    "botinok_no_target": "❌ Укажите пользователя. Пример: /botinok @nickname",
    "botinok_self": "❌ Самому себе ауру снимать нельзя.",
    "botinok_already_voted": "❌ @{user}, вы уже голосовали против @{target}.",
    "botinok_vote": "👞 Голос против @{target} засчитан. Сейчас голосов: {votes}/2.",
    "botinok_fined": "💸 @{target} получает штраф: -1000 к ауре.",
    "botinok_button": "🔨 Добить @{target}",

    "list_members_error": "❌ Не удалось получить список участников группы.",
    "list_no_zaruba": "🚫 Заруба пока не намечается.",
    "list_registered": "📜 *Список участников:*",

    "unsubscribe": "❌ Дневные уведомления отключены.",
    "subscribe": "✅ Дневные уведомления подключены: футбол + праздник дня.",

    "football_game": "⚽ *{home} vs {away}* ({league})\n⏰ *{match_time}*\n\n",
    "todays_football": "🔥 *Сегодняшний футбольчик:*\n\n",
    "football_zaruba_cta": (
        "📺 Собираемся на футбол, братва! Регистрация на зарубу — /reg"
    ),
    "football_time": "футбольное время 🕒",
    "todays_holiday": "🎉 <b>С праздником, братва!</b>\n\nСегодня: {title}\n\n{description}",
    "holiday_fallback_description": "Сегодня отличный повод немного отметить.",

    "beer_check_button": "Ты в пиве?",
    "beer_check_yes": "Да",
    "beer_check_no": "Да пашел ты",
}
