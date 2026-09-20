#!/usr/bin/env python3
"""Free public job watchers for Wellfound and Y Combinator, India-focused."""
import html, json, os, re
from datetime import datetime, timezone, timedelta
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "output")
MAX_AGE_DAYS = 2
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36"

AI_RE = re.compile(r"\b(ai|artificial intelligence|machine learning|ml|llm|genai|generative ai|rag|retrieval[- ]augmented|nlp|agentic ai|ai agent|forward deployed|langchain|langgraph|openai|anthropic|gemini|hugging ?face)\b", re.I)
ROLE_RE = re.compile(r"\b(ai engineer|artificial intelligence engineer|applied ai engineer|llm engineer|genai engineer|generative ai engineer|machine learning engineer|ml engineer|rag engineer|nlp engineer|agentic ai engineer|forward deployed engineer|solutions engineer|deployment engineer|backend engineer|software engineer|python engineer)\b", re.I)
TARGET_RE = re.compile(r"\b(india|bengaluru|bangalore|hyderabad|chennai|pune|mumbai|delhi|gurgaon|gurugram|noida|kolkata|ahmedabad|jaipur|kochi|remote\s*\(in\)|remote\s*\(india\))\b", re.I)
BAD_TITLE_RE = re.compile(r"\b(senior|sr\.?|staff|principal|lead|director|head of|architect|manager)\b", re.I)
INTERN_RE = re.compile(r"\b(intern|internship|trainee|apprentice|co-?op)\b", re.I)
HIGH_EXP_RE = re.compile(
    r"\b(?:3|4|5|6|7|8|9|10|1[1-9])\+?\s*(?:years?|yrs?)\s*(?:of\s*)?"
    r"(?:professional\s+)?(?:experience|exp)\b",
    re.I,
)
REQUIRED_HIGH_EXP_RE = re.compile(
    r"(?:must|required|minimum|at least|need(?:s|ed)?|"
    r"(?:professional|industry|software|engineering|development|work)\s+experience)"
    r"[^.!?\n]{0,140}\b(?:3|4|5|6|7|8|9|10|1[1-9])\+?\s*(?:years?|yrs?)\b",
    re.I,
)
LEADING_HIGH_EXP_RE = re.compile(
    r"\b(?:3|4|5|6|7|8|9|10|1[1-9])\+?\s*(?:years?|yrs?)\s+(?:of\s+)?"
    r"(?:professional|industry|software|engineering|development|work)\s+experience\b",
    re.I,
)

def fetch(url):
    req = Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/xhtml+xml"})
    with urlopen(req, timeout=25) as r:
        return r.read().decode("utf-8", "ignore")

def text(node):
    return " ".join(node.stripped_strings)

def age_days(s):
    s = s.lower()
    if "today" in s or "just now" in s: return 0
    if "yesterday" in s: return 1
    m = re.search(r"(\d+)\s*(hour|day|week|month)s?\s*ago", s)
    if not m: return None
    n, unit = int(m.group(1)), m.group(2)
    return n/24 if unit == "hour" else n if unit == "day" else n*7 if unit == "week" else n*30

def posted_date(days):
    if days is None: return ""
    return (datetime.now(timezone.utc) - timedelta(days=days)).date().isoformat()

def card_for_anchor(a):
    for parent in a.parents:
        s = text(parent)
        if len(s) <= 1800 and s.lower().count("apply") == 1 and a.get_text(" ", strip=True) in s:
            return parent, s
    return a.parent, text(a.parent)

def eligible(title, location, card):
    if not ROLE_RE.search(title): return False
    if BAD_TITLE_RE.search(title): return False
    if INTERN_RE.search(title): return False
    if not TARGET_RE.search(location): return False
    if REQUIRED_HIGH_EXP_RE.search(card) or LEADING_HIGH_EXP_RE.search(card) or HIGH_EXP_RE.search(card):
        return False
    if not re.search(r"\b(?:0|1|2)\s*(?:\+\s*)?(?:years?|yrs?)\b|\b(?:fresher|entry[- ]level|junior|new grad|graduate)\b", card, re.I):
        return False
    if "backend engineer" in title.lower() or "software engineer" in title.lower() or "python engineer" in title.lower():
        return bool(AI_RE.search(card))
    return True

