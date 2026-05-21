#!/usr/bin/env python3
"""Admin panel for szqyjs.com.cn - Form-based site management."""
import http.server, urllib.parse, os, json, re, base64, time, glob, html

ADMIN_PASSWORD = 'szqyjs668'
WWW = '/www/wwwroot/szqyjs.com.cn'
IMG_DIR = WWW + '/images'
DATA_DIR = WWW + '/data'
SITE_FILE = DATA_DIR + '/site-content.json'
MSG_FILE = DATA_DIR + '/messages.json'

# ====== HTML GENERATOR ======

def load_json(path):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def save_json(path, data):
    d = os.path.dirname(path)
    if not os.path.exists(d):
        os.makedirs(d)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def generate_html():
    sc = load_json(SITE_FILE) or {}
    comp = sc.get('company', {})
    hero = sc.get('hero', {})
    services = sc.get('services', [])
    cases = load_json(DATA_DIR + '/cases.json') or []
    news = load_json(DATA_DIR + '/news.json') or []
    news.sort(key=lambda x: x.get('date', ''), reverse=True)
    stats = hero.get('stats', [])

    # Render services
    svc_html = ''
    for s in services:
        img = s.get('image','')
        img_tag = f'<img src="{img}" alt="{html.escape(s.get("title",""))}" class="service-img">' if img else '<div class="service-icon">&#x1f3d7;</div>'
        svc_html += f'''        <div class="service-card">
          <div class="service-icon">{img_tag}</div>
          <h3>{html.escape(s.get('title',''))}</h3>
          <p>{html.escape(s.get('desc',''))}</p>
        </div>
'''

    # Render cases
    def cat_label(c):
        m = {'building':'房屋建筑','municipal':'市政工程','industrial':'工业项目'}
        return m.get(c, '工业项目')

    case_html = ''
    for c in cases:
        case_html += f'''        <div class="case-card" data-category="{c.get('category','building')}">
          <div class="case-img-placeholder"><img src="{c.get('image','')}" alt="{html.escape(c.get('title',''))}" class="case-img" loading="lazy"></div>
          <div class="case-info"><h4>{html.escape(c.get('title',''))}</h4>
          <p class="case-cat">{cat_label(c.get('category',''))}</p>
          <p>{html.escape(c.get('desc',''))}</p></div>
        </div>
'''

    if not case_html:
        case_html = '        <p style="text-align:center;color:#999;grid-column:1/-1">暂无案例</p>'

    # Render news
    news_html = ''
    for n in news:
        nimg = n.get('image','')
        nimg_tag = f'<img src="{nimg}" alt="{html.escape(n.get("title",""))}" loading="lazy">' if nimg else ''
        news_html += f'''        <div class="news-item" onclick="this.classList.toggle(\'expanded\')">
          <div class="news-item-header">
            <span class="news-item-date">{n.get('date','')}</span>
            <span class="news-item-title">{html.escape(n.get('title',''))}</span>
            <span class="news-item-arrow">&#9660;</span>
          </div>
          <div class="news-item-body">
            {nimg_tag}
            <p>{html.escape(n.get('summary',''))}</p>
          </div>
        </div>
'''
    if not news_html:
        news_html = '        <p style="text-align:center;color:#999">暂无新闻</p>'

    # Render highlights
    hl = comp.get('highlights', [])
    hl_html = '\n'.join(f'              <div class="highlight-item"><span class="highlight-icon">&#9989;</span><span>{html.escape(h)}</span></div>' for h in hl[:4])

    # Render stats
    stats_html = ''
    for st in stats[:4]:
        val = str(st.get('value', 0))
        sfx = str(st.get('suffix', ''))
        lbl = html.escape(st.get('label', ''))
        stats_html += f'''        <div class="stat-item">
          <span class="stat-number" data-count="{val}">{val}</span><span>{sfx}</span>
          <p>{lbl}</p>
        </div>
'''

    # Render cases filter buttons
    cat_btns = '<button class="filter-btn active" data-filter="all">全部</button>'
    for cat, name in [('building','房屋建筑'),('municipal','市政工程'),('industrial','工业项目')]:
        cat_btns += f'\n          <button class="filter-btn" data-filter="{cat}">{name}</button>'

    # Pre-compute conditional HTML to avoid f-string + raw-string concatenation
    cname = html.escape(comp.get('name',''))
    caddr = html.escape(comp.get('address',''))
    cphone = comp.get('phone','')
    cemail = comp.get('email','')
    cicp = comp.get('icp','')
    cfounded = comp.get('founded','')
    cabout_sub = html.escape(comp.get('about_subtitle',''))
    cabout1 = html.escape(comp.get('about_text1',''))
    cabout2 = html.escape(comp.get('about_text2',''))
    htitle = html.escape(hero.get('title',''))
    hsub = html.escape(hero.get('subtitle',''))
    logo_img = comp.get('logo','')
    hero_bg = hero.get('background_image','')
    about_img = comp.get('about_image','')
    qr_img = comp.get('qr_image','')
    logo_html = f'<img src="{logo_img}" alt="{cname}" class="logo-img">' if logo_img else '<span class="logo-icon">QY</span>'
    hero_attr = f' style="background: url({hero_bg}) center/cover no-repeat"' if hero_bg else ''
    about_img_html = f'<img src="{about_img}" alt="关于我们" class="about-real-img">' if about_img else '<div class="about-img-placeholder"><div class="img-icon">&#x1f3d7;</div></div>'
    qr_html_img = f'<img src="{qr_img}" alt="公众号二维码" class="qr-real-img">' if qr_img else '<div class="qr-placeholder">QR</div>'

    full = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{cname} - 专业项目管理服务</title>
  <meta name="description" content="{cname}，提供工程建设监理、工程造价咨询、招标代理、全过程项目管理等专业服务。">
  <meta name="baidu-site-verification" content="codeva-O90R15xA8b" />
  <meta name="keywords" content="苏州清韵项目管理,工程监理,造价咨询,招标代理,全过程项目管理,苏州项目管理公司,苏州清韵">
  <meta property="og:title" content="{cname}">
  <meta property="og:description" content="{cname}，提供工程监理、造价咨询、招标代理等全过程项目管理服务。">
  <meta property="og:type" content="website">
  <meta property="og:url" content="https://szqyjs.com.cn">
  <meta property="og:image" content="https://szqyjs.com.cn/images/og-image.jpg">
  <link rel="canonical" href="https://szqyjs.com.cn">
  <link rel="stylesheet" href="css/style-2026.css">
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "Organization",
    "name": "{cname}",
    "url": "https://szqyjs.com.cn",
    "description": "提供工程监理、造价咨询、招标代理、全过程项目管理等专业服务",
    "address": {{
      "@type": "PostalAddress",
      "streetAddress": "{caddr}",
      "addressLocality": "苏州市",
      "addressRegion": "江苏省"
    }},
    "telephone": "{cphone}",
    "email": "{cemail}",
    "foundingDate": "{cfounded}-08-05"
  }}
  </script>
