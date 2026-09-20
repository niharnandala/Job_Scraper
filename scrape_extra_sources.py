#!/usr/bin/env python3
"""Free public job watchers for Wellfound and Y Combinator, India-focused."""
import html, json, os, re
from datetime import datetime, timezone, timedelta
from urllib.request import Request, urlopen

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "output")
LOOKBACK_DAYS = 2
AI_RE = re.compile(r"\b(ai|artificial intelligence|machine learning|ml|llm|genai|generative ai|rag|nlp|agentic ai|ai agent|forward deployed)\b", re.I)
TARGET_RE = re.compile(r"\b(india|bengaluru|bangalore|hyderabad|chennai|pune|mumbai|delhi|gurgaon|gurugram|noida|kolkata|ahmedabad|jaipur|kochi)\b|remote", re.I)
BAD_RE = re.compile(r"\b(senior|sr\.?|staff|principal|lead|director|head of|architect|manager|internship|intern)\b", re.I)
ENTRY_RE = re.compile(r"\b(0|1|2)\s*(?:\+\s*)?(?:years?|yrs?)\b|\b(fresher|entry[- ]level|junior|new grad|graduate)\b", re.I)
EXPERIENCE_HIGH_RE = re.compile(r"\b(?:3|4|5|6|7|8|9|10|1[1-9])\+?\s*(?:years?|yrs?)\b", re.I)
ROLE_RE = re.compile(r"\b(ai|artificial intelligence|ml|machine learning|llm|genai|generative ai|rag|nlp|agentic ai|forward deployed|backend engineer|software engineer)\b", re.I)

def fetch(url):
    req = Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/xhtml+xml"})
    with urlopen(req, timeout=25) as r:
        return r.read().decode("utf-8", "ignore")

def strip_tags(s):
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s))).strip()

def clean_url(u):
    return html.unescape(u).replace("&amp;", "&")

def parse_age(s):
    s = s.lower()
    m = re.search(r"(\d+)\s*(hour|day|week|month)s?\s*ago", s)
    if not m: return ""
    n, unit = int(m.group(1)), m.group(2)
    if unit == "hour": return datetime.now(timezone.utc).date().isoformat()
    if unit == "day": return (datetime.now(timezone.utc)-timedelta(days=n)).date().isoformat()
    if unit == "week": return (datetime.now(timezone.utc)-timedelta(days=7*n)).date().isoformat()
    return (datetime.now(timezone.utc)-timedelta(days=30*n)).date().isoformat()

def eligible(title, location, context):
    text = f"{title} {context}"
    if not AI_RE.search(text): return False
    if not TARGET_RE.search(location): return False
    if BAD_RE.search(title): return False
    if EXPERIENCE_HIGH_RE.search(context) and not ENTRY_RE.search(context): return False
    return bool(ROLE_RE.search(title) or AI_RE.search(context))

def wellfound():
    jobs = []
    urls = [
        "https://wellfound.com/role/l/ai-engineer/india",
        "https://wellfound.com/role/l/machine-learning-engineer/india",
        "https://wellfound.com/role/l/backend-engineer/india",
        "https://wellfound.com/role/l/software-engineer/india",
    ]
    seen = set()
    for page_url in urls:
        try: raw = fetch(page_url)
        except Exception as e:
            print("Wellfound fetch failed:", e); continue
        for m in re.finditer(r'href="(/jobs/[^"]+)"[^>]*>(.*?)</a>', raw, re.I|re.S):
            url = "https://wellfound.com" + clean_url(m.group(1))
            if url in seen: continue
            title = strip_tags(m.group(2))
            if not title or len(title) > 180: continue
            block = raw[max(0,m.start()-2200):min(len(raw),m.end()+1800)]
            ctx = strip_tags(block)
            loc_m = re.search(r"(?:Remote only|Onsite or remote|In office|Remote)\s*[•·]\s*([^<\n]{2,100})", ctx, re.I)
            loc = strip_tags(loc_m.group(1)) if loc_m else "India"
            age_m = re.search(r"\b(?:\d+\s+(?:hour|day|week|month)s?\s+ago)\b", ctx, re.I)
            date = parse_age(age_m.group(0)) if age_m else datetime.now(timezone.utc).date().isoformat()
            company_m = re.search(r'href="/company/[^"]+"[^>]*>(.*?)</a>', block, re.I|re.S)
            company = strip_tags(company_m.group(1)) if company_m else "Wellfound startup"
            if eligible(title, loc, ctx):
                seen.add(url)
                jobs.append({"company":company,"title":title,"location":loc,"url":url,"date_posted":date,"ats":"Wellfound","description":ctx[:12000]})
    return jobs

