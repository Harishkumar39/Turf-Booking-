import random
import json

import torch
import re

import datetime
import pymongo

from dateutil import parser
from model import NeuralNet
from geopy.distance import great_circle
from nltk_utils import bag_of_words, tokenize
from mailing import confirmation_mail

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

with open('intents.json', 'r') as json_data:
    intents = json.load(json_data)

FILE = "data.pth"
data = torch.load(FILE)

input_size = data["input_size"]
hidden_size = data["hidden_size"]
output_size = data["output_size"]
all_words = data['all_words']
tags = data['tags']
model_state = data["model_state"]

model = NeuralNet(input_size, hidden_size, output_size).to(device)
model.load_state_dict(model_state)
model.eval()

bot_name = "Sam"

booking_requested = False

def replace_placeholders(response, placeholders):
    for placeholder, value in placeholders.items():
        response = response.replace(f'{{{placeholder}}}', str(value))
    return response

# Connect to the MongoDB server
client = pymongo.MongoClient("mongodb://localhost:27017/")
# Access the database
db = client["admin"]
#Access a specific collection (similar to a table in SQL)
collection = db["register"]


# print(e_data)
# Find documents in the collection
# documents = collection.find({"email":"hibye@gmail.com"})
# print(documents)
turf_name = None
parsed_date = None
extracted_day = None
extracted_time = None

# Load turf data from JSON
with open('C:/java_prog/xlsheet/data.json', 'r', encoding='utf-8') as json_file:
    turf_data = json.load(json_file)

with open('latlong.json','r') as file:
    data = json.load(file)

lati = data.get('lat')
longi = data.get('long')
# Function to find nearby turfs
def find_nearby_turfs(current_lat=lati, current_long=longi):
    nearby_turfs = []

    # Coordinates of the current location
    current_location = (current_lat, current_long)

    # Loop through each turf in the data
    for turf in turf_data:
        # Get the Google Maps link
        direction_link = turf['Direction']

        # Extract latitude and longitude from the Google Maps link
        # This assumes the link structure is consistent across all turfs
        lat_start = direction_link.index('!3d') + 3
        lat_end = direction_link.index('!4d')
        lng_start = direction_link.index('!4d') + 3
        lng_end = direction_link.index('!16s')

        turf_lat = float(direction_link[lat_start:lat_end])
        turf_long = float(direction_link[lng_start:lng_end])

        turf_location = (turf_lat, turf_long)

        # Calculate distance between current location and turf
        distance = great_circle(current_location, turf_location).km

        # If distance is within 5 km, consider it as nearby
        if distance <= 5:
            nearby_turfs.append(turf)

    return nearby_turfs

