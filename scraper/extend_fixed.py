#!/usr/bin/env python3
"""
補入 c01/c08/c12/c13/c14 固定班表的 3月份 sessions（3/2–3/31）
直接從現有的週班週期延伸
"""
import json
from datetime import date
from pathlib import Path

SCHEDULES_FILE = Path('/Users/yezuhao/Projects/scraper/schedules.json')

with open(SCHEDULES_FILE, encoding='utf-8') as f:
    data = json.load(f)

# March 2026 dates (Mon–Sat)
MARCH_DATES = [date(2026, 3, d) for d in range(1, 32)]
DAY_MAP = {0:'Mon',1:'Tue',2:'Wed',3:'Thu',4:'Fri',5:'Sat',6:'Sun'}

SLOT_LABELS = {
    'morning':   '早診 09:00–12:00',
    'afternoon': '下午 14:00–17:30',
    'evening':   '晚診 18:00–21:00',
}

# Fixed weekly schedule extracted from existing Feb sessions
# Format: { clinic_id: { (day_name, slot): [doctors] } }
FIXED_SCHEDULES = {
    'c01': {
        ('Mon','morning'):  ['陳柏誠'],
        ('Mon','evening'):  ['陳柏誠'],
        ('Tue','morning'):  ['陳柏誠'],
        ('Wed','morning'):  ['陳柏誠'],
        ('Thu','morning'):  ['陳柏誠'],
        ('Thu','evening'):  ['陳柏誠'],
        ('Fri','morning'):  ['陳柏誠'],
    },
    'c08': {
        ('Mon','morning'):   ['蘇哲惟'],
        ('Mon','afternoon'): ['黃英庭','黃旭東'],
        ('Mon','evening'):   ['曾鵬文','黃旭東'],
        ('Tue','morning'):   ['曾鵬文'],
        ('Tue','afternoon'): ['黃旭東'],
        ('Tue','evening'):   ['黃旭東'],
        ('Wed','morning'):   ['黃旭東'],
        ('Wed','afternoon'): ['黃英庭','曾鵬文'],
        ('Wed','evening'):   ['曾鵬文'],
        ('Thu','morning'):   ['曾鵬文'],
        ('Thu','afternoon'): ['黃旭東','蔡馥如'],
        ('Thu','evening'):   ['黃旭東','蔡馥如'],
        ('Fri','morning'):   ['黃旭東'],
        ('Fri','afternoon'): ['蘇哲惟'],
        ('Fri','evening'):   ['曾鵬文'],
        ('Sat','morning'):   ['黃旭東'],
        ('Sat','afternoon'): ['曾鵬文'],
    },
    'c12': {
        ('Mon','morning'):   ['陳正傑'],
        ('Mon','afternoon'): ['陳正傑'],
        ('Tue','morning'):   ['陳正傑'],
        ('Tue','afternoon'): ['陳正傑'],
        ('Tue','evening'):   ['陳正傑'],
        ('Wed','morning'):   ['陳正傑'],
        ('Thu','morning'):   ['陳正傑'],
        ('Thu','afternoon'): ['陳正傑'],
        ('Thu','evening'):   ['陳正傑'],
        ('Fri','morning'):   ['陳正傑'],
        ('Fri','afternoon'): ['陳正傑'],
    },
    'c13': {
        ('Mon','morning'):   ['悅滿意江'],
        ('Mon','evening'):   ['悅滿意林'],
        ('Tue','morning'):   ['悅滿意李'],
        ('Tue','afternoon'): ['悅滿意李'],
        ('Tue','evening'):   ['悅滿意江'],
        ('Wed','morning'):   ['悅滿意王'],
        ('Thu','afternoon'): ['悅滿意王'],
        ('Thu','evening'):   ['悅滿意江'],
        ('Fri','morning'):   ['悅滿意江'],
        ('Fri','afternoon'): ['悅滿意丁'],
        ('Sat','morning'):   ['悅滿意江'],
    },
    'c14': {
        ('Mon','morning'):   ['悅滿意李'],
        ('Mon','afternoon'): ['悅滿意丁'],
        ('Mon','evening'):   ['悅滿意王'],
        ('Tue','morning'):   ['悅滿意丁'],
        ('Tue','afternoon'): ['悅滿意王'],
        ('Tue','evening'):   ['悅滿意王'],
        ('Wed','morning'):   ['悅滿意羅'],
        ('Wed','afternoon'): ['悅滿意王'],
        ('Wed','evening'):   ['悅滿意江'],
        ('Thu','morning'):   ['悅滿意王'],
        ('Thu','evening'):   ['悅滿意李'],
        ('Fri','morning'):   ['悅滿意王'],
        ('Fri','afternoon'): ['悅滿意江'],
        ('Sat','morning'):   ['悅滿意王'],
    },
}

PREFIX_MAP = {
    'c01': 'ha',   # 禾安
    'c08': 'zy',   # 正陽
    'c12': 'cjj',  # 陳正傑
    'c13': 'ywyw', # 悅滿意永和
    'c14': 'ywyx', # 悅滿意新店
}

SLOT_CHAR = {'morning':'m','afternoon':'a','evening':'e'}

# Get existing March dates for these clinics (to avoid duplicates)
march_date_strs = {str(d) for d in MARCH_DATES}

for clinic_id, schedule in FIXED_SCHEDULES.items():
    prefix = PREFIX_MAP[clinic_id]
    
    # Remove any existing March sessions for this clinic (avoid duplicates)
    existing_count = len(data['sessions'])
    data['sessions'] = [
        s for s in data['sessions']
        if not (s['clinic_id'] == clinic_id and s['date'] in march_date_strs)
    ]
    removed = existing_count - len(data['sessions'])
    
    new_sessions = []
    for d in MARCH_DATES:
        day_name = DAY_MAP[d.weekday()]
        date_str = str(d)
        mmdd = d.strftime('%m%d')
        
        for slot in ['morning', 'afternoon', 'evening']:
            doctors = schedule.get((day_name, slot), [])
            for i, doctor in enumerate(doctors):
                suffix = '' if i == 0 else 'b'
                new_sessions.append({
                    'id': f'{prefix}_{SLOT_CHAR[slot]}_{mmdd}_{doctor[:1]}{suffix}',
                    'doctor_name': doctor,
                    'clinic_id': clinic_id,
                    'date': date_str,
                    'slot': slot,
                    'time_label': SLOT_LABELS[slot],
                    'source_note': '固定班表 2026-03-02 延伸',
                })
    
    data['sessions'].extend(new_sessions)
    print(f'[{clinic_id}] 刪除舊:{removed} 新增:{len(new_sessions)}')

# Conflict check
from collections import defaultdict
clinics = {c['id']: c['name'] for c in data['clinics']}
conflicts = defaultdict(list)
for s in data['sessions']:
    key = (s['doctor_name'], s['date'], s['slot'])
    conflicts[key].append((s['clinic_id'], clinics.get(s['clinic_id'], s['clinic_id'])))
found = False
for key, entries in conflicts.items():
    if len(entries) > 1:
        print(f'⚠️ 衝突: {key}')
        for e in entries: print(f'  → {e}')
        found = True
if not found:
    print('✅ 無衝突')

with open(SCHEDULES_FILE, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f'✅ 儲存完成，總 sessions: {len(data["sessions"])}')
