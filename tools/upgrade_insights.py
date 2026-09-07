from pathlib import Path
import re, json

root=Path('.')
img='https://aymanesam.com/assets/Gemini_Generated_Image_16oe0q16oe0q16oe.jpg'
portrait='../../assets/Gemini_Generated_Image_qzp1flqzp1flqzp1.jpg'

pairs={
'cash-flow-discipline.html':('Cash Flow Discipline Is a Management System','الانضباط في التدفقات النقدية نظام إداري','Treasury & Working Capital','الخزينة ورأس المال العامل'),
'finance-transformation.html':('Finance Transformation Beyond ERP','التحول المالي يتجاوز تطبيق ERP','Finance Transformation','التحول المالي'),
'budgeting-as-management-system.html':('Budgeting as a Management System','الموازنة كنظام إداري','Budgeting & Planning','الموازنات والتخطيط'),
'working-capital-discipline.html':('Working Capital Discipline','الانضباط في رأس المال العامل','Working Capital','رأس المال العامل'),
'month-end-close-discipline.html':('A Better Month-End Close','إقفال شهري أفضل','Financial Control','الرقابة المالية'),
'fp-and-a-for-better-decisions.html':('FP&A for Better Management Decisions','FP&A لقرارات إدارية أفضل','FP&A','FP&A')}

def meta_upsert(s,attr,key,val):
    pat=rf'<meta {attr}="{re.escape(key)}"[^>]*>'
    tag=f'<meta {attr}="{key}" content="{val}">'
    return re.sub(pat,tag,s,count=1) if re.search(pat,s) else s.replace('</head>',tag+'</head>',1)

def link_upsert(s,rel,href,hreflang=None):
    if hreflang:
        pat=rf'<link rel="{rel}" hreflang="{hreflang}"[^>]*>'
        tag=f'<link rel="{rel}" hreflang="{hreflang}" href="{href}">'
    else:
        return s
    return re.sub(pat,tag,s,count=1) if re.search(pat,s) else s.replace('</head>',tag+'</head>',1)

