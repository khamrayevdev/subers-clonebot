# 💎 Premium Telegram Management Bot (Open Source)

Ushbu bot Telegram kanallari va guruhlarini boshqarish, obunachilar bazasini yig'ish va ommaviy rassilkalarni amalga oshirish uchun mo'ljallangan professional vositadir. To'liq ochiq kodli va Telegram Premium imkoniyatlari (Custom Emojis) bilan boyitilgan.

## 🚀 Asosiy Imkoniyatlar

- **✨ Telegram Premium Integratsiyasi**: Barcha tugmalar va tizim xabarlarida maxsus Premium emojilar qo'llanilgan.
- **📁 Baza Boshqaruvi**: Foydalanuvchilar bazasini JSON formatida eksport va import qilish imkoniyati.
- **🤖 Bot Maker**: Bir nechta "Child" botlarni bir vaqtda boshqarish.
- **📤 Smart Mailing**: 
    - Yuqori tezlikdagi ommaviy xabarlar.
    - Media (rasm/video) va URL-tugmalar qo'llab-quvvatlanadi.
    - **💾 Xotira Optimizatsiyasi**: Rassilka tugagandan so'ng media fayllar serverdan avtomatik tozalanadi.
- **🛡 Himoya va Monitoring**:
    - Captcha tizimi (Robot emasligini tekshirish).
    - Xabarlarni nusxalashni taqiqlash (Protect Content).
    - Bloklangan foydalanuvchilarni avtomatik aniqlash.

## 🛠 O'rnatish (Installation)

1. **Repozitoriyani yuklab oling:**
   ```bash
   git clone https://github.com/yourusername/subs-clone.git
   cd subs-clone
   ```

2. **Virtual muhitni yarating va faollashtiring:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Mac/Linux uchun
   venv\Scripts\activate     # Windows uchun
   ```

3. **Kerakli kutubxonalarni yuklang:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Konfiguratsiya (.env):**
   Bot tokenini o'rnatish uchun `.env` faylini yarating:
   ```env
   BOT_TOKEN=Sizning_Admin_Bot_Tokeningiz
   ```

## 🏁 Ishga tushirish

Botni ishga tushirish uchun quyidagi buyruqni bering:
```bash
python3 run.py
```

## 📂 Loyiha Strukturasi

- `main.py` - Botning asosiy kirish nuqtasi.
- `child_bot_manager.py` - Ikkinchi darajali botlarni boshqaradigan worker.
- `database/` - Ma'lumotlar bazasi (SQLite) va boshqaruv funksiyalari.
- `handlers/` - Bot buyruqlari va mantiqiy qismlari.
- `keyboards/` - Barcha tugmalar va menyular.
- `media/` - Vaqtinchalik media fayllar saqlanadigan joy.

## 📄 Litsenziya

Ushbu loyiha ochiq kodli bo'lib, o'rnatish va foydalanish mutlaqo bepul.
