from time import sleep


def try_or_retry_times(action, number_of_tries: int, retry_interval_seconds=60):
    for i in range(number_of_tries):
        try:
            action()
        except Exception as e:
            print('exception')
            print(str(e))
            if i < number_of_tries - 1:
                sleep(retry_interval_seconds)
                continue
            else:
                raise
        break