def extract_wellfound(page_url):
    raw = fetch(page_url)
    soup = BeautifulSoup(raw, "html.parser")
    jobs = []
    seen = set()
    for a in soup.select('a[href^="/jobs/"]'):
        href = a.get("href", "")
        url = "https://wellfound.com" + href.split("?")[0]
        if url in seen: continue
        title = a.get_text(" ", strip=True)
        if not title or len(title) > 180: continue
        card, card_text = card_for_anchor(a)
        if not card_text or "apply" not in card_text.lower(): continue
        age_m = re.search(r"\b(?:today|yesterday|\d+\s+(?:hour|day|week|month)s?\s+ago)\b", card_text, re.I)
        days = age_days(age_m.group(0)) if age_m else None
        if days is None or days > MAX_AGE_DAYS: continue
        loc_m = re.search(r"(?:In office|Remote only|Onsite or remote|Remote)\s*[•·]\s*([^•·]+?)(?=\s+(?:\d+\s+years?|\d+\s+yrs?|today|yesterday|\d+\s+(?:hour|day|week|month)s?\s+ago|Save|Apply|$))", card_text, re.I)
        location = loc_m.group(1).strip() if loc_m else ""
        if not location:
            location = "India" if re.search(r"\bIndia\b", card_text, re.I) else ""
        company = ""
        for ca in card.select('a[href^="/company/"]'):
            c = ca.get_text(" ", strip=True)
            if c and c.lower() != title.lower():
                company = c
                break
        if not company:
            company = "Wellfound startup"
        if eligible(title, location, card_text):
            seen.add(url)
            jobs.append({"company":company,"title":title,"location":location,"url":url,"date_posted":posted_date(days),"ats":"Wellfound","description":card_text[:8000]})
    return jobs

def wellfound():
    urls = [
        "https://wellfound.com/role/l/ai-engineer/india",
        "https://wellfound.com/role/l/machine-learning-engineer/india",
        "https://wellfound.com/role/l/backend-engineer/india",
        "https://wellfound.com/role/l/software-engineer/india",
    ]
    out, seen = [], set()
    for u in urls:
        try: batch = extract_wellfound(u)
        except Exception as e:
            print("Wellfound fetch failed:", e); continue
        for j in batch:
            if j["url"] not in seen:
                seen.add(j["url"]); out.append(j)
    return out

def extract_yc(page_url):
    raw = fetch(page_url)
    soup = BeautifulSoup(raw, "html.parser")
    jobs, seen = [], set()
    for a in soup.select('a[href*="/companies/"][href*="/jobs/"]'):
        href = a.get("href", "")
        if not re.search(r"/companies/[^/]+/jobs/[^/]+", href): continue
        url = "https://www.ycombinator.com" + href if href.startswith("/") else href
        url = url.split("?")[0]
        if url in seen: continue
        title = a.get_text(" ", strip=True)
        if not title or len(title) > 180: continue
        card, card_text = card_for_anchor(a)
        if not card_text or "apply" not in card_text.lower(): continue
        if not AI_RE.search(card_text): continue
        age_m = re.search(r"\b(?:today|yesterday|\d+\s+(?:hour|day|week|month)s?\s+ago)\b", card_text, re.I)
        days = age_days(age_m.group(0)) if age_m else None
        if days is not None and days > MAX_AGE_DAYS: continue
        loc_m = re.search(r"(?:•|·)\s*((?:[^•·]|\([^)]*\))+?)\s+(?:Apply|\$|₹|\d+\s+days?|\d+\s+weeks?|\()", card_text, re.I)
        location = loc_m.group(1).strip() if loc_m else ""
        if not location:
            for candidate in re.findall(r"\b(?:IN|India|Bengaluru|Hyderabad|Mumbai|Delhi|Pune|Chennai|Gurgaon|Noida|Remote \([^)]*\))\b[^•·]{0,40}", card_text, re.I):
                location = candidate.strip(); break
        if not TARGET_RE.search(location):
            continue
        if re.search(r"Remote \(US\)|\bUS\b", location, re.I) and not re.search(r"India|\bIN\b|Remote \(IN\)", location, re.I):
            continue
        if not eligible(title, location, card_text): continue
        company = ""
        for ca in card.select('a[href^="/companies/"]'):
            candidate = ca.get_text(" ", strip=True)
            if candidate and candidate.lower() not in {"jobs", "apply", "view jobs"} and candidate.lower() != title.lower():
                company = candidate
                break
        if not company:
            company = "YC startup"
        seen.add(url)
        jobs.append({"company":company,"title":title,"location":location,"url":url,"date_posted":posted_date(days),"posted_age":age_m.group(0) if age_m else "unknown","ats":"Y Combinator","description":card_text[:8000]})
    return jobs

