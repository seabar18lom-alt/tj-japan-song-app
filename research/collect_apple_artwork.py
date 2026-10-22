#!/usr/bin/env python3
"""Search Apple Music catalog for artwork candidates. Never auto-publish images."""
import json, pathlib, re, time, urllib.parse, urllib.request, unicodedata
ROOT = pathlib.Path(__file__).resolve().parents[1]
source = json.loads((ROOT/"research/gemini-song-catalog-245.json").read_text(encoding="utf-8"))
dest = ROOT/"research/apple-artwork-candidates.json"
def norm(s):
    return re.sub(r"[^\w]+","",unicodedata.normalize("NFKC",str(s)).casefold())
def fetch(term):
    url="https://itunes.apple.com/search?"+urllib.parse.urlencode({"term":term,"country":"JP","entity":"song","limit":30})
    req=urllib.request.Request(url,headers={"User-Agent":"TJ-Japan-Song-Research/1.0 (catalog research)"})
    with urllib.request.urlopen(req,timeout=18) as response:
        return json.load(response).get("results",[])
def find(song):
    title=song.get("jp") or song["ko"]
    artist=song.get("artist") or ""
    terms=[title+" "+artist,title]
    found={}
    for term in terms:
        try:
            for hit in fetch(term):
                if hit.get("trackId"): found[hit["trackId"]]=hit
            if found: break
        except Exception as e:
            print("Search failed:",song["id"],str(e))
        time.sleep(0.8)
    scored=[]
    for item in found.values():
        actual=item.get("trackName","")
        title_match=norm(actual)==norm(title) or norm(actual)==norm(song["ko"])
        # Artist names in catalog may be written in Japanese rather than Korean.
        artist_match=bool(artist) and norm(artist)==norm(item.get("artistName",""))
        if not title_match: continue
        scored.append({"trackName":actual,"artistName":item.get("artistName"),"collectionName":item.get("collectionName"),
          "artworkUrl":item.get("artworkUrl100"),"sourceUrl":item.get("trackViewUrl"),
          "appleTrackId":item.get("trackId"),"exactTitleMatch":title_match,"exactArtistMatch":artist_match,
          "reviewStatus":"manual_review_required","rights":"unverified; do not bundle or hotlink without permission"})
    return sorted(scored,key=lambda x:x["exactArtistMatch"],reverse=True)[:5]
out=[]
for i,s in enumerate(source["songs"],1):
    out.append({"id":s["id"],"ko":s["ko"],"jp":s.get("jp"),"artist":s.get("artist"),
      "candidates":find(s)})
    print(f'{i}/{len(source["songs"])} {s["ko"]} candidates={len(out[-1]["candidates"])}',flush=True)
    if i%10==0:
        dest.write_text(json.dumps({"schemaVersion":1,"completed":i,"total":len(source["songs"]),"songs":out},ensure_ascii=False,indent=2),encoding="utf-8")
    time.sleep(1.1)
dest.write_text(json.dumps({"schemaVersion":1,"completed":len(out),"total":len(source["songs"]),"songs":out},ensure_ascii=False,indent=2),encoding="utf-8")
print("Saved:",dest)
