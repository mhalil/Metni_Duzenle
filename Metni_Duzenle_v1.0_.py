import sys
import re
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QPushButton, QPlainTextEdit)
from PySide6.QtGui import QGuiApplication, QFont, QIcon
from PySide6.QtCore import Qt

class MetinDuzenleyici(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(".:: Metni Düzenle (v1.0) - PySide6 ::.")
        self.resize(850, 425)
        
        # Ana widget ve layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Metin kutusu
        self.metin_kutusu = QPlainTextEdit()
        font = QFont("Tahoma", 11)
        self.metin_kutusu.setFont(font)
        # Daha iyi bir görünüm için metin kutusu arka planını ve kenarlığını ayarlıyoruz
        self.metin_kutusu.setStyleSheet("""
            QPlainTextEdit {
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 5px;
                background-color: #fafafa;
                color: #333;
            }
        """)
        layout.addWidget(self.metin_kutusu)
        
        # Buton layout'u
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.buton_duzenle = QPushButton("Kopyalanmış Metni Düzenle ve Panoya Kopyala")
        self.buton_duzenle.setMinimumHeight(45)
        self.buton_duzenle.setFont(QFont("Tahoma", 10, QFont.Bold))
        self.buton_duzenle.setCursor(Qt.PointingHandCursor)
        self.buton_duzenle.setStyleSheet("""
            QPushButton {
                background-color: #20c997;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #1ba87e;
            }
            QPushButton:pressed {
                background-color: #168a66;
            }
        """)
        self.buton_duzenle.clicked.connect(self.duzenle)
        button_layout.addWidget(self.buton_duzenle)
        
        layout.addLayout(button_layout)

    def duzenle(self):
        clipboard = QGuiApplication.clipboard()
        pano_icerigi = clipboard.text()
        
        if not pano_icerigi:
            return
            
        satirlar = pano_icerigi.splitlines()
        satirlar_temiz = [s.rstrip() for s in satirlar]
        
        # En uzun satırı bularak, normal metin satırlarının ortalama genişliğini tahmin edelim
        uzunluklar = [len(s) for s in satirlar_temiz if s]
        if not uzunluklar:
            return
            
        max_uzunluk = max(uzunluklar)
        # Eğer bir satır, en uzun satırın %60'ından daha kısaysa, büyük ihtimalle bir başlıktır veya paragrafın son cümlesidir.
        esik_uzunluk = max_uzunluk * 0.60 if max_uzunluk > 40 else 0
        
        metin = ""
        # Cümle bitiş işaretleri (paragraf sonunu tahmin etmek için)
        bitis_isaretleri = (".", "!", "?", ":", '."', '!"', '?"', ".'", "!'", "?'")
        
        for satir_temiz in satirlar_temiz:
            if not satir_temiz:
                metin += "\n\n"  # Zaten boş satır varsa paragraf ayrımıdır
            # Standart tire (-) veya Word/PDF'lerde çıkan özel tire (‐, ‑) ile bitiyorsa
            elif satir_temiz.endswith("-") or satir_temiz.endswith("‐") or satir_temiz.endswith("‑"):
                metin += satir_temiz[:-1]
            elif satir_temiz.endswith(bitis_isaretleri):
                # Cümle sonu işaretiyle bitiyorsa paragrafı bitir
                metin += satir_temiz + "\n\n"
            elif len(satir_temiz) < esik_uzunluk:
                # Satır belirgin derecede kısaysa (örn: Başlıklar) yeni paragrafa geç
                metin += satir_temiz + "\n\n"
            else:
                # Cümle devam ediyorsa boşluk bırakıp devam et
                metin += satir_temiz + " "
                
        # Fazladan oluşan satır atlamalarını 2 satıra (tek boşluk) indir
        metin = re.sub(r'\n{3,}', '\n\n', metin)
        metin = metin.strip()
        
        # Düzenlenmiş metni kutuya yazdır
        self.metin_kutusu.setPlainText(metin)
        
        # Panoya kopyala
        clipboard.setText(metin)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    pencere = MetinDuzenleyici()
    pencere.show()
    sys.exit(app.exec())