</head>
<body>
  <nav class="navbar" id="navbar">
    <div class="container nav-container">
      <a href="#home" class="logo">
        {logo_html}
        <span class="logo-text">苏州清韵项目管理</span>
      </a>
      <ul class="nav-menu" id="navMenu">
        <li><a href="#home" class="nav-link active">首页</a></li>
        <li><a href="#about" class="nav-link">关于我们</a></li>
        <li><a href="#services" class="nav-link">服务项目</a></li>
        <li><a href="#cases" class="nav-link">客户案例</a></li>
        <li><a href="#news" class="nav-link">新闻动态</a></li>
        <li><a href="#contact" class="nav-link">联系我们</a></li>
      </ul>
      <div class="hamburger" id="hamburger">
        <span></span><span></span><span></span>
      </div>
    </div>
  </nav>

  <section class="hero" id="home"{hero_attr}>
    <div class="hero-overlay"></div>
    <div class="container hero-content">
      <h1 class="hero-title">{htitle}</h1>
      <p class="hero-subtitle">{hsub}</p>
      <div class="hero-btns">
        <a href="#services" class="btn btn-primary">了解服务</a>
        <a href="#contact" class="btn btn-outline">联系咨询</a>
      </div>
    </div>
    <div class="hero-stats">
      <div class="container stats-row">
{stats_html}
      </div>
    </div>
  </section>

  <section class="about section" id="about">
    <div class="container">
      <div class="section-header">
        <h2 class="section-title">关于我们</h2>
        <p class="section-subtitle">{cabout_sub}</p>
      </div>
      <div class="about-grid">
        <div class="about-image">
          {about_img_html}
        </div>
        <div class="about-text">
          <h3>{cname}</h3>
          <p>{cabout1}</p>
          <p>{cabout2}</p>
          <div class="about-highlights">
{hl_html}
          </div>
        </div>
      </div>
    </div>
  </section>

  <section class="services section bg-light" id="services">
    <div class="container">
      <div class="section-header">
        <h2 class="section-title">服务项目</h2>
        <p class="section-subtitle">全过程、全方位的项目管理解决方案</p>
      </div>
      <div class="services-grid">
{svc_html}
      </div>
    </div>
  </section>

  <section class="cases section" id="cases">
    <div class="container">
      <div class="section-header">
        <h2 class="section-title">客户案例</h2>
        <p class="section-subtitle">以实力赢得信赖，用成果说话</p>
      </div>
      <div class="cases-filter">
        {cat_btns}
      </div>
      <div class="cases-grid" id="casesGrid">
{case_html}
      </div>
    </div>
  </section>

  <section class="news section bg-light" id="news">
    <div class="container">
      <div class="section-header">
        <h2 class="section-title">新闻动态</h2>
        <p class="section-subtitle">了解公司最新资讯与行业动态</p>
      </div>
      <div class="news-grid" id="newsGrid">
{news_html}
      </div>
    </div>
  </section>

  <section class="contact section" id="contact">
    <div class="container">
      <div class="section-header">
        <h2 class="section-title">联系我们</h2>
        <p class="section-subtitle">期待与您的合作，欢迎随时联系我们</p>
      </div>
      <div class="contact-grid">
        <div class="contact-info">
          <div class="contact-item">
            <span class="contact-icon">&#x1f4cd;</span>
            <div>
              <h4>公司地址</h4>
              <p>{caddr}</p>
            </div>
          </div>
          <div class="contact-item">
            <span class="contact-icon">&#x1f4de;</span>
            <div>
              <h4>联系电话</h4>
              <p>{cphone}</p>
            </div>
          </div>
          <div class="contact-item">
            <span class="contact-icon">&#x2709;</span>
            <div>
              <h4>电子邮箱</h4>
              <p>{cemail}</p>
            </div>
          </div>
          <div class="contact-item">
            <span class="contact-icon">&#x1f310;</span>
            <div>
              <h4>工作时间</h4>
              <p>周一至周五 9:00 - 18:00</p>
            </div>
          </div>
        </div>
        <form class="contact-form" id="contactForm">
          <div class="form-row">
            <div class="form-group">
              <label for="uname">姓名 *</label>
              <input type="text" id="uname" name="name" placeholder="请输入您的姓名" required>
            </div>
            <div class="form-group">
              <label for="uphone">电话 *</label>
              <input type="tel" id="uphone" name="phone" placeholder="请输入您的电话" required>
            </div>
          </div>
          <div class="form-group">
            <label for="uemail">邮箱</label>
            <input type="email" id="uemail" name="email" placeholder="请输入您的邮箱">
          </div>
          <div class="form-group">
            <label for="uservice">咨询类型</label>
            <select id="uservice" name="service">
              <option value="">请选择咨询类型</option>
              <option value="监理">工程监理</option>
              <option value="造价">造价咨询</option>
              <option value="招标">招标代理</option>
              <option value="全过程">全过程项目管理</option>
              <option value="其他">其他</option>
            </select>
          </div>
          <div class="form-group">
            <label for="umsg">留言内容 *</label>
            <textarea id="umsg" name="message" rows="4" placeholder="请描述您的需求..." required></textarea>
          </div>
          <button type="submit" class="btn btn-primary btn-submit">提交留言</button>
        </form>
      </div>
    </div>
  </section>

  <footer class="footer">
    <div class="container footer-grid">
      <div class="footer-about">
        <h3>苏州清韵项目管理</h3>
        <p>以专业能力和诚信服务，为客户创造价值，为行业发展助力。</p>
      </div>
      <div class="footer-links">
        <h4>快速链接</h4>
        <ul>
          <li><a href="#about">关于我们</a></li>
          <li><a href="#services">服务项目</a></li>
          <li><a href="#cases">客户案例</a></li>
          <li><a href="#news">新闻动态</a></li>
        </ul>
      </div>
      <div class="footer-services">
        <h4>服务项目</h4>
        <ul>
          <li><a href="#services">工程监理</a></li>
          <li><a href="#services">造价咨询</a></li>
          <li><a href="#services">招标代理</a></li>
          <li><a href="#services">全过程项目管理</a></li>
        </ul>
      </div>
      <div class="footer-qr">
        <h4>关注我们</h4>
        {qr_html_img}
        <p>扫码关注公众号</p>
      </div>
    </div>
    <div class="footer-bottom">
      <div class="container">
        <p>&copy; 2026 {cname} 版权所有 | <a href="https://beian.miit.gov.cn/" target="_blank" rel="nofollow" style="color:rgba(255,255,255,.5)">{cicp}</a></p>
      </div>
    </div>
  </footer>

  <script>
(function() {{'use strict';
var navbar=document.getElementById('navbar');
function onScroll(){{navbar.classList.toggle('scrolled',window.scrollY>60);updateActiveNav();}}
function updateActiveNav(){{var ss=document.querySelectorAll('section[id]');var ls=document.querySelectorAll('.nav-link');var c='';ss.forEach(function(s){{if(window.scrollY>=s.offsetTop-120)c=s.getAttribute('id');}});ls.forEach(function(l){{l.classList.toggle('active',l.getAttribute('href')==='#'+c);}});}}
var hb=document.getElementById('hamburger'),nm=document.getElementById('navMenu');
hb.addEventListener('click',function(){{nm.classList.toggle('active');}});
nm.querySelectorAll('a').forEach(function(a){{a.addEventListener('click',function(){{nm.classList.remove('active');}});}});
document.querySelectorAll('a[href^="#"]').forEach(function(a){{a.addEventListener('click',function(e){{e.preventDefault();var t=document.querySelector(this.getAttribute('href'));if(t)window.scrollTo({{top:t.offsetTop-70,behavior:'smooth'}});}});}});
function animateCounters(){{var ss=document.querySelectorAll('.stat-number');var started=false;function sc(el){{var t=parseInt(el.getAttribute('data-count')),c=0,d=2000,step=Math.ceil(t/(d/30));var ti=setInterval(function(){{c+=step;if(c>=t){{c=t;clearInterval(ti);}}el.textContent=c;}},30);}}function check(){{if(started)return;ss.forEach(function(el){{var r=el.getBoundingClientRect();{started=true;ss.forEach(function(s){{sc(s);}});}}});}}window.addEventListener('scroll',check);check();}}
function catLabel(c){{return c==='building'?'房屋建筑':c==='municipal'?'市政工程':'工业项目';}}
function loadCases(){{var g=document.getElementById('casesGrid');if(!g)return;fetch('/data/cases.json').then(function(r){{return r.json();}}).then(function(d){{if(!d.length)return;var h='';d.forEach(function(c){{h+='<div class="case-card" data-category="'+c.category+'"><div class="case-img-placeholder"><img src="'+c.image+'" alt="'+c.title+'" class="case-img" loading="lazy"></div><div class="case-info"><h4>'+c.title+'</h4><p class="case-cat">'+catLabel(c.category)+'</p><p>'+c.desc+'</p></div></div>';}});if(h)g.innerHTML=h;initCaseFilter();}}).catch(function(){{initCaseFilter();}});}}
function initCaseFilter(){{var fbs=document.querySelectorAll('.filter-btn');fbs.forEach(function(b){{var nb=b.cloneNode(true);b.parentNode.replaceChild(nb,b);}});fbs=document.querySelectorAll('.filter-btn');fbs.forEach(function(b){{b.addEventListener('click',function(){{fbs.forEach(function(x){{x.classList.remove('active');}});b.classList.add('active');var f=b.getAttribute('data-filter');document.querySelectorAll('.case-card').forEach(function(c){{c.style.display=(f==='all'||c.getAttribute('data-category')===f)?'':'none';}});}});}});}}
function loadNews(){{var g=document.getElementById('newsGrid');if(!g)return;fetch('/data/news.json').then(function(r){{return r.json();}}).then(function(d){{if(!d.length)return;d.sort(function(a,b){{return(b.date||'').localeCompare(a.date||'');}});var h='';d.forEach(function(n){{h+='<div class="news-item" onclick="this.classList.toggle(\'expanded\')"><div class="news-item-header"><span class="news-item-date">'+n.date+'</span><span class="news-item-title">'+n.title+'</span><span class="news-item-arrow">&#9660;</span></div><div class="news-item-body">'+(n.image?'<img src="'+n.image+'" alt="'+n.title+'" loading="lazy">':'')+'<p>'+n.summary+'</p></div></div>';}});if(h)g.innerHTML=h;}}).catch(function(){{}});}}
window.addEventListener('scroll',onScroll,{{passive:true}});onScroll();animateCounters();loadCases();loadNews();
}})();
  </script>
  <script>
