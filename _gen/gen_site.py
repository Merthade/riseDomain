#!/usr/bin/env python3
"""Generate risemorning.app's guides, guides hub, support page, 404, sitemap and robots, and
inject the FAQ + guides blocks into index.html between their markers.

Modelled on AlarmPlanner's website/_gen/gen_guides.py. Edit PAGES / HUB_FAQ, then:
    python3 _gen/gen_site.py
Jekyll (GitHub Pages) skips _-prefixed dirs, so this folder is never deployed.

Guide topics follow AlarmPlanner's Search Console lesson (2026-08-08): narrow, feature-shaped
questions rank (pos 8-10); broad advice queries owned by big sites sit at pos 30+. Every claim
about Rise must match the shipped app (1.33): check ARCHITECTURE.md's Free vs Pro matrix before
adding one.
"""
import os, json, re, html

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOMAIN = "https://risemorning.app"
APP_ID = "6760960639"
STORE_CANONICAL = f"https://apps.apple.com/app/rise-morning-routine-alarm/id{APP_ID}"
TODAY = "2026-10-01"

# App Analytics campaign links: BOTH pt and ct are required (AlarmPlanner shipped ct alone and
# reported nothing until 2026-08-08). pt is the account's provider token. Coarse buckets, because a
# campaign shows in App Analytics only after 5 first-time downloads.
PROVIDER_TOKEN = "2187944"
CT_HOME = "Website_Home"
CT_GUIDE = "Website_Guide"

def store_url(ct):
    assert 0 < len(ct) <= 30 and ct == ct.strip()
    return f"https://apps.apple.com/app/apple-store/id{APP_ID}?pt={PROVIDER_TOKEN}&amp;ct={ct}&amp;mt=8"

AP = "https://alarmclockplanner.com"

ANALYTICS = """<link rel="preconnect" href="https://eu.i.posthog.com">
<script>
    !function(t,e){var o,n,p,r;e.__SV||(window.posthog=e,e._i=[],e.init=function(i,s,a){function g(t,e){var o=e.split(".");2==o.length&&(t=t[o[0]],e=o[1]),t[e]=function(){t.push([e].concat(Array.prototype.slice.call(arguments,0)))}}(p=t.createElement("script")).type="text/javascript",p.async=!0,p.src=s.api_host+"/static/array.js",(r=t.getElementsByTagName("script")[0]).parentNode.insertBefore(p,r);var u=e;for(void 0!==a?u=e[a]=[]:a="posthog",u.people=u.people||[],u.toString=function(t){var e="posthog";return"posthog"!==a&&(e+="."+a),t||(e+=" (stub)"),e},u.people.toString=function(){return u.toString(1)+".people (stub)"},o="init capture register register_once register_for_session unregister opt_in_capturing opt_out_capturing has_opted_in_capturing has_opted_out_capturing clear_opt_in_out_capturing startSessionRecording stopSessionRecording isSessionRecordingStarted".split(" "),n=0;n<o.length;n++)g(u,o[n]);e._i.push([i,s,a])},e.__SV=1)}(document,window.posthog||[]);
    if (!/^(localhost|127\\.0\\.0\\.1|\\[::1\\])$/.test(location.hostname) && location.hostname !== '') {
        posthog.init('phc_ztIjBWZp495eGWUZSUprsXSLzyElBWMcf2xc65kKfE5', {
            api_host: 'https://eu.i.posthog.com',
            person_profiles: 'anonymous',
            persistence: 'memory'
        });
        posthog.register({ app_name: 'rise_web' });
    }
</script>
<script>
    (function() {
        var theme = null;
        try { theme = localStorage.getItem('theme'); } catch (e) {}
        if (!theme) theme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
        document.documentElement.setAttribute('data-theme', theme);
    })();
</script>"""

PAGE_JS = """<script>
    document.getElementById('theme-toggle').addEventListener('click', function() {
        var next = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', next);
        try { localStorage.setItem('theme', next); } catch (e) {}
    });
    document.addEventListener('click', function (e) {
        var el = e.target.closest('[data-ph]');
        if (el && window.posthog) posthog.capture(el.getAttribute('data-ph'), { page: location.pathname });
    });
</script>"""

MOON = '<svg class="moon-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>'
SUN = '<svg class="sun-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>'

def nav(ct):
    return f"""<nav>
    <div class="nav-inner">
        <a href="/" class="nav-brand">
            <img src="/assets/appicon.png" alt="Rise app icon">
            <span>Rise</span>
        </a>
        <div class="nav-links">
            <a href="/#how-it-works">How It Works</a>
            <a href="/#features">Features</a>
            <a href="/guides/">Guides</a>
            <a href="/#faq">FAQ</a>
        </div>
        <div class="nav-right">
            <a href="{store_url(ct)}" class="nav-download" data-ph="appstore_click">Download</a>
            <button class="theme-toggle" id="theme-toggle" aria-label="Toggle theme">
                {MOON}
                {SUN}
            </button>
        </div>
    </div>
</nav>"""

FOOTER = """<footer>
    <div class="container">
        <div class="footer-inner">
            <div class="footer-brand">
                <img src="/assets/appicon.png" alt="Rise">
                <div class="footer-brand-text">
                    <h4>Rise</h4>
                    <p>Your morning ritual, reinvented.</p>
                </div>
            </div>
            <div class="footer-links">
                <a href="/guides/">Guides</a>
                <a href="/#faq">FAQ</a>
                <a href="/support/">Support</a>
                <a href="/terms.html">Terms of Use</a>
                <a href="/privacy.html">Privacy Policy</a>
                <a href="https://alarmclockplanner.com/" data-ph="crosssell_alarmplanner">Alarm Clock Planner</a>
            </div>
        </div>
        <p class="footer-copy">Made by Emils Ozols &copy; 2026 Rise</p>
    </div>
</footer>"""

