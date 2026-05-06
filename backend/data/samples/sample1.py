import random, datetime

levels = ['INFO', 'WARNING', 'ERROR', 'DEBUG']
messages = [
    'User login successful',
    'Database connection timeout',
    'Request processed in 120ms',
    'File not found: config.yaml',
    'Cache miss for key user_42',
    'Retrying connection attempt 3',
    'Memory threshold exceeded',
    'Scheduled job completed',
]

with open('data/samples/sample.log', 'w') as f:
    base = datetime.datetime(2024, 1, 1, 0, 0, 0)
    for i in range(10000):
        ts = base + datetime.timedelta(seconds=i)
        level = random.choice(levels)
        msg = random.choice(messages)
        f.write(f'[{ts}] [{level}] {msg}\n')

print('Generated 10000 lines in data/samples/sample.log')