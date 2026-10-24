select kanal_key, kanal, beschreibung
from {{ ref('kanaele') }}
