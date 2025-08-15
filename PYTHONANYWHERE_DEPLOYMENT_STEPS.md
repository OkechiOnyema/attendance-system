# 🚀 PythonAnywhere Deployment Guide

## 🌐 **Step 1: Create PythonAnywhere Account**

1. **Go to [www.pythonanywhere.com](https://www.pythonanywhere.com)**
2. **Click "Create a Beginner account"** (free tier)
3. **Choose username** (e.g., `Okechi`)
4. **Set password** (make it strong!)
5. **Verify email address**

## 📁 **Step 2: Upload Your Project**

### **Option A: Upload Files (Recommended for first time)**
1. **Open PythonAnywhere dashboard**
2. **Go to Files tab**
3. **Click "Upload a file"**
4. **Upload your entire project folder** (zip it first)

### **Option B: Git Clone (If you have GitHub)**
1. **Go to Consoles tab**
2. **Start a new Bash console**
3. **Run:**
   ```bash
   git clone https://github.com/yourusername/attendance-system.git
   ```

## 🐍 **Step 3: Set Up Virtual Environment**

1. **Go to Consoles tab**
2. **Start a new Bash console**
3. **Navigate to your project:**
   ```bash
   cd attendance-system
   ```

4. **Create virtual environment:**
   ```bash
   mkvirtualenv --python=/usr/bin/python3.9 attendance-env
   ```

5. **Activate virtual environment:**
   ```bash
   workon attendance-env
   ```

6. **Install requirements:**
   ```bash
   pip install -r requirements.txt
   ```

## ⚙️ **Step 4: Configure Django Settings**

1. **Edit settings file:**
   ```bash
   nano config/settings_production.py
   ```

2. **Replace `yourusername` with your actual PythonAnywhere username**
3. **Save the file**

4. **Create a new settings file for production:**
   ```bash
   cp config/settings.py config/settings_local.py
   cp config/settings_production.py config/settings.py
   ```

## 🗄️ **Step 5: Set Up Database**

1. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

2. **Create superuser:**
   ```bash
   python manage.py createsuperuser
   ```

3. **Collect static files:**
   ```bash
   python manage.py collectstatic
   ```

## 🌐 **Step 6: Configure Web App**

1. **Go to Web tab**
2. **Click "Add a new web app"**
3. **Choose:**
   - **Manual configuration** (not Django)
   - **Python 3.9**
4. **Set source code:** `/home/yourusername/attendance-system`
5. **Set working directory:** `/home/yourusername/attendance-system`

## 🔧 **Step 7: Configure WSGI File**

1. **Click on the WSGI file** in Web tab
2. **Replace content with:**
   ```python
   import os
   import sys
   
   # Add your project directory to the sys.path
   path = '/home/yourusername/attendance-system'
   if path not in sys.path:
       sys.path.append(path)
   
   # Set environment variable
   os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
   
   # Import Django WSGI application
   from django.core.wsgi import get_wsgi_application
   application = get_wsgi_application()
   ```

## 🚀 **Step 8: Reload and Test**

1. **Click the green "Reload" button**
2. **Wait for reload to complete**
3. **Click on your web app URL**
4. **Your app should now be live!**

## 🔒 **Step 9: Test Access Control**

1. **Try accessing from your computer** (should work)
2. **Try accessing from a different network** (should be blocked)
3. **Test student login and attendance marking**

## 📱 **Step 10: ESP32 Integration (Next Phase)**

After PythonAnywhere is working:
1. **Update ESP32 code** to connect to your WiFi
2. **Configure ESP32** to send data to PythonAnywhere
3. **Test ESP32 attendance detection**

## 🆘 **Troubleshooting**

### **Common Issues:**

#### **Import Error: No module named 'django'**
- **Solution:** Make sure virtual environment is activated
- **Run:** `workon attendance-env`

#### **Static files not loading**
- **Solution:** Run `python manage.py collectstatic`
- **Check:** STATIC_ROOT path in settings

#### **Database errors**
- **Solution:** Run `python manage.py migrate`
- **Check:** Database path in settings

#### **Permission denied**
- **Solution:** Check file permissions
- **Run:** `chmod 755 /home/yourusername/attendance-system`

## 📞 **Need Help?**

- **PythonAnywhere Help:** [help.pythonanywhere.com](https://help.pythonanywhere.com)
- **Django Documentation:** [docs.djangoproject.com](https://docs.djangoproject.com)
- **Check logs:** Look at the error logs in Web tab

## 🎯 **Next Steps After Deployment**

1. **Test all functionality** on PythonAnywhere
2. **Update ESP32 code** for cloud hosting
3. **Implement WiFi network restriction**
4. **Test end-to-end system**

---

**🎉 Congratulations! Your Django app is now hosted on PythonAnywhere!**

**Next: We'll implement the ESP32 WiFi network restriction system.**
