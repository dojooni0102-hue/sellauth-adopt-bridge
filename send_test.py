import requests

webhook = 'https://discord.com/api/webhooks/1538040897579651202/7Ff-K6xh72JSw6xQwU6YB0ZhRLcsCdgzJALNJjESlJPeYYBFHA5YPzLk5_lAWodyrndU'
embed = {
    'title': '🧪 [테스트 시뮬레이션] 1번 상품 자동 배송 테스트',
    'description': '가상 손님이 결제했을 때의 실시간 배송 및 알림 테스트입니다.',
    'color': 0x3498DB,
    'fields': [
        {'name': '📦 상품명', 'value': '`[입양하세요] 326~350 포션 + 25만 벅스 계정`', 'inline': True},
        {'name': '💰 결제 금액', 'value': '`1,500 KRW`', 'inline': True},
        {'name': '🔑 발급 계정', 'value': '```roblox_adopt_test01:PassWord999! | Potion Account```', 'inline': False},
        {'name': '⚡ 상태', 'value': '✅ 0.8초 만에 손님 화면에 전달 완료', 'inline': True}
    ],
    'footer': {'text': 'SellAuth Dropship Bridge 24/7 Engine'}
}
requests.post(webhook, json={'embeds': [embed]})
print('TEST ALERT SENT OK')
