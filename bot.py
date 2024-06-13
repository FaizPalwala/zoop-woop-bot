import logging
import os
import requests
from telegram import (
    InputPollOption, 
    Update
)
from telegram.ext import (
    ApplicationBuilder, 
    ContextTypes, 
    CommandHandler, 
    PollAnswerHandler
)
from dotenv import load_dotenv

from DBUtil import add_subscriptions

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Load .env file
load_dotenv()

# use the variable names as defined in .env file
api_key = os.getenv("ZOOPLA_RAPIDAPI_KEY") 
api_host = os.getenv("ZOOPLA_RAPIDAPI_HOST") 
bot_token = os.getenv("BOT_TOKEN")
auto_comp_url = os.getenv("AUTO_COMP_API_URL")

querystring = {"locationPrefix":""}

headers = {
	"x-rapidapi-key": api_key,
	"x-rapidapi-host": api_host
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        
    if(len(context.args)==0):
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Incorrect Usage\n"\
                                                                            "use /help for more info")
        return
    
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Processing your request, please wait...")

    search_str = ""
    for arg in context.args:
        search_str+= arg + " "

    querystring["locationPrefix"] = search_str
    response = requests.get(auto_comp_url, headers=headers, params=querystring)

    poll_options = []
    geo_data = []
    for x in response.json()['data']['geoSuggestion']:
        poll_options.append(InputPollOption(text=x['geoLabel']))
        geo_data.append({
            'geoIdentifier': x['geoIdentifier'],
            'geoLabel': x['geoLabel']
            })
    
    message = await context.bot.send_poll(chat_id=update.effective_chat.id,
                                question="What location do you want to subscribe?",
                                options=poll_options,
                                is_anonymous=False,
                                allows_multiple_answers=True)
    
    # Save some info about the poll the bot_data for later use in receive_poll_answer
    payload = {
        message.poll.id: {
            'geo_data': geo_data,
            'message_id': message.message_id,
            'chat_id': update.effective_chat.id,
        }
    }
    context.bot_data.update(payload)

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Following are available commands and their usage\n\n" \
                                                                        "use /start [Location] - to start a new subscription\n" \
                                                                        "use /help - to display this message\n" \
                                                                        "\n*No more than 10 concurrent subscriptions are permitted*" )
    
async def receive_poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):

    answer = update.poll_answer
    answered_poll = context.bot_data[answer.poll_id]

    await context.bot.send_message(chat_id=answered_poll["chat_id"], text="Processing your request, please wait...")
    
    try:
        geo_data = answered_poll['geo_data']
    # this means this poll answer update is from an old poll, we can't do our answering then
    except KeyError:
        return
    selected_options = answer.option_ids
    
    subscriptions = []
    for selection in selected_options:
        sub = {}
        sub['chat_id'] = answered_poll['chat_id']
        sub['geo_id'] = geo_data[selection]['geoIdentifier']
        sub['geo_label'] = geo_data[selection]['geoLabel']
        sub['price_limit'] = 2000
        subscriptions.append(sub)

    if(len(add_subscriptions(subscriptions)[1])==len(subscriptions)):
        await context.bot.stop_poll(answered_poll["chat_id"], answered_poll["message_id"])
        await context.bot.send_message(chat_id=answered_poll["chat_id"], text="Subscription Sucessfull")
    else:
        await context.bot.send_message(chat_id=answered_poll["chat_id"], text="DB Error")


if __name__ == '__main__':
    application = ApplicationBuilder().token(api_key).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help))
    application.add_handler(PollAnswerHandler(receive_poll_answer))
    application.run_polling(allowed_updates=Update.ALL_TYPES)