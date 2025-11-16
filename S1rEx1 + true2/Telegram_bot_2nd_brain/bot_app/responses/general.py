"""General-purpose response helpers."""


def cancel_message() -> str:
    return "❌ Операция отменена."


def error_message() -> str:
    return (
        "❌ Произошла ошибка при обработке вашего запроса. "
        "Пожалуйста, попробуйте еще раз или напишите /start для перезапуска."
    )
