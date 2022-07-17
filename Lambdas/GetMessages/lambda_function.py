import traceback
import boto3
from boto3.dynamodb.types import TypeDeserializer
import json
from datetime import date

def flatten_dynamoDB_item(ddb_item):
    type_deserializer = TypeDeserializer()
    return {k: type_deserializer.deserialize(v) for k, v in ddb_item.items()}

def error_response(error_message: str) -> str:
    return json.dumps({
        "error": error_message
    })

def success_response(messages: list) -> str:
    return json.dumps({
        "messages": messages
    })

def lambda_handler(event, context): 
    try:
        client = boto3.client('dynamodb')
        today = date.today()

        # Query table for today's scheduled messages 
        query_response = client.query(
            TableName='TextSchedulerMessages',
            KeyConditionExpression=f"created_by = :createdByVal AND begins_with ( id , :sortval )",
            ExpressionAttributeValues = {
                ":sortval": {
                    "S": str(today)
                },
                ":createdByVal": {
                    "S": "saahilc"
                }
            },
            ProjectionExpression="contact_first_name,contact_last_name,contact_phone_no,message"
        )
        response_items = query_response['Items']
        print(response_items)

        # Convert messages from dynamoDB JSON to normal JSON
        todays_messages = list(map(flatten_dynamoDB_item, response_items))
        print(todays_messages)
        return {
            "statusCode": 200,
            "body": success_response(todays_messages)
        }
    except Exception as e:
        print(e)
        print(traceback.format_exc())
        return {
            "statusCode": 500,
            "body": error_response("Internal server error")
        }
