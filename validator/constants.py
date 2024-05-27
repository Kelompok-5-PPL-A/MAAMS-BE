class ErrorMsg:
    NOT_FOUND = "Analisis tidak ditemukan"
    CAUSE_NOT_FOUND = "Sebab tidak ditemukan"
    FORBIDDEN_GET = "Pengguna tidak diizinkan untuk melihat analisis ini."
    FORBIDDEN_UPDATE = "Pengguna tidak diizinkan untuk mengubah analisis ini."
    FORBIDDEN_DELETE = "Pengguna tidak diizinkan untuk menghapus analisis ini."
    INVALID_TIME_RANGE = 'Invalid time range format.'
    EMPTY_TAG = "Berikan minimal 1 kategori."
    TOO_MANY_TAG = 'Kategori terlalu banyak. Berikan maksimal 3.'
    TAG_NAME_TOO_LONG = 'Kategori maksimal 10 karakter.'
    TAG_MUST_BE_UNIQUE = 'Kategori harus unik.'
    VALUE_NOT_UPDATED = "Tidak boleh sama dengan yang sebelumnya"
    INVALID_FILTERS = 'Invalid filter option.'
    AI_SERVICE_ERROR = "Failed to call the AI service."
    
class FeedbackMsg:
    # Root Cause Messages
    ROOT_FOUND = "Akar masalah kolom {column} ditemukan"

    # False Messages
    FALSE_ROW_1_NOT_CAUSE = "Sebab {column}1 bukan merupakan sebab dari pertanyaan"
    FALSE_ROW_N_NOT_CAUSE = "Sebab {column}{row} bukan merupakan sebab dari {column}{prev_row}"
    FALSE_ROW_N_POSITIVE_NEUTRAL = "Sebab {column}{row} merupakan sebab positif atau netral"
    FALSE_ROW_N_SIMILAR_PREVIOUS = "Sebab {column}{row} mirip dengan sebab sebelumnya"