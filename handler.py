import base64
import json
import logging
import os
import sys
import boto3

import glob
print(glob.glob("/opt/*")) 

sys.path.insert(0, '/opt/')
from hfst_optimized_lookup import TransducerFile

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

QUEUE_URL = os.getenv('QUEUE_URL')

class SetEncoder(json.JSONEncoder):
  def default(self, obj):
    if isinstance(obj, set):
      return list(obj)
    return json.JSONEncoder.default(self, obj)

# for testing
def get_transducer(string_path):
  return TransducerFile(string_path)

def do_lookup(haystack, needle):
  return haystack(needle)

# Do bulk lookup here
def bulk_lookup(event, context):
  status_code = 200
  message = {}
  if not event.get('body'):
    return {'statusCode': 400, 'body': json.dumps({'message': 'No body was found'})}
  try:
    body = json.loads(event['body'])
    logger.info(f'Body: {body}')
    # perform lookup
    fst = get_transducer("/opt/crk-strict-analyzer.hfstol")
    result = do_lookup(fst.bulk_lookup, body)
  except Exception as e:
    logger.exception('Error reading post body')
    message = str(e)
    status_code = 500
  print(result)
  return {'statusCode': status_code, 'body': json.dumps(result, cls=SetEncoder)}

def suggest(event, context):
  status_code = 200
  message = {}
  if not event.get('body'):
    return {'statusCode': 400, 'body': json.dumps({'message': 'No body was found'})}
  try:
    body = json.loads(event['body'])
    logger.info(f'Body: {body}')
    # perform lookup
    fst = get_transducer("/opt/crk-relaxed-analyzer.hfstol")
    result = do_lookup(fst.bulk_lookup, body)

    result = result.get(body[0])
    if result and len(result):
      fst = get_transducer("/opt/crk-strict-generator.hfstol")
      result = do_lookup(fst.bulk_lookup, result)

  except Exception as e:
    logger.exception('Error reading post body')
    message = str(e)
    status_code = 500
  print(result)
  return {'statusCode': status_code, 'body': json.dumps(result, cls=SetEncoder)}


## Queue/DB stuff below here

def producer(event, context):
  SQS = boto3.client('sqs')
  status_code = 200
  message = ''

  if not event.get('body'):
    return {'statusCode': 400, 'body': json.dumps({'message': 'No body was found'})}

  try:
    message_attrs = {
      'AttributeName': {'StringValue': 'AttributeValue', 'DataType': 'String'}
    }
    SQS.send_message(
      QueueUrl=QUEUE_URL,
      MessageBody=event['body'],
      MessageAttributes=message_attrs,
    )
    message = 'Message accepted!'
  except Exception as e:
    logger.exception('Sending message to SQS queue failed!')
    message = str(e)
    status_code = 500

  return {'statusCode': status_code, 'body': json.dumps({'message': message})}


# acitamow:acitamo VAIio ;
# encoded: YWNpdGFtb3c6YWNpdGFtbyBWQUlpbyA7

    # const tParams = {
    #   TableName: tTable,
    #   Key: {
    #     'id': transcriptionId
    #   }
    # }

def consumer(event, context):
  dynamodb = boto3.resource('dynamodb')
  table = dynamodb.Table('users')
  for record in event['Records']:
    body = base64.b64decode(record.get('body')).decode("utf-8")
    logger.info(f'Body {body}')