document.getElementById('contactForm').addEventListener('submit',function(e){{e.preventDefault();var f=e.target,b=f.querySelector('.btn-submit'),ot=b.textContent;b.textContent='提交中...';b.disabled=true;var p='name='+encodeURIComponent(f.name.value)+'&phone='+encodeURIComponent(f.phone.value)+'&email='+encodeURIComponent(f.email.value)+'&service='+encodeURIComponent(f.service.value)+'&message='+encodeURIComponent(f.message.value);fetch('/admin/contact',{{method:'POST',headers:{{'Content-Type':'application/x-www-form-urlencoded'}},body:p}}).then(function(r){{return r.json();}}).then(function(d){{if(d.ok){{b.textContent='提交成功！';b.style.background='#28a745';b.style.borderColor='#28a745';f.reset();}}else{{b.textContent=d.error||'失败';b.style.background='#e74c3c';b.style.borderColor='#e74c3c';}}}}).catch(function(){{b.textContent='网络错误';b.style.background='#e74c3c';b.style.borderColor='#e74c3c';}}).then(function(){{setTimeout(function(){{b.textContent=ot;b.style.background='';b.style.borderColor='';b.disabled=false;}},2500);}});}});
  </script>
  <script>
  (function(){{var bp=document.createElement('script');var curProtocol=window.location.protocol.split(':')[0];if(curProtocol==='https'){{bp.src='https://zz.bdstatic.com/linksubmit/push.js';}}else{{bp.src='http://push.zhanzhang.baidu.com/push.js';}}var s=document.getElementsByTagName('script')[0];s.parentNode.insertBefore(bp,s);}})();
  </script>
</body>
</html>'''

    with open(WWW + '/index.html', 'w', encoding='utf-8') as fp:
        fp.write(full)
    return True


# ====== PAGES ======

def page_login():
    return r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>网站后台 - 苏州清韵</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:"PingFang SC","Microsoft YaHei",sans-serif;background:linear-gradient(135deg,#1a3a5c,#2c5f8a);min-height:100vh;display:flex;align-items:center;justify-content:center}
.box{background:#fff;padding:40px;border-radius:12px;box-shadow:0 20px 60px rgba(0,0,0,.3);width:400px;max-width:90%}
.box h2{text-align:center;color:#1a3a5c;margin-bottom:6px;font-size:24px}
.box .sub{text-align:center;color:#999;margin-bottom:24px;font-size:14px}
.box label{display:block;color:#333;margin-bottom:6px;font-size:14px}
.box input{width:100%;padding:12px 14px;border:1px solid #ddd;border-radius:6px;font-size:15px;outline:none;transition:.3s}
.box input:focus{border-color:#2c5f8a;box-shadow:0 0 0 3px rgba(44,95,138,.1)}
.btn{width:100%;padding:13px;background:#c9a84c;color:#fff;border:none;border-radius:6px;font-size:16px;cursor:pointer;margin-top:16px}
.btn:hover{background:#b8922f}
.err{color:#e74c3c;text-align:center;margin-top:12px;font-size:14px;display:none}
</style>
</head>
<body>
<div class="box">
<h2>网站后台管理</h2><p class="sub">苏州清韵项目管理有限公司</p>
<div><label>管理密码</label><input type="password" id="pwd" placeholder="请输入管理密码"></div>
<button class="btn" onclick="login()">登 录</button>
<p class="err" id="err">密码错误，请重试</p>
</div>
<script>
function login(){var p=document.getElementById("pwd").value;if(p){document.cookie="t="+btoa(p)+";path=/";setTimeout(function(){location.href=location.pathname+"?t="+Date.now();},100);}}
</script>
</body>
</html>'''


def page_admin(sc):
    comp = sc.get('company', {})
    hero = sc.get('hero', {})
    services = sc.get('services', [])
    stats = hero.get('stats', [])
    hl = comp.get('highlights', [])

    # fill empty service slots
    while len(services) < 6:
        services.append({'icon': '', 'title': '', 'desc': ''})
    while len(stats) < 4:
        stats.append({'label': '', 'value': 0, 'suffix': ''})
    while len(hl) < 4:
        hl.append('')

    def esc(s):
        if s is None: return ''
        return str(s).replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace('"','&quot;')

    # Build services form rows - dynamic
    svc_rows = ''
    for i, s in enumerate(services):
        img_tag = f'<img src="../{esc(s.get("image",""))}" style="width:60px;height:45px;object-fit:cover;border-radius:4px">' if s.get('image','') else ''
        img_html = f'<div class="svc-thumb" id="svcThumb{i}" style="display:{"block" if img_tag else "none"}">{img_tag}</div>'
        svc_rows += f'''<div class="svc-row" id="svcRow{i}">
  <span class="svc-idx">#{i+1}</span>
  <div class="svc-img-box">
    {img_html}
    <button onclick="uploadSvcImg({i})" class="btn-sm">上传图片</button>
    <input type="hidden" id="svcImg{i}" value="{esc(s.get('image',''))}" data-svc="{i}" data-field="image">
  </div>
  <input value="{esc(s.get('title',''))}" placeholder="服务名称" data-svc="{i}" data-field="title" style="flex:1">
  <textarea placeholder="服务描述" data-svc="{i}" data-field="desc" rows="2" style="flex:2">{esc(s.get('desc',''))}</textarea>
  <button onclick="deleteSvc({i})" class="btn-sm btn-del" title="删除此服务">✕</button>
</div>
'''
    # Empty placeholder row template (hidden, used by JS)
    empty_row_tpl = r'''<div class="svc-row" id="svcRow{i}">
  <span class="svc-idx">#{n}</span>
  <div class="svc-img-box">
    <div class="svc-thumb" id="svcThumb{i}" style="display:none"></div>
    <button onclick="uploadSvcImg({i})" class="btn-sm">上传图片</button>
    <input type="hidden" id="svcImg{i}" value="" data-svc="{i}" data-field="image">
  </div>
  <input value="" placeholder="服务名称" data-svc="{i}" data-field="title" style="flex:1">
  <textarea placeholder="服务描述" data-svc="{i}" data-field="desc" rows="2" style="flex:2">{desc}</textarea>
  <button onclick="deleteSvc({i})" class="btn-sm btn-del" title="删除此服务">✕</button>
</div>'''

    # Build stats form rows
    stat_rows = ''
    labels = ['服务客户', '完成项目', '客户满意度(%)', '行业经验(年)']
    for i, s in enumerate(stats[:4]):
        lb = esc(s.get('label', labels[i] if i < len(labels) else ''))
        vl = str(s.get('value', 0))
        sf = esc(s.get('suffix', '+'))
        stat_rows += f'''<div class="stat-row">
  <input value="{lb}" placeholder="标签" data-stat="{i}" data-field="label" style="flex:2">
  <input value="{vl}" placeholder="数字" data-stat="{i}" data-field="value" type="number" style="flex:1">
  <input value="{sf}" placeholder="后缀" data-stat="{i}" data-field="suffix" style="flex:1;max-width:60px">
</div>
'''

    # Build highlights form
    hl_rows = ''
    for i, h in enumerate(hl[:4]):
        hl_rows += f'<input value="{esc(h)}" placeholder="亮点{i+1}" data-hl="{i}" style="flex:1">'

    # Escape company values
    c_vals = {k: esc(comp.get(k, '')) for k in ['name','address','phone','email','icp','founded','about_subtitle','about_text1','about_text2','logo','about_image','qr_image']}

    return r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>网站后台管理</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:"PingFang SC","Microsoft YaHei",sans-serif;background:#f0f2f5}
