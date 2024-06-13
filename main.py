# Import libraries
import asyncio
import requests
import os
from dotenv import load_dotenv
from telegram import Bot, InputMediaPhoto
import telegram
from DBUtil import add_listings, create_transaction, delete_stale_listings, get_listing_by_geo_id, get_listing_param, get_listing_to_send, get_subscriptions
import pickle 


# Load .env file
load_dotenv()

# use the variable names as defined in .env file
listing_api_url = os.getenv("LISTING_API_URL")
api_key = os.getenv("ZOOPLA_RAPIDAPI_KEY")  
api_host = os.getenv("ZOOPLA_RAPIDAPI_HOST")
bot_token = os.getenv("BOT_TOKEN")

#Generate an instance of the bot to send media
bot:Bot = telegram.Bot(token = bot_token)

headers = {
	"X-RapidAPI-Key": api_key,
	"X-RapidAPI-Host": api_host
}

def save_for_testing(dict):
    with open('saved_dictionary.pkl', 'wb') as f:
        pickle.dump(dict, f)

def get_for_testing():     
    with open('saved_dictionary.pkl', 'rb') as f:
        loaded_dict = pickle.load(f)
    return loaded_dict

async def get_subs_and_send_notification(change_map):
    subs = get_subscriptions()
    for sub in subs:
        listings = get_listing_to_send(sub['geo_id'],sub['chat_id'],sub['price_limit'],change_map[sub['geo_id']])
        for listing in listings:
            await send_message(chat_id=sub['chat_id'],listing=listing,change_map=change_map)

async def send_message(chat_id, listing, change_map):

    caption = "Price Update!!\n" if listing['listing_id'] in change_map[listing['geo_id']] else "New Listing\n"
    caption += listing['type'] + "\n" + listing['address'] + "\n" + listing['rent_label'] + "\n" + listing['url']

    media_group = []
    for index, img in enumerate(listing['images']):
        media_group.append(InputMediaPhoto(media=img, caption=caption if index==0 else ""))

    transaction =  dict()
    transaction['chat_id'] = chat_id
    transaction['listing_id'] = listing['listing_id']
    transaction['price'] = listing['rent']
    
    await bot.send_media_group(chat_id=chat_id, media= media_group)
    create_transaction(transaction)


def get_new_listings_by_param(param):
    #prepare request
    querystring = {"locationValue":"","locationIdentifier":"","furnishedState":"Any","includeRetirementHomes":"false","includeSharedAccommodation":"true","section":"to-rent","priceMax":"","sortOrder":"newest_listings","radius":"2"}
    querystring['locationValue'] = param['geo_label']
    querystring['locationIdentifier'] = param['geo_id']
    querystring['priceMax'] = str(param['price'])

    #process response
    response = requests.get(listing_api_url, headers=headers, params=querystring)
    resListingData = response.json()['data']['listings']

    listings = []
    listing_base_url = "https://www.zoopla.co.uk/to-rent/details/"
    for listing in resListingData['regular']:
        temp_listing = dict()
        temp_listing['listing_id'] = listing['listingId']
        temp_listing['geo_id'] = param['geo_id']
        temp_listing['type'] = "House Share" if listing['title']=="Room to rent" else listing['title']
        temp_listing['rent'] = listing['pricing']['value']
        temp_listing['rent_label'] = listing['pricing']['label']
        temp_listing['address'] = listing['address']
        temp_listing['url'] = listing_base_url+listing['listingId']
        temp_listing['images'] = listing['imageUris'][0:4] if len(listing['imageUris']) >4 else listing['imageUris'][0:len(listing['imageUris'])]
        listings.append(temp_listing)
    
    # save_for_testing(listings)
    return listings

def process_listings(params):
    map = dict()
    for param in params:
        new_listings = get_new_listings_by_param(param)
        # new_listings = get_for_testing()
        old_listings = get_listing_by_geo_id(param['geo_id'])
        map[param['geo_id']] = []
        if(len(old_listings)!=0):
            for old in old_listings:
                for new in new_listings:
                    if(old['listing_id'] == new['listing_id'] and old['rent'] != new['rent']):
                        map[param['geo_id']].append(old['listing_id'])

        add_listings(new_listings)
    return map

async def main():
    
    listing_param = get_listing_param()
    change_map = process_listings(listing_param.data)
    delete_stale_listings()
    await get_subs_and_send_notification(change_map)
  
  
if __name__=="__main__": 
    asyncio.run(main()) 
