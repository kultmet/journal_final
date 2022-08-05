from datetime import datetime


def year(request):
    """Добавляет переменную с текущим годом."""
    date_year = datetime.now().year
    return {
        'year': date_year,
    }
