
# Replace 'YOUR_BOT_TOKEN' with your actual bot token
BOT_TOKEN = '6378511CctkaN-tmQcOcTUT_5We0W-g'
import logging
import os
import json
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import ParseMode
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage

import asyncio

async def subscription_expiry_check():
    while True:
        # Check for expired subscriptions and remove users
        # ...

        await asyncio.sleep(24 * 60 * 60)  # Run once a day


storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=storage)
# Improved logging configuration
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

# File to store user details (user_id and balance)
USER_DETAILS_FILE = 'user_details.json'

# Function to load user details from the JSON file
def load_user_details():
    if os.path.exists(USER_DETAILS_FILE):
        with open(USER_DETAILS_FILE, 'r') as file:
            return json.load(file)
    else:
        return {}

# Function to save user details to the JSON file
def save_user_details(user_details):
    with open(USER_DETAILS_FILE, 'w') as file:
        json.dump(user_details, file)

# Define states for interactive user inputs
class Form(StatesGroup):
    amount = State()  # For /addbalance
    transfer_recipient = State()  # For /transfer recipient ID
    transfer_amount = State()  # For /transfer amount

# Function to send a message to the specified group
async def send_to_group(chat_id, message_text):
    try:
        await bot.send_message(chat_id, message_text)
    except Exception as e:
        logging.error(f"Failed to send message to group (Chat ID: {chat_id}): {e}")


from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    args = message.get_args()

    if args.startswith('group_'):
        group_id = args.split('_')[1]
        subscription_file = f'group_{group_id}_subscription.json'

        if os.path.exists(subscription_file):
            with open(subscription_file, 'r') as file:
                subscription_details = json.load(file)
            response_message = f"Subscription Plan for Group ID {group_id}: {subscription_details.get('title')}"

            # Inline button to join the group
            join_button = InlineKeyboardButton('Join Group', callback_data=f'join_{group_id}')
            join_markup = InlineKeyboardMarkup().add(join_button)

            await message.reply(response_message, reply_markup=join_markup)
        else:
            await message.reply("No subscription plan details found for this group.")
    else:
        # Regular start command without parameters
        # ... handle regular start ...

        # Regular start command without parameters
        # ... handle regular start ..
     user_id = message.from_user.id
    user_name = message.from_user.username or "Abhibots"

    user_details_file = f'user_{user_id}_details.json'
    
    if os.path.exists(user_details_file):
        # Load the user's details from their specific file
        with open(user_details_file, 'r') as file:
            user_details = json.load(file)
    else:
        # Create a new user details dictionary if the file does not exist
        user_details = {'balance': 0}
        # Save the new user details
        with open(user_details_file, 'w') as file:
            json.dump(user_details, file)

    # Extract user's balance from user_details
    user_balance = user_details.get('balance', 0)

    # Create an inline keyboard with two buttons
    inline_kb = InlineKeyboardMarkup(row_width=2)
    add_money_button = InlineKeyboardButton('Add Money', callback_data='add_money')
    transfer_button = InlineKeyboardButton('Transfer Money', callback_data='transfer_money')
    
    inline_kb.add(add_money_button, transfer_button)

    # Send the message with the inline keyboard and user's ID and balance
    await message.reply(f"Welcome, {user_name}!\nYour User ID: {user_id}\nYour Balance: {user_balance} INR\nSelect an option:", reply_markup=inline_kb)

###Add money 


@dp.callback_query_handler(lambda c: c.data == 'add_money', state=None)
async def prompt_add_money(callback_query: types.CallbackQuery):
    await Form.amount.set()
    await bot.send_message(callback_query.from_user.id, "Please enter the amount to add:", reply_markup=back_to_start_kb)

