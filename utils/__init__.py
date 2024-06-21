import uuid


def create_uuid():
    """
    自动生成36位uuid
    :param name:
    :return:
    """
    return str(uuid.uuid1())
