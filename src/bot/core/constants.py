"""Application constants."""

import pytz

# Zaruba reliability threshold
# Users with cancel/unreg ratio above this are considered unreliable
BAD_THRESHOLD = 0.2

# Timezones
MOSCOW_TZ = pytz.timezone("Europe/Moscow")
UTC_TZ = pytz.timezone("UTC")