@dp.message_handler(state=Form.amount)
async def process_add_balance(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user_details_file = f'user_{user_id}_details.json'

    try:
        # Parse and validate the amount
        amount_to_add = int(message.text)
        if amount_to_add <= 0:
            raise ValueError("Amount must be positive")

        # Load or initialize user's details
        if os.path.exists(user_details_file):
            with open(user_details_file, 'r') as file:
                user_details = json.load(file)
        else:
            user_details = {'balance': 0}

        # Update the user's balance
        user_details['balance'] += amount_to_add

        # Save the updated user details
        with open(user_details_file, 'w') as file:
            json.dump(user_details, file)

        await message.reply(f"Added {amount_to_add} INR to your balance. Your new balance: {user_details['balance']} INR")
                                # Notify the group
        group_message = f"User {user_id} has added {amount_to_add} INR to their balance.\n His new balance: {user_details['balance']} INR"
        await send_to_group(-1002113531445, group_message)
        
    except ValueError as e:
        logger.error(f"Error processing add balance for user {user_id}: {e}")
        await message.reply(str(e))
    finally:
        # End the state irrespective of the outcome
        await state.finish()

# Callback query handler for the transfer money button
@dp.callback_query_handler(lambda c: c.data == 'transfer_money', state=None)
async def prompt_transfer(callback_query: types.CallbackQuery):
    await Form.transfer_recipient.set()
    await callback_query.message.answer("Please enter the recipient's user ID:", reply_markup=back_to_start_kb)


# Global Inline Keyboard for 'Back' or 'Main Menu'
back_to_start_kb = InlineKeyboardMarkup()
back_to_start_button = InlineKeyboardButton('Main Menu', callback_data='back_to_start')
back_to_start_kb.add(back_to_start_button)

@dp.callback_query_handler(lambda c: c.data == 'back_to_start', state='*')
async def back_to_start(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.delete()  # Delete the original message
    await state.finish()  # Reset state
    await start(callback_query.message)  # Call the start function to show the main menu


# State handler for transfer recipient ID
@dp.message_handler(state=Form.transfer_recipient)
async def process_transfer_recipient(message: types.Message, state: FSMContext):
    recipient_id = message.text
    if recipient_id.isdigit():
        async with state.proxy() as data:
            data['recipient'] = recipient_id
        # Send the prompt and store its message ID
        prompt_message = await message.reply("Please enter the amount to transfer:", reply_markup=back_to_start_kb)
        async with state.proxy() as data:
            data['prompt_message_id'] = prompt_message.message_id
        await Form.next()
    else:
        # Retrieve the stored message ID and delete the prompt
        async with state.proxy() as data:
            prompt_message_id = data.get('prompt_message_id')
        if prompt_message_id:
            await bot.delete_message(chat_id=message.chat.id, message_id=prompt_message_id)

        # Send the error message
        await message.reply("Invalid User ID. Please enter a numerical User ID.", reply_markup=back_to_start_kb)



@dp.message_handler(state=Form.transfer_amount)
async def process_transfer_amount(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user_name = message.from_user.username or "Abhibots"
    async with state.proxy() as data:
        try:
            # Validate and parse the amount
            transfer_amount = int(message.text)
            if transfer_amount <= 0:
                raise ValueError("Amount must be positive")

            sender_id = message.from_user.id
            sender_username = message.from_user.username or "Anonymous"
            recipient_id = int(data['recipient'])

            # Check for self-transfer
            if sender_id == recipient_id:
                await message.reply("You cannot transfer credits to yourself.")
                await state.finish()
                return

            # Load sender's details
            sender_file = f'user_{sender_id}_details.json'
            if os.path.exists(sender_file):
                with open(sender_file, 'r') as file:
                    sender_details = json.load(file)
            else:
                await message.reply("You do not have an account.")
                await state.finish()
                return

            # Check for sufficient balance
            if sender_details['balance'] < transfer_amount:
                await message.reply("Insufficient balance.")
                await state.finish()
                return

            # Load or create recipient's details
            recipient_file = f'user_{recipient_id}_details.json'
            if os.path.exists(recipient_file):
                with open(recipient_file, 'r') as file:
                    recipient_details = json.load(file)
            else:
                recipient_details = {'balance': 0}

            # Perform the transfer
            sender_details['balance'] -= transfer_amount
            recipient_details['balance'] += transfer_amount

            # Save updated details
            with open(sender_file, 'w') as file:
                json.dump(sender_details, file)
            with open(recipient_file, 'w') as file:
                json.dump(recipient_details, file)

            # Confirmation message to sender
            await message.reply(f"Your User ID: {user_id}\nTransferred {transfer_amount} INR to user {recipient_id}.\nYour new balance: {sender_details['balance']} INR")
                        # Notification message to group
            group_message = f"User {user_id} has transferred {transfer_amount} INR to user {recipient_id}."
            await send_to_group(-1002113531445, group_message)
            # Notification message to recipient
            try:
                await bot.send_message(recipient_id, f"Your User ID: {user_id}\nYou have received {transfer_amount} INR from @{sender_username}\n(User ID: {sender_id}).\nYour new balance: {recipient_details['balance']} INR")
            except Exception as e:
                logging.error(f"Failed to send notification to recipient (User ID: {recipient_id}): {e}")

        except ValueError as e:
            await message.reply(str(e))
        finally:
            # End the state irrespective of the outcome
            await state.finish()
            
class Form(StatesGroup):
    # ... existing states ...
    subscription_details = State()  # For /setsubscription
    

async def is_user_admin_or_owner(message: types.Message):
    user_id = message.from_user.id
    member = await bot.get_chat_member(message.chat.id, user_id)
    return member.is_chat_admin() or member.status == types.ChatMemberStatus.CREATOR

class SubscriptionForm(StatesGroup):
    title = State()
    plan_name = State()
    days = State()

@dp.message_handler(commands=['setsubscription'], chat_type=[types.ChatType.GROUP, types.ChatType.SUPERGROUP])
async def start_subscription_setup(message: types.Message):
    if await is_user_admin_or_owner(message):
        await SubscriptionForm.title.set()
        await message.reply("Please enter the subscription title:")
    else:
        await message.reply("You must be the group owner to set the subscription.")
        
@dp.message_handler(state=SubscriptionForm.title)
async def set_title(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['title'] = message.text
    await SubscriptionForm.next()
    await message.reply("Please enter the plan name:")

@dp.message_handler(state=SubscriptionForm.plan_name)
async def set_plan_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['plan_name'] = message.text
    await SubscriptionForm.next()
    await message.reply("Please enter the number of days:")

@dp.message_handler(state=SubscriptionForm.days)
async def set_days(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['days'] = message.text
    await state.finish()

    group_id = message.chat.id
    await save_subscription_details(data, group_id)

    # Generate and send the unique start link
    bot_username = (await bot.get_me()).username
    start_link = f"https://t.me/{bot_username}?start=group_{group_id}"
    await message.reply(f"Subscription details set successfully. Here is your unique bot start link to view the plan: {start_link}")

    
async def save_subscription_details(subscription_data, group_id):
    subscription_file = f'group_{group_id}_subscription.json'
    subscription_info = {
        'title': subscription_data['title'],
        'plan_name': subscription_data['plan_name'],
        'number_of_days': subscription_data['days']
    }
    with open(subscription_file, 'w') as file:
        json.dump(subscription_info, file)


async def is_user_group_owner(message: types.Message):
    user_id = message.from_user.id
    member = await bot.get_chat_member(message.chat.id, user_id)
    return member.status == types.ChatMemberStatus.CREATOR

async def generate_group_join_link(group_id):
    try:
        # Generate a new invite link for the group
        chat_invite_link = await bot.export_chat_invite_link(chat_id=group_id)
        return chat_invite_link
    except Exception as e:
        print(f"Error generating group join link: {e}")
        return None


async def revoke_invite_link(group_id, invite_link):
    try:
        await bot.export_chat_invite_link(chat_id=group_id)  # This revokes the previous link
    except Exception as e:
        print(f"Error revoking group invite link: {e}")


from datetime import datetime, timedelta

def calculate_expiry_date(number_of_days):
    current_date = datetime.now()
    expiry_date = current_date + timedelta(days=int(number_of_days))
    return expiry_date.strftime('%Y-%m-%d')

class Form(StatesGroup):
    # ... other states ...
    save_subscription = State()
    
async def get_group_info(group_id):
    try:
        # Fetch chat information for the given group ID
        chat = await bot.get_chat(chat_id=group_id)
        
        if chat:
            # Retrieve the group's subscription plan and expiry date from the group's subscription JSON file
            subscription_file = f'group_{group_id}_subscription.json'
            
            if os.path.exists(subscription_file):
                with open(subscription_file, 'r') as file:
                    subscription_details = json.load(file)
                
                group_info = {
                    'name': chat.title,  # Group name
                    'plan': subscription_details.get('plan_name', 'N/A'),  # Subscription plan
                    'expiry_date': subscription_details.get('expiry_date', 'N/A')  # Expiry date
                }
                return group_info
            else:
                return None  # Handle group subscription details not found
        else:
            return None  # Handle group not found or other error cases
    except Exception as e:
        print(f"Error fetching group information: {e}")
        return None


def calculate_user_expiry_date(subscription_plan, group_expiry_date):
    # Implement your logic to calculate the user's expiry date based on the group plan
    # and the group's expiry date.
    
    # For example, you can add a certain number of days to the group's expiry date
    # based on the user's subscription plan.
    
    # Return the calculated expiry date as a string in the format 'YYYY-MM-DD'.
    
    # Here, we're simply using the group's expiry date as-is.
    return group_expiry_date


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('join_'))
async def handle_join(callback_query: types.CallbackQuery):
    group_id = callback_query.data.split('_')[1]
    user_id = callback_query.from_user.id

    # Generate a one-time use group join link (implementation depends on your method)
    group_join_link = await generate_group_join_link(group_id)

    # Pass the group ID to the get_group_info function
    group_info = await get_group_info(group_id)

    if group_info:
        group_name = group_info['name']
        subscription_plan = group_info['plan']
        group_expiry_date = group_info['expiry_date']

        # Calculate user's expiry date based on the group plan and group expiry date
        user_expiry_date = calculate_user_expiry_date(subscription_plan, group_expiry_date)

        # Save user's subscription details in a new JSON file
        user_subscription_details = {
            'group_id': group_id,
            'group_name': group_name,
            'subscription_plan': subscription_plan,
            'expiry_date': user_expiry_date,
            'join_date': str(datetime.now())
        }
        user_subscription_file = f'user_{user_id}_subscription.json'
        with open(user_subscription_file, 'w') as file:
            json.dump(user_subscription_details, file)
            
    # Send the join link to the user
    await bot.send_message(user_id, f"Here is your one-time group join link: {group_join_link}")

async def remove_expired_subscriptions():
    while True:
        current_date = datetime.now()
        for filename in os.listdir():
            if filename.startswith('user_') and filename.endswith('_subscription.json'):
                user_id = filename.split('_')[1]
                user_subscription_file = f'user_{user_id}_subscription.json'

                if os.path.exists(user_subscription_file):
                    with open(user_subscription_file, 'r') as file:
                        user_subscription_details = json.load(file)

                    if 'expiry_date' in user_subscription_details:
                        expiry_date = datetime.strptime(user_subscription_details['expiry_date'], '%Y-%m-%d')
                        if current_date > expiry_date:
                            # Subscription has expired, remove it
                            os.remove(user_subscription_file)

        await asyncio.sleep(24 * 60 * 60)  # Run once a day


# Start the subscription removal loop
asyncio.ensure_future(remove_expired_subscriptions())

# Run the bot
if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
