# Instagram Connection Progress & Next Steps (Saved State)

**Date Saved:** 2026-09-10  
**Current Status:** App and Facebook Page successfully created; awaiting Instagram account link to Page.

---

## 1. Saved Credentials & Identifiers
* **Meta App Name:** `Autopilot Publisher`
* **Meta App ID:** `2303296440406722`
* **Meta App Type:** `Business` (Development Mode)
* **Facebook Page Name:** `Autopilot Media`
* **Facebook Page ID:** `1203341672873654`
* **Active Permissions Granted:**
  - `pages_show_list`
  - `instagram_basic`
  - `instagram_manage_comments`
  - `instagram_manage_insights`
  - `instagram_content_publish`
  - `instagram_manage_contents`

---

## 2. Where We Left Off & Steps to Resume (Tomorrow)

### Step 1: Link Instagram Account to "Autopilot Media" Page
On your mobile phone:
1. Open the **Instagram App**.
2. Go to **Profile** → **Edit Profile**.
3. Under **Public Business Information**, tap **Page**.
4. Tap **Connect existing Page** and choose **`Autopilot Media`** (ID: `1203341672873654`).
5. Save changes.

*(Alternatively via PC: Go to facebook.com → Switch to "Autopilot Media" Page → Settings → Linked Accounts → Instagram → Connect Account).*

### Step 2: Retrieve Instagram Business Account ID
1. Open [Graph API Explorer](https://developers.facebook.com/tools/explorer/).
2. Run query:
   ```text
   1203341672873654?fields=instagram_business_account{id,username}
   ```
3. Copy the `instagram_business_account.id` (e.g. `178414xxxxxxxxxxx`).

### Step 3: Get 60-Day Long-Lived Token
1. Next to the Access Token field in Graph API Explorer, click the blue **`(i)`** icon.
2. Click **Open in Access Token Tool**.
3. Scroll down and click **Extend Access Token** to generate the 60-day token.

### Step 4: Add to `.env`
Add these two lines to your project `.env`:
```env
IG_BUSINESS_ACCOUNT_ID=178414xxxxxxxxxxx
IG_LONG_LIVED_TOKEN=EAA...your_60_day_token_here...
```

Verify with:
```powershell
python -m agents.ig_publisher --info
```
