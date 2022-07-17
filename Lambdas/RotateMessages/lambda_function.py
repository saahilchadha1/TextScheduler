import json
import traceback
from datetime import date, datetime, timedelta, timezone
from uuid import uuid4
from utils import read_secrets

import boto3
import requests
from boto3.dynamodb.types import TypeDeserializer, TypeSerializer
from dateutil.relativedelta import relativedelta

TABLE_NAME = 'TextSchedulerMessages'
SLACK_HOOK = read_secrets()['SLACK_HOOK']

def dynamo_obj_to_python_obj(dynamo_obj: dict) -> dict:
    deserializer = TypeDeserializer()
    return {
        k: deserializer.deserialize(v) 
        for k, v in dynamo_obj.items()
    }  
  
def python_obj_to_dynamo_obj(python_obj: dict) -> dict:
    serializer = TypeSerializer()
    return {
        k: serializer.serialize(v)
        for k, v in python_obj.items()
    }

def query_messages_before_date(ddb_client, before_date: str):
    return ddb_client.query(
        TableName=TABLE_NAME,
        KeyConditionExpression=f"created_by = :createdByVal AND id < :sortval",
        ExpressionAttributeValues = {
            ":sortval": {
                "S": before_date
            },
            ":createdByVal": {
                "S": "saahilc"
            }
        }
    )['Items']

def write_new_items(ddb_client, new_items):
    ddb_client.batch_write_item(
        RequestItems={
            TABLE_NAME: [{"PutRequest": {"Item": new_item}} for new_item in new_items]
        }
    )

def delete_old_items(ddb_client, old_items):
    ddb_client.batch_write_item(
        RequestItems={
            TABLE_NAME: [{"DeleteRequest": {
                "Key": {
                    'created_by': old_item['created_by'],
                    'id': old_item['id']
                }
            }} for old_item in old_items]
        }
    )

def find_next_scheduled_date(prev_scheduled_date:str, rate_expression:str) -> str:
    prev_scheduled_date = date.fromisoformat(prev_scheduled_date)
    tokens = rate_expression.split(' ')
    value = int(tokens[0])
    unit = tokens[1]
    if value <= 0:
        return None
    elif unit in ['day', 'days']:
        return str(prev_scheduled_date + timedelta(days=value))
    elif unit in ['week', 'weeks']:
        return str(prev_scheduled_date + timedelta(days=value * 7))
    elif unit in ['year', 'years']: 
        return str(prev_scheduled_date + relativedelta(years=value))
    else:
        return None

def get_new_dynamo_db_items(old_items): 
    new_items = []
    serializer = TypeSerializer()
    for old_item in old_items:
        next_scheduled_date = find_next_scheduled_date(
            prev_scheduled_date=old_item['scheduled_for']['S'],
            rate_expression=old_item['rate_expression']['S']
        )
        if next_scheduled_date: 
            new_item = old_item.copy()
            new_item['scheduled_for'] = serializer.serialize(next_scheduled_date)
            new_item['id'] = serializer.serialize(f"{next_scheduled_date}#{uuid4()}")
            new_item['created_at'] = serializer.serialize(str(datetime.now(timezone.utc)))
            
            new_items.append(new_item)
    return new_items



def lambda_handler(event, context): 
    try:
        client = boto3.client('dynamodb')
        today = date.today()

        # Query table for all messages scheduled before today 
        old_items = query_messages_before_date(client, str(today))
        print(f"Old Items: {old_items}")

        # Only update table if there are old messages
        if len(old_items) > 0:
            # Iterate through messages and create new ones based on the rate_expression
            new_items = get_new_dynamo_db_items(old_items)
            print(f"New Items: {new_items}")

            # Add new messages to the table
            write_new_items(client, new_items)

            # Delete all the old messages
            delete_old_items(client, old_items)
        
        date_in_three_days = today + timedelta(days=3)
        upcoming_messages = query_messages_before_date(client, str(date_in_three_days))
        print(f"Upcoming Messages: {upcoming_messages}")
        if len(upcoming_messages) > 0:
            deserialized_upcoming_messages = list(map(dynamo_obj_to_python_obj, upcoming_messages))
            upcoming_messages_formatted = [
                f"- {msg['scheduled_for']}: {msg['contact_first_name']} {msg['contact_last_name']} - {msg['message']}\n" for msg in deserialized_upcoming_messages
            ]
            requests.post(
                url=SLACK_HOOK,
                json={
                    'text': f"TextScheduler Upcoming Messages:\n{''.join(upcoming_messages_formatted)}"
                }
            )
        

    except Exception as e:
        print(e)
        print(traceback.format_exc())
        requests.post(
            url=SLACK_HOOK,
            json={
                'text': f"TextScheduler Error: {e}"
            }
        )