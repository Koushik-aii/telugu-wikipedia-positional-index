"""Check available Telugu Wikipedia dumps and download the latest."""
import urllib.request
import json
import re
import os
import sys

RAW_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "raw")
os.makedirs(RAW_DIR, exist_ok=True)

def check_and_download():
    url = 'https://dumps.wikimedia.org/tewiki/'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'TeluguWikiIndexer/1.0'})
        resp = urllib.request.urlopen(req, timeout=15)
        html = resp.read().decode('utf-8')
        
        dates = re.findall(r'href="(\d{8})/"', html)
        print(f'Available dump dates (last 10): {dates[-10:]}')
        
        if not dates:
            print('No dumps found.')
            return
        
        # Try from most recent backwards
        for latest in reversed(dates):
            print(f'\nChecking dump date: {latest}')
            status_url = f'https://dumps.wikimedia.org/tewiki/{latest}/dumpstatus.json'
            
            try:
                req2 = urllib.request.Request(status_url, headers={'User-Agent': 'TeluguWikiIndexer/1.0'})
                resp2 = urllib.request.urlopen(req2, timeout=15)
                status = json.loads(resp2.read().decode('utf-8'))
            except Exception as e:
                print(f'  Could not get status: {e}')
                continue
            
            jobs = status.get('jobs', {})
            
            # Try articlesmultistreamdump first, then articlesdump
            for key in ['articlesmultistreamdump', 'articlesdump']:
                if key not in jobs:
                    continue
                job = jobs[key]
                job_status = job.get('status', 'unknown')
                print(f'  {key}: {job_status}')
                
                if job_status != 'done':
                    continue
                
                if 'files' not in job:
                    continue
                
                for fname, finfo in job['files'].items():
                    if fname.endswith('.xml.bz2'):
                        size = finfo.get('size', 0)
                        download_url = f'https://dumps.wikimedia.org/tewiki/{latest}/{fname}'
                        print(f'  File: {fname}')
                        print(f'  Size: {size} bytes ({size/(1024*1024):.1f} MB)')
                        print(f'  URL: {download_url}')
                        
                        # Download it
                        filepath = os.path.join(RAW_DIR, fname)
                        if os.path.exists(filepath):
                            print(f'  Already downloaded: {filepath}')
                            return filepath
                        
                        print(f'  Downloading to: {filepath}')
                        try:
                            req3 = urllib.request.Request(download_url, headers={'User-Agent': 'TeluguWikiIndexer/1.0'})
                            resp3 = urllib.request.urlopen(req3, timeout=30)
                            
                            downloaded = 0
                            with open(filepath, 'wb') as f:
                                while True:
                                    chunk = resp3.read(1024 * 1024)
                                    if not chunk:
                                        break
                                    f.write(chunk)
                                    downloaded += len(chunk)
                                    pct = (downloaded / size * 100) if size else 0
                                    print(f'\r  Progress: {downloaded/(1024*1024):.1f} MB / {size/(1024*1024):.1f} MB ({pct:.1f}%)', end='', flush=True)
                            
                            print(f'\n  Download complete: {filepath}')
                            return filepath
                        except Exception as e:
                            print(f'\n  Download error: {e}')
                            if os.path.exists(filepath):
                                os.remove(filepath)
                            continue
            
            # If we found a done dump, we already handled it above
            # Try next date if this one didn't work

    except Exception as e:
        print(f'Error: {e}')
        return None

if __name__ == '__main__':
    check_and_download()

