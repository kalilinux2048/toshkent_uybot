import asyncio
import re
from datetime import datetime
from telethon import TelegramClient, events
from telethon.tl.types import MessageMediaPhoto
from telethon.errors import FloodWaitError

from database import (
    add_or_update_listing, delete_listing_by_source, get_all_active_channels,
    update_channel_sync_time, get_channels_by_region
)
from config import API_ID, API_HASH, PHONE_NUMBER, MAX_LISTINGS_PER_CHANNEL

class ListingCollector:
    def __init__(self):
        self.client = TelegramClient('user_session', API_ID, API_HASH)
        self.is_running = False
    
    async def start(self):
        """Collectorni ishga tushirish"""
        await self.client.start(phone=PHONE_NUMBER)
        print("✅ Collector ishga tushdi!")
        
        # Barcha faol kanallarni yuklash
        await self.load_and_sync_channels()
        
        # Yangi xabarlar uchun handler
        @self.client.on(events.NewMessage)
        async def new_message_handler(event):
            await self.process_new_message(event)
        
        # Xabar o'chirilganda handler
        @self.client.on(events.MessageDeleted)
        async def delete_handler(event):
            await self.process_deleted_message(event)
        
        await self.client.run_until_disconnected()
    
    async def load_and_sync_channels(self):
        """Barcha biriktirilgan kanallarni yuklash va oxirgi xabarlarni olish"""
        channels = await get_all_active_channels()
        
        if not channels:
            print("⚠️ Hech qanday kanal biriktirilmagan!")
            return
        
        print(f"📡 {len(channels)} ta kanal sinxronizatsiya qilinmoqda...")
        
        for channel in channels:
            try:
                await self.sync_channel_messages(channel)
                await asyncio.sleep(1)  # Rate limitdan saqlanish
            except Exception as e:
                print(f"❌ Kanal sinxronizatsiyasida xatolik {channel['channel_title']}: {e}")
    
    async def sync_channel_messages(self, channel):
        """Bir kanaldan oxirgi 10 ta xabarni olish"""
        try:
            channel_id = int(channel['channel_id'])
            
            # Kanalga ulanish
            entity = await self.client.get_entity(channel_id)
            
            # Oxirgi 10 ta xabarni olish
            messages = []
            async for message in self.client.iter_messages(entity, limit=MAX_LISTINGS_PER_CHANNEL):
                messages.append(message)
            
            print(f"📥 {channel['channel_title']} dan {len(messages)} ta xabar olindi")
            
            # Har bir xabarni qayta ishlash
            for message in messages:
                await self.process_single_message(message, channel)
            
            # Oxirgi sinxronizatsiya vaqtini yangilash
            await update_channel_sync_time(channel['channel_id'])
            
        except FloodWaitError as e:
            print(f"⏳ Flood wait {e.seconds} sekund")
            await asyncio.sleep(e.seconds)
        except Exception as e:
            print(f"❌ Xatolik: {e}")
    
    async def process_new_message(self, event):
        """Yangi xabar kelganda"""
        message = event.message
        chat = await event.get_chat()
        chat_id = str(chat.id)
        
        # Bu kanal biriktirilganmi tekshirish
        channels = await get_all_active_channels()
        channel_ids = [c['channel_id'] for c in channels]
        
        if chat_id not in channel_ids:
            return
        
        # Kanal ma'lumotlarini topish
        channel_info = next((c for c in channels if c['channel_id'] == chat_id), None)
        if not channel_info:
            return
        
        await self.process_single_message(message, channel_info)
    
    async def process_single_message(self, message, channel_info):
        """Bitta xabarni qayta ishlash"""
        # Faqat matnli xabarlarni qayta ishlash
        if not message.text and not message.caption:
            return
        
        text = message.text or message.caption or ""
        
        # E'lon ekanligini tekshirish (ixtiyoriy)
        if not self.is_listing(text):
            return
        
        # E'lon ma'lumotlarini olish
        listing_data = self.extract_listing_data(text)
        
        # Rasmlarni olish
        images = []
        image_url = None
        
        if message.media and isinstance(message.media, MessageMediaPhoto):
            photo_id = str(message.media.photo.id)
            images.append(photo_id)
            image_url = photo_id
        
        try:
            # Bazaga saqlash (yoki yangilash)
            listing_id = await add_or_update_listing(
                region_key=channel_info['region_key'],
                region_name=channel_info['region_name'],
                category="🏠 Ijaraga beriladigan xonadonlar",  # Default, keyin o'zgartirish mumkin
                source_chat_id=channel_info['channel_id'],
                source_chat_title=channel_info['channel_title'],
                source_message_id=str(message.id),
                title=listing_data.get('title', text[:100]),
                price=listing_data.get('price', 'Narxi aniqlanmadi'),
                rooms=listing_data.get('rooms', '?'),
                description=listing_data.get('description', text[:500]),
                phone=listing_data.get('phone', 'Raqam topilmadi'),
                image_url=image_url,
                media_group=images if images else None
            )
            print(f"✅ E'lon saqlandi! ID: {listing_id}, Kanal: {channel_info['channel_title']}")
        except Exception as e:
            print(f"❌ E'lon saqlashda xatolik: {e}")
    
    async def process_deleted_message(self, event):
        """Xabar o'chirilganda"""
        deleted_ids = event.deleted_ids
        chat_id = str(event.chat_id)
        
        for msg_id in deleted_ids:
            await delete_listing_by_source(chat_id, str(msg_id))
            print(f"🗑 E'lon o'chirildi! Kanal: {chat_id}, Xabar: {msg_id}")
    
    def is_listing(self, text):
        """Matn e'lon ekanligini tekshirish"""
        keywords = [
            'sotiladi', 'sotish', 'ijaraga', 'ijara', 'xona', 'uy', 
            'kvartira', 'so\'m', 'dollar', 'tel', 'telefon'
        ]
        text_lower = text.lower()
        return any(kw in text_lower for kw in keywords)
    
    def extract_listing_data(self, text):
        """Matndan e'lon ma'lumotlarini olish"""
        data = {
            'title': text.split('\n')[0][:100] if text.split('\n') else text[:100],
            'description': text[:500],
            'price': self.extract_price(text),
            'rooms': self.extract_rooms(text),
            'phone': self.extract_phone(text),
        }
        return data
    
    def extract_price(self, text):
        patterns = [
            r'(\d[\d\s]*)\s*(?:so\'?m|\$|USD)',
            r'narx[:\s]*(\d[\d\s]*)',
            r'(\d{5,})'
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).replace(' ', '')
        return "Narxi aniqlanmadi"
    
    def extract_rooms(self, text):
        patterns = [r'(\d+)\s*xona', r'(\d+)\s*xonadan?', r'(\d+)\s*honali']
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return "?"
    
    def extract_phone(self, text):
        patterns = [
            r'(\+998[\s\-]?\d{2}[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2})',
            r'(?:[+]*[9]*[8]*)?[\s\-]?(\d{2})[\s\-]?(\d{3})[\s\-]?(\d{2})[\s\-]?(\d{2})'
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                phone = match.group(0)
                if phone and len(phone.replace(' ', '').replace('-', '')) >= 9:
                    return phone
        return "Raqam topilmadi"


collector = ListingCollector()

async def run_collector():
    await collector.start()
