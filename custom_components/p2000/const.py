DOMAIN = "p2000"

DEFAULT_NAME = "p2000"
DEFAULT_ICON = "mdi:ambulance"
DEFAULT_SCAN_INTERVAL = 30
MIN_SCAN_INTERVAL = 10
MAX_SCAN_INTERVAL = 3600

# Event entity: one event per new message; a follow-up message belongs to an
# earlier melding of the same incident.
EVENT_MELDING = "melding"
EVENT_VERVOLGMELDING = "vervolgmelding"
# Safety limits so an outage or a filter change cannot cause a flood of events.
MAX_EVENTS_PER_UPDATE = 10
SEEN_IDS_LIMIT = 500

CONF_ICON = "icon"
CONF_GEMEENTEN = "gemeenten"
CONF_CAPCODES = "capcodes"
CONF_REGIOS = "regios"
CONF_DISCIPLINES = "disciplines"
CONF_PRIO1 = "prio1"
