def format_time(seconds) -> str:
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return f"{hours:02d}:{minutes:02d}"


def convert_to_seconds(time: str):
    return (
        int(time.split(":")[0]) * 3600 +
        int(time.split(":")[1]) * 60
    )
