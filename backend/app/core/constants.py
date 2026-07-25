from enum import Enum


class AuditAction(str, Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


class AuditEntity(str, Enum):
    CUSTOMER = "CUSTOMER"
    CONTACT = "CONTACT"
    PROJECT = "PROJECT"
    TASK = "TASK"
    USER = "USER"


DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
