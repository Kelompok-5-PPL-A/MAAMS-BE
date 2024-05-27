from enum import Enum


class QuestionType(Enum):
    PENGAWASAN = 'PENGAWASAN'
    PRIBADI = 'PRIBADI'


class HistoryType(Enum):
    LAST_WEEK = 'last_week'
    OLDER = 'older'


class FilterType(Enum):
    SEMUA = 'semua'
    TOPIK = 'topik'
    JUDUL = 'judul'
    PENGGUNA = 'pengguna'

class ValidationType(Enum):
    NORMAL = 'normal'
    ROOT = 'root'
    FALSE = 'false'