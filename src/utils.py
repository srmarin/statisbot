from datetime import timedelta, datetime
import os

from constants import PROFILE_IMG_DIR


def get_current_week(date):
    # Asegurarse de que la fecha dada sea un objeto datetime
    if isinstance(date, datetime):
        given_date = date
    else:
        given_date = datetime.strptime(date, "%Y-%m-%d")

    # Obtener el lunes de la semana actual
    start_of_week = given_date - timedelta(days=given_date.weekday())
    # Obtener el domingo de la semana actual
    end_of_week = start_of_week + timedelta(days=6)

    return start_of_week, end_of_week


def check_saved_user_profile(user_id):
    return os.path.isfile(f"{PROFILE_IMG_DIR}{user_id}.jpg")
