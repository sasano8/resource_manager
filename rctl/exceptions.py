class RctlError(Exception): ...


# Base Exception
class ExistsError(RctlError): ...


class AbsentError(RctlError): ...


#
class NoRecordError(AbsentError): ...
