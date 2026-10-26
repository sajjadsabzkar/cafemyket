# ربات تلگرام و داشبورد وب دیده‌بان ۲۴ ساعته کافه‌بازار و مایکت (GitHub Actions + GitHub Pages)

این مخزن همزمان شامل **ربات تلگرام ۲۴ ساعته** و **صفحه وب زنده رادار بازار و مایکت (قابل میزبانی رایگان روی `github.io`)** است.

## ساختار فایل‌ها
```text
├── .github/workflows/daily-radar.yml   # اجرای خودکار ۲۴ ساعته و بروزرسانی دیتای سایت github.io
├── index.html                          # داشبورد وب «رادار بازار و مایکت» ویژه GitHub Pages (github.io)
├── apps_data.json                      # دیتای زنده برنامه‌های جدید که توسط bot.py بروزرسانی می‌شود
├── bot.py                              # اسکریپت پایتون دریافت API کافه‌بازار و مایکت + ارسال به تلگرام
├── requirements.txt
├── seen_apps.json
└── README.md
```

## ۱. راه‌اندازی ربات تلگرام در گیت‌هاب (GitHub Actions)
1. تمام فایل‌های این پکیج را در مخزن گیت‌هاب خود آپلود (Push) کنید.
2. در مخزن گیت‌هاب به مسیر **Settings → Secrets and variables → Actions → New repository secret** بروید و دو متغیر زیر را بسازید:
   - `TELEGRAM_BOT_TOKEN`: توکن ربات تلگرام دریافتی از `@BotFather`
   - `TELEGRAM_CHAT_ID`: آیدی عددی چت یا نام کاربری کانال (مانند `@my_channel`)
3. وارد تب **Actions** شوید و روی **Run workflow** کلیک کنید.

## ۲. بالا آوردن صفحه وب رادار روی `github.io` (GitHub Pages)
چون API مایکت در مرورگر دارای محدودیت CORS است، معماری این پکیج به گونه‌ای طراحی شده که **GitHub Actions** هر بار اسکریپت `bot.py` را روی سرور اوبونتو اجرا کرده، جدیدترین برنامه‌های کافه‌بازار و مایکت را داخل فایل `apps_data.json` ذخیره و در مخزن Commit می‌کند و صفحه `index.html` آن را روی `github.io` نمایش می‌دهد:
1. در مخزن گیت‌هاب خود به **Settings → Pages** بروید.
2. در بخش **Build and deployment**، گزینه **Source** را روی **Deploy from a branch** بگذارید.
3. شاخه (**Branch**) را روی `main` (یا `master`) و پوشه را روی `/ (root)` قرار داده و **Save** را بزنید.
4. پس از ۱ دقیقه، داشبورد گرافیکی رادار بازار و مایکت روی آدرس `https://<username>.github.io/<repo-name>/` بالا می‌آید!
