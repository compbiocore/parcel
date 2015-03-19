###############################################################################
#                              Constants
###############################################################################

GB = 1024 * 1024 * 1024
MB = 1024 * 1024


# ======== Lengths ========
LEN_CONTROL = 10
LEN_TOKEN = 60
LEN_PAYLOAD_SIZE = 100
RES_CHUNK_SIZE = 128 * MB
HTTP_CHUNK_SIZE = 1 * MB

# ======== CONTROL TYPES ========
CNTL_HANDSHAKE = chr(1)
CNTL_DOWNLOAD = chr(2)
CNTL_EXIT = chr(255)


# ======== States ========
STATE_IDLE = 'STATE_IDLE'