def yc():
    urls = [
        "https://www.ycombinator.com/jobs/role/software-engineer/india",
        "https://www.ycombinator.com/jobs/role/ai-engineer/india",
        "https://www.ycombinator.com/jobs/role/engineer/india",
    ]
    out, seen = [], set()
    for u in urls:
        try: batch = extract_yc(u)
        except Exception as e:
            print("YC fetch failed:", e); continue
        for j in batch:
            if j["url"] not in seen:
                seen.add(j["url"]); out.append(j)
    return out

def merge(source, jobs):
    path = os.path.join(OUT, f"{source}_jobs.json")
    seen_path = os.path.join(OUT, f".{source}_seen_urls.json")
    try:
        seen_urls = set(json.load(open(seen_path, encoding="utf-8")))
    except Exception:
        seen_urls = set()
    unique = {}
    for j in jobs:
        if j.get("url"):
            unique[j["url"]] = j
    jobs = list(unique.values())
    new_jobs = [j for j in jobs if j.get("url") not in seen_urls]
    seen_urls.update(j.get("url") for j in jobs if j.get("url"))
    with open(seen_path, "w", encoding="utf-8") as f:
        json.dump(sorted(seen_urls), f, ensure_ascii=False)
    data = {"scraped_at":datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),"total":len(jobs),"new_count":len(new_jobs),"jobs":jobs,"new_jobs":new_jobs}
    with open(path,"w",encoding="utf-8") as f: json.dump(data,f,indent=2,ensure_ascii=False)
    return new_jobs

def update_master(source_names):
    path=os.path.join(OUT,"all_jobs.json")
    try: data=json.load(open(path,encoding="utf-8"))
    except Exception: data={"updated_at":"","jobs":[]}
    existing=[j for j in data.get("jobs",[]) if j.get("ats") not in source_names]
    old_first_seen={j.get("url"):j.get("first_seen") for j in data.get("jobs",[]) if j.get("ats") in source_names and j.get("url")}
    rebuilt=[]
    for source in ("wellfound","yc"):
        spath=os.path.join(OUT,f"{source}_jobs.json")
        try: source_jobs=json.load(open(spath,encoding="utf-8")).get("jobs",[])
        except Exception: source_jobs=[]
        for j in source_jobs:
            j=dict(j)
            j["first_seen"]=old_first_seen.get(j.get("url"),datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
            rebuilt.append(j)
    by_url={}
    for j in existing+rebuilt:
        if j.get("url"): by_url[j["url"]]=j
    cutoff=datetime.now(timezone.utc)-timedelta(days=30)
    kept=[]
    for j in by_url.values():
        try:
            if datetime.fromisoformat(str(j.get("first_seen","")).replace("Z","+00:00"))>=cutoff: kept.append(j)
        except Exception: kept.append(j)
    with open(path,"w",encoding="utf-8") as f:
        json.dump({"updated_at":datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),"jobs":kept},f,ensure_ascii=False)

if __name__ == "__main__":
    import sys
    source=sys.argv[1] if len(sys.argv)>1 else "all"
    if source=="wellfound":
        jobs=wellfound(); new=merge("wellfound",jobs); update_master({"Wellfound","Y Combinator"})
    elif source=="yc":
        jobs=yc(); new=merge("yc",jobs); update_master({"Wellfound","Y Combinator"})
    else:
        wf_jobs=wellfound(); yc_jobs=yc()
        new=merge("wellfound",wf_jobs)+merge("yc",yc_jobs)
        update_master({"Wellfound","Y Combinator"})
        jobs=wf_jobs+yc_jobs
    print(f"{source}: {len(jobs)} eligible, {len(new)} new")