def get_response(msg, current_lat=None, current_long=None):
    global booking_requested, turf_name, extracted_day, extracted_time, parsed_date
    sentence = tokenize(msg)
    X = bag_of_words(sentence, all_words)
    X = X.reshape(1, X.shape[0])
    X = torch.from_numpy(X).to(device)

    output = model(X)
    _, predicted = torch.max(output, dim=1)

    tag = tags[predicted.item()]
    probs = torch.softmax(output, dim=1)
    prob = probs[0][predicted.item()]
    print(tag)
    if prob.item() > 0.40:

        if tag == "book_turf":
            booking_requested = True

        if tag == "confirm_booking":
            if booking_requested:
                #implement the code to send the confirmation mail
                with open('emailDetails.json', 'r') as email_data:
                    e_data = json.load(email_data)
                documents = collection.find({"email":e_data['email']})
                direction = next((turf['Direction'] for turf in turf_data if turf_name.lower() in turf['Name'].lower()), None)
                for doc in documents:
                    mail_id = doc['email']
                    name = doc['fname']
                    subject = "Turf confirmation mail"
                    message = f"Greeting from G_TURF!!!\nHi {name},\nThis is to indicate that you have confirmed your booking for the {turf_name} turf on\nDATE : {parsed_date.date()}  \nTIME : {extracted_time}\nFollow the link to reach the turf : {direction}\nDon't miss to spend your time at {turf_name} turf and be there on time!!"
                    confirmation_mail(mail_id, subject, message)

                return "You have successfully booked the turf. We have sent you a confirmation email. Please check your inbox"
            else:
                return "please make a booking request first."

                # Check if the intent is to get best-rated turf suggestions
        if tag == "best_suggestions":
            suggestions = get_best_rated_turfs(num_suggestions=5)
            response = "Here are some highly-rated turfs:\n"
            response += "\n".join(suggestions)
            return response

        for intent in intents['intents']:

            if tag == intent["tag"]:
                response = random.choice(intent['responses'])
                placeholders={}
                try:

                    if "{date}" in response:
                        parsed_date = parser.parse(msg, dayfirst=True, fuzzy=True)
                        today = datetime.date.today()
                        if parsed_date.date() < today:
                            return "Sorry, you cannot book a turf for a past date."
                        placeholders['date'] = parsed_date.strftime('%d/%m/%Y')


                    if "{day}" in response:

                        extracted_day = extract_day_from_input(msg)
                        if extracted_day:
                            placeholders['day'] = extracted_day
                        else:
                            # Handle extraction failure, if needed
                            pass

                    if "{time}" in response:
                        extracted_time = extract_duration_from_input(msg)
                        # placeholders['time'] = extracted_time

                        if extracted_time:
                            if parsed_date and extracted_time:
                                booking_datetime = datetime.datetime.combine(parsed_date.date(),parser.parse(extracted_time).time())
                                current_datetime = datetime.datetime.now()
                                if booking_datetime>current_datetime:
                                    # print("invalid")
                                    opening_status = get_opening_status(turf_name)
                                    closing_status = get_closing_status(turf_name)
                                    print(opening_status,closing_status)
                                    if opening_status.lower() == "open 24 hours":
                                        # Turf is open 24 hours, so no time restrictions apply
                                        pass
                                    else:
                                        opening_status = datetime.datetime.combine(parsed_date.date(),parser.parse(opening_status).time())
                                        if closing_status=="12am":
                                            parsed_date += datetime.timedelta(days=1)
                                            closing_status = datetime.datetime.combine(parsed_date.date(), parser.parse(closing_status).time())
                                        else:
                                            closing_status = datetime.datetime.combine(parsed_date.date(),parser.parse(closing_status).time())
                                        if opening_status < booking_datetime < closing_status:
                                            pass
                                        else:
                                            return "Please provide a valid date or time!!!"
                                else:
                                    return "Invalid booking date or time!!"

                            placeholders['time'] = extracted_time
                        else:
                            # Handle extraction failure, if needed
                            pass

                    if "{duration}" in response:
                        extracted_duration = extract_dura_from_input(msg)
                        if extracted_duration:
                            placeholders['duration'] = extracted_duration
                        else:
                            # Handle extraction failure, if needed
                            pass

                    if "{price}" in response:

                        # else:
                        extracted_price = extract_price_from_input(msg)
                        if extracted_price=="request":
                            return "please make a booking request first..."
                        print(extracted_duration.split(" "))
                        dur = int(extracted_duration[0])
                        extracted_price=int(extracted_price)*dur
                        if extracted_price:
                            placeholders['price'] = extracted_price
                        else:
                            # Handle extraction failure, if needed
                            pass

                    if "{equipment}" in response:

                        extracted_equipment = extract_equipment_from_input(msg)
                        if extracted_equipment:
                            placeholders['equipment'] = extracted_equipment
                        else:
                            # Handle extraction failure, if needed
                            pass

                    if "{location}" in response:

                        # maps_link = turf_data['Direction']
                        current_lat, current_long=lati,longi
                        lat, long = current_lat, current_long

                        if current_lat is not None and current_long is not None:
                            nearby_turfs = find_nearby_turfs(float(lat), float(long))

                            if nearby_turfs:
                                nearby_turf_names = [turf['Name'] for turf in nearby_turfs]
                                placeholders['location'] = ", ".join(nearby_turf_names)
                            else:
                                placeholders['location'] = "No nearby turfs found."



                    if "{turf_name}" in response:

                        turf_name = extract_turf_name_from_input(msg)
                        if turf_name:
                            placeholders['turf_name'] = turf_name
                        else:
                            # Handle extraction failure, if needed
                            pass

                    if "{address}" in response:
                        print(turf_name)
                        turf_address = find_turf_location(turf_name)
                        placeholders['address']=turf_address
                    # Add more placeholder handling as needed

                    return replace_placeholders(response, placeholders)
                except ValueError:
                    # If date parsing fails, return the response with the placeholder
                    return replace_placeholders(response, {'date': 'Unknown'})
                # return replace_placeholders(response, {'date': '25/10/2023'})



    return "I do not understand..."

