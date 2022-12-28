
class ArubaCentralException(Exception):
    pass


class DevException(ArubaCentralException):
    pass

class TimeoutException(ArubaCentralException):
    pass