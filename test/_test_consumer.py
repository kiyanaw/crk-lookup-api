import base64

from handler import consumer

def _test_consumer():
  event = {
    'Records': [
      {
        'body': base64.b64encode(bytes('akohtêw:akohtê VIIw ;', 'utf-8'))
      }
    ]
  }
  consumer(event, {})

  # mock dynamodb call 

