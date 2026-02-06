from app import app
c = app.test_client()
for path in ['/', '/login', '/contests', '/dashboard']:
    r = c.get(path)
    loc = getattr(r, 'location', None)
    print(path, r.status_code, '->', loc)