def head(title, desc, canonical, og_type="article"):
    t, d = html.escape(title, quote=True), html.escape(desc, quote=True)
    return f"""<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{t}</title>
<meta name="description" content="{d}">
<link rel="canonical" href="{canonical}">
<meta name="apple-itunes-app" content="app-id={APP_ID}">
<meta name="theme-color" content="#D4882A">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="apple-touch-icon" href="/assets/appicon.png">
<link rel="stylesheet" href="/styles.css">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="Rise">
<meta property="og:title" content="{t}">
<meta property="og:description" content="{d}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{DOMAIN}/assets/ogshare.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{t}">
<meta name="twitter:description" content="{d}">
<meta name="twitter:image" content="{DOMAIN}/assets/ogshare.png">
{ANALYTICS}"""

def ld(obj):
    return f'<script type="application/ld+json">\n{json.dumps(obj, indent=2, ensure_ascii=False)}\n</script>'

def fig(src, alt, cap):
    return f"""<figure>
  <img src="/assets/{src}" alt="{alt}" loading="lazy" width="600" height="1203">
  <figcaption>{cap}</figcaption>
</figure>"""

def cross(text):
    return f"""<div class="cross-sell">
  <img src="/assets/alarmplanner-icon.png" alt="" width="44" height="44">
  <p>{text}</p>
</div>"""

