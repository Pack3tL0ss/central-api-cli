
class ArubaCentralException(Exception):
    pass

class CentralCliException(Exception):
    pass

class MissingFieldException(CentralCliException):
    pass

class ImportException(CentralCliException):
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
