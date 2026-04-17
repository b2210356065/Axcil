import openpyxl
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

def create_excel(data: dict = None, output_path: str = 'Oda_Yerlesim_Plani.xlsx') -> str:
    """
    Turizm ajansı oda yerleştirme otomasyonu.
    1000 kişilik grup, 230 oda (640 kapasite) yönetimi.
    """
    # 1. ODA ENVANTERİ TANIMLAMA
    # 2'lik: 100 (101-200), 3'lük: 80 (201-280), 4'lük: 50 (281-330)
    rooms = []
    for i in range(101, 201): rooms.append({'no': i, 'tip': '2 Kişilik', 'kap': 2, 'misf': [], 'manzara': 'Standart', 'not': ''})
    for i in range(201, 281): rooms.append({'no': i, 'tip': '3 Kişilik', 'kap': 3, 'misf': [], 'manzara': 'Standart', 'not': ''})
    for i in range(281, 331): rooms.append({'no': i, 'tip': '4 Kişilik', 'kap': 4, 'misf': [], 'manzara': 'Standart', 'not': ''})

    # 2. VERİ KONTROLÜ VE MOCK VERİ ÜRETİMİ
    guests = []
    if not data or 'misafirler' not in data or len(data['misafirler']) == 0:
        # Senaryo 1: 4 Kişilik Aile (Karışık Cinsiyet OK)
        for i in range(1, 5):
            guests.append({'isim': f'AileÜye{i}', 'soyisim': 'YILMAZ', 'tc': f'1111111110{i}', 'cinsiyet': 'E' if i%2==0 else 'K', 'yas': 40-i, 'grup_id': 'GRUP-1', 'iliski': 'Aile', 'tercih': '4 Kişilik', 'ozel': None})
        # Senaryo 2: 4 Kişilik Arkadaş Grubu (Cinsiyet Ayrımı Şart - 2E 2K)
        for i in range(1, 3):
            guests.append({'isim': f'ErkekArk{i}', 'soyisim': 'KAYA', 'tc': f'2222222220{i}', 'cinsiyet': 'E', 'yas': 25, 'grup_id': 'GRUP-5', 'iliski': 'Arkadaş', 'tercih': '4 Kişilik', 'ozel': None})
            guests.append({'isim': f'KadinArk{i}', 'soyisim': 'DEMİR', 'tc': f'2222222220{i+2}', 'cinsiyet': 'K', 'yas': 24, 'grup_id': 'GRUP-5', 'iliski': 'Arkadaş', 'tercih': '4 Kişilik', 'ozel': None})
        # Senaryo 3: 5 Kişilik Erkek Grubu (Oda Dağıtma 4+1)
        for i in range(1, 6):
            guests.append({'isim': f'GrupÜye{i}', 'soyisim': 'ÇELİK', 'tc': f'3333333330{i}', 'cinsiyet': 'E', 'yas': 30, 'grup_id': 'GRUP-10', 'iliski': 'Arkadaş', 'tercih': '4 Kişilik', 'ozel': None})
        # Senaryo 4: Özel İstekli Çift
        guests.append({'isim': 'Cem', 'soyisim': 'GÜNEŞ', 'tc': '55555555501', 'cinsiyet': 'E', 'yas': 30, 'grup_id': 'GRUP-50', 'iliski': 'Evli', 'tercih': '2 Kişilik', 'ozel': 'Deniz manzaralı, Engelli erişimi'})
        guests.append({'isim': 'Seda', 'soyisim': 'GÜNEŞ', 'tc': '55555555502', 'cinsiyet': 'K', 'yas': 28, 'grup_id': 'GRUP-50', 'iliski': 'Evli', 'tercih': '2 Kişilik', 'ozel': 'Deniz manzaralı, Engelli erişimi'})
        # 1000 kişiye tamamla (Kapasite aşımı testi)
        for i in range(len(guests), 1000):
            guests.append({'isim': f'M{i}', 'soyisim': 'S', 'tc': str(90000000000+i), 'cinsiyet': 'E' if i%2==0 else 'K', 'yas': 20, 'grup_id': f'GRUP-{100+(i//2)}', 'iliski': 'Arkadaş', 'tercih': '2 Kişilik', 'ozel': None})
    else:
        guests = data['misafirler']

    # 3. YERLEŞTİRME ALGORİTMASI
    waiting_list = []
    # Gruplandır
    groups = {}
    for g in guests: 
        groups.setdefault(g['grup_id'], []).append(g)
    
    # Kapasite Optimizasyonu: Önce büyük gruplar
    sorted_gids = sorted(groups.keys(), key=lambda x: len(groups[x]), reverse=True)

    def can_stay(g1, g2):
        if g1['cinsiyet'] == g2['cinsiyet']: return True
        return g1['iliski'] in ['Aile', 'Evli', 'Nişanlı', 'Birlikte Kalabilir']

    for gid in sorted_gids:
        mems = groups[gid]
        # Grup içi cinsiyet/ilişki alt grupları oluştur
        sub_groups = []
        current_sub = []
        for m in mems:
            if not current_sub or can_stay(current_sub[0], m):
                current_sub.append(m)
            else:
                sub_groups.append(current_sub)
                current_sub = [m]
        sub_groups.append(current_sub)

        for sub in sub_groups:
            while sub:
                placed = False
                # Tercih sırası: Tercih edilen -> 4 -> 3 -> 2
                pref = sub[0].get('tercih', '2 Kişilik')
                order = [pref, '4 Kişilik', '3 Kişilik', '2 Kişilik']
                
                for o_tip in order:
                    for r in rooms:
                        if r['tip'] == o_tip and len(r['misf']) == 0:
                            take = min(len(sub), r['kap'])
                            to_place = sub[:take]
                            r['misf'].extend(to_place)
                            if to_place[0].get('ozel'):
                                if 'Deniz' in to_place[0]['ozel']: r['manzara'] = 'Deniz'
                                if 'Engelli' in to_place[0]['ozel']: r['not'] = 'Engelli Erişimi Gerekli'
                            sub = sub[take:]
                            placed = True; break
                    if placed: break
                
                if not placed: # Dolu odalara tekil eşleştirme (aynı cinsiyet/grup)
                    for r in rooms:
                        if len(r['misf']) > 0 and len(r['misf']) < r['kap']:
                            if can_stay(r['misf'][0], sub[0]) and (r['misf'][0]['grup_id'] == sub[0]['grup_id'] or r['misf'][0]['cinsiyet'] == sub[0]['cinsiyet']):
                                r['misf'].append(sub[0])
                                sub = sub[1:]
                                placed = True; break
                    if not placed:
                        for leftover in sub: waiting_list.append(leftover)
                        sub = []

    # 4. EXCEL ÜRETİMİ
    wb = Workbook()
    ws = wb.active
    ws.title = "Oda Yerleşim Planı"
    headers = ["Satır Tipi", "Oda No", "Oda Tipi", "Manzara", "Özel Not (Oda)", "İsim", "Soyisim", "TC/Pasaport", "Cinsiyet", "Yaş", "Grup ID", "İlişki Tipi", "Oda Tercihi", "Durum", "Uyarı Açıklama"]
    ws.append(headers)

    # Stiller
    header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    oda_fill = PatternFill(start_color="B8CCE4", end_color="B8CCE4", fill_type="solid")
    uyari_fill = PatternFill(start_color="FF0000", end_color="FF0000", fill_type="solid")
    white_bold = Font(color="FFFFFF", bold=True)
    blue_font = Font(color="0000FF"); pink_font = Font(color="FF00FF")
    border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))

    for cell in ws[1]:
        cell.fill = header_fill; cell.font = white_bold; cell.alignment = Alignment(horizontal='center')

    for r in rooms:
        if not r['misf']: continue
        # Başlık
        ws.append(["ODA_BAŞLIK", r['no'], r['tip'], r['manzara'], r['not'], "", "", "", "", "", "", "", "", "Yerleştirildi", ""])
        for cell in ws[ws.max_row]: cell.fill = oda_fill; cell.font = Font(bold=True); cell.border = border
        # Misafirler
        for m in r['misf']:
            mask_tc = "*******" + str(m['tc'])[-4:]
            ws.append(["MİSAFİR", "", "", "", "", m['isim'], m['soyisim'].upper(), mask_tc, m['cinsiyet'], m['yas'], m['grup_id'], m['iliski'], m['tercih'], "Yerleştirildi", ""])
            for cell in ws[ws.max_row]: cell.border = border
            ws.cell(ws.max_row, 9).font = blue_font if m['cinsiyet'] == 'E' else pink_font
        ws.append([""] * 15)

    if waiting_list:
        for m in waiting_list:
            ws.append(["UYARI", "", "", "", "", m['isim'], m['soyisim'].upper(), "", m['cinsiyet'], m['yas'], m['grup_id'], m['iliski'], m['tercih'], "Bekleme Listesi", "Oda Kapasitesi Yetersiz"])
            for cell in ws[ws.max_row]: cell.fill = uyari_fill; cell.font = white_bold; cell.border = border

    for col in ws.columns: ws.column_dimensions[col[0].column_letter].width = 16
    wb.save(output_path)
    return output_path