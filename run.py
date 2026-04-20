import asyncio
import sys
import os

# Loyiha ildiz direktoriyasini PYTHONPATH'ga qo'shish
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import main

if __name__ == "__main__":
    try:
        print("\n" + "="*40)
        print("🚀 SUBERS Klon bot ishga tushmoqda...")
        print("📈 Versiya: 1.0.0 (Open Source)")
        print("="*40 + "\n")
        
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n" + "="*40)
        print("🛑 Bot to'xtatildi.")
        print("="*40 + "\n")
    except Exception as e:
        print(f"\n❌ Xatolik yuz berdi: {e}\n")
