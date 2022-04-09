### Required Libraries ###
from datetime import datetime
from dateutil.relativedelta import relativedelta
from botocore.vendored import requests
import boto3
import csv


### def function to import and read csv data ###
s3_client = boto3.client("s3")
S3_BUCKET = 'arbitrageadvisor'
object_key = "options.csv"
file_content = s3_client.get_object(
     Bucket=S3_BUCKET, Key=object_key)["Body"].read()
     
decoded_content = file_content.decode('utf-8')
reader = csv.reader(decoded_content.splitlines ())
rows = list(reader)
for row in rows:
    best = row[5:8]
   

### Functionality Helper Functions ###
def parse_int(n):
    """
    Securely converts a non-integer value to integer.
    """
    try:
        return int(n)
    except ValueError:
        return float("nan")
def build_validation_result(is_valid, violated_slot, message_content):
    """
    Define a result message structured as Lex response.
    """
    if message_content is None:
        return {"isValid": is_valid, "violatedSlot": violated_slot}
    return {
        "isValid": is_valid,
        "violatedSlot": violated_slot,
        "message": {"contentType": "PlainText", "content": message_content},
    }
def validate_data(birthday, meta_acct, avail_dex, intent_request):
    """
    Validates the data provided by the user.
    """
    # Validate that the user is over 18 years old
    if birthday is not None:
        birth_date = datetime.strptime(birthday, "%Y-%m-%d")
        age = relativedelta(datetime.now(), birth_date).years
        if age < 18:
            return build_validation_result(
                False,
                "birthday",
                "You should be at least 18 years old to use this service, "
                "please provide a different date of birth.",
            )
    
    # Validate Meta Mask account
    if meta_acct is not None:
        if meta_acct == 'No':
            return build_validation_result(
                False,
                "metaAccount",
                "You will need a Meta Mask account to use this service, please come back once you've created an account.",
            )
    # Validate the available DEX
    if avail_dex is not None:
        if avail_dex == 'No':
            return build_validation_result(
                False,
                "availableDex",
                "You will need to use the available DEX to use this service.",
            )
    # A True results is returned if age or amount are valid
    return build_validation_result(True, None, None)


### Dialog Actions Helper Functions ###
def get_slots(intent_request):
    """
    Fetch all the slots and their values from the current intent.
    """
    return intent_request["currentIntent"]["slots"]
def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    """
    Defines an elicit slot type response.
    """
    return {
        "sessionAttributes": session_attributes,
        "dialogAction": {
            "type": "ElicitSlot",
            "intentName": intent_name,
            "slots": slots,
            "slotToElicit": slot_to_elicit,
            "message": message,
        },
    }
def delegate(session_attributes, slots):
    """
    Defines a delegate slot type response.
    """
    return {
        "sessionAttributes": session_attributes,
        "dialogAction": {"type": "Delegate", "slots": slots},
    }
def close(session_attributes, fulfillment_state, message):
    """
    Defines a close slot type response.
    """
    response = {
        "sessionAttributes": session_attributes,
        "dialogAction": {
            "type": "Close",
            "fulfillmentState": fulfillment_state,
            "message": message,
        },
    }
    return response


### Intents Handlers ###
def arbitrage_token(intent_request):
    """
    Performs dialog management and fulfillment for recommending arbitrage.
    """
    # Gets slots' values
    first_name = get_slots(intent_request)["firstName"]
    last_name = get_slots(intent_request)["lastName"]
    birthday = get_slots(intent_request)["birthday"]
    meta_acct = get_slots(intent_request)["metaAccount"]
    avail_dex = get_slots(intent_request)["availableDex"]
    # Gets the invocation source, for Lex dialogs "DialogCodeHook" is expected.
    source = intent_request["invocationSource"]
    
    if source == "DialogCodeHook":
        # Perform basic validation on the supplied input slots.
        # Use the elicitSlot dialog action to re-prompt for the first violation detected.
        # Gets all the slots
        slots = get_slots(intent_request)
        # Validates user's input using the validate_data function
        validation_result = validate_data(birthday, meta_acct, avail_dex, intent_request)
        # If the data provided by the user is not valid
        if not validation_result["isValid"]:
            slots[validation_result["violatedSlot"]] = None
            
            return elicit_slot(
                intent_request["sessionAttributes"],
                intent_request["currentIntent"]["name"],
                slots,
                validation_result["violatedSlot"],
                validation_result["message"],
            )
        # Fetch current session attibutes
        output_session_attributes = intent_request["sessionAttributes"]
        # Once all slots are valid, a delegate dialog is returned to Lex to choose the next course of action.
        return delegate(output_session_attributes, get_slots(intent_request))
    # Return a message with the best arbitage conversion result
    return close(
        intent_request["sessionAttributes"],
        "Fulfilled",
        {
            "contentType": "PlainText",
            "content": """{} thank you for your information;
             The best 3 options to trade are {}
            """.format(
                first_name, best
            ),
        },
    )


### Intents Dispatcher ###
def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """
    intent_name = intent_request["currentIntent"]["name"]
    # Dispatch to bot's intent handlers
    if intent_name == "RecommendArbitrage":
        return arbitrage_token(intent_request)
    raise Exception("Intent with name " + intent_name + " not supported")


### Main Handler ###
def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """
    return dispatch(event)