# ------------------------------------------------------------------------------------------
# Guides. Facts every page may rely on (Rise 1.33):
# - Alarm: AlarmKit system alarm, rings through Silent and Focus. The alert has ONLY Stop, no
#   snooze button (removed 2026-09-26); an optional snooze lives on the Home screen.
# - iPhone app (TARGETED_DEVICE_FAMILY 1); installs on iPad in iPhone mode. iOS 26.2+.
# - Widgets: Home Screen only (systemSmall). Lock Screen = Live Activities, not widgets.
# - Restore Purchases is on the Pro screen (paywall), not a Settings row.
# - iCloud backup is a toggle in Settings; a new install offers Restore from Backup.
# - Stopping the alarm opens the wake-up screen: pick a focus length, start the session.
# - Focus: free 5/10/15 min, Pro 5-120 min + extend +5/+15/+30. Focus now on Home starts one
#   at any hour if today's session is not done yet (one session per day).
#   Live Activity on the Lock Screen + Dynamic Island (free).
# - Wake-up check (Pro): a second alarm "Are you still up?" 5, 10 or 20 min after the alarm,
#   only if no focus session has started; starting one moves it to tomorrow.
# - Streak: free number; Pro history + freezes (tapped manually, one per 7 days).
# - Wind Down (opens in the evening): sounds Fireplace, Space Ship, Storm, Waves, White Noise.
#   Free up to 10 min, Pro up to 30. Live Activity.
# - Reflection: prompt free, typing Pro. Titles: Beginner free, 45 more Pro. Early-wake titles
#   unlock by STARTING a focus session by 8/7/6/5/4 AM (Early Riser, Sun Chaser, Early Bird...).
# - iOS facts (checked 2026-10-01): iOS 26 Clock has per-alarm snooze 1-15 min (default 9) and
#   Snooze can be switched off; iOS 27 adds separate alarm volume only. Clock still has no date
#   alarms. Not every iPhone has a Dynamic Island.
# - Apple Health (Pro): wake time + mindful minutes. iCloud backup free.
# ------------------------------------------------------------------------------------------
PAGES = [
dict(
slug="how-to-stop-snoozing-your-alarm",
title="How to Stop Snoozing Your Alarm (and Actually Get Up)",
meta="Snoozing is a habit loop, not a character flaw. Why it happens, what helps, and how to give the first minute after your alarm a job so you stop hitting snooze.",
h1="How to Stop Snoozing Your Alarm and Actually Get Up",
lede="The alarm goes off, your thumb finds the snooze button before your brain is awake, and a few minutes later you do it again. Here is how to break the loop.",
quick="""<strong>Quick answer:</strong> Snoozing sticks because the moment after the alarm has no plan, so going back to sleep wins by default. Give that moment a job: put the phone out of reach, decide the night before what the first five minutes are, and use an alarm that leads straight into a short timed session, like <a href="/">Rise</a>, instead of back to the lock screen.""",
body=f"""
<h2>Why you keep hitting snooze</h2>
<p>Right after waking, the brain is in a state called sleep inertia: slower reaction times, foggy decisions, a strong pull back to sleep. That fog usually lasts 15 to 30 minutes, sometimes longer. It is exactly the window in which the snooze button asks you to make a decision, and a foggy brain picks the option that requires nothing.</p>
<p>Snoozing also does not buy you real rest. A snooze of a few minutes, nine by default on iPhone, is too short to get back into deep sleep, so what you collect is a series of interrupted light naps. Most people feel worse after three snoozes than they would have felt getting up on the first alarm.</p>

<h2>What actually helps</h2>
<ol>
  <li><strong>Move the phone.</strong> Charge it across the room. Walking to it does half the work of getting up.</li>
  <li><strong>Pick the first five minutes the night before.</strong> Read ten pages, stretch, write one line, sit with a coffee. A plan you made yesterday beats a decision you have to make now.</li>
  <li><strong>Make the first step tiny.</strong> "Go for a run" loses to the snooze button. "Five minutes of anything" usually wins.</li>
  <li><strong>Keep the wake time steady.</strong> The same time on most days, weekends within an hour or so, makes the alarm land in lighter sleep more often.</li>
  <li><strong>Get light early.</strong> Open the curtains or step outside. Light is the strongest signal your body clock has.</li>
</ol>

<h2>Give the alarm a next step</h2>
<p>The built-in Clock app gives you Stop or Snooze, and either way you land back on the lock screen. Rise was built around what comes after:</p>
<ol>
  <li>Set your wake-up alarm in Rise. It is a real system alarm, so it rings through Silent mode and Focus.</li>
  <li>The alarm has one button, Stop. There is no snooze on it. Stopping it opens Rise straight onto the wake-up screen with a focus timer, not onto your notifications.</li>
  <li>Pick a length, 5 minutes is enough on a hard morning, and start. The session runs on your Lock Screen as a Live Activity, so you can put the phone down.</li>
  <li>Finish it and your streak grows by a day. That small win is what you are trading the snooze for.</li>
</ol>
{fig("shot-wake.webp", "Rise wake-up screen after the alarm, with a focus length slider", "Stopping the alarm opens a short session, not your inbox.")}

<h2>Should you remove snooze completely?</h2>
<p>For some people, yes. If you snooze by reflex, an alarm with no snooze forces the decision once. In the Clock app you can switch Snooze off per alarm, and since iOS 26 you can also set its length from 1 to 15 minutes. For others a single snooze is a buffer they actually use. The useful test is simple: if you snooze more than once on most days, the snooze is not helping you wake up, it is postponing the decision.</p>
<div class="note-box">If you tend to stop the alarm and drift off again, Rise Pro can ring a second time, 5, 10 or 20 minutes later, but only if you have not started your session yet. See <a href="/guides/how-to-not-fall-back-asleep-after-alarm/">how to stop falling back asleep after your alarm</a>.</div>
""",
cross=f"""Need a wake-up alarm for one specific date, like an early flight? <a href="{AP}/guides/alarm-for-a-flight/" data-ph="crosssell_alarmplanner">Alarm Clock Planner</a>, from the same maker, sets alarms for any future date, which the Clock app cannot.""",
related=["how-to-not-fall-back-asleep-after-alarm", "stop-checking-phone-in-the-morning", "build-a-morning-routine-that-sticks"],
cta_h="Make the alarm the start of something",
cta_p="Alarm, then a short focus session. Free to try.",
),
dict(
slug="how-to-not-fall-back-asleep-after-alarm",
title="How to Not Fall Back Asleep After Your Alarm",
meta="You turn the alarm off and wake up an hour later. Why it happens, and how a wake-up check alarm catches you if you drift back to sleep.",
h1="How to Not Fall Back Asleep After Your Alarm",
lede="You were sure you got up. Then you open your eyes and it is 8:40. Turning the alarm off and falling straight back asleep is common, and there is a simple safety net for it.",
quick="""<strong>Quick answer:</strong> Get vertical within a minute of the alarm, and keep a backup that only rings if you did not actually get going. In <a href="/">Rise</a>, the wake-up check (Pro) is a second alarm 5, 10 or 20 minutes after your wake-up alarm that is cancelled the moment you start your morning session, so it only rings if you went back to sleep.""",
body=f"""
<h2>Why it happens</h2>
<p>Stopping an alarm takes almost no awareness. Your hand can do it while your brain is still mostly asleep, which is why some people have no memory of turning it off at all. Lying back down "for a second" in that state usually ends in real sleep, because nothing else is asking for your attention.</p>

<h2>Habits that help</h2>
<ul>
  <li><strong>Sit up before you decide anything.</strong> Feet on the floor first, thinking second.</li>
  <li><strong>Put the phone out of reach</strong> so stopping the alarm means standing up.</li>
  <li><strong>Have one small thing to do next</strong>, decided the night before, so the minute after the alarm is not empty.</li>
  <li><strong>Avoid a second alarm that always rings.</strong> A backup that goes off every day, even when you are already up, trains you to ignore it.</li>
</ul>

<h2>A backup alarm that only rings when you need it</h2>
<p>The trouble with setting two alarms in the Clock app is that the second one rings every morning, including the mornings you got up fine. Rise's wake-up check works the other way round:</p>
<ol>
  <li>Turn on the wake-up check from the Home screen, and pick 5, 10 or 20 minutes in Settings.</li>
  <li>Your alarm rings. You stop it and start your morning focus session.</li>
  <li>Starting the session moves the check to tomorrow. Nothing else rings.</li>
  <li>If you stopped the alarm and fell back asleep instead, the check rings: "Are you still up?"</li>
</ol>
<p>The alarm itself has no snooze button. If you set a snooze on purpose from Rise's Home screen, the check waits until after it, so the two never ring on top of each other. The wake-up check is part of Rise Pro.</p>
{fig("shot-home.webp", "Rise Home screen with the alarm time and the wake-up check toggle", "The wake-up check sits next to your alarm on the Home screen.")}

<h2>Does it ring on Silent?</h2>
<p>Yes. Both the wake-up alarm and the wake-up check are system alarms built on Apple's AlarmKit, so they ring in Silent mode and through Do Not Disturb and Focus, the same way the Clock app's alarms do.</p>
""",
cross=None,
related=["how-to-stop-snoozing-your-alarm", "build-a-morning-routine-that-sticks", "focus-timer-lock-screen-iphone"],
cta_h="A backup alarm that knows you got up",
cta_p="Rings again only if you went back to sleep. Part of Rise Pro, with a 7-day free trial on the yearly plan.",
),
dict(
slug="stop-checking-phone-in-the-morning",
title="How to Stop Checking Your Phone First Thing in the Morning",
meta="The phone that wakes you up is also the one with every notification on it. Practical ways to stop doomscrolling in bed and start the morning on your own terms.",
h1="How to Stop Checking Your Phone First Thing in the Morning",
lede="The alarm is on your phone, so the first thing you touch every day is the device with every email, message and feed on it. Ten minutes later you are still in bed.",
quick="""<strong>Quick answer:</strong> You do not need to ban the phone, you need the first thing it shows you to be something other than your feeds. Keep notifications out of the first half hour with a Focus mode, and use an alarm that opens onto a short timed session instead of the lock screen, which is what <a href="/">Rise</a> does.""",
body=f"""
<h2>Why the morning scroll is so sticky</h2>
<p>Checking the phone right after waking feels like getting a head start. In practice you hand the first part of your day to other people's priorities: an email you cannot answer yet, news you cannot change, a feed designed to keep you there. It is also very easy, which is the main reason it wins.</p>

<h2>Practical ways to break it</h2>
<ol>
  <li><strong>Set a morning Focus mode.</strong> In Settings, Focus, create one that silences notifications and schedule it to end at, say, 7:30. Alarms still ring through Focus.</li>
  <li><strong>Charge the phone out of reach</strong>, so picking it up is a decision, not a reflex.</li>
  <li><strong>Remove the apps you open by default</strong> from the first Home Screen page.</li>
  <li><strong>Replace, do not just remove.</strong> "No phone" leaves a gap. "Ten pages of a book" or "ten minutes of stretching" fills it.</li>
</ol>

<h2>Use the phone to get off the phone</h2>
<p>Since the alarm lives on the phone anyway, it can point you somewhere better. In Rise:</p>
<ol>
  <li>Your alarm rings and you stop it.</li>
  <li>Rise opens onto a focus timer instead of your notifications. Choose a length and start.</li>
  <li>The countdown stays on the Lock Screen as a Live Activity, and in the Dynamic Island on iPhones that have one, so the phone can go face down on the table.</li>
  <li>When the session ends, the day is yours. You checked the phone exactly once, to start the timer.</li>
</ol>
{fig("shot-timer.webp", "Rise focus session timer running in the morning", "A timed session gives the first minutes a job.")}

<h2>What to do in that first session</h2>
<p>Anything that is yours and not a feed: read, journal, stretch, meditate, plan the day on paper, drink a coffee by the window. Five minutes counts. The point is that the day starts with something you chose.</p>
""",
cross=None,
related=["how-to-stop-snoozing-your-alarm", "focus-timer-lock-screen-iphone", "build-a-morning-routine-that-sticks"],
cta_h="Start the day before the feed does",
cta_p="Alarm, then a focus timer. Short sessions are free.",
),
dict(
slug="focus-timer-lock-screen-iphone",
title="How to Keep a Focus Timer on Your iPhone Lock Screen",
meta="See your focus or Pomodoro countdown on the Lock Screen and Dynamic Island without unlocking the phone. How Live Activity timers work and how to set one up.",
h1="How to Keep a Focus Timer on Your iPhone Lock Screen",
lede="A timer you have to unlock the phone to check is a timer that pulls you back into the phone. A Lock Screen countdown solves that.",
quick="""<strong>Quick answer:</strong> Timers that use Live Activities show a live countdown on the Lock Screen, and in the Dynamic Island on iPhones that have one. The Clock app's timer does this for a single countdown. For a focus session with its own length, streak and history, <a href="/">Rise</a> runs its focus timer as a Live Activity, free, for 5 to 120 minutes.""",
body=f"""
<h2>What a Live Activity is</h2>
<p>Live Activities are the live-updating panels iOS shows on the Lock Screen and in the Dynamic Island: a delivery on its way, a sports score, a running timer. They update without you opening the app, which makes them ideal for a focus timer: you can glance at the time left without unlocking anything.</p>

<h2>The quick option: the Clock app timer</h2>
<p>Start a timer in the Clock app and it appears on the Lock Screen. That is enough for a single countdown. It does not know what the time was for, so there is no history, no streak, and nothing that connects the session to the rest of your day.</p>

<h2>A focus timer built for it</h2>
<ol>
  <li>Start from your morning alarm, or tap Focus now on the Home screen at any other hour (one session per day).</li>
  <li>Choose a length with the slider. 5, 10 and 15 minutes are free; Pro goes up to 120 and lets you extend a running session by 5, 15 or 30 minutes.</li>
  <li>Start, then lock the phone. The countdown keeps running on the Lock Screen, and in the Dynamic Island if your iPhone has one.</li>
  <li>When it ends, it counts as your session for the day and, with Pro, is saved as mindful minutes in Apple Health.</li>
</ol>
{fig("shot-timer.webp", "Rise focus timer counting down during a session", "The same countdown follows you to the Lock Screen.")}

<h2>Does Rise do Pomodoro?</h2>
<p>Rise runs one focused block at a time, any length you pick, rather than a fixed 25/5 Pomodoro cycle. If you like Pomodoro, set 25 minutes, take your break, and start another. Many people find that one longer morning block suits deep work better than strict intervals.</p>
""",
cross=None,
related=["stop-checking-phone-in-the-morning", "5am-club-routine", "wind-down-routine-before-bed"],
cta_h="A focus timer that lives on your Lock Screen",
cta_p="Live Activity countdown, free for sessions up to 15 minutes.",
),
dict(
slug="build-a-morning-routine-that-sticks",
title="How to Build a Morning Routine That Actually Sticks",
meta="Most morning routines fail in week two because they start too big. A small, repeatable routine, a streak you can keep, and what to do on the days you miss.",
h1="How to Build a Morning Routine That Actually Sticks",
lede="The ten-step routine from a video lasts four days. Here is how to build one that is still running in a month.",
quick="""<strong>Quick answer:</strong> Start with one small block, five to fifteen minutes, at the same time every day, tied to your alarm. Track it so a missed day is visible, allow yourself a planned day off without losing the chain, and only add more once the small version runs on autopilot. <a href="/">Rise</a> is built around exactly that loop: alarm, short session, streak.""",
body=f"""
<h2>Why most routines fail</h2>
<p>They start at the finish line. Cold shower, workout, journal, meditation, reading, all before 7 AM, on day one. It works while motivation is high, and motivation is always highest on day one. The first bad night of sleep breaks it, and an all-or-nothing routine has no small version to fall back to.</p>

<h2>A routine that survives a bad week</h2>
<ol>
  <li><strong>Anchor it to the alarm.</strong> The alarm already happens every day. Make the routine the thing that happens next.</li>
  <li><strong>Start with one block.</strong> One activity, five to fifteen minutes. Reading, journaling, stretching, planning.</li>
  <li><strong>Keep the time fixed, not the content.</strong> Some days it is reading, some days it is sitting quietly. Showing up is the habit.</li>
  <li><strong>Make it visible.</strong> A streak turns "I usually do it" into a number you do not want to reset.</li>
  <li><strong>Plan for misses.</strong> You will miss days. The routine that survives is the one where one miss does not mean starting from zero.</li>
  <li><strong>Grow it slowly.</strong> Add five minutes or one activity at a time, only when the current version feels easy.</li>
</ol>

<h2>How Rise sets this up</h2>
<p>Rise turns the steps above into the app's default flow:</p>
<ul>
  <li>Your alarm rings and leads straight into a focus session of the length you pick.</li>
  <li>Each completed morning adds a day to your streak, shown in the app and in a Home Screen widget.</li>
  <li>With Pro, you can freeze your streak once a week: tap the freeze on a day you cannot do your session, and a sick day does not wipe out a month.</li>
  <li>Milestones unlock titles like Routinist or Early Bird, shown in your morning greeting. The first one is free, the rest come with Pro.</li>
</ul>
{fig("shot-streak.webp", "Rise progress screen with a 30-day streak calendar", "A streak makes the habit visible, and freezes keep one bad day from erasing it.")}

<h2>How long until it feels automatic?</h2>
<p>Longer than the popular "21 days". Research on habit formation puts the typical range at a couple of months, with wide variation between people and habits. That is another argument for starting small: a routine you can keep for 60 days beats an ambitious one you keep for 6.</p>
""",
cross=None,
related=["how-to-stop-snoozing-your-alarm", "5am-club-routine", "75-hard-morning-routine"],
cta_h="A morning routine small enough to keep",
cta_p="Alarm, focus session, streak. The basics are free.",
),
dict(
slug="75-hard-morning-routine",
title="A 75 Hard Morning Routine That Fits Before Work",
meta="How to fit 75 Hard into your mornings: the daily tasks, which ones to do before work, and how to protect the reading block with a timer and a streak.",
h1="A 75 Hard Morning Routine That Fits Before Work",
lede="75 Hard is mostly a scheduling problem. Two workouts, the reading, the water and the photo all have to fit around a normal day, every day, for 75 days.",
quick="""<strong>Quick answer:</strong> Do the parts that are easiest to lose later in the day first: one workout and the 10 pages of reading. Wake at a fixed time, train, then read in a timed block before you open your phone. <a href="/">Rise</a> handles the wake-up alarm and the reading block, and its streak shows your run of mornings. It does not track the other 75 Hard tasks.""",
body=f"""
<h2>The daily tasks</h2>
<p>The program, created by Andy Frisella, asks for the same list every day for 75 days, with a restart from day one if you miss anything:</p>
<ul>
  <li>Two 45-minute workouts, one of them outdoors.</li>
  <li>Follow a diet of your choice, with no cheat meals and no alcohol.</li>
  <li>Drink a gallon of water.</li>
  <li>Read 10 pages of a non-fiction book.</li>
  <li>Take a progress photo.</li>
</ul>

<h2>What to do in the morning</h2>
<p>Evenings are where 75 Hard attempts fail: late meetings, plans with friends, being tired. Moving tasks into the morning removes most of that risk.</p>
<ol>
  <li><strong>Fixed wake time.</strong> Work back from your first commitment. One 45-minute workout plus reading needs about 75 minutes with a shower.</li>
  <li><strong>Workout one.</strong> Outdoors if you can, since the outdoor one is the hardest to fit in after dark.</li>
  <li><strong>Read 10 pages in a timed block.</strong> Ten pages takes most people 15 to 20 minutes. Do it before the phone gets a chance to pull you in.</li>
  <li><strong>Progress photo and the first bottle of water</strong> while you are already up.</li>
</ol>
<p>That leaves the second workout and the rest of the water for later, which is far easier to rescue on a busy day than reading at midnight.</p>

<h2>Using Rise for the reading block</h2>
<ol>
  <li>Set your wake-up alarm in Rise. It rings through Silent mode.</li>
  <li>After your workout, start a focus session sized for your 10 pages, for example 20 minutes. Sessions over 15 minutes need Pro.</li>
  <li>The timer runs on the Lock Screen, so the phone can stay face down while you read.</li>
  <li>Each completed morning adds to your streak, a simple visual of your run.</li>
</ol>
{fig("shot-timer.webp", "Rise focus timer used as a reading block", "A timed block for the 10 pages, before the phone gets a say.")}
<div class="note-box">Be honest with the streak. 75 Hard has no freezes: a missed task means day one. Rise Pro's streak freeze is for normal routines, so leave it unused during the challenge.</div>
""",
cross=f"""Training alarms piling up? <a href="{AP}/guides/group-organize-alarms-iphone/" data-ph="crosssell_alarmplanner">Alarm Clock Planner</a>, from the same maker, groups alarms with tags, so a whole group can be switched off for a rest week and back on after.""",
related=["5am-club-routine", "build-a-morning-routine-that-sticks", "focus-timer-lock-screen-iphone"],
cta_h="Protect the reading block",
cta_p="Wake-up alarm, then a timed session. Free to try.",
),
dict(
slug="5am-club-routine",
title="The 5AM Club Routine: 20/20/20 With an Alarm and a Timer",
meta="The 5AM Club's 20/20/20 formula explained: move, reflect, grow. How to set it up on iPhone with one alarm and timed blocks, and how to make 5 AM realistic.",
h1="The 5AM Club Routine: 20/20/20 With an Alarm and a Timer",
lede="Robin Sharma's 5AM Club splits the first hour into three 20-minute blocks. The structure is simple. Getting up at 5 is the hard part.",
quick="""<strong>Quick answer:</strong> The 20/20/20 formula is 20 minutes of intense movement, 20 minutes of reflection (journaling, planning, meditation) and 20 minutes of growth (reading or learning), starting at 5 AM. Set one alarm, then time the hour. In <a href="/">Rise</a>, the alarm opens straight onto a focus timer, and the streak tracks how many mornings you made it.""",
body=f"""
<h2>The 20/20/20 formula</h2>
<ul>
  <li><strong>Move (5:00 to 5:20).</strong> Something that makes you sweat. It clears the sleep fog faster than coffee.</li>
  <li><strong>Reflect (5:20 to 5:40).</strong> Journal, plan the day, meditate, or just think without input.</li>
  <li><strong>Grow (5:40 to 6:00).</strong> Read, study, listen to something that teaches you.</li>
</ul>

<h2>Making 5 AM realistic</h2>
<p>Most failed attempts are a sleep problem, not a willpower problem. Getting up at 5 with seven hours of sleep means lights out around 10.</p>
<ol>
  <li><strong>Move the wake time gradually.</strong> 15 minutes earlier every few days is far easier than jumping from 7 to 5.</li>
  <li><strong>Fix the bedtime first.</strong> An evening wind-down routine makes the earlier night realistic. See <a href="/guides/wind-down-routine-before-bed/">how to wind down before bed</a>.</li>
  <li><strong>Prepare the night before.</strong> Workout clothes out, journal open, book on the table.</li>
  <li><strong>Keep weekends close.</strong> Sleeping until 9 on Saturday makes Monday at 5 feel like jet lag.</li>
</ol>

<h2>Setting it up in Rise</h2>
<ol>
  <li>Set your alarm for 5:00 in Rise. It rings in Silent mode and through Focus.</li>
  <li>Stop it and the wake-up screen opens with a focus timer. Sessions over 15 minutes need Pro.</li>
  <li>Rise runs one session per morning, so time the whole hour as one 60-minute session and switch activity every 20 minutes.</li>
  <li>The streak counts every morning you complete, and with Pro the early titles mark starting a session by 8, 7, 6, 5 and 4 AM.</li>
</ol>
{fig("shot-ringing.webp", "Rise alarm ringing on the Lock Screen at 5:00", "One alarm at 5, then the first timed block.")}

<h2>Do you have to wake at exactly 5?</h2>
<p>No. The value is in having a protected hour before the day's demands start, not in the number on the clock. A 6:30 version of the same structure works the same way if that is when your house is quiet.</p>
""",
cross=f"""Need a one-off 5 AM alarm on a specific date, like race day? <a href="{AP}/guides/set-alarm-for-specific-date-iphone/" data-ph="crosssell_alarmplanner">Alarm Clock Planner</a>, from the same maker, sets alarms for any future date.""",
related=["75-hard-morning-routine", "build-a-morning-routine-that-sticks", "wind-down-routine-before-bed"],
cta_h="Your 5 AM hour, timed",
cta_p="One alarm, then focus sessions. Free to try.",
),
dict(
slug="wind-down-routine-before-bed",
title="A Simple Wind-Down Routine Before Bed",
meta="A good morning starts the night before. A simple wind-down routine for adults: what to stop, what to do instead, and a timed session with calming sounds.",
h1="A Simple Wind-Down Routine Before Bed",
lede="Most of a good morning is decided the night before. If you go from bright screens to lights off in one step, falling asleep takes longer and the alarm hurts more.",
quick="""<strong>Quick answer:</strong> Give the last 10 to 30 minutes before sleep a fixed shape: lights down, phone away, one calm activity, at roughly the same time every night. A timed session with ambient sound makes it easy to stick to. <a href="/">Rise</a>'s Wind Down does that, free for up to 10 minutes and up to 30 with Pro.""",
body=f"""
<h2>Why winding down helps</h2>
<p>Your body needs a transition between the day and sleep. Bright light, work email and fast feeds keep you alert at exactly the moment you are trying to switch off. A short, repeated routine becomes a cue on its own: after a couple of weeks, starting it is enough to make you feel sleepy.</p>

<h2>A simple routine</h2>
<ol>
  <li><strong>Pick a start time.</strong> Count back from your alarm. For a 6:30 alarm and 7.5 hours of sleep, wind down from about 10:30.</li>
  <li><strong>Dim the lights</strong> and turn on Night Shift or a Sleep Focus on the phone.</li>
  <li><strong>Put work away.</strong> Close the laptop, write tomorrow's top task on paper so it stops circling.</li>
  <li><strong>One calm activity</strong> for 10 to 30 minutes: reading on paper, stretching, breathing, or just sitting with a calm sound.</li>
  <li><strong>Lights out at the same time</strong> most nights.</li>
</ol>

<h2>Wind Down in Rise</h2>
<ol>
  <li>In the evening, open Rise and tap Wind Down on the Home screen.</li>
  <li>Pick a sound: fireplace, storm, waves, white noise or space ship.</li>
  <li>Choose a length. Up to 10 minutes is free; Pro offers up to 30.</li>
  <li>The session runs on the Lock Screen as a Live Activity, so you can put the phone down and let the sound play.</li>
</ol>
{fig("shot-winddown.webp", "Rise Wind Down evening session with ambient sound", "A timed evening session with calming sound.")}

<h2>Should the phone be in the bedroom?</h2>
<p>If it is your alarm, it probably will be. Then make it boring: Sleep Focus on, notifications off, face down, out of reach. The alarm will still ring.</p>
""",
cross=None,
related=["5am-club-routine", "how-to-stop-snoozing-your-alarm", "build-a-morning-routine-that-sticks"],
cta_h="End the day on purpose",
cta_p="Wind Down with ambient sound. Free for up to 10 minutes.",
),
]