# turf opening and closing time
def get_opening_status(turf_name):
    open_status = next((turf['Status_Open'] for turf in turf_data if turf_name.lower() in turf['Name'].lower()), None)
    return extract_duration_from_input(open_status)

def get_closing_status(turf_name):
    close_status = next((turf['Status_Close'] for turf in turf_data if turf_name.lower() in turf['Name'].lower()), None)
    return extract_duration_from_input(close_status)



def get_best_rated_turfs(num_suggestions=5):

    sorted_turfs = sorted(find_nearby_turfs(lati, longi), key=lambda x: x.get('Rating', 0), reverse=True)

    # Take the top 'num_suggestions' turfs
    top_turfs = sorted_turfs[:num_suggestions]

    suggestions = []
    for turf in top_turfs:
        name = turf.get('Name', 'Unknown Name')
        rating = turf.get('Rating', 'No Rating')
        suggestions.append(f"{name} (Rating: {rating})")

    return suggestions


def find_turf_location(turf_name):
    selected_turf = next((turf for turf in turf_data if turf_name.lower() in turf['Name'].lower()), None)

    if selected_turf:
        address = selected_turf.get("Address", "Address not available")
        return address
    else:
        return f"No turf found with the name '{turf_name}'"

# Example function for extracting time
def extract_time_from_input(input_text):
    try:
        match = re.search(r'\b\d{1,2}:\d{2}\b', input_text)

        if match:
            return match.group()

    except ValueError:
        pass

    return None

# Add the function to extract turf name from input
def extract_turf_name_from_input(input_text):
    # Implement a function to extract the turf name from the input text.
    match = re.search(r'book the (.+?) turf', input_text, re.IGNORECASE)
    if match:
        return match.group(1)
    return None

# Example function for extracting day
def extract_day_from_input(input_text):
    days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    for day in days_of_week:
        if day.lower() in input_text.lower():
            return day

    return None

# Example function for extracting duration
def extract_dura_from_input(input_text):
    try:
        words = input_text.split()
        for i, word in enumerate(words):
            if word.isdigit():
                if i + 1 < len(words) and words[i + 1].lower() in ['hour', 'hours', 'minute', 'minutes']:
                    return f"{word} {words[i + 1]}"
        return None
    except ValueError:
        return None

def extract_duration_from_input(input_text):
    try:
        # match = re.search(r'\b\d{1,2}(?::\d{2})?\s*(am|pm)\b', input_text)
        #
        # if match:
        #     return match.group()
        if "24 hours" in input_text.lower():
            return "Open 24 hours"

            # Use regex to extract time
        match = re.search(r'(\d{1,2}(?:am|pm))', input_text, re.IGNORECASE)
        if match:
            return match.group(1)

    except ValueError:
        pass

    return None


# Example function for extracting price
def extract_price_from_input(input_text):
    try:
        if turf_name is not None:
            price = next((turf['Price_per_hour'] for turf in turf_data if turf_name.lower() in turf['Name'].lower()), None)
            return price
        else:
            return "request"
    except ValueError:
        return None


# Example function for extracting equipment
def extract_equipment_from_input(input_text):
    equipment_list = ["footballs", "cones", "goalposts", "nets","cricket bats", "cricket balls", ""]

    for equipment in equipment_list:
        if equipment.lower() in input_text.lower():
            return equipment

    return None



if __name__ == "__main__":
    print("Let's chat! (type 'quit' to exit)")
    while True:
        # sentence = "do you use credit cards?"
        sentence = input("You: ")
        if sentence == "quit":
            break

        resp = get_response(sentence)

        print(resp)

