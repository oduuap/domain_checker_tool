#!/usr/bin/env python3
"""
DOMAIN FINDER WEB APP
Web interface để tìm expired domains với traffic
"""

from flask import Flask, render_template, request, jsonify, send_file, Response
from flask_cors import CORS
import json
import time
import os
from datetime import datetime
from threading import Thread, Lock
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue
import whois
import dns.resolver
import requests
import re
from typing import Dict, List, Optional
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from bs4 import BeautifulSoup
from urllib.parse import quote
from keyword_database import KeywordGenerator

app = Flask(__name__)
CORS(app)

# Initialize keyword generator
keyword_gen = KeywordGenerator()

# API Keys
RAPIDAPI_KEY = "3267466f8dmshf9b9f3bb87d2afcp10c10bjsnccecb46bc96a"
C99_API_KEY = "POM2S-E8ZC6-7KFVA-VH8TP"

# Global variables cho progress tracking
search_progress = {
    'status': 'idle',
    'current': 0,
    'total': 0,
    'message': '',
    'domains_found': [],
    'current_domain': ''
}

class DomainChecker:
    def __init__(self, rapidapi_key=None, c99_api_key=None):
        self.rapidapi_key = rapidapi_key
        self.c99_api_key = c99_api_key

    def check_domain_availability(self, domain: str) -> Dict:
        """Kiểm tra domain có available không"""
        result = {
            'domain': domain,
            'available': None,
            'creation_date': None,
            'age_years': None,
            'registrar': None,
            'status': None
        }

        try:
            w = whois.whois(domain)

            if w.domain_name:
                result['available'] = False
                result['registrar'] = w.registrar
                result['status'] = 'Registered'

                creation_date = w.creation_date
                if isinstance(creation_date, list):
                    creation_date = creation_date[0]

                if creation_date:
                    result['creation_date'] = creation_date.strftime('%Y-%m-%d') if isinstance(creation_date, datetime) else str(creation_date)
                    if isinstance(creation_date, datetime):
                        creation_date_naive = creation_date.replace(tzinfo=None) if creation_date.tzinfo else creation_date
                        age = datetime.now() - creation_date_naive
                        result['age_years'] = round(age.days / 365.25, 1)
            else:
                result['available'] = True

        except Exception as e:
            error_msg = str(e).lower()
            if 'no match' in error_msg or 'not found' in error_msg or 'no data' in error_msg:
                result['available'] = True
                result['status'] = 'Available'

        return result

    def check_wayback_history(self, domain: str) -> Dict:
        """Kiểm tra lịch sử trên Wayback Machine"""
        result = {
            'snapshot_count': 0,
            'first_archive': None,
            'last_archive': None,
            'age_years': 0,
            'has_history': False
        }

        try:
            url = f"http://web.archive.org/cdx/search/cdx?url={domain}&output=json&limit=10000"
            response = requests.get(url, timeout=15)

            if response.status_code == 200:
                data = response.json()

                if len(data) > 1:
                    result['snapshot_count'] = len(data) - 1
                    result['has_history'] = True

                    first_timestamp = data[1][1]
                    last_timestamp = data[-1][1]

                    result['first_archive'] = first_timestamp[:8]
                    result['last_archive'] = last_timestamp[:8]

                    first_year = int(first_timestamp[:4])
                    current_year = datetime.now().year
                    result['age_years'] = current_year - first_year

        except Exception as e:
            pass

        return result

    def check_seo_metrics_rapidapi(self, domain: str) -> Dict:
        """Kiểm tra DR/UR/SEO metrics qua RapidAPI"""
        result = {
            'domain_rating': 0,
            'url_rating': 0,
            'organic_traffic': 0,
            'backlinks': 0,
            'referring_domains': 0,
            'has_seo_value': False
        }

        if not self.rapidapi_key:
            return result

        try:
            url = "https://seo-api-dr-rd-rank-keywords-backlinks.p.rapidapi.com/url-metrics"

            headers = {
                'x-rapidapi-host': 'seo-api-dr-rd-rank-keywords-backlinks.p.rapidapi.com',
                'x-rapidapi-key': self.rapidapi_key
            }

            params = {'url': f'https://{domain}'}

            response = requests.get(url, headers=headers, params=params, timeout=15)

            if response.status_code == 200:
                data = response.json()

                # Parse ĐÚNG structure của RapidAPI response
                if data.get('success') and 'data' in data:
                    api_data = data['data']

                    # Lấy domain metrics
                    domain_metrics = api_data.get('domain', {})
                    page_metrics = api_data.get('page', {})

                    result['domain_rating'] = domain_metrics.get('domainRating', 0) or 0
                    result['url_rating'] = page_metrics.get('urlRating', 0) or 0
                    # GIỮ TRAFFIC DẠNG FLOAT để không mất traffic nhỏ (< 1)
                    result['organic_traffic'] = float(domain_metrics.get('trafficVol', 0) or 0)
                    result['backlinks'] = domain_metrics.get('backlinks', 0) or 0
                    result['referring_domains'] = domain_metrics.get('refDomains', 0) or 0
                    result['has_seo_value'] = result['domain_rating'] > 0 or result['organic_traffic'] > 0

        except Exception as e:
            pass

        return result

    def check_registrar_availability(self, domain: str) -> Dict:
        """Kiểm tra domain có mua được không tại Namecheap"""
        result = {
            'purchasable': False,
            'price': None,
            'url': None,
            'is_premium': False
        }

        try:
            search_url = f"https://www.namecheap.com/domains/registration/results/?domain={domain}"
            result['url'] = search_url

            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }

            response = requests.get(search_url, headers=headers, timeout=15)

            if response.status_code == 200:
                content = response.text.lower()

                if 'available' in content and 'add to cart' in content:
                    result['purchasable'] = True

                    price_match = re.search(r'\$(\d+\.\d+)', response.text)
                    if price_match:
                        result['price'] = f"${price_match.group(1)}"

                if 'premium' in content:
                    result['is_premium'] = True

            time.sleep(1)

        except Exception as e:
            pass

        return result

    def generate_keyword_variations(self, keyword: str, max_variations: int = 20) -> List[str]:
        """Tạo variations từ keyword"""
        variations = [keyword]

        suffixes = ['hub', 'app', 'pro', 'web', 'net', 'zone', 'spot', 'land', 'world']
        prefixes = ['my', 'get', 'the', 'top', 'best', 'new', 'hot']

        for suffix in suffixes:
            variations.append(f"{keyword}{suffix}")

        for prefix in prefixes:
            variations.append(f"{prefix}{keyword}")

        return list(dict.fromkeys(variations))[:max_variations]

    def fetch_subdomains_c99_api(self, domain: str) -> List[str]:
        """
        Lấy subdomains qua C99 API - CHÍNH XÁC & NHANH

        Args:
            domain: TLD (vd: 'sa.com', 'ca.com')

        Returns:
            List subdomains
        """
        subdomains = []

        if not self.c99_api_key:
            return subdomains

        try:
            # C99 Subdomain Finder API
            url = "https://api.c99.nl/subdomainfinder"

            params = {
                'key': self.c99_api_key,
                'domain': domain,
                'json': 'true'
            }

            print(f"  📡 Calling C99 API for {domain}...", end=' ')

            response = requests.get(url, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()

                # Check response success
                if data.get('success') == True or data.get('success') == 1:
                    # Parse subdomains từ response
                    if 'subdomains' in data:
                        subdomains = data['subdomains']
                    elif 'result' in data:
                        result = data['result']
                        if isinstance(result, list):
                            subdomains = result
                        elif isinstance(result, dict) and 'subdomains' in result:
                            subdomains = result['subdomains']

                    print(f"✓ Found {len(subdomains)} subdomains")

                else:
                    error = data.get('error', 'Unknown error')
                    print(f"✗ API Error: {error}")

            else:
                print(f"✗ HTTP {response.status_code}")

        except Exception as e:
            print(f"✗ Error: {str(e)[:50]}")

        return subdomains

    def fetch_domains_from_c99(self, tld: str) -> List[str]:
        """
        Lấy danh sách domains từ c99.nl API

        Args:
            tld: TLD cần lấy (vd: 'ca.com', 'sa.com', 'ru.com')

        Returns:
            List domains
        """
        domains = []

        # Try C99 API
        if self.c99_api_key:
            print(f"\n📡 Fetching domains from C99 API for {tld}...")
            raw_domains = self.fetch_subdomains_c99_api(tld)

            if raw_domains:
                # Parse domains - handle multiple formats
                parsed_domains = []

                for item in raw_domains:
                    try:
                        if isinstance(item, str):
                            # Format 1: ["domain.com", "domain2.com"]
                            parsed_domains.append(item.lower().strip())
                        elif isinstance(item, dict):
                            # Format 2: [{"domain": "domain.com", "ip": "1.2.3.4"}]
                            if 'domain' in item:
                                parsed_domains.append(item['domain'].lower().strip())
                            elif 'subdomain' in item:
                                parsed_domains.append(item['subdomain'].lower().strip())
                        elif isinstance(item, list) and len(item) > 0:
                            # Format 3: [["domain.com", "1.2.3.4"], ...]
                            parsed_domains.append(str(item[0]).lower().strip())
                    except Exception as e:
                        # Skip invalid items
                        continue

                # Remove duplicates
                domains = list(set(parsed_domains))

                # Filter bỏ domains quá dài (>50 chars) và không hợp lệ
                domains = [d for d in domains if d and len(d) <= 50 and '.' in d]

                print(f"  ✓ Got {len(domains)} valid domains from C99.NL")
                return domains

        print(f"  ✗ Could not fetch domains from C99 API")
        return domains


def search_domains_background(keywords, tlds, max_check, min_dr, search_id, mode='keyword', c99_domains=None):
    """Background task để search domains"""
    global search_progress

    try:
        search_progress['status'] = 'running'
        search_progress['message'] = 'Đang khởi tạo...'