TITLES = {p["slug"]: p["h1"] for p in PAGES}

def related_html(slugs):
    items = "\n".join(f'      <li><a href="/guides/{s}/">{TITLES[s]}</a></li>' for s in slugs)
    return f"""<div class="related">
    <h2>Related guides</h2>
    <ul>
{items}
    </ul>
    <p><a href="/guides/">All guides</a></p>
  </div>"""

def cta_html(h, p, ct=CT_GUIDE):
    return f"""<a class="article-cta" href="{store_url(ct)}" data-ph="appstore_click" aria-label="Download Rise on the App Store">
    <h2>{h}</h2>
    <p>{p}</p>
    <span class="btn">Download Rise for iPhone</span>
  </a>"""

def article_ld(p, canonical):
    return ld({
        "@context": "https://schema.org", "@type": "Article",
        "headline": p["h1"], "description": p["meta"],
        "image": f"{DOMAIN}/assets/ogshare.png",
        "datePublished": TODAY, "dateModified": TODAY,
        "author": {"@type": "Person", "name": "Emils Ozols", "url": "https://ozols.dev"},
        "publisher": {"@type": "Organization", "name": "Rise", "logo": {"@type": "ImageObject", "url": f"{DOMAIN}/assets/appicon.png"}},
        "mainEntityOfPage": canonical,
    }) + "\n" + ld({
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{DOMAIN}/"},
            {"@type": "ListItem", "position": 2, "name": "Guides", "item": f"{DOMAIN}/guides/"},
            {"@type": "ListItem", "position": 3, "name": p["h1"], "item": canonical},
        ]})