for lang in ('en','ar'):
    for p in (root/lang/'insights').glob('*.html'):
        if p.name not in pairs: continue
        s=p.read_text(encoding='utf-8')
        en_title,ar_title,en_cat,ar_cat=pairs[p.name]
        title=en_title if lang=='en' else ar_title
        cat=en_cat if lang=='en' else ar_cat
        canonical=f'https://aymanesam.com/{lang}/insights/{p.name}'
        other='ar' if lang=='en' else 'en'
        other_url=f'https://aymanesam.com/{other}/insights/{p.name}'
        descm=re.search(r'<meta name="description" content="([^"]*)">',s)
        desc=descm.group(1) if descm else (title+' by Ayman Esam.')
        page_title=(f'{title} | Ayman Esam | أيمن عصام')
        s=re.sub(r'<title>.*?</title>',f'<title>{page_title}</title>',s,count=1,flags=re.S)
        s=meta_upsert(s,'name','author','Ayman Esam')
        s=meta_upsert(s,'property','og:type','article')
        s=meta_upsert(s,'property','og:title',page_title)
        s=meta_upsert(s,'property','og:description',desc)
        s=meta_upsert(s,'property','og:url',canonical)
        s=meta_upsert(s,'property','og:image',img)
        s=meta_upsert(s,'property','og:image:alt','Ayman Esam | أيمن عصام')
        s=meta_upsert(s,'property','og:site_name','Ayman Esam')
        s=meta_upsert(s,'property','og:locale','en_US' if lang=='en' else 'ar_SA')
        s=meta_upsert(s,'property','og:locale:alternate','ar_SA' if lang=='en' else 'en_US')
        s=meta_upsert(s,'name','twitter:card','summary_large_image')
        s=meta_upsert(s,'name','twitter:title',page_title)
        s=meta_upsert(s,'name','twitter:description',desc)
        s=meta_upsert(s,'name','twitter:image',img)
        s=link_upsert(s,'alternate',f'https://aymanesam.com/en/insights/{p.name}','x-default')
        if 'custom-v12.css' not in s:
            s=s.replace('</head>','<link rel="stylesheet" href="../../assets/custom-v12.css?v=18"></head>',1)
        else:
            s=re.sub(r'custom-v12\.css\?v=\d+','custom-v12.css?v=18',s)
        s=re.sub(r'style\.css\?v=\d+','style.css?v=14',s)
        schema={"@context":"https://schema.org","@type":"Article","headline":title,"description":desc,"mainEntityOfPage":canonical,"inLanguage":lang,"image":img,"author":{"@type":"Person","name":"Ayman Esam","alternateName":"أيمن عصام","url":"https://aymanesam.com/"}}
        sch=f'<script type="application/ld+json">{json.dumps(schema,ensure_ascii=False,separators=(",",":"))}</script>'
        if '<script type="application/ld+json">' in s:
            s=re.sub(r'<script type="application/ld\+json">.*?</script>',sch,s,count=1,flags=re.S)
        else: s=s.replace('</head>',sch+'</head>',1)
        # standardize article nav
        label='Menu' if lang=='en' else 'القائمة'
        if 'class="menu-toggle"' not in s:
            s=s.replace('<div class="links">',f'<button class="menu-toggle" type="button" aria-expanded="false" aria-controls="site-links" aria-label="{label}"><span></span><span></span><span></span></button><div class="links" id="site-links">',1)
        if 'nav-cta' not in s:
            marker='<a class="lang"'
            s=s.replace(marker,('<a class="nav-cta" href="../book-service.html">'+('Book a Service' if lang=='en' else 'احجز خدمة')+'</a>'+marker),1)
        # author box after article opening
        if 'class="author-box"' not in s:
            author=(f'<div class="author-box"><img src="{portrait}" alt="Ayman Esam"><div><span>Written by</span><b>Ayman Esam</b><p>Group Financial Controller · FP&A · Finance Transformation</p></div></div>' if lang=='en' else f'<div class="author-box"><img src="{portrait}" alt="أيمن عصام"><div><span>بقلم</span><b>أيمن عصام</b><p>مدير رقابة مالية للمجموعة · FP&A · التحول المالي</p></div></div>')
            s=s.replace('<article class="wrap article-page">','<article class="wrap article-page">'+author,1)
        # upgrade CTA and related section before article close
        if 'class="related-insights"' not in s:
            rel_en=[('fp-and-a-for-better-decisions.html','FP&A for Better Management Decisions'),('budgeting-as-management-system.html','Budgeting as a Management System'),('working-capital-discipline.html','Working Capital Discipline'),('month-end-close-discipline.html','A Better Month-End Close')]
            rel_ar=[('fp-and-a-for-better-decisions.html','FP&A لقرارات إدارية أفضل'),('budgeting-as-management-system.html','الموازنة كنظام إداري'),('working-capital-discipline.html','الانضباط في رأس المال العامل'),('month-end-close-discipline.html','إقفال شهري أفضل')]
            rels=[x for x in (rel_en if lang=='en' else rel_ar) if x[0]!=p.name][:3]
            cards=''.join(f'<a href="{fn}"><b>{tx}</b><span>{"Finance Insight" if lang=="en" else "مقال مالي"}</span></a>' for fn,tx in rels)
            related=(f'<div class="article-cta"><div><b>Need focused finance support?</b><span>Explore advisory support across FP&A, cash flow, financial control and finance transformation.</span></div><a class="btn primary" href="../book-service.html">Book a Finance Service</a></div><div class="related-insights"><div class="eyebrow">Related Insights</div><h3>Continue reading</h3><div class="related-grid">{cards}</div></div>' if lang=='en' else f'<div class="article-cta"><div><b>هل تحتاج إلى دعم مالي مركز؟</b><span>استكشف خدمات FP&A والتدفقات النقدية والرقابة المالية والتحول المالي.</span></div><a class="btn primary" href="../book-service.html">احجز خدمة مالية</a></div><div class="related-insights"><div class="eyebrow">مقالات ذات صلة</div><h3>تابع القراءة</h3><div class="related-grid">{cards}</div></div>')
            s=s.replace('</article>',related+'</article>',1)
        # professional footer if old simple footer
        if '<footer><div class="wrap foot">' in s:
            footer=(f'<footer class="site-footer"><div class="wrap footer-grid"><div><div class="footer-brand">Ayman Esam</div><p>Group Financial Controller · FP&A · Finance Transformation</p><p>Al Khobar, Saudi Arabia</p></div><div><b>Quick Links</b><a href="../about.html">About</a><a href="../expertise.html">Expertise</a><a href="../experience.html">Experience</a><a href="../insights.html">Insights</a></div><div><b>Connect</b><a href="mailto:ayman.esam90@gmail.com">ayman.esam90@gmail.com</a><a href="https://www.linkedin.com/in/aymanisam/" target="_blank" rel="noopener">LinkedIn</a><a href="../book-service.html">Book a Service</a></div></div><div class="wrap footer-bottom"><span>© 2026 Ayman Esam</span><span>Finance Leadership · Saudi Arabia</span></div></footer>' if lang=='en' else f'<footer class="site-footer"><div class="wrap footer-grid"><div><div class="footer-brand">Ayman Esam | أيمن عصام</div><p>مدير رقابة مالية للمجموعة · FP&A · التحول المالي</p><p>الخبر، المملكة العربية السعودية</p></div><div><b>روابط سريعة</b><a href="../about.html">نبذة</a><a href="../expertise.html">الخبرات</a><a href="../experience.html">المسيرة</a><a href="../insights.html">المقالات</a></div><div><b>تواصل</b><a href="mailto:ayman.esam90@gmail.com">ayman.esam90@gmail.com</a><a href="https://www.linkedin.com/in/aymanisam/" target="_blank" rel="noopener">LinkedIn</a><a href="../book-service.html">احجز خدمة</a></div></div><div class="wrap footer-bottom"><span>© 2026 Ayman Esam</span><span>القيادة المالية · السعودية</span></div></footer>')
            s=re.sub(r'<footer><div class="wrap foot">.*?</footer>',footer,s,count=1,flags=re.S)
        if 'querySelector(\'.menu-toggle\')' not in s:
            js="<script>(function(){const b=document.querySelector('.menu-toggle'),l=document.querySelector('.links');if(!b||!l)return;b.addEventListener('click',()=>{const o=b.getAttribute('aria-expanded')==='true';b.setAttribute('aria-expanded',String(!o));l.classList.toggle('open',!o)});l.querySelectorAll('a').forEach(a=>a.addEventListener('click',()=>{b.setAttribute('aria-expanded','false');l.classList.remove('open')}));})();</script>"
            s=s.replace('</body>',js+'</body>',1)
        p.write_text(s,encoding='utf-8')

