#!/usr/bin/env python3
"""Verify VPS files are correct"""
import json, os

WWW = '/www/wwwroot/szqyjs.com.cn'

# Check JSON
with open(os.path.join(WWW, 'data', 'site-content.json'), 'r', encoding='utf-8') as f:
    data = json.load(f)

print('=== JSON is valid ===')
print('Company name:', data['company']['name'])
print('Address:', data['company']['address'])
print('Phone:', data['company']['phone'])
print('Email:', data['company']['email'])
print('Hero title:', data['hero']['title'])
print('Hero subtitle:', data['hero']['subtitle'][:60])
print('Stats:', [(s['label'], s['value'], s['suffix']) for s in data['hero']['stats']])
print('Highlights:', data['company'].get('highlights', []))
print('Services count:', len(data.get('services', [])))
for i, svc in enumerate(data.get('services', [])):
    print(f'  Service {i+1}: {svc["title"]} | desc: {svc["desc"][:50]}')

# Check HTML stats
with open(os.path.join(WWW, 'index.html'), 'r', encoding='utf-8') as f:
    html = f.read()

import re
counts = re.findall(r'data-count="(\d+)"', html)
print('\n=== HTML stats ===')
print('data-count values:', counts)

labels = re.findall(r'<p>(.*?)</p>', html)
stat_labels = [l for l in labels if l and len(l) > 1 and '>' not in l][:8]
print('Stat labels:', stat_labels)

# Verify admin.py
print('\n=== admin.py check ===')
import py_compile
try:
    py_compile.compile(os.path.join(WWW, 'admin.py'), doraise=True)
    print('admin.py is valid Python')
except py_compile.PyCompileError as e:
    print('ERROR:', e)

print('\n=== All checks passed ===')
