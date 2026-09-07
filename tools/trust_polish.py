from pathlib import Path
import re

root=Path('.')
for lang in ('en','ar'):
    p=root/lang/'index.html'
    s=p.read_text(encoding='utf-8')
    s=re.sub(r'custom-v12\.css\?v=\d+','custom-v12.css?v=18',s)
    if lang=='en':
        s=s.replace('<span>Finance & accounting leadership</span>','<span>Finance & accounting experience</span>')
        s=s.replace('<div class="eyebrow">Client Feedback</div><h3>Selected clients and businesses I have supported.</h3><p class="client-note">Selected relationships across telecommunications, travel, retail, manufacturing, business services, real estate, construction, hospitality and food & beverage.</p>', '<div class="eyebrow">Selected Organizations</div><h3>Businesses and organizations I have supported across my career.</h3><p class="client-note">Professional experience and finance support across telecommunications, travel, retail, manufacturing, business services, real estate, construction, hospitality and food & beverage.</p>')
    else:
        s=s.replace('<div class="eyebrow">آراء العملاء</div><h3>عملاء وشركات تشرفت بدعمها.</h3><p class="client-note">علاقات عمل مختارة عبر قطاعات الاتصالات والسفر والتجزئة والصناعة وخدمات الأعمال والعقارات والمقاولات والضيافة والأغذية والمشروبات.</p>', '<div class="eyebrow">جهات مختارة</div><h3>شركات وجهات عملت معها أو دعمتها خلال مسيرتي المهنية.</h3><p class="client-note">خبرات وعلاقات عمل مهنية عبر قطاعات الاتصالات والسفر والتجزئة والصناعة وخدمات الأعمال والعقارات والمقاولات والضيافة والأغذية والمشروبات.</p>')
    s=re.sub(r'<div class="stars"[^>]*>.*?</div>','',s)
    p.write_text(s,encoding='utf-8')

cssp=root/'assets/custom-v12.css'
c=cssp.read_text(encoding='utf-8')
if 'V20 trust and personal brand' not in c:
    c+='''\n/* V20 trust and personal brand */\n.client-card{justify-content:center!important}.client-card b{font-size:17px!important}.client-card span{margin-top:5px}.client-section .client-note{max-width:820px}.stats{border:1px solid rgba(181,138,82,.12)}.stat b{color:var(--deep)}.stat span{line-height:1.45}.hero .float-card strong{letter-spacing:-.02em}.hero .float-card span{line-height:1.35}\n'''
cssp.write_text(c,encoding='utf-8')
