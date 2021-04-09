bio_hash = None

def set_bio_hash(hash_data) -> None:
    """
    在本地保存生物hash信息。
    TODO: 还不知道过来数据的格式是啥，怎么解码需要修改一下
    """
    bio_hash = hash_data

def clear_local_data() -> None:
    """
    清楚本地的生物hash信息。
    """
    bio_hash = None

def send_log_data() -> str:
    """
    读取本地缓存的认证日志文件，发送到服务器端。
    TODO: 完成这一部分。
    """
    return '{check_status:"OK", user_info: {user_id: 11451419198, state: 0.98}}'

def check_hash() -> None:
    """
    检查生物hash信息，并缓存
    """
    return