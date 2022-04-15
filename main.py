from application import start
from retry import try_or_retry_times

try_or_retry_times(start, 3)

