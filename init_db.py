import os
from werkzeug.security import generate_password_hash
from models import init_db, get_db


def seed():
    conn = init_db()
    c = conn.cursor()

    # 创建两个管理用户
    c.execute('DELETE FROM users')
    c.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)',
              ('admin', generate_password_hash('admin123')))
    c.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)',
              ('admin2', generate_password_hash('admin456')))

    # ===== 网站内容 =====
    content = [
        # 首页横幅
        ('hero', 'title', '苏州清韵项目管理  铸就卓越品质'),
        ('hero', 'subtitle', '致力于为客户提供全过程、全方位的项目管理解决方案，涵盖工程监理、造价咨询、招标代理等核心业务'),
        ('hero', 'stat1_num', '200'),
        ('hero', 'stat1_label', '服务客户'),
        ('hero', 'stat2_num', '500'),
        ('hero', 'stat2_label', '完成项目'),
        ('hero', 'stat3_num', '98'),
        ('hero', 'stat3_label', '客户满意度(%)'),
        ('hero', 'stat4_num', '15'),
        ('hero', 'stat4_label', '行业经验(年)'),
        # 关于我们
        ('about', 'company_name', '苏州清韵项目管理有限公司'),
        ('about', 'desc1', '苏州清韵项目管理有限公司成立于2010年，是一家集工程监理、造价咨询、招标代理、全过程项目管理于一体的综合性专业服务机构。公司拥有住建部颁发的工程监理甲级资质、工程造价咨询甲级资质。'),
        ('about', 'desc2', '公司汇聚了一批经验丰富的注册监理工程师、注册造价工程师、一级建造师等专业人才，建立了一套科学完善的质量管理体系和项目管理流程。'),
        ('about', 'highlight1', '甲级监理资质'),
        ('about', 'highlight2', '甲级造价咨询'),
        ('about', 'highlight3', 'ISO 9001 认证'),
        ('about', 'highlight4', '200+ 专业团队'),
        # 页脚
        ('footer', 'about_text', '以专业能力和诚信服务，为客户创造价值，为行业发展助力。'),
        ('footer', 'copyright', '© 2026 苏州清韵项目管理有限公司 版权所有'),
        # 站点设置
        ('settings', 'logo_text', 'QY'),
        ('settings', 'logo_image', ''),
        ('settings', 'about_image', ''),
        ('settings', 'footer_qr', ''),
    ]
    c.execute('DELETE FROM site_content')
    for section, key, val in content:
        c.execute('INSERT INTO site_content (section, field_key, content) VALUES (?, ?, ?)',
                  (section, key, val))

    # ===== 服务项目 =====
    services = [
        ('🔨', '工程监理', '提供房屋建筑、市政公用、机电安装等工程监理服务，严格把控工程质量、进度与投资。', 0),
        ('📊', '造价咨询', '涵盖投资估算、设计概算、施工图预算、竣工结算等全过程造价管理服务。', 1),
        ('📋', '招标代理', '提供工程施工、设备采购、服务类招标代理，确保招标过程规范、公平、高效。', 2),
        ('🏢', '全过程项目管理', '从项目立项到竣工验收的全生命周期管理，协调各方资源，确保项目目标达成。', 3),
        ('🔍', '项目咨询', '提供可行性研究、项目评估、投资决策等专业咨询服务，为项目科学决策提供依据。', 4),
        ('⚖️', '合同管理', '专业的合同起草、审核、履约管理，有效防范合同风险，保障各方合法权益。', 5),
    ]
    c.execute('DELETE FROM services')
    for icon, title, desc, sort in services:
        c.execute('INSERT INTO services (icon, title, description, sort_order) VALUES (?, ?, ?, ?)',
                  (icon, title, desc, sort))

    # ===== 客户案例 =====
    cases = [
        ('building', '恒隆商业广场', '总建筑面积28万㎡，提供全过程监理及造价咨询服务', '', 0),
        ('municipal', '滨海大道改造工程', '全长12.6公里城市主干道，监理及全过程管理', '', 1),
        ('building', '翡翠湾住宅小区', '35万㎡高端住宅项目，造价咨询与监理服务', '', 2),
        ('industrial', '华鑫电子产业园', '占地200亩产业园区，全过程项目管理服务', '', 3),
        ('municipal', '市体育中心', '容纳3万人综合体育场馆，全过程监理服务', '', 4),
        ('building', '天汇国际商务中心', '5A甲级写字楼，造价咨询与招标代理服务', '', 5),
    ]
    c.execute('DELETE FROM cases')
    for cat, title, desc, img, sort in cases:
        c.execute('INSERT INTO cases (category, title, description, image_path, sort_order) VALUES (?, ?, ?, ?, ?)',
                  (cat, title, desc, img, sort))

    # ===== 新闻动态 =====
    news = [
        ('2026-04-28', '公司荣获2025年度"优秀监理企业"称号', '近日，在省建设监理协会组织的评选中，我公司荣获年度优秀监理企业称号。', '', 0),
        ('2026-04-15', '中标滨海新区市政道路项目全过程管理', '公司成功中标滨海新区市政道路建设项目全过程管理服务，项目总投资约3.2亿元。', '', 1),
        ('2026-03-20', '公司召开2026年春季安全生产工作会议', '会议总结了上年度安全生产情况，部署了新一年安全生产工作重点任务。', '', 2),
        ('2026-03-05', '引进BIM技术，提升项目管理数字化水平', '公司正式引入BIM技术平台，推动项目管理向数字化、智能化方向转型升级。', '', 3),
    ]
    c.execute('DELETE FROM news')
    for date, title, summary, img, sort in news:
        c.execute('INSERT INTO news (date, title, summary, image_path, sort_order) VALUES (?, ?, ?, ?, ?)',
                  (date, title, summary, img, sort))

    # ===== 联系信息 =====
    contact = [
        ('📍', '公司地址', '苏州市姑苏区王洗马巷15-1号114室', 0),
        ('📞', '联系电话', '400-XXX-XXXX | 0512-XXXXXXXX', 1),
        ('✉️', '电子邮箱', 'szqyjskj@163.com', 2),
        ('🌐', '工作时间', '周一至周五 9:00 - 18:00', 3),
    ]
    c.execute('DELETE FROM contact_info')
    for icon, label, value, sort in contact:
        c.execute('INSERT INTO contact_info (icon, label, value, sort_order) VALUES (?, ?, ?, ?)',
                  (icon, label, value, sort))

    conn.commit()
    conn.close()
    print('数据库初始化完成！')
    print('  管理员账号: admin / admin123')
    print('  管理员账号: admin2 / admin456')


if __name__ == '__main__':
    seed()
