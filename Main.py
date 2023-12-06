
# Replace 'YOUR_BOT_TOKEN' with your actual bot token
BOT_TOKEN = '637851120'
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



@dp.message_handler(commands=['start'])
async def start(message: types.Message):
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
    async with state.proxy() as data:
        try:
            # Validate and parse the amount
            transfer_amount = int(message.text)
            if transfer_amount <= 0:
                raise ValueError("Amount must be positive")

            sender_id = message.from_user.id
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

            # Check for sufficient balance including transaction fee
            transaction_fee = 1
            if sender_details['balance'] < transfer_amount + transaction_fee:
                await message.reply("Insufficient balance including transaction fee.")
                await state.finish()
                return

            # Load or create recipient's details
            recipient_file = f'user_{recipient_id}_details.json'
            if os.path.exists(recipient_file):
                with open(recipient_file, 'r') as file:
                    recipient_details = json.load(file)
            else:
                recipient_details = {'balance': 0}

            # Load or create bot owner's details
            bot_owner_id = 890382857
            bot_owner_file = f'user_{bot_owner_id}_details.json'
            if os.path.exists(bot_owner_file):
                with open(bot_owner_file, 'r') as file:
                    bot_owner_details = json.load(file)
            else:
                bot_owner_details = {'balance': 0}

            # Perform the transfer and update balances
            sender_details['balance'] -= (transfer_amount + transaction_fee)
            recipient_details['balance'] += transfer_amount
            bot_owner_details['balance'] += transaction_fee

            # Save updated details
            with open(sender_file, 'w') as file:
                json.dump(sender_details, file)
            with open(recipient_file, 'w') as file:
                json.dump(recipient_details, file)
            with open(bot_owner_file, 'w') as file:
                json.dump(bot_owner_details, file)



             # Confirmation message to sender
            await message.reply(f"Transferred {transfer_amount} INR to user {recipient_id}. "
                                f"Transaction fee of {transaction_fee} INR was applied. "
                                f"Your new balance: {sender_details['balance']} INR")

            # Notification message to recipient
            try:
                await bot.send_message(recipient_id, f"You have received {transfer_amount} INR from user {user_id}. "
                                                    f"Your new balance: {recipient_details['balance']} INR")
            except Exception as e:
                logging.error(f"Failed to send notification to recipient (User ID: {recipient_id}): {e}")

            # Notification message to group (if applicable)
            group_message = f"User {user_id} has transferred {transfer_amount} INR to user {recipient_id}. " \
                            f"A transaction fee of {transaction_fee} INR was applied."
            await send_to_group(-1002113531445, group_message)  # Replace with your group ID

            # Notification to bot owner about the fee collection (optional)
            try:
                await bot.send_message(bot_owner_id, f"You have received a transaction fee of {transaction_fee} INR from user {user_id}'s transfer.")
            except Exception as e:
                logging.error(f"Failed to send fee collection notification to bot owner (User ID: {bot_owner_id}): {e}")


        except ValueError as e:
            await message.reply(str(e))
        finally:
            # End the state irrespective of the outcome
            await state.finish()
# Run the bot
if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