.top{background:#1a3a5c;color:#fff;padding:10px 24px;display:flex;align-items:center;gap:16px;flex-wrap:wrap}
.top h2{font-size:18px}
.top .tabs{display:flex;gap:4px;margin-left:20px}
.top .tabs button{padding:8px 18px;border:1px solid rgba(255,255,255,.3);background:transparent;color:rgba(255,255,255,.8);border-radius:4px 4px 0 0;cursor:pointer;font-size:14px;transition:.2s;white-space:nowrap}
.top .tabs button.active{background:#fff;color:#1a3a5c;border-color:#fff;font-weight:600}
.bar{background:#fff;padding:10px 24px;border-bottom:1px solid #e5e5e5;display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.bar button{padding:8px 18px;border-radius:4px;border:1px solid #ddd;font-size:13px;cursor:pointer;background:#fff;white-space:nowrap}
.bar button.save{background:#27ae60;color:#fff;border-color:#27ae60}
.bar button.exit{background:#e74c3c;color:#fff;border-color:#e74c3c;margin-left:auto}
.panel{display:none;padding:24px;overflow-y:auto;max-height:calc(100vh - 140px)}
.panel.active{display:block}
.panel h3{color:#1a3a5c;margin-bottom:16px;font-size:18px;border-bottom:2px solid #c9a84c;padding-bottom:8px}
.card{background:#fff;border-radius:8px;padding:24px;margin-bottom:20px;box-shadow:0 2px 8px rgba(0,0,0,.06)}
.card h4{color:#1a3a5c;margin-bottom:16px;font-size:15px;display:flex;align-items:center;gap:8px}
.form-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.form-grid.col3{grid-template-columns:1fr 1fr 1fr}
.form-group{display:flex;flex-direction:column}
.form-group label{font-size:13px;color:#666;margin-bottom:4px}
.form-group input,.form-group textarea,.form-group select{padding:10px 12px;border:1px solid #ddd;border-radius:4px;font-size:14px;font-family:inherit;outline:none;resize:vertical}
.form-group input:focus,.form-group textarea:focus{border-color:#2c5f8a;box-shadow:0 0 0 3px rgba(44,95,138,.1)}
.form-full{grid-column:1/-1}

/* Services */
.svc-row{display:flex;gap:10px;margin-bottom:10px;align-items:center;flex-wrap:wrap}
.svc-row .svc-idx{font-weight:700;color:#c9a84c;min-width:24px}
.svc-row input,.svc-row textarea{padding:8px 10px;border:1px solid #ddd;border-radius:4px;font-size:13px;font-family:inherit;outline:none;flex:1}
.svc-row textarea{resize:vertical;min-width:200px}
.svc-row .svc-img-box{width:80px;display:flex;flex-direction:column;align-items:center;gap:4px}
.svc-row .svc-img-box img{width:60px;height:45px;object-fit:cover;border-radius:4px;border:1px solid #eee}
.svc-thumb{width:60px;height:45px;border:1px dashed #ddd;border-radius:4px;display:flex;align-items:center;justify-content:center}
.btn-sm{padding:4px 8px;border-radius:3px;border:1px solid #ddd;font-size:11px;cursor:pointer;background:#fff;white-space:nowrap}
.btn-sm.add{background:#27ae60;color:#fff;border-color:#27ae60}
.btn-sm.btn-del{background:#fff;color:#e74c3c;border-color:#e74c3c;font-weight:700}
.svc-row .btn-del{margin-left:4px;align-self:center}

/* Stats */
.stat-row{display:flex;gap:10px;margin-bottom:8px}
.stat-row input{padding:8px 10px;border:1px solid #ddd;border-radius:4px;font-size:13px;font-family:inherit;outline:none}

/* Cases / News tables */
.toolbar{display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap}
.toolbar button{padding:8px 18px;border-radius:4px;border:1px solid #ddd;font-size:13px;cursor:pointer;background:#fff}
.toolbar button.add{background:#27ae60;color:#fff;border-color:#27ae60}
table{width:100%;border-collapse:collapse;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.06)}
th,td{padding:12px 14px;text-align:left;border-bottom:1px solid #eee;font-size:14px}
th{background:#f8f9fa;color:#1a3a5c;font-weight:600}
tr:hover{background:#fafbfc}
td img{width:60px;height:45px;object-fit:cover;border-radius:4px}
td .act button{padding:4px 10px;margin:0 2px;border-radius:3px;border:1px solid #ddd;font-size:12px;cursor:pointer;background:#fff}
td .act .edit{color:#2c5f8a;border-color:#2c5f8a}
td .act .del{color:#e74c3c;border-color:#e74c3c}
.img-preview{max-width:120px;max-height:90px;object-fit:contain;border-radius:4px;margin-top:6px;border:1px solid #eee}

/* Modal */
.modal{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.5);z-index:10000;align-items:center;justify-content:center}
.modal.open{display:flex}
.modal-box{background:#fff;border-radius:12px;padding:30px;width:520px;max-width:90%;max-height:80vh;overflow-y:auto;box-shadow:0 20px 60px rgba(0,0,0,.3)}
.modal-box h3{color:#1a3a5c;margin-bottom:20px}
.modal-box label{display:block;font-size:13px;color:#666;margin-bottom:4px;margin-top:12px}
.modal-box input,.modal-box select,.modal-box textarea{width:100%;padding:10px 12px;border:1px solid #ddd;border-radius:4px;font-size:14px;font-family:inherit;outline:none}
.modal-box input:focus,.modal-box select:focus,.modal-box textarea:focus{border-color:#2c5f8a}
.modal-box textarea{resize:vertical;min-height:80px}
.modal-box .img-preview{width:120px;height:90px;object-fit:cover;border-radius:4px;margin-top:8px;border:1px solid #eee}
.modal-btns{display:flex;gap:8px;margin-top:20px;justify-content:flex-end}
.modal-btns button{padding:10px 24px;border-radius:4px;border:1px solid #ddd;font-size:14px;cursor:pointer}
.modal-btns .btn-save{background:#27ae60;color:#fff;border-color:#27ae60}
.modal-btns .btn-cancel{background:#fff;color:#666}
.toast{position:fixed;top:20px;right:20px;padding:12px 24px;border-radius:6px;color:#fff;font-size:14px;z-index:9999;display:none}
.toast.ok{background:#27ae60}
.toast.er{background:#e74c3c}
.img-upload-row{display:flex;gap:8px}.img-upload-row input{flex:1}.img-upload-row button{padding:8px 14px;border:1px solid #2c5f8a;border-radius:4px;cursor:pointer;font-size:13px;background:#fff;color:#2c5f8a;white-space:nowrap}
.note{font-size:12px;color:#999;margin-top:8px}
.service-img{width:60px;height:60px;object-fit:contain;display:block;margin:0 auto}
</style>
</head>
<body>
<div class="top">
<h2>网站后台管理</h2>
<div class="tabs">
<button class="active" onclick="switchTab('site')">网站信息</button>
<button onclick="switchTab('cases')">案例管理</button>
<button onclick="switchTab('news')">新闻管理</button>
<button onclick="switchTab('msgs')">留言管理</button>
</div>
</div>

<!-- Tab 1: Site Info -->
<div class="panel active" id="panel-site">

<div class="bar">
<button class="save" onclick="saveSite()">保存网站信息</button>
<span class="note" style="margin-left:8px">保存后网站自动更新</span>
<button class="exit" onclick="logout()">退出</button>
</div>

<div class="card">
<h4>公司信息</h4>
<div class="form-grid">
<div class="form-group"><label>公司名称</label><input value="''' + c_vals['name'] + r'''" data-field="company.name"></div>
<div class="form-group"><label>Logo 图片</label><div class="img-upload-row"><input value="''' + c_vals['logo'] + r'''" data-field="company.logo" placeholder="images/logo.png"><button type="button" onclick="uploadToField('company.logo','logoPreview')">上传</button></div><img class="img-preview" id="logoPreview"''' + (f' src="../{c_vals["logo"]}" style="display:block"' if c_vals['logo'] else ' style="display:none"') + r'''></div>
<div class="form-group"><label>地址</label><input value="''' + c_vals['address'] + r'''" data-field="company.address"></div>
<div class="form-group"><label>电话</label><input value="''' + c_vals['phone'] + r'''" data-field="company.phone"></div>
<div class="form-group"><label>邮箱</label><input value="''' + c_vals['email'] + r'''" data-field="company.email"></div>
<div class="form-group"><label>ICP备案号</label><input value="''' + c_vals['icp'] + r'''" data-field="company.icp"></div>
<div class="form-group"><label>成立年份</label><input value="''' + c_vals['founded'] + r'''" data-field="company.founded"></div>
<div class="form-group form-full"><label>关于我们 - 副标题</label><input value="''' + c_vals['about_subtitle'] + r'''" data-field="company.about_subtitle"></div>
<div class="form-group form-full"><label>关于我们 - 第一段</label><textarea data-field="company.about_text1" rows="3">''' + c_vals['about_text1'] + r'''</textarea></div>
<div class="form-group form-full"><label>关于我们 - 第二段</label><textarea data-field="company.about_text2" rows="3">''' + c_vals['about_text2'] + r'''</textarea></div>
<div class="form-group form-full"><label>关于我们 - 配图</label><div class="img-upload-row"><input value="''' + c_vals['about_image'] + r'''" data-field="company.about_image" placeholder="images/about.jpg"><button type="button" onclick="uploadToField('company.about_image','aboutPreview')">上传</button></div><img class="img-preview" id="aboutPreview"''' + (f' src="../{c_vals["about_image"]}" style="display:block"' if c_vals['about_image'] else ' style="display:none"') + r'''></div>
<div class="form-group form-full"><label>公众号二维码</label><div class="img-upload-row"><input value="''' + c_vals['qr_image'] + r'''" data-field="company.qr_image" placeholder="images/qr.jpg"><button type="button" onclick="uploadToField('company.qr_image','qrPreview')">上传</button></div><img class="img-preview" id="qrPreview"''' + (f' src="../{c_vals["qr_image"]}" style="display:block"' if c_vals['qr_image'] else ' style="display:none"') + r'''></div>
</div>
<div style="margin-top:12px"><label style="font-size:13px;color:#666">资质亮点（4个）</label>
<div style="display:flex;gap:8px;margin-top:4px">
''' + hl_rows + r'''
</div></div>
</div>

<div class="card">
<h4>首页横幅</h4>
<div class="form-grid">
<div class="form-group form-full"><label>背景图片</label><div class="img-upload-row"><input value="''' + esc(hero.get('background_image','')) + r'''" data-field="hero.background_image" placeholder="images/hero-bg.jpg"><button type="button" onclick="uploadToField('hero.background_image','heroBgPreview')">上传</button></div><img class="img-preview" id="heroBgPreview"''' + (f' src="../{esc(hero.get("background_image",""))}" style="display:block"' if hero.get('background_image','') else ' style="display:none"') + r'''></div>
<div class="form-group form-full"><label>大标题</label><input value="''' + esc(hero.get('title','')) + r'''" data-field="hero.title"></div>
<div class="form-group form-full"><label>副标题</label><textarea data-field="hero.subtitle" rows="2">''' + esc(hero.get('subtitle','')) + r'''</textarea></div>
</div>
<div style="margin-top:12px"><label style="font-size:13px;color:#666">统计数字（4个）</label>
''' + stat_rows + r'''
</div>
</div>

<div class="card">
<h4>服务项目 <button onclick="addSvc()" class="btn-sm add" style="margin-left:8px">+ 添加服务</button></h4>
<div id="svcContainer">
''' + svc_rows + r'''</div>
</div>

</div>

<!-- Tab 2: Case Management -->
<div class="panel" id="panel-cases">
<div class="toolbar">
<button class="add" onclick="openCaseModal()">+ 添加案例</button>
<button onclick="loadCaseTable()">刷新列表</button>
</div>
<table><thead><tr><th>图片</th><th>项目名称</th><th>分类</th><th>描述</th><th>操作</th></tr></thead>
<tbody id="caseTableBody"><tr><td colspan="5" style="color:#999;text-align:center">加载中...</td></tr></tbody></table>
</div>

<!-- Tab 3: News Management -->
<div class="panel" id="panel-news">
<div class="toolbar">
<button class="add" onclick="openNewsModal()">+ 添加新闻</button>
<button onclick="loadNewsTable()">刷新列表</button>
</div>
<table><thead><tr><th>图片</th><th>日期</th><th>标题</th><th>摘要</th><th>操作</th></tr></thead>
<tbody id="newsTableBody"><tr><td colspan="5" style="color:#999;text-align:center">加载中...</td></tr></tbody></table>
</div>

<!-- Tab 4: Messages -->
<div class="panel" id="panel-msgs">
<div class="toolbar">
<span class="note" id="msgNote">0 条留言</span>
<span id="msgPageNav" style="margin-left:16px"></span>
</div>
<table><thead><tr><th>状态</th><th>时间</th><th>姓名</th><th>电话</th><th>邮箱</th><th>咨询类型</th><th>留言内容</th><th>操作</th></tr></thead>
<tbody id="msgTableBody"><tr><td colspan="8" style="color:#999;text-align:center">加载中...</td></tr></tbody></table>
</div>

<!-- Case Modal -->
<div class="modal" id="caseModal">
<div class="modal-box">
<h3 id="caseModalTitle">添加案例</h3>
<input type="hidden" id="caseId">
<label>项目名称 *</label><input id="caseTitle" placeholder="如：恒隆商业广场">
<label>分类</label><select id="caseCat"><option value="building">房屋建筑</option><option value="municipal">市政工程</option><option value="industrial">工业项目</option></select>
<label>图片</label>
<div style="display:flex;gap:8px;align-items:center">
<input id="caseImg" placeholder="images/xxx.jpg" style="flex:1">
<button onclick="document.getElementById('caseImgUpload').click()" style="padding:8px 12px;border:1px solid #ddd;border-radius:4px;cursor:pointer;font-size:13px;background:#fff;white-space:nowrap">上传图片</button>
</div>
<input type="file" id="caseImgUpload" accept="image/*" style="display:none" onchange="uploadCaseImg()">
<img class="img-preview" id="caseImgPreview" style="display:none">
<label>描述</label><textarea id="caseDesc" placeholder="项目简介..."></textarea>
<div class="modal-btns">
<button class="btn-cancel" onclick="closeCaseModal()">取消</button>
<button class="btn-save" onclick="saveCase()">保存</button>
</div>
</div>
</div>

<!-- News Modal -->
<div class="modal" id="newsModal">
<div class="modal-box">
<h3 id="newsModalTitle">添加新闻</h3>
<input type="hidden" id="newsId">
<label>标题 *</label><input id="newsTitle" placeholder="新闻标题">
<label>日期</label><input type="date" id="newsDate">
<label>图片</label>
<div style="display:flex;gap:8px;align-items:center">
<input id="newsImg" placeholder="images/xxx.jpg" style="flex:1">
<button onclick="document.getElementById('newsImgUpload').click()" style="padding:8px 12px;border:1px solid #ddd;border-radius:4px;cursor:pointer;font-size:13px;background:#fff;white-space:nowrap">上传图片</button>
</div>
<input type="file" id="newsImgUpload" accept="image/*" style="display:none" onchange="uploadNewsImg()">
<img class="img-preview" id="newsImgPreview" style="display:none">
<label>摘要</label><textarea id="newsSummary" placeholder="新闻摘要..."></textarea>
<div class="modal-btns">
<button class="btn-cancel" onclick="closeNewsModal()">取消</button>
<button class="btn-save" onclick="saveNews()">保存</button>
</div>
</div>
</div>

<div class="toast" id="toast"></div>

<script>
var activeTab="site";

function toast(t,c){var e=document.getElementById("toast");e.textContent=t;e.className="toast "+c;e.style.display="block";clearTimeout(e._t);e._t=setTimeout(function(){e.style.display="none"},2500);}
function logout(){document.cookie="t=;path=/;max-age=0";location.reload();}

function switchTab(tab){
  activeTab=tab;
  document.querySelectorAll(".panel").forEach(function(p){p.classList.remove("active");});
  document.getElementById("panel-"+tab).classList.add("active");
  document.querySelectorAll(".tabs button").forEach(function(b){b.classList.remove("active");});
  if(tab==="cases"){loadCaseTable();}
  if(tab==="news"){loadNewsTable();}
  if(tab==="msgs"){loadMsgTable();startMsgPoll();}
  else{stopMsgPoll();}
}

/* ====== Generic image upload-to-field ====== */
function uploadToField(fieldName, previewId){
  var inp=document.createElement("input");
  inp.type="file";inp.accept="image/*";
  inp.style.display="none";
  document.body.appendChild(inp);
  inp.onchange=function(){
    var f=inp.files[0];if(!f)return;
    var fd=new FormData();fd.append("img",f);
    toast("上传中...","ok");
    fetch("/admin/upload",{method:"POST",body:fd})
    .then(function(r){return r.json();})
    .then(function(d){
      if(d.ok){
        var el=document.querySelector('[data-field="'+fieldName+'"]');if(el)el.value=d.path;
        var pre=document.getElementById(previewId);
        if(pre){pre.src="../"+d.path+"?t="+Date.now();pre.style.display="block";}
        toast("已上传，正在保存...","ok");
        saveSite();
      }else{toast("失败:"+d.error,"er");}
    }).catch(function(){toast("网络错误","er");});
    document.body.removeChild(inp);
  };
  inp.click();
}

/* ====== Site content save ====== */
function saveSite(){
  var sc={company:{},hero:{stats:[{}, {}, {}, {}]},services:[]};

  // Company
  document.querySelectorAll('[data-field^="company."]').forEach(function(el){
    var field=el.getAttribute("data-field").replace("company.","");
    sc.company[field]=el.value;
  });
  // Highlights
  sc.company.highlights=[];
  document.querySelectorAll('[data-hl]').forEach(function(el){sc.company.highlights.push(el.value);});

  // Hero
  document.querySelectorAll('[data-field^="hero."]').forEach(function(el){
    var field=el.getAttribute("data-field").replace("hero.","");
    sc.hero[field]=el.value;
  });
  // Stats
  document.querySelectorAll('[data-stat][data-field="label"]').forEach(function(el,i){
    sc.hero.stats[i]={label:el.value,value:0,suffix:""};
  });
  document.querySelectorAll('[data-stat][data-field="value"]').forEach(function(el,i){
    if(sc.hero.stats[i])sc.hero.stats[i].value=parseInt(el.value)||0;
  });
  document.querySelectorAll('[data-stat][data-field="suffix"]').forEach(function(el,i){
    if(sc.hero.stats[i])sc.hero.stats[i].suffix=el.value;
  });

  // Services (dynamic)
  var svcImgs=document.querySelectorAll('[data-svc][data-field="image"]');
  var svcTitles=document.querySelectorAll('[data-svc][data-field="title"]');
  var svcDescs=document.querySelectorAll('[data-svc][data-field="desc"]');
  var seen={};
  svcImgs.forEach(function(el){
    var i=el.getAttribute("data-svc");
    if(!seen[i]){seen[i]={image:"",title:"",desc:""};}
    seen[i].image=el.value;
  });
  svcTitles.forEach(function(el){
    var i=el.getAttribute("data-svc");
    if(!seen[i]){seen[i]={image:"",title:"",desc:""};}
    seen[i].title=el.value;
  });
  svcDescs.forEach(function(el){
    var i=el.getAttribute("data-svc");
    if(!seen[i]){seen[i]={image:"",title:"",desc:""};}
    seen[i].desc=el.value;
  });
  Object.values(seen).forEach(function(svc){
    if(svc.image||svc.title||svc.desc)sc.services.push(svc);
  });

  toast("保存中...","ok");
  fetch("/admin/site-content",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(sc)})
  .then(function(r){return r.json();})
  .then(function(d){if(d.ok){toast("已保存！网站已更新","ok");}else{toast("失败:"+d.error,"er");}})
  .catch(function(){toast("网络错误","er");});
}

/* ====== Dynamic services ====== */
var svcCounter=''' + str(len(services)) + r''';
function addSvc(){
  var i=svcCounter++;
  var row=document.createElement("div");
  row.className="svc-row";
  row.id="svcRow"+i;
  row.innerHTML='<span class="svc-idx">#'+(i+1)+'</span>'
    +'<div class="svc-img-box">'
    +'<div class="svc-thumb" id="svcThumb'+i+'" style="display:none"></div>'
    +'<button onclick="uploadSvcImg('+i+')" class="btn-sm">上传图片</button>'
    +'<input type="hidden" id="svcImg'+i+'" value="" data-svc="'+i+'" data-field="image">'
    +'</div>'
    +'<input value="" placeholder="服务名称" data-svc="'+i+'" data-field="title" style="flex:1">'
    +'<textarea placeholder="服务描述" data-svc="'+i+'" data-field="desc" rows="2" style="flex:2"></textarea>'
    +'<button onclick="deleteSvc('+i+')" class="btn-sm btn-del" title="删除此服务">✕</button>';
  document.getElementById("svcContainer").appendChild(row);
  renumberSvc();
}
function deleteSvc(i){
  var row=document.getElementById("svcRow"+i);
  if(row)row.remove();
  renumberSvc();
}
function renumberSvc(){
  var rows=document.querySelectorAll("#svcContainer .svc-row");
  rows.forEach(function(r,idx){
    r.querySelector(".svc-idx").textContent="#"+(idx+1);
  });
}
function uploadSvcImg(i){
  var inp=document.createElement("input");
  inp.type="file";inp.accept="image/*";
  inp.style.display="none";
  document.body.appendChild(inp);
  inp.onchange=function(){
    var f=inp.files[0];if(!f)return;
    var fd=new FormData();fd.append("img",f);
    toast("上传中...","ok");
    fetch("/admin/upload",{method:"POST",body:fd})
    .then(function(r){return r.json();})
    .then(function(d){
      if(d.ok){
        var el=document.getElementById("svcImg"+i);if(el)el.value=d.path;
        var th=document.getElementById("svcThumb"+i);
        if(th){th.innerHTML='<img src="../'+d.path+'?t='+Date.now()+'" style="width:60px;height:45px;object-fit:cover;border-radius:4px">';th.style.display="block";}
        toast("图片已上传","ok");
      }else{toast("失败:"+d.error,"er");}
    }).catch(function(){toast("网络错误","er");});
    document.body.removeChild(inp);
  };
  inp.click();
}

/* ====== Case management ====== */
function loadCaseTable(){
  fetch("/admin/cases").then(function(r){return r.json();}).then(function(data){
    var t=document.getElementById("caseTableBody");
    if(!data.length){t.innerHTML='<tr><td colspan="5" style="color:#999;text-align:center">暂无案例，点击"添加案例"</td></tr>';return}
    t.innerHTML="";
    data.forEach(function(c,i){
      t.innerHTML+='<tr><td><img src="../'+c.image+'?t='+Date.now()+'" onerror="this.style.display=none"></td><td>'+c.title+'</td><td>'+catName(c.category)+'</td><td>'+c.desc.substring(0,40)+'...</td><td class="act"><button class="edit" onclick="editCase('+i+')">编辑</button><button class="del" onclick="deleteCase('+i+')">删除</button></td></tr>';
    });
  });
}
function catName(c){return c==="building"?"房屋建筑":c==="municipal"?"市政工程":"工业项目";}

function openCaseModal(idx){
  document.getElementById("caseId").value="";
  document.getElementById("caseTitle").value="";
  document.getElementById("caseCat").value="building";
  document.getElementById("caseImg").value="";
  document.getElementById("caseDesc").value="";
  var pre=document.getElementById("caseImgPreview");pre.style.display="none";
  document.getElementById("caseModalTitle").textContent="添加案例";
  if(idx!==undefined){
    fetch("/admin/cases").then(function(r){return r.json();}).then(function(data){
      var c=data[idx];
      document.getElementById("caseId").value=idx;
      document.getElementById("caseTitle").value=c.title;
      document.getElementById("caseCat").value=c.category;
      document.getElementById("caseImg").value=c.image;
      document.getElementById("caseDesc").value=c.desc;
      if(c.image){pre.src="../"+c.image+"?t="+Date.now();pre.style.display="block";}
      document.getElementById("caseModalTitle").textContent="编辑案例";
    });
  }
  document.getElementById("caseModal").classList.add("open");
}
function closeCaseModal(){document.getElementById("caseModal").classList.remove("open");}
function editCase(idx){openCaseModal(idx);}
function deleteCase(idx){
  if(!confirm("确定删除这个案例吗？"))return;
  fetch("/admin/cases/delete",{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded"},body:"idx="+idx})
  .then(function(r){return r.json();}).then(function(d){
    if(d.ok){toast("案例已删除，网站已更新","ok");loadCaseTable();}else{toast("失败:"+d.error,"er");}
  }).catch(function(){toast("网络错误","er");});
}
function saveCase(){
  var cid=document.getElementById("caseId").value;
  var c={title:document.getElementById("caseTitle").value,category:document.getElementById("caseCat").value,image:document.getElementById("caseImg").value,desc:document.getElementById("caseDesc").value};
  if(!c.title||!c.image){toast("请填写项目名称和图片路径","er");return}
  var body="title="+encodeURIComponent(c.title)+"&category="+encodeURIComponent(c.category)+"&image="+encodeURIComponent(c.image)+"&desc="+encodeURIComponent(c.desc);
  if(cid!=="")body+="&idx="+cid;
  fetch("/admin/cases/save",{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded"},body:body})
  .then(function(r){return r.json();}).then(function(d){
    if(d.ok){toast("案例已保存，网站已更新","ok");closeCaseModal();loadCaseTable();}else{toast("失败:"+d.error,"er");}
  }).catch(function(){toast("网络错误","er");});
}
function uploadCaseImg(){
  var f=document.getElementById("caseImgUpload").files[0];if(!f)return;
  var fd=new FormData();fd.append("img",f);
  toast("上传中...","ok");
  fetch("/admin/upload",{method:"POST",body:fd}).then(function(r){return r.json();}).then(function(d){
    if(d.ok){document.getElementById("caseImg").value=d.path;document.getElementById("caseImgPreview").src="../"+d.path+"?t="+Date.now();document.getElementById("caseImgPreview").style.display="block";toast("图片已上传","ok");}else{toast("失败:"+d.error,"er");}
  }).catch(function(){toast("网络错误","er");});
}

/* ====== News management ====== */
function loadNewsTable(){
  fetch("/admin/news").then(function(r){return r.json();}).then(function(data){
    var t=document.getElementById("newsTableBody");
    if(!data.length){t.innerHTML='<tr><td colspan="5" style="color:#999;text-align:center">暂无新闻，点击"添加新闻"</td></tr>';return}
    t.innerHTML="";
    data.forEach(function(n,i){
      var imgTag=n.image?'<img src="../'+n.image+'?t='+Date.now()+'" onerror="this.style.display=none">':'';
      t.innerHTML+='<tr><td>'+imgTag+'</td><td>'+n.date+'</td><td>'+n.title+'</td><td>'+n.summary.substring(0,40)+'...</td><td class="act"><button class="edit" onclick="editNews('+i+')">编辑</button><button class="del" onclick="deleteNews('+i+')">删除</button></td></tr>';
    });
  });
}
function openNewsModal(idx){
  document.getElementById("newsId").value="";
  document.getElementById("newsTitle").value="";
  document.getElementById("newsDate").value=new Date().toISOString().substring(0,10);
  document.getElementById("newsImg").value="";
  document.getElementById("newsSummary").value="";
  var pre=document.getElementById("newsImgPreview");pre.style.display="none";
  document.getElementById("newsModalTitle").textContent="添加新闻";
  if(idx!==undefined){
    fetch("/admin/news").then(function(r){return r.json();}).then(function(data){
      var n=data[idx];
      document.getElementById("newsId").value=idx;
      document.getElementById("newsTitle").value=n.title;
      document.getElementById("newsDate").value=n.date;
      document.getElementById("newsImg").value=n.image||'';
      document.getElementById("newsSummary").value=n.summary;
      if(n.image){pre.src="../"+n.image+"?t="+Date.now();pre.style.display="block";}
      document.getElementById("newsModalTitle").textContent="编辑新闻";
    });
  }
  document.getElementById("newsModal").classList.add("open");
}
function closeNewsModal(){document.getElementById("newsModal").classList.remove("open");}
function editNews(idx){openNewsModal(idx);}
function deleteNews(idx){
  if(!confirm("确定删除这条新闻吗？"))return;
  fetch("/admin/news/delete",{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded"},body:"idx="+idx})
  .then(function(r){return r.json();}).then(function(d){
    if(d.ok){toast("新闻已删除，网站已更新","ok");loadNewsTable();}else{toast("失败:"+d.error,"er");}
  }).catch(function(){toast("网络错误","er");});
}
function uploadNewsImg(){
  var f=document.getElementById("newsImgUpload").files[0];if(!f)return;
  var fd=new FormData();fd.append("img",f);
  toast("上传中...","ok");
  fetch("/admin/upload",{method:"POST",body:fd}).then(function(r){return r.json();}).then(function(d){
    if(d.ok){document.getElementById("newsImg").value=d.path;document.getElementById("newsImgPreview").src="../"+d.path+"?t="+Date.now();document.getElementById("newsImgPreview").style.display="block";toast("图片已上传","ok");}else{toast("失败:"+d.error,"er");}
  }).catch(function(){toast("网络错误","er");});
}
function saveNews(){
  var nid=document.getElementById("newsId").value;
  var n={title:document.getElementById("newsTitle").value,date:document.getElementById("newsDate").value,image:document.getElementById("newsImg").value,summary:document.getElementById("newsSummary").value};
  if(!n.title){toast("请填写标题","er");return}
  var body="title="+encodeURIComponent(n.title)+"&date="+encodeURIComponent(n.date)+"&image="+encodeURIComponent(n.image)+"&summary="+encodeURIComponent(n.summary);
  if(nid!=="")body+="&idx="+nid;
  fetch("/admin/news/save",{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded"},body:body})
  .then(function(r){return r.json();}).then(function(d){
    if(d.ok){toast("新闻已保存，网站已更新","ok");closeNewsModal();loadNewsTable();}else{toast("失败:"+d.error,"er");}
  }).catch(function(){toast("网络错误","er");});
}
/* ====== Messages ====== */
var allMsgs=[],msgPage=0,msgPageSize=10;
function loadMsgTable(){
  fetch("/admin/messages?t="+Date.now()).then(function(r){return r.json();}).then(function(data){
    allMsgs=data;msgPage=0;
    var note=document.getElementById("msgNote");
    var unread=data.filter(function(m){return !m.read;}).length;
    note.textContent=data.length+" 条留言"+(unread?"，"+unread+" 条未读":"");
    renderMsgPage();
  });
}
function renderMsgPage(){
  var t=document.getElementById("msgTableBody");
  var total=Math.ceil(allMsgs.length/msgPageSize)||1;
  if(!allMsgs.length){t.innerHTML='<tr><td colspan="8" style="color:#999;text-align:center">暂无留言</td></tr>';document.getElementById("msgPageNav").textContent='';return}
  var start=msgPage*msgPageSize,end=Math.min(start+msgPageSize,allMsgs.length);
  t.innerHTML="";
  for(var i=start;i<end;i++){
    var m=allMsgs[i];
    var st=m.read?'<span style="color:#999">已读</span>':'<span style="color:#e74c3c;font-weight:500">未读</span>';
    t.innerHTML+='<tr><td>'+st+'</td><td>'+m.time+'</td><td>'+m.name+'</td><td>'+m.phone+'</td><td>'+m.email+'</td><td>'+m.service+'</td><td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'+m.message+'</td><td class="act"><button class="edit" onclick="markRead('+i+')">标记已读</button><button class="del" onclick="deleteMsg('+i+')">删除</button></td></tr>';
  }
  var nav=document.getElementById("msgPageNav");
  nav.innerHTML=(msgPage>0?'<button onclick="msgPage--;renderMsgPage()" style="padding:2px 10px;cursor:pointer">上一页</button>':'')+' <span style="font-size:13px;color:#666">'+(msgPage+1)+'/'+total+'</span> '+(msgPage+1<total?'<button onclick="msgPage++;renderMsgPage()" style="padding:2px 10px;cursor:pointer">下一页</button>':'');
}
function markRead(idx){
  fetch("/admin/messages/read",{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded"},body:"idx="+idx})
  .then(function(r){return r.json();}).then(function(d){
    if(d.ok){allMsgs[idx].read=true;renderMsgPage();}else{toast("失败:"+d.error,"er");}
  }).catch(function(){toast("网络错误","er");});
}
function deleteMsg(idx){
  if(!confirm("确定删除这条留言吗？"))return;
  fetch("/admin/messages/delete",{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded"},body:"idx="+idx})
  .then(function(r){return r.json();}).then(function(d){
    if(d.ok){allMsgs.splice(idx,1);renderMsgPage();toast("留言已删除","ok");}else{toast("失败:"+d.error,"er");}
  }).catch(function(){toast("网络错误","er");});
}
var msgPollTimer=null,msgPollActive=false;
function startMsgPoll(){msgPollActive=true;nextPoll();}
function nextPoll(){if(!msgPollActive)return;if(msgPollTimer)clearTimeout(msgPollTimer);msgPollTimer=setTimeout(function(){loadMsgTable();nextPoll();},8000);}
function stopMsgPoll(){msgPollActive=false;if(msgPollTimer){clearTimeout(msgPollTimer);msgPollTimer=null;}}
document.addEventListener('visibilitychange',function(){if(!document.hidden&&activeTab==='msgs'){loadMsgTable();nextPoll();}});
window.addEventListener('focus',function(){if(activeTab==='msgs'){loadMsgTable();nextPoll();}});
</script>
</body>
</html>'''


# ====== SERVER ======

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        if not self.auth():
            self.html(page_login())
            return
        if path == '/admin' or path == '/admin/':
            sc = load_json(SITE_FILE) or {}
            self.html(page_admin(sc))
        elif path == '/admin/cases':
            self.json(load_json(DATA_DIR + '/cases.json') or [])
        elif path == '/admin/news':
            news = load_json(DATA_DIR + '/news.json') or []
            news.sort(key=lambda x: x.get('date', ''), reverse=True)
            self.json(news)
        elif path == '/admin/messages':
            self.json(load_json(MSG_FILE) or [])
        elif path == '/admin/site-content':
            self.json(load_json(SITE_FILE) or {})
        elif path == '/admin/images':
            imgs = []
            for fp in sorted(glob.glob(IMG_DIR+'/*'), key=os.path.getmtime, reverse=True):
                fn = os.path.basename(fp)
                if fn.rsplit('.',1)[-1].lower() in ('jpg','jpeg','png','gif','webp','svg','ico'):
                    imgs.append({'name':fn,'path':'images/'+fn,'size':os.path.getsize(fp)})
            self.json({'images':imgs})
        else:
            self.redirect('/admin')

    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path
        if path == '/admin/contact':
            self.save_message()
            return
        if not self.auth(): self.json({'ok':False,'error':'未登录'}); return
        if path == '/admin/cases/save': self.save_case()
        elif path == '/admin/cases/delete': self.delete_case()
        elif path == '/admin/news/save': self.save_news()
        elif path == '/admin/news/delete': self.delete_news()
        elif path == '/admin/messages/read': self.mark_read()
        elif path == '/admin/messages/delete': self.delete_message()
        elif path == '/admin/upload': self.upload()
        elif path == '/admin/site-content': self.save_site_content()
        else: self.send_error(404)

    def auth(self):
        c = self.headers.get('Cookie','')
        m = re.search(r't=([^;]+)', c)
        if m:
            try: return base64.b64decode(m.group(1)).decode() == ADMIN_PASSWORD
            except: pass
        return False

    # ====== Site content ======
    def save_site_content(self):
        body = self.rfile.read(int(self.headers.get('Content-Length',0))).decode()
        try:
            sc = json.loads(body)
            save_json(SITE_FILE, sc)
            generate_html()
            self.json({'ok':True})
        except Exception as e:
            self.json({'ok':False,'error':str(e)})

    # ====== Cases ======
    def save_case(self):
        body = self.rfile.read(int(self.headers.get('Content-Length',0))).decode()
        d = urllib.parse.parse_qs(body)
        c = {'title':d.get('title',[''])[0],'category':d.get('category',['building'])[0],
             'image':d.get('image',[''])[0],'desc':d.get('desc',[''])[0]}
        cases = load_json(DATA_DIR + '/cases.json') or []
        idx = d.get('idx',[''])[0]
        if idx != '' and idx.isdigit() and int(idx) < len(cases): cases[int(idx)] = c
        else: cases.append(c)
        save_json(DATA_DIR + '/cases.json', cases)
        generate_html()
        self.json({'ok':True})

    def delete_case(self):
        body = self.rfile.read(int(self.headers.get('Content-Length',0))).decode()
        idx = urllib.parse.parse_qs(body).get('idx',[''])[0]
        if not idx.isdigit(): self.json({'ok':False,'error':'无效索引'}); return
        cases = load_json(DATA_DIR + '/cases.json') or []
        i = int(idx)
        if i < 0 or i >= len(cases): self.json({'ok':False,'error':'超出范围'}); return
        cases.pop(i)
        save_json(DATA_DIR + '/cases.json', cases)
        generate_html()
        self.json({'ok':True})

    # ====== News ======
    def save_news(self):
        body = self.rfile.read(int(self.headers.get('Content-Length',0))).decode()
        d = urllib.parse.parse_qs(body)
        n = {'title':d.get('title',[''])[0],'date':d.get('date',[''])[0],
             'image':d.get('image',[''])[0],'summary':d.get('summary',[''])[0]}
        news = load_json(DATA_DIR + '/news.json') or []
        idx = d.get('idx',[''])[0]
        if idx != '' and idx.isdigit() and int(idx) < len(news): news[int(idx)] = n
        else: news.insert(0, n)
        news.sort(key=lambda x: x.get('date', ''), reverse=True)
        save_json(DATA_DIR + '/news.json', news)
        generate_html()
        self.json({'ok':True})

    def delete_news(self):
        body = self.rfile.read(int(self.headers.get('Content-Length',0))).decode()
        idx = urllib.parse.parse_qs(body).get('idx',[''])[0]
        if not idx.isdigit(): self.json({'ok':False,'error':'无效索引'}); return
        news = load_json(DATA_DIR + '/news.json') or []
        i = int(idx)
        if i < 0 or i >= len(news): self.json({'ok':False,'error':'超出范围'}); return
        news.pop(i)
        save_json(DATA_DIR + '/news.json', news)
        generate_html()
        self.json({'ok':True})

    # ====== Messages ======
    def save_message(self):
        body = self.rfile.read(int(self.headers.get('Content-Length',0))).decode()
        d = urllib.parse.parse_qs(body)
        m = {
            'name': d.get('name',[''])[0].strip(),
            'phone': d.get('phone',[''])[0].strip(),
            'email': d.get('email',[''])[0].strip(),
            'service': d.get('service',[''])[0].strip(),
            'message': d.get('message',[''])[0].strip(),
            'time': time.strftime('%Y-%m-%d %H:%M:%S'),
            'read': False
        }
        if not m['name'] or not m['phone']:
            self.json({'ok':False,'error':'请填写姓名和电话'}); return
        msgs = load_json(MSG_FILE) or []
        msgs.insert(0, m)
        save_json(MSG_FILE, msgs)
        self.json({'ok':True})

    def mark_read(self):
        body = self.rfile.read(int(self.headers.get('Content-Length',0))).decode()
        d = urllib.parse.parse_qs(body)
        idx = d.get('idx',[''])[0]
        if not idx.isdigit(): self.json({'ok':False,'error':'无效索引'}); return
        msgs = load_json(MSG_FILE) or []
        i = int(idx)
        if i < 0 or i >= len(msgs): self.json({'ok':False,'error':'超出范围'}); return
        msgs[i]['read'] = True
        save_json(MSG_FILE, msgs)
        self.json({'ok':True})

    def delete_message(self):
        body = self.rfile.read(int(self.headers.get('Content-Length',0))).decode()
        d = urllib.parse.parse_qs(body)
        idx = d.get('idx',[''])[0]
        if not idx.isdigit(): self.json({'ok':False,'error':'无效索引'}); return
        msgs = load_json(MSG_FILE) or []
        i = int(idx)
        if i < 0 or i >= len(msgs): self.json({'ok':False,'error':'超出范围'}); return
        msgs.pop(i)
        save_json(MSG_FILE, msgs)
        self.json({'ok':True})

    # ====== Upload ======
    def upload(self):
        fn, data = self._parse_upload()
        if not data: self.json({'ok':False,'error':'未找到图片'}); return
        if len(data) > 500 * 1024:
            self.json({'ok':False,'error':f'图片太大({len(data)//1024}KB)，请压缩到500KB以内'}); return
        ext = fn.rsplit('.',1)[-1].lower() if '.' in fn else 'jpg'
        if ext not in ('jpg','jpeg','png','gif','webp','svg','ico'): ext='jpg'
        name = 'img_'+str(int(time.time()))+'.'+ext
        with open(IMG_DIR+'/'+name,'wb') as fp: fp.write(data)
        self.json({'ok':True,'path':'images/'+name})

    def _parse_upload(self):
        ct = self.headers.get('Content-Type','')
        if 'multipart/form-data' not in ct: return None,None
        body = self.rfile.read(int(self.headers.get('Content-Length',0)))
        boundary = ct.split('boundary=')[1].encode()
        for part in body.split(boundary):
            if b'filename=' in part:
                s = part.find(b'filename="')+10; e = part.find(b'"',s)
                fn = part[s:e].decode()
                h = part.find(b'\r\n\r\n')+4; t = part.rfind(b'\r\n')
                return fn, part[h:t]
        return None,None

    # ====== Helpers ======
    def html(self, h):
        self.send_response(200); self.send_header('Content-Type','text/html; charset=utf-8'); self.end_headers()
        self.wfile.write(h.encode())

    def redirect(self, url):
        self.send_response(302); self.send_header('Location',url); self.end_headers()

    def json(self, d):
        self.send_response(200); self.send_header('Content-Type','application/json'); self.end_headers()
        self.wfile.write(json.dumps(d, ensure_ascii=False).encode())

    def log_message(self, *a): pass

if __name__ == '__main__':
    http.server.HTTPServer(('127.0.0.1',8889), Handler).serve_forever()
