# How to Get YouTube PO Token & Visitor Data

If you are experiencing "Sign in to confirm you're not a bot" errors, you need to provide a **PO Token** (Proof of Origin) and **Visitor Data**.

## Method 1: Network Tab (Advanced)

1. Open **Chrome** or **Edge** in Incognito mode.
2. Go to `https://www.youtube.com`.
3. Open Developer Tools (`F12` or `Right Click > Inspect`).
4. Go to the **Network** tab.
5. In the "Filter" box, type `v1/player`.
6. Click on any video on YouTube to start playing it.
7. Look for a request in the Network tab named `player?key=...` (it might just say `player`).
8. Click it and go to the **Payload** tab (or **Request Body**).
9. Look for `context` -> `client` -> `visitorData`.
    - **Copy this value string.** (e.g., `Cgt...%3D%3D`)
    - This is your **VISITOR_DATA**.

## Method 2: Browser Console (Easiest)

1. Go to YouTube.
2. Press `F12` to open Developer Tools.
3. Click on the **Console** tab.
4. Type the following and press Enter:
   ```javascript
   yt.config_.VISITOR_DATA
   ```
5. Copy the string that appears (without the quotes). This is your **VISITOR_DATA**.

*Note: For `PO_TOKEN`, it is slightly more complex as it is sometimes generated via specific scripts. However, often just providing the `VISITOR_DATA` along with a valid cookie file is enough. If you specifically need a PO Token, you may need to use a browser extension or specific script to extract `po_token` from the `serviceIntegrityDimensions` in the detailed stats or internal calls, but standard users often find `VISITOR_DATA` + Cookies sufficient.*

## Step 2: Add to Environment Variables

**On Render:**
1. Go to your Dashboard -> Service -> Environment.
2. Add Environment Variable:
   - Key: `VISITOR_DATA`
   - Value: `PASTE_YOUR_VALUE_HERE`
3. (Optional) Add `PO_TOKEN` if you have one.

**Locally (.env or Environment):**
- Set `VISITOR_DATA=...`

## Step 3: Redeploy
Redeploy your application. The app currently prioritizes the Web Client if a PO Token is present, or attempts standard fallbacks with the Visitor Data injected.
