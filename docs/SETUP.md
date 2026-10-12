# Setup: the parts only you can do

Everything else (code, content system, rendering, scheduling) is already set up.
These steps need you because they involve your identity, your accounts or your money.
Total time: about 20 minutes.

## 0. Finish the daily Routine (about 1 min)

The Routine **Daily money short** already exists and runs every day at 08:59 Berlin time. It was
created without connectors, so open it under Routines at https://claude.ai/code, choose **Edit**, then:

- add the **Higgsfield** connector (it makes the narrator voice), and
- add the **LeonShira/Ferien** repository,

and save. Without the connector, each run stops and reports that it's missing.

## 1. Create the two channels (about 10 min)

- **TikTok:** create a new account for the channel (a personal account, not a Business account:
  Creator Rewards excludes business accounts). Pick a name and handle, and put a short bio and the
  line "Made with AI, numbers fact-checked. Education, not financial advice." in the bio.
- **YouTube:** create a channel (a Brand Account under your Google account works well) with the same
  name and bio line.
- If you are in Germany and monetise, both profiles need an Impressum (legal notice):
  a link in the bio to a page with your name and address is the usual way.

## 2. Connect them to Upload-Post (about 5 min)

1. Sign up at https://app.upload-post.com. The **Basic plan** ($24/mo, or $16/mo billed yearly) is the
   cheapest plan that includes TikTok. The free plan does not post to TikTok.
2. Create one profile (e.g. `money-explained`) and connect TikTok and YouTube to it (two OAuth clicks).
3. Copy your API key from the dashboard.

## 3. Give the cloud environment the key (about 2 min)

In the Claude app, open the cloud environment menu in this session's title bar, choose **Edit**, and add
the key under **Network secrets** (called "API credentials" in older app versions); if that section isn't
offered, add it as an environment variable:

```
UPLOAD_POST_API_KEY=<your key>
```

Optional: `UPLOAD_POST_USER=<profile name>` if you created more than one Upload-Post profile.
New sessions, including the daily Routine, pick it up automatically.

## 4. Keep Higgsfield topped up

Narration costs about 5 credits per video, so roughly 150 credits a month at one video a day.
The pipeline stops and tells you before credits run out; it never buys credits on its own.

## 5. Later: monetisation

| Program | Typical bar (check the app, it changes) |
|---|---|
| TikTok Creator Rewards | 18+, 10,000 followers, 100,000 views in the last 30 days, videos over 1 minute |
| YouTube Partner Program | 1,000 subscribers + 10M Shorts views in 90 days (or 4,000 watch hours) |

Both pay only for original content. That's why the pipeline varies formats, checks every fact, and
labels AI use.