def yc():
    jobs = []
    urls = [
        "https://www.ycombinator.com/jobs/role/software-engineer/india",
        "https://www.ycombinator.com/jobs/role/ai-engineer/india",
        "https://www.ycombinator.com/jobs/role/engineer/india",
    ]
    seen = set()
    for page_url in urls:
        try: raw = fetch(page_url)
        except Exception as e:
            print("YC fetch failed:", e); continue
        for m in re.finditer(r'href="([^"]*/jobs/[^"]+)"[^>]*>(.*?)</a>', raw, re.I|re.S):
            url = clean_url(m.group(1))
            if url.startswith("/"): url = "https://www.ycombinator.com" + url
            if url in seen: continue
            title = strip_tags(m.group(2))
            if not title or len(title) > 180: continue
            block = raw[max(0,m.start()-2500):min(len(raw),m.end()+2200)]
            ctx = strip_tags(block)
            loc = "India"
            loc_m = re.search(r"(?:IN|India|Bengaluru|Hyderabad|Mumbai|Delhi|Pune|Chennai)[^<]{0,120}", ctx, re.I)
            if loc_m: loc = strip_tags(loc_m.group(0))[:160]
            if eligible(title, loc, ctx):
                seen.add(url)
                jobs.append({"company":"YC startup","title":title,"location":loc,"url":url,"date_posted":datetime.now(timezone.utc).date().isoformat(),"ats":"Y Combinator","description":ctx[:12000]})
    return jobs

def merge(source, jobs):
    path = os.path.join(OUT, f"{source}_jobs.json")
    old = {}
    if os.path.exists(path):
        try:
            old = json.load(open(path, encoding="utf-8"))
        except Exception: old = {}
    old_jobs = old.get("jobs", [])
    old_ids = {j.get("url") or (j.get("company"),j.get("title")) for j in old_jobs}
    unique = {}
    for j in old_jobs + jobs:
        unique[j.get("url") or (j.get("company"),j.get("title"))] = j
    all_source = list(unique.values())
    new_jobs = [j for j in jobs if (j.get("url") or (j.get("company"),j.get("title"))) not in old_ids]
    data = {"scraped_at":datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),"total":len(all_source),"new_count":len(new_jobs),"jobs":all_source,"new_jobs":new_jobs}
    with open(path,"w",encoding="utf-8") as f: json.dump(data,f,indent=2,ensure_ascii=False)
    return new_jobs

def update_master(new_jobs):
    path=os.path.join(OUT,"all_jobs.json")
    try: data=json.load(open(path,encoding="utf-8"))
    except Exception: data={"updated_at":"","jobs":[]}
    existing=data.get("jobs",[])
    seen={j.get("url") for j in existing if j.get("url")}
    for j in new_jobs:
        if j.get("url") not in seen:
            j=dict(j); j["first_seen"]=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            existing.append(j); seen.add(j.get("url"))
    cutoff=(datetime.now(timezone.utc)-timedelta(days=30)).date()
    kept=[]
    for j in existing:
        try:
            if datetime.fromisoformat(str(j.get("first_seen","")).replace("Z","+00:00")).date() >= cutoff: kept.append(j)
        except Exception: kept.append(j)
    data={"updated_at":datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),"jobs":kept}
    with open(path,"w",encoding="utf-8") as f: json.dump(data,f,ensure_ascii=False)

if __name__ == "__main__":
    import sys
    source=sys.argv[1] if len(sys.argv)>1 else "all"
    jobs = wellfound() if source=="wellfound" else yc() if source=="yc" else wellfound()+yc()
    new = merge("wellfound" if source=="wellfound" else "yc" if source=="yc" else "extra", jobs)
    update_master(new)
    print(f"{source}: {len(jobs)} eligible, {len(new)} new")
