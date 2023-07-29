
class ArubaCentralException(Exception):
    pass


class DevException(ArubaCentralException):
    pass

class TimeoutException(ArubaCentralException):
    pass

class ServiceNowException(Exception):
    pass

class RefreshFailedException(ServiceNowException):
    pass

class IncidentException(ServiceNowException):
    pass