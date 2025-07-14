from datetime import datetime, timezone, timedelta
import pytz

KENYA_TZ = timezone(timedelta(hours=3))
# KENYA_TZ = pytz.timezone('Africa/Nairobi')
DEADLINE = datetime(2025, 7, 14, 21, 1, 59, tzinfo=KENYA_TZ)

def check_deadline():
    """Check if current time is past the deadline"""
    current_time = datetime.now(KENYA_TZ)
    # return current_time, DEADLINE
    return current_time > DEADLINE

print(check_deadline())