# landing pages: add author/positioning and CTA, bump CSS
for lang in ('en','ar'):
    p=root/lang/'insights.html'; s=p.read_text(encoding='utf-8')
    s=re.sub(r'custom-v12\.css\?v=\d+','custom-v12.css?v=18',s)
    if 'insights-author-intro' not in s:
        intro=(f'<div class="insights-author-intro"><img src="../assets/Gemini_Generated_Image_qzp1flqzp1flqzp1.jpg" alt="Ayman Esam"><div><div class="eyebrow">By Ayman Esam</div><h3>Finance insights built around management decisions.</h3><p>Practical thinking from a Group Financial Controller across FP&A, cash flow, controls, reporting and finance transformation.</p></div></div>' if lang=='en' else f'<div class="insights-author-intro"><img src="../assets/Gemini_Generated_Image_qzp1flqzp1flqzp1.jpg" alt="أيمن عصام"><div><div class="eyebrow">بقلم أيمن عصام</div><h3>مقالات مالية مبنية حول القرار الإداري.</h3><p>رؤية عملية من مدير رقابة مالية للمجموعة حول FP&A والتدفقات النقدية والرقابة والتقارير والتحول المالي.</p></div></div>')
        s=s.replace('<div class="article-grid">',intro+'<div class="article-grid">',1)
    s=s.replace('This section will continue to grow into a practical knowledge base around financial control, FP&A, cash flow, ERP and finance leadership in Saudi Arabia.','Explore the articles, then connect the ideas to your own finance function through focused advisory support.')
    s=s.replace('ستتطور هذه الصفحة إلى قاعدة معرفة عملية حول الرقابة المالية وFP&A والتدفقات النقدية والأنظمة والقيادة المالية في السعودية.','استكشف المقالات، ثم اربط الأفكار باحتياجات شركتك من خلال دعم مالي واستشاري مركز.')
    if 'insights-page-cta' not in s:
        cta=(f'<div class="insights-page-cta"><div><b>Turn finance insight into execution.</b><span>Need support with FP&A, cash flow, controls, budgeting or finance transformation?</span></div><a class="btn primary" href="book-service.html">Explore Finance Services</a></div>' if lang=='en' else f'<div class="insights-page-cta"><div><b>حوّل المعرفة المالية إلى تنفيذ.</b><span>تحتاج دعماً في FP&A أو التدفقات النقدية أو الرقابة أو الموازنات أو التحول المالي؟</span></div><a class="btn primary" href="book-service.html">استعرض الخدمات المالية</a></div>')
        s=s.replace('</div></div></main>',cta+'</div></div></main>',1)
    p.write_text(s,encoding='utf-8')