def write(rel, text):
    path = os.path.join(SITE, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(text)
    print("wrote", rel)

def page(head_html, body, ct):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
{head_html}
</head>
<body>

{nav(ct)}

<main class="page-main">
{body}
</main>

{FOOTER}
{PAGE_JS}
</body>
</html>
"""

for p in PAGES:
    canonical = f"{DOMAIN}/guides/{p['slug']}/"
    body = f"""<article class="article">
  <div class="breadcrumb" role="navigation" aria-label="Breadcrumb"><a href="/">Home</a> › <a href="/guides/">Guides</a> › {p['h1']}</div>
  <h1>{p['h1']}</h1>
  <p class="lede">{p['lede']}</p>
  <div class="quick-answer"><p>{p['quick']}</p></div>
{p['body']}
{cross(p['cross']) if p['cross'] else ''}
{cta_html(p['cta_h'], p['cta_p'])}
{related_html(p['related'])}
</article>"""
    write(f"guides/{p['slug']}/index.html",
          page(head(p["title"], p["meta"], canonical) + "\n" + article_ld(p, canonical), body, CT_GUIDE))

# ---------- hub ----------
CLUSTERS = [
    ("Getting out of bed",
     """The hardest part of any morning routine is the first minute after the alarm. These guides cover why
     snoozing and drifting back to sleep happen, and how to give that minute a next step.""",
     ["how-to-stop-snoozing-your-alarm", "how-to-not-fall-back-asleep-after-alarm"]),
    ("The first hour",
     """What happens in the first hour decides whether the day starts on your terms or your inbox's. Keeping
     the phone from taking over, and timing a focused block you can see without unlocking anything.""",
     ["stop-checking-phone-in-the-morning", "focus-timer-lock-screen-iphone"]),
    ("Morning routines",
     """From a five-minute habit to a full 5 AM hour: how to build a routine that survives a bad week, and how
     two popular formats fit into a real morning.""",
     ["build-a-morning-routine-that-sticks", "5am-club-routine", "75-hard-morning-routine"]),
    ("The night before",
     """A good morning starts the evening before. A short, repeatable wind-down makes the earlier bedtime, and
     the earlier alarm, realistic.""",
     ["wind-down-routine-before-bed"]),
]
BY = {p["slug"]: p for p in PAGES}
_clustered = [s for _, _, ss in CLUSTERS for s in ss]
assert sorted(_clustered) == sorted(BY), f"hub out of sync: {set(BY) ^ set(_clustered)}"

# Shared by the hub and the homepage FAQ (index.html, between the FAQ markers).
HUB_FAQ = [
    ("Does Rise's alarm ring on Silent mode?",
     """Yes. Rise uses Apple's AlarmKit, the framework for real system alarms, so your alarm rings in Silent
     mode and through Do Not Disturb and Focus. It needs iOS 26.2 or later.""",
     "how-to-not-fall-back-asleep-after-alarm"),
    ("What happens after the alarm rings?",
     """The alarm has one button, Stop, and stopping it opens Rise's wake-up screen with a focus timer. Pick a length and start a session:
     read, journal, stretch, or just sit with a coffee. Finishing it adds a day to your streak.""",
     "how-to-stop-snoozing-your-alarm"),
    ("Can I use the focus timer outside the morning?",
     """Yes. If you have not had a session yet today, Focus now on the Home screen starts one at any hour.""",
     "focus-timer-lock-screen-iphone"),
    ("What is the wake-up check?",
     """A second alarm, 5, 10 or 20 minutes after your wake-up alarm, that rings only if you have not started
     your morning session. Starting the session cancels it for the day. It is part of Rise Pro.""",
     "how-to-not-fall-back-asleep-after-alarm"),
    ("What is free and what is Pro?",
     """Free: the alarm, focus sessions of 5, 10 or 15 minutes, Wind Down up to 10 minutes, your streak, the
     Beginner title, Live Activities, the Home Screen widgets and iCloud backup. Pro adds sessions up to 120 minutes, the wake-up check,
     streak history and freezes, reflections, all titles, Apple Health and longer Wind Down. Pro is a yearly
     plan with a 7-day free trial, or a one-time Lifetime purchase.""",
     None),
    ("What if I miss a morning?",
     """Your streak resets. With Pro you can freeze it once a week: tap the freeze on a day you cannot make it and the streak holds.""",
     "build-a-morning-routine-that-sticks"),
    ("Does Rise work on iPad?",
     """Rise is designed for iPhone. You can also install it on an iPad, where it runs as an iPhone app.""",
     None),
    ("Do I need an account?",
     """No. There is no sign-up. Your routine data stays on your device, with an optional backup to your own iCloud.""",
     None),
]

def faq_details(items, indent="      "):
    out = []
    for q, a, slug in items:
        link = f' <a href="/guides/{slug}/">Read the guide</a>' if slug else ""
        out.append(f"""{indent}<details>
{indent}  <summary>{q}</summary>
{indent}  <p>{" ".join(a.split())}{link}</p>
{indent}</details>""")
    return "\n".join(out)

def faq_ld():
    return ld({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": " ".join(a.split())}}
        for q, a, _ in HUB_FAQ]})

def cluster_html(h, intro, slugs):
    cards = "\n".join(f"""      <a class="guide-card" href="/guides/{s}/">
        <h3>{BY[s]['h1']}</h3>
        <p>{BY[s]['lede'].split('. ')[0].rstrip('.')}.</p>
        <span class="more">Read the guide</span>
      </a>""" for s in slugs)
    return f"""<div class="container guide-cluster">
    <h2>{h}</h2>
    <p class="cluster-intro">{" ".join(intro.split())}</p>
    <div class="guide-grid">
{cards}
    </div>
  </div>"""

hub_body = f"""<div class="container hub-head">
    <div class="breadcrumb" role="navigation" aria-label="Breadcrumb"><a href="/">Home</a> › Guides</div>
    <h1>Morning Routine Guides</h1>
    <p>Practical guides to the first hour of the day: getting out of bed on the first alarm, keeping the phone
    from taking over, timing a focus block, and building a routine that survives a bad week.</p>
  </div>
{chr(10).join(cluster_html(*c) for c in CLUSTERS)}
  <section class="section">
    <div class="container">
      <h2 class="section-title" style="text-align:center;margin-bottom:28px">Common questions</h2>
      <div class="faq-list">
{faq_details(HUB_FAQ)}
      </div>
      <div class="container" style="max-width:780px;padding:0">
{cross(f'Need an alarm for a specific date, like a flight or an appointment, rather than a daily wake-up? <a href="{AP}/" data-ph="crosssell_alarmplanner">Alarm Clock Planner</a>, from the same maker, sets alarms for any future date.')}
      </div>
    </div>
  </section>"""
hub_ld = ld({"@context": "https://schema.org", "@type": "CollectionPage", "name": "Morning Routine Guides",
             "description": "Guides to waking up, the first hour of the day, focus timers and morning routines.",
             "url": f"{DOMAIN}/guides/"})
write("guides/index.html", page(
    head("Morning Routine Guides: Wake Up, Focus, Build the Habit | Rise",
         "Guides to getting up on the first alarm, keeping your phone from taking over the morning, focus timers on the Lock Screen, and routines like the 5AM Club and 75 Hard.",
         f"{DOMAIN}/guides/", og_type="website") + "\n" + hub_ld, hub_body, CT_GUIDE))

# ---------- support ----------
SUPPORT = [
    ("My alarm did not ring",
     """Check that Rise still has permission to set alarms, in the iPhone Settings app under Rise. Alarms ring in Silent mode and
     through Focus, but not when the phone is off or the battery is empty. If it still did not ring, email us the date,
     time and your iOS version."""),
    ("How do I restore my purchase?",
     """Open the Rise Pro screen, for example from the upgrade option in Rise's Settings, and tap Restore at the bottom. Use the same Apple Account you bought Pro with."""),
    ("How do I cancel the free trial or subscription?",
     """In the iPhone Settings app, tap your name, then Subscriptions, then Rise. Cancel at least a day before the
     trial ends and you will not be charged. Rise shows the days left in its own Settings too."""),
    ("How do I move Rise to a new iPhone?",
     """Turn on iCloud backup in Rise's Settings on the old phone. On the new iPhone, signed in to the same Apple
     Account, install Rise and tap Restore from Backup when it offers it."""),
    ("Can I get a refund?",
     """Refunds for App Store purchases are handled by Apple at reportaproblem.apple.com."""),
]
support_body = f"""<article class="article">
  <div class="breadcrumb" role="navigation" aria-label="Breadcrumb"><a href="/">Home</a> › Support</div>
  <h1>Rise Support</h1>
  <p class="lede">Questions, bugs or ideas: email <a href="mailto:info@risemorning.app">info@risemorning.app</a>. Rise is made by one person, so replies come from the developer directly, usually within a day or two.</p>
  <div class="faq-list">
{faq_details([(q, a, None) for q, a in SUPPORT])}
  </div>
  <p style="margin-top:28px">More answers in the <a href="/#faq">FAQ</a> and the <a href="/guides/">guides</a>.</p>
</article>"""
write("support/index.html", page(head("Rise Support", "Help with Rise: alarms that did not ring, restoring purchases, cancelling a trial, moving to a new iPhone.", f"{DOMAIN}/support/", og_type="website"), support_body, CT_HOME))

