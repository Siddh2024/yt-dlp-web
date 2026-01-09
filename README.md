# How to Deploy "yt-dlp Web" Online

To let friends use this without your computer being on, you need to host it on a cloud server.
**GitHub** stores your code, and a service like **Render** (free tier available) runs it.

## Step 1: Push Code to GitHub
1.  **Create a GitHub Account** if you haven't.
2.  **Create a New Repository** named `ytdlp-web`.
3.  **Upload Files**:
    - Upload ALL files in this folder to that repository.
    - (Especially: `Dockerfile`, `Procfile`, `requirements.txt`, `app.py`, `downloader.py`, `templates/`, `static/`).
    - *Note: Do NOT upload the `downloads` folder or `ytdlp.exe` if present. The server uses Linux.*

## Step 2: Deploy on Render (Free)
1.  Go to [dashboard.render.com](https://dashboard.render.com/) and Sign Up (you can use your GitHub account).
2.  Click **New +** -> **Web Service**.
3.  Select **Build and deploy from a Git repository**.
4.  Connect your `ytdlp-web` repository.
5.  **Configuration**:
    - **Name**: `my-downloader` (or anything).
    - **Runtime**: Select **Docker**.
    - **Region**: Choose one close to you (e.g. Frankfurt, Singapore, Oregon).
    - **Instance Type**: **Free**.
6.  Click **Create Web Service**.

## Step 3: Fix "Sign in to confirm you’re not a bot"
Youtube blocks cloud servers. To fix this, provide `cookies.txt`.

**Method: Secret File (Recommended)**
Since cookies can be large, use a "Secret File" instead of an Environment Variable to avoid errors.
1.  **Get Cookies**: Install "Get cookies.txt LOCALLY" extension and download `cookies.txt`.
2.  **Add to Render**:
    - Go to Dashboard -> Your Service -> **Environment**.
    - Scroll down to **Secret Files**.
    - Click **Add Secret File**.
    - **Filename**: `cookies.txt`
    - **File Content**: Paste the content of your `cookies.txt`.
    - Click **Save**.
3.  **Delete the old Variable**: If you added `COOKIES_CONTENT` earlier, **delete it** to fix the "argument list too long" error.
4.  Render will redeploy automatically.

## Step 4: Wait & Share
- Render will take about 2-5 minutes to build.
- Once it says **Live**, you will get a URL like: `https://my-downloader.onrender.com`.
- **Share this URL** with your friends. They can use it from any phone or computer!

## Important Notes
- **Spin Down**: On the free tier, if no one uses the site for 15 minutes, it goes to "sleep". When you visit it again, it might take **50 seconds** to wake up.
- **Cookie Expiry**: Cookies eventually expire (usually after a few months or if you change password). If downloads fail again, just update the `COOKIES_CONTENT` variable with fresh cookies.
