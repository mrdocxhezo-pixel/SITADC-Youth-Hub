content = open(r'D:\Django Projects\sitadc-youth-hub\DEVELOPMENT_STATUS.md', 'r', encoding='utf-16').read()
old = """| 1.11.0   | 2026-08-21 | Development | Phase 30 Communication and Media implemented (`apps/communications`, 16 models, 141 tests, full communication framework with media, brand, social, web, news, campaigns, newsletters, announcements, notifications, distribution, audit) |

---"""
new = """| 1.11.0   | 2026-08-21 | Development | Phase 30 Communication and Media implemented (`apps/communications`, 16 models, 141 tests, full communication framework with media, brand, social, web, news, campaigns, newsletters, announcements, notifications, distribution, audit) |
| 1.12.0   | 2026-08-21 | Development | Phase 31 System Configuration implemented (`apps/configuration`, 21 models, 28 configuration categories, lifecycle management, versioning, timeline, org scoping, 50+ tests) |

---"""
content = content.replace(old, new)
open(r'D:\Django Projects\sitadc-youth-hub\DEVELOPMENT_STATUS.md', 'w', encoding='utf-16').write(content)
print('Done')