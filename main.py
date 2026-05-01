"""
CloneMaster - تطبيق لإدارة حسابات متعددة مع رموز QR ثابتة
يمكن تحويله إلى APK مباشرة
"""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.utils import get_color_from_hex
import json
import os
import qrcode
import datetime
import hashlib
import uuid
from io import BytesIO
from kivy.core.image import Image as CoreImage
from kivy.graphics.texture import Texture

# ===================== الإعدادات الأساسية =====================
DATA_FILE = 'clone_master_data.json'

# ===================== ألوان التطبيق =====================
COLORS = {
    'primary': get_color_from_hex('#25D366'),
    'secondary': get_color_from_hex('#128C7E'),
    'background': get_color_from_hex('#0a0e1a'),
    'card': get_color_from_hex('#1e2740'),
    'text': get_color_from_hex('#ffffff'),
    'text_secondary': get_color_from_hex('#a0a0a0'),
    'success': get_color_from_hex('#00ff9d'),
    'danger': get_color_from_hex('#ff5555'),
}

# ===================== كلاس الحساب =====================
class Account:
    def __init__(self, account_id, name, phone_number, created_at=None):
        self.id = account_id
        self.name = name
        self.phone_number = phone_number
        self.created_at = created_at or datetime.datetime.now().isoformat()
        self.is_active = True
        self.qr_code_data = self.generate_qr_data()
    
    def generate_qr_data(self):
        unique_string = f"CLONEMASTER_{self.id}_{self.phone_number}_{self.created_at}"
        hashed = hashlib.sha256(unique_string.encode()).hexdigest()
        return hashed[:32]
    
    def get_qr_texture(self, size=300):
        qr = qrcode.QRCode(version=1, box_size=8, border=2)
        qr.add_data(self.qr_code_data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        from PIL import Image as PILImage
        img = img.convert('RGBA')
        data = img.tobytes()
        texture = Texture.create(size=img.size, colorfmt='rgba')
        texture.blit_buffer(data, colorfmt='rgba', bufferfmt='ubyte')
        return texture
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'phone_number': self.phone_number,
            'created_at': self.created_at,
            'is_active': self.is_active,
            'qr_code_data': self.qr_code_data
        }
    
    @classmethod
    def from_dict(cls, data):
        account = cls(data['id'], data['name'], data['phone_number'], data['created_at'])
        account.is_active = data.get('is_active', True)
        account.qr_code_data = data.get('qr_code_data', account.qr_code_data)
        return account

# ===================== مدير الحسابات =====================
class AccountManager:
    def __init__(self):
        self.accounts = []
        self.load_accounts()
    
    def generate_id(self):
        return str(uuid.uuid4())[:8]
    
    def add_account(self, name, phone_number):
        account_id = self.generate_id()
        account = Account(account_id, name, phone_number)
        self.accounts.append(account)
        self.save_accounts()
        return account
    
    def remove_account(self, account_id):
        self.accounts = [a for a in self.accounts if a.id != account_id]
        self.save_accounts()
    
    def get_account(self, account_id):
        for account in self.accounts:
            if account.id == account_id:
                return account
        return None
    
    def toggle_account(self, account_id):
        account = self.get_account(account_id)
        if account:
            account.is_active = not account.is_active
            self.save_accounts()
            return account.is_active
        return None
    
    def save_accounts(self):
        data = [acc.to_dict() for acc in self.accounts]
        try:
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(data,