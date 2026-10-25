select channel_key, channel, description
from {{ ref('channels') }}