cssp=root/'assets/custom-v12.css'; c=cssp.read_text(encoding='utf-8')
if '/* V20 Insights authority */' not in c:
    c+='''\n/* V20 Insights authority */\n.insights-author-intro{display:grid;grid-template-columns:110px 1fr;gap:24px;align-items:center;margin:0 0 38px;padding:24px;border:1px solid var(--line);border-radius:22px;background:rgba(255,253,249,.88)}.insights-author-intro img{width:110px;height:110px;object-fit:cover;border-radius:18px}.insights-author-intro h3{margin:3px 0 7px;font-size:25px}.insights-author-intro p{margin:0;color:var(--muted)}.article-card{transition:transform .22s ease,box-shadow .22s ease,border-color .22s ease}.article-card:hover{transform:translateY(-4px);box-shadow:0 16px 38px rgba(67,54,40,.08);border-color:rgba(181,138,82,.35)}.author-box{display:grid;grid-template-columns:72px 1fr;gap:16px;align-items:center;margin:0 0 34px;padding:18px;border:1px solid var(--line);border-radius:18px;background:rgba(255,253,249,.86)}.author-box img{width:72px;height:72px;object-fit:cover;border-radius:14px}.author-box span{display:block;font-size:11px;color:var(--accent-dark);font-weight:800;text-transform:uppercase;letter-spacing:.08em}.author-box b{display:block;font-size:18px;color:var(--deep)}.author-box p{margin:2px 0 0!important;font-size:13px;color:var(--muted)}.article-cta span{display:block;color:var(--muted);font-size:13px;margin-top:4px}.related-insights{margin-top:48px}.related-insights h3{margin:5px 0 18px}.related-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}.related-grid a{display:block;padding:18px;border:1px solid var(--line);border-radius:16px;background:#fffdf9}.related-grid a b{display:block;color:var(--deep);margin-bottom:4px}.related-grid a span{font-size:12px;color:var(--muted)}.insights-page-cta{margin-top:34px;padding:25px;border-radius:20px;background:#2d302b;color:#fff;display:flex;justify-content:space-between;align-items:center;gap:20px}.insights-page-cta b{display:block;font-size:18px}.insights-page-cta span{display:block;color:#d4cec5;font-size:13px;margin-top:4px}@media(max-width:700px){.insights-author-intro{grid-template-columns:72px 1fr;gap:16px;padding:18px}.insights-author-intro img{width:72px;height:72px}.insights-author-intro h3{font-size:20px}.related-grid{grid-template-columns:1fr}.insights-page-cta{flex-direction:column;align-items:flex-start}.author-box{grid-template-columns:58px 1fr}.author-box img{width:58px;height:58px}}\n'''
cssp.write_text(c,encoding='utf-8')
