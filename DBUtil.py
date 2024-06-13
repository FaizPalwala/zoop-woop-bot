import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load .env file
load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(url, key)

def add_subscriptions(subs):
    data, count = supabase.table('subscriptions').upsert(subs).execute()
    return data

def get_subscriptions():
    data, count = supabase.table('subscriptions').select('*').execute()
    return data[1]

def get_listing_to_send(geo_id, chat_id, rent_limit, ignore_listings):
    return supabase.rpc(fn='get_listings_to_send',
                        params={
                            'curr_geo_id' : geo_id,
                            'curr_chat' : chat_id,
                            'rent_limit' : rent_limit,
                            'ignore_listings' : ignore_listings
                        }).select('*').execute().data

def get_listing_param():
    return supabase.rpc('get_listing_param').select('*').execute()

def add_listings(listings):
    data, count = supabase.table('listings').upsert(listings).execute()
    return data

def get_listing_by_geo_id(geo_id):
    data, count = supabase.table('listings').select('*').eq('geo_id', geo_id).execute()
    return data[1]

def create_transaction(transaction):
    data, count = supabase.table('transactions').upsert(transaction).execute()
    return data

def delete_stale_listings():
    return supabase.rpc('delete_stale_listings').execute()