# ---------- 404 ----------
write("404.html", page(head("Page not found | Rise", "This page does not exist.", f"{DOMAIN}/404.html", og_type="website"),
      """<article class="article">
  <h1>This page overslept</h1>
  <p class="lede">It does not exist, or it moved. Try the <a href="/">home page</a> or the <a href="/guides/">guides</a>.</p>
</article>""", CT_HOME).replace('<meta name="viewport"', '<meta name="robots" content="noindex">\n<meta name="viewport"'))

# ---------- homepage injections ----------
idx_path = os.path.join(SITE, "index.html")
idx = open(idx_path).read()
def inject(text, name, content):
    a, b = f"<!-- {name}:START -->", f"<!-- {name}:END -->"
    assert a in text and b in text, f"index.html missing {name} markers"
    return re.sub(re.escape(a) + r".*?" + re.escape(b), lambda _: f"{a}\n{content}\n{b}", text, flags=re.S)

home_guides = "\n".join(f"""            <a class="guide-card" href="/guides/{s}/">
                <h3>{BY[s]['h1']}</h3>
                <span class="more">Read the guide</span>
            </a>""" for s in ["how-to-stop-snoozing-your-alarm", "how-to-not-fall-back-asleep-after-alarm",
                               "stop-checking-phone-in-the-morning", "build-a-morning-routine-that-sticks",
                               "5am-club-routine", "wind-down-routine-before-bed"])
idx = inject(idx, "GUIDES", home_guides)
idx = inject(idx, "FAQ", faq_details(HUB_FAQ, indent="            "))
idx = inject(idx, "FAQLD", faq_ld())
open(idx_path, "w").write(idx)
print("updated index.html (guides, faq, faq json-ld)")

# ---------- sitemap / robots ----------
urls = [("/", "1.0"), ("/guides/", "0.8")] + [(f"/guides/{p['slug']}/", "0.7") for p in PAGES] + \
       [("/support/", "0.4"), ("/terms.html", "0.2"), ("/privacy.html", "0.2")]
sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for u, pr in urls:
    sm.append(f"  <url><loc>{DOMAIN}{u}</loc><lastmod>{TODAY}</lastmod><priority>{pr}</priority></url>")
sm.append("</urlset>")
write("sitemap.xml", "\n".join(sm) + "\n")
write("robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {DOMAIN}/sitemap.xml\n")
