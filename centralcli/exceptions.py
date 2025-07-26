# Aruba Central API GW ISSUES
class ArubaCentralException(Exception):
    pass

class DevException(ArubaCentralException):
    pass

class TimeoutException(ArubaCentralException):
    pass

# CentralCLI Exceptions
class CentralCliException(Exception):
    pass

class MissingFieldException(CentralCliException):
    pass

class ImportException(CentralCliException):
    pass

class InvalidConfigException(CentralCliException):
    pass

class WorkSpaceNotFoundException(CentralCliException):
    pass


# SNOW
class ServiceNowException(Exception):
    pass

class RefreshFailedException(ServiceNowException):
    pass

class IncidentException(ServiceNowException):
    pass
