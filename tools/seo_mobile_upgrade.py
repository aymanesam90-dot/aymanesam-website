from pathlib import Path
import re, json

root=Path('.')
social_image='https://aymanesam.com/assets/Gemini_Generated_Image_16oe0q16oe0q16oe.jpg'

def upsert_meta(s, attr, key, content):
    pat=rf'<meta {attr}="{re.escape(key)}"[^>]*>'
    repl=f'<meta {attr}="{key}" content="{content}">'
    return re.sub(pat,repl,s,count=1) if re.search(pat,s) else s.replace('</head>',repl+'</head>',1)

for lang in ['en','ar']:
    for p in (root/lang).rglob('*.html'):
        s=p.read_text(encoding='utf-8')
        title=re.search(r'<title>(.*?)</title>',s,re.S)
        desc=re.search(r'<meta name="description" content="([^"]*)">',s)
        canon=re.search(r'<link rel="canonical" href="([^"]+)">',s)
        title=title.group(1).strip() if title else 'Ayman Esam | أيمن عصام'
        desc=desc.group(1).strip() if desc else ('Finance leadership, FP&A, financial control and transformation.' if lang=='en' else 'القيادة المالية والتخطيط والتحليل المالي والرقابة والتحول المالي.')
        canon=canon.group(1) if canon else 'https://aymanesam.com/'
        for attr,key,val in [
            ('property','og:type','profile' if p.name in ['index.html','about.html'] else 'website'),
            ('property','og:title',title),('property','og:description',desc),('property','og:url',canon),
            ('property','og:image',social_image),('property','og:image:alt','Ayman Esam | أيمن عصام'),
            ('property','og:site_name','Ayman Esam'),('property','og:locale','en_US' if lang=='en' else 'ar_SA'),
            ('name','twitter:card','summary_large_image'),('name','twitter:title',title),
            ('name','twitter:description',desc),('name','twitter:image',social_image)]:
            s=upsert_meta(s,attr,key,val)
        if 'hreflang="x-default"' not in s:
            xhref=canon if lang=='en' else canon.replace('/ar/','/en/')
            s=s.replace('</head>',f'<link rel="alternate" hreflang="x-default" href="{xhref}"></head>',1)
        if p.parent==root/lang and 'class="menu-toggle"' not in s:
            label='Menu' if lang=='en' else 'القائمة'
            s=s.replace('<div class="links">',f'<button class="menu-toggle" type="button" aria-expanded="false" aria-controls="site-links" aria-label="{label}"><span></span><span></span><span></span></button><div class="links" id="site-links">',1)
            js="""<script>(function(){const b=document.querySelector('.menu-toggle'),l=document.querySelector('.links');if(!b||!l)return;b.addEventListener('click',()=>{const o=b.getAttribute('aria-expanded')==='true';b.setAttribute('aria-expanded',String(!o));l.classList.toggle('open',!o)});l.querySelectorAll('a').forEach(a=>a.addEventListener('click',()=>{b.setAttribute('aria-expanded','false');l.classList.remove('open')}));})();</script>"""
            s=s.replace('</body>',js+'</body>',1)
        s=re.sub(r'custom-v12\.css\?v=\d+','custom-v12.css?v=17',s)
        p.write_text(s,encoding='utf-8')

p=root/'en/index.html'
s=p.read_text(encoding='utf-8')
m=re.search(r'<script type="application/ld\+json">(.*?)</script>',s,re.S)
if m:
    try:
        data=json.loads(m.group(1))
        data['email']='mailto:ayman.esam90@gmail.com'
        data['sameAs']=['https://www.linkedin.com/in/aymanisam/']
        data['knowsLanguage']=['English','Arabic']
        s=s[:m.start(1)]+json.dumps(data,ensure_ascii=False,separators=(',',':'))+s[m.end(1):]
        p.write_text(s,encoding='utf-8')
    except Exception:
        pass

cssp=root/'assets/custom-v12.css'
c=cssp.read_text(encoding='utf-8')
if '/* V17 mobile navigation */' not in c:
    c+='''\n/* V17 mobile navigation */\n.menu-toggle{display:none;margin-inline-start:auto;width:44px;height:44px;border:1px solid rgba(141,103,56,.24);border-radius:12px;background:rgba(255,255,255,.72);align-items:center;justify-content:center;flex-direction:column;gap:5px;cursor:pointer}.menu-toggle span{display:block;width:20px;height:2px;background:#2d302b;border-radius:99px;transition:.2s}.menu-toggle[aria-expanded="true"] span:nth-child(1){transform:translateY(7px) rotate(45deg)}.menu-toggle[aria-expanded="true"] span:nth-child(2){opacity:0}.menu-toggle[aria-expanded="true"] span:nth-child(3){transform:translateY(-7px) rotate(-45deg)}\n@media(max-width:850px){.nav{position:relative;flex-wrap:nowrap;padding:12px 16px}.menu-toggle{display:flex}.links{display:none!important;position:absolute;top:100%;left:12px;right:12px;width:auto!important;max-height:calc(100vh - 90px);overflow-y:auto!important;overflow-x:hidden!important;flex-direction:column;align-items:stretch;background:#fffdf9;border:1px solid rgba(65,57,48,.16);border-radius:16px;padding:10px;box-shadow:0 18px 45px rgba(65,52,38,.16);z-index:90}.links.open{display:flex!important}.links a{padding:12px 14px!important;border-bottom:0!important;border-radius:10px;font-size:14px!important}.links a:hover,.links a.current{background:rgba(181,138,82,.09)}.links .lang{margin-inline-start:0!important;text-align:center;margin-top:4px}.links .nav-cta{background:#2d302b;color:#fff!important;text-align:center}.hero{padding-top:34px!important}.hero-visual{min-height:430px!important}.hero-img{height:430px!important}.float-one{left:10px!important;bottom:24px!important}.float-two{right:10px!important;top:20px!important}.stats{grid-template-columns:1fr 1fr!important}.stat{padding:18px!important}.executive-panel,.book-panel,.feature-grid,.impact-band,.contact-grid{grid-template-columns:1fr!important}.client-carousel-shell{padding:0 44px!important}}\n@media(max-width:520px){.hero h1{font-size:48px!important}.hero h2{font-size:25px!important}.hero p,.lead{font-size:16px!important}.stats{grid-template-columns:1fr!important}.stat:not(:last-child){border-inline-end:0!important;border-bottom:1px solid rgba(65,57,48,.16)}.client-carousel-shell{padding:0 40px!important}.footer-grid{grid-template-columns:1fr!important}}\n'''
    cssp.write_text(c,encoding='utf-8')
