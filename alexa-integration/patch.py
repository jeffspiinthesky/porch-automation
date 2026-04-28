import re
path = '/venv/lib/python3.12/site-packages/oscrypto/_openssl/_libcrypto_cffi.py'
with open(path, 'r') as f:
    content = f.read()

# Match the actual escaped string in the file
old = "'\\\\b(\\\\d\\\\.\\\\d\\\\.\\\\d[a-z]*)\\\\b'"
new = "'\\\\b(\\\\d+\\\\.\\\\d+\\\\.\\\\d+[a-z]*)\\\\b'"

if old in content:
    content = content.replace(old, new)
    with open(path, 'w') as f:
        f.write(content)
    print('Patched successfully')
else:
    print('Pattern not found - dumping relevant section:')
    for i, line in enumerate(content.splitlines()):
        if 'version_match' in line:
            print(f'{i}: {repr(line)}')
