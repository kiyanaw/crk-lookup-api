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

def analyze_strict(lookup):
  fst = get_transducer("/opt/crk-strict-analyzer.hfstol")
  return do_lookup(fst.bulk_lookup, lookup)

def analyze_relaxed(lookup):
  fst = get_transducer("/opt/crk-relaxed-analyzer.hfstol")
  return do_lookup(fst.bulk_lookup, lookup)

def generate_strict(lookup):
  fst = get_transducer("/opt/crk-strict-generator.hfstol")
  return do_lookup(fst.bulk_lookup, lookup)


# Do bulk lookup here
def bulk_lookup(event, context):
  status_code = 200
  result = {}
  if not event.get('body'):
    return {'statusCode': 400, 'body': json.dumps({'message': 'No body was found'})}

  # load main lookups
  try:
    body = json.loads(event['body'])
    logger.info(f'Body: {body}')
    # perform lookup
    result = analyze_strict(body)
    print(f'result {result}')
  except Exception as e:
    logger.exception('Error reading post body')
    result = {"error": str(e)}
    status_code = 500

  # load suggestions
  try:
    unknowns = [s for s in result if len(result[s]) == 0]
    fst = get_transducer("/opt/crk-strict-generator.hfstol")
    result['_suggestions'] = check_unknowns(unknowns)
  except Exception as e:
    print(e)
    pass

  logger.info(f'final {result}')
  return {'statusCode': status_code, 'body': json.dumps(result, cls=SetEncoder)}

# abstraction for spelling suggestions
def check_unknowns(items):
  final = {}
  result = analyze_relaxed(items)
  logger.info(f'result: {result}')
  # {'owāhkomākan': {'PV/o+wâhkômêw+V+TA+Imp+Del+2Sg+3SgO+Err/Orth'}, 'ekwa': {'êkwa+Ipc'}}

  # build a set of {analysis: original} from {original: {analysis}}
  original_lookup = {result[k].pop(): k for k in result}
  logger.info(f'original {original_lookup}')
  # {'PV/o+wâhkômêw+V+TA+Imp+Del+2Sg+3SgO+Err/Orth': 'owāhkomākan', 'êkwa+Ipc': 'ekwa'}

  to_lookup = original_lookup.keys()
  if to_lookup and len(to_lookup):
    suggested = generate_strict(to_lookup)
    logger.info(f'suggested {suggested}')
    # {'PV/o+wâhkômêw+V+TA+Imp+Del+2Sg+3SgO+Err/Orth': {'ôwâhkômâhkan'}, 'êkwa+Ipc': {'êkwa'}}
    # match the results
    for key in suggested.keys():
      final[original_lookup[key]] = suggested[key].pop()

  return final

def suggest(event, context):
  status_code = 200
  final = {}
  if not event.get('body'):
    return {'statusCode': 400, 'body': json.dumps({'message': 'No body was found'})}
  try:
    body = json.loads(event['body'])
    logger.info(f'Body: {body}')
    final = check_unknowns(body)
  except Exception as e:
    logger.exception('Error reading post body', e)
    message = str(e)
    status_code = 500
  logger.info(f'final {final}')
  return {'statusCode': status_code, 'body': json.dumps(final, cls=SetEncoder)}


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


