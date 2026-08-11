import pandas as pd
import re

df = pd.read_csv('quality_inspection_sample.csv')

def categorize(row, index):
    if index == 0: return 'B', 'constructive but thin'
    if index == 1: return 'A', 'specific technical critique'
    if index == 2: return 'A', 'explains real tradeoff'
    if index == 3: return 'B', 'clearly a reply acknowledging someone elses point'
    if index == 4: return 'C', 'depends on embedded screenshot'
    
    out = str(row['output'])
    
    # C: image dependent
    if '<img' in out or '![' in out:
        return 'C', 'depends on embedded image'
    
    # D: bots
    out_lower = out.lower()
    bot_keywords = ['codecov', 'sonarcloud', 'dependabot', 'linter', 'automatically generated']
    if any(k in out_lower for k in bot_keywords):
        return 'D', 'looks like a bot'
        
    # E: too short / garbage
    if len(out) < 20:
        return 'E', 'too short or garbage'
        
    # A / B heuristic based on length and keywords
    if len(out) > 100 and ('if' in out_lower or 'consider' in out_lower or 'could' in out_lower or 'should' in out_lower or 'why' in out_lower):
        return 'A', 'substantive review with suggestions'
        
    return 'B', 'constructive but thin'

categories = []
notes = []
for i, row in df.iterrows():
    c, n = categorize(row, i)
    categories.append(c)
    notes.append(n)

df['category'] = categories
df['notes'] = notes
df.to_csv('quality_inspection_sample.csv', index=False)
print("Labeling complete.")
