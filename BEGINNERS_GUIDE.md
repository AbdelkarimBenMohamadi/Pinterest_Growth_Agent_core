# 🚀 Pinterest Growth Agent: Zero to Hero Beginner's Guide!

Welcome! Imagine you have a super-smart robot assistant. You tell this robot, "Hey, I want to be famous for pictures of cute cats on Pinterest." The robot nods, goes to the internet to find out what kind of cat pictures people love the most right now, draws those pictures, writes a catchy title for them, and then logs into your Pinterest to post them for you. It does this every day while you sleep or play games!

This guide will teach you how to set up your own robot (we call it the **Pinterest Growth Agent** or **PGA**). Because we have built a "magic button" for you, you don't need to know anything about coding to set this up!

---

## 🛠️ Step 1: Getting Your Tools Ready

Before you build a robot, you need to grab three free things from the internet:

### 1. Python (The Robot's Engine)
Python is a language that computers understand. We need it to run our robot.
- **Go to:** [python.org/downloads](https://www.python.org/downloads/)
- Click the big yellow button to download the latest version for your computer.
- **⚠️ VERY IMPORTANT:** When you run the installer, look at the very bottom of the first screen. There is a little checkbox that says **"Add Python to PATH"**. You **MUST** check that box before clicking "Install Now". If you forget, the robot won't wake up!

### 2. Node.js (The Robot's Hands)
Node.js gives our robot the tools it needs to safely interact with websites.
- **Go to:** [nodejs.org](https://nodejs.org/en/)
- Download and install the one that says **"LTS"** (which means it's the most stable).

### 3. Groq API Key (The Robot's Brain Juice)
Our robot uses artificial intelligence (AI) to think of smart titles and words for your pins. Groq is a super-fast AI, and it gives us a free "key" to use it.
- **Go to:** [console.groq.com](https://console.groq.com/)
- Sign in with your Google account.
- Click on **API Keys** on the left menu, then click **Create API Key**.
- Give it a name (like "My Pinterest Robot") and copy the long secret code it gives you. **Don't lose this code!** Paste it somewhere safe for now.

---

## 📥 Step 2: Download the Robot

1. Go to the GitHub page where this project lives.
2. Click the big green **"Code"** button near the top right.
3. Click **"Download ZIP"**.
4. Once it downloads, right-click the ZIP file and choose **"Extract All..."**. Extract it to your Desktop so it's easy to find.
5. Open the folder you just extracted. It should be called `Pinterest_Growth_Agent_core-main`.

---

## 🪄 Step 3: The Magic Setup Button

This used to be the hard part, but we made it incredibly easy for you!

1. Look inside your robot folder for a file called **`start_windows.bat`**.
2. **Double-click it!** 
3. A black window will open. This is normal! The script is automatically building the robot's house, installing all its parts, and downloading its browser. (This might take 1 to 2 minutes, so just let it work).
4. Once it finishes installing, it will ask you for your keys right there in the window!
   - It will ask for your **Groq API Key**. (Paste the secret code you saved earlier and hit Enter).
   - It will ask for your **Pinterest Email**.
   - It will ask for your **Pinterest Password**.
5. The window will then ask: *"Do you want to wake up the robot right now? (Y/N)"*. 
   - Type **N** and press Enter for now. We have one more quick thing to do!

*(Don't worry, these secrets stay locked on your computer. The robot never shares them with anyone).*

---

## 🎨 Step 4: Teaching the Robot Your Niche

Now you have to tell the robot what kind of pictures to make. 

1. Inside your folder, look for a file called **`config.yaml`**. Right-click it and open it with **Notepad**.
2. Find the part that says `niche:`. This is where you tell the robot your topic!
3. Change the `seed_keywords` to whatever you want. For example, if you want a cooking account, you could write:
   ```yaml
   niche:
     seed_keywords:
       - "easy dinner recipes"
       - "healthy snacks"
       - "baking for beginners"
   ```
4. Save the file and close Notepad!

---

## ⏰ Step 5: Waking Up the Robot

Everything is ready! You can now turn the robot on whenever you want.

1. **Double-click `start_windows.bat`** again.
2. Because it's already set up, it will skip the installation and go straight to: *"Do you want to wake up the robot right now? (Y/N)"*
3. Type **Y** and hit Enter!

**What happens now?**
The robot wakes up! You'll see text popping up on your screen. The robot is looking at Pinterest, thinking of ideas, drawing pictures, and scheduling them. 

*(Note: The robot is smart—it knows a brand new account shouldn't post 100 times a day, so it will only post a little bit at first, and slowly post more as it grows older).*

> **💡 Want to test it right now?** 
> If you don't want to wait for the schedule and just want to see the robot make exactly **one post immediately**, you can double-click the **`test_one_post.bat`** file instead!

---

## 📊 Step 6: Checking the Robot's Work

Want to see all the awesome things your robot is doing? It has a built-in website just for you!

1. Open your computer's terminal: Click your Windows Start button, type **`cmd`**, and hit Enter.
2. Drag and drop your robot folder into the black window, but type `cd ` (with a space) before it. It should look like this: `cd C:\Users\YourName\Desktop\Pinterest_Growth_Agent_core-main`. Press Enter.
3. Step inside the robot's bubble by typing: `venv\Scripts\activate` and press Enter.
4. Type this command to launch your dashboard:
   ```bash
   python -m src.main dashboard
   ```
5. Open your web browser (like Chrome or Safari) and go to `http://localhost:3000`.

You will see a beautiful dashboard showing you exactly what pictures the robot made, what keywords are popular, and how many people are looking at your pins!

---

## 👯‍♂️ Step 7: Running Multiple Accounts (Advanced)

Even though our robot is built to run only one account at a time (to keep it simple and safe), there is a very easy trick to run multiple accounts. We call it the **"Folder Duplication" Method**!

1. **Copy the Robot's House:**
   Right now, your robot lives in the `Pinterest_Growth_Agent_core-main` folder. Simply copy and paste that entire folder for as many accounts as you have! Rename the folders so you don't get confused (for example: `Robot_Cats`, `Robot_Dogs`).
2. **Give Them Their Own Keys:**
   Go into each new folder. You will see an `.env` file that was created. Open it in Notepad and change the email and password for that specific account.
3. **Change the Keywords:**
   Open the `config.yaml` file in the new folder and change the niche keywords.
4. **⚠️ VERY IMPORTANT: Use Proxies!**
   If you run 3 robots from the exact same Wi-Fi address, Pinterest might ban you. To protect your robots, open the `config.yaml` in each folder, find the `safety:` section, and add a different Residential Proxy URL to `proxy_url:`. This makes Pinterest think one robot is in New York and the other is in Texas!
5. **Wake Them All Up:**
   Just double-click the `start_windows.bat` file inside each folder!

---

🎉 **CONGRATULATIONS!** 🎉
You just built your own AI-powered Pinterest Growth Agent! You can now let the robot run in the background while you go do fun stuff. Check back on the dashboard every few days to watch your numbers grow!
