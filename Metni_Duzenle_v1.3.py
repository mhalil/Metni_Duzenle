import sys
import re
import json
import os
from datetime import datetime

try:
    import keyboard
    HAS_KEYBOARD = True
except ImportError:
    HAS_KEYBOARD = False

from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QPushButton, QPlainTextEdit, QListWidget,
                               QSplitter, QDialog, QLabel, QCheckBox, QLineEdit,
                               QMessageBox, QListWidgetItem, QFrame, QScrollArea, QFormLayout,
                               QGroupBox, QRadioButton, QButtonGroup)
from PySide6.QtGui import QGuiApplication, QFont, QIcon, QColor, QPalette, QTextCursor
from PySide6.QtCore import Qt, Signal, QObject, QTimer

SETTINGS_FILE = "ayarlar.json"
HISTORY_FILE = "gecmis.json"

class HotkeyListener(QObject):
    pressed = Signal()

class MetinDuzenleyici(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(".:: Metni Düzenle ::.")
        self.resize(1150, 600)
        
        self.history_data = []
        self.current_original_text = ""
        self.hotkey_listener = HotkeyListener()
        self.hotkey_listener.pressed.connect(self.arka_planda_duzenle)
        
        self.load_settings()
        self.init_ui()
        self.load_history()
        self.apply_settings()
        self.register_hotkey()

    def load_settings(self):
        self.settings = {
            "always_on_top": False,
            "dark_mode": False,
            "clean_page_numbers": True,
            "fix_turkish_chars": True,
            "global_hotkey": "ctrl+shift+e"
        }
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    self.settings.update(loaded)
            except Exception as e:
                print("Ayarlar yüklenemedi:", e)

    def save_settings(self):
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            print("Ayarlar kaydedilemedi:", e)

    def load_history(self):
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    self.history_data = json.load(f)
                    
                for text in self.history_data:
                    ozet = text[:40].replace('\n', ' ') + "..." if len(text) > 40 else text.replace('\n', ' ')
                    self.list_history.addItem(ozet)
            except Exception as e:
                print("Geçmiş yüklenemedi:", e)

    def save_history(self):
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.history_data, f, indent=4)
        except Exception as e:
            print("Geçmiş kaydedilemedi:", e)

    def apply_settings(self):
        # Always on top
        if self.settings.get("always_on_top"):
            self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        else:
            self.setWindowFlag(Qt.WindowStaysOnTopHint, False)
        self.show() # Pencere bayrakları değiştiğinde yeniden göstermek gerekir
        
        # Dark Mode
        if self.settings.get("dark_mode"):
            self.setStyleSheet("""
                QMainWindow, QDialog, QWidget { background-color: #2b2b2b; color: #f1f1f1; }
                QPlainTextEdit { background-color: #1e1e1e; color: #d4d4d4; border: 1px solid #555; }
                QListWidget { background-color: #1e1e1e; color: #d4d4d4; border: 1px solid #555; }
                QListWidget::item:selected { background-color: #0e639c; }
                QPushButton { background-color: #3a3d41; border: 1px solid #555; padding: 5px; color: #f1f1f1; border-radius: 3px;}
                QPushButton:hover { background-color: #4a4d51; }
                QLineEdit { background-color: #1e1e1e; color: white; border: 1px solid #555; }
                QGroupBox { border: 1px solid #555; border-radius: 4px; margin-top: 2ex; font-weight: bold; }
                QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 3px; }
            """)
        else:
            self.setStyleSheet("""
                QMainWindow, QDialog, QWidget { background-color: #f0f0f0; color: #333; }
                QPlainTextEdit { background-color: #ffffff; color: #333; border: 1px solid #ccc; }
                QListWidget { background-color: #ffffff; color: #333; border: 1px solid #ccc; }
                QListWidget::item:selected { background-color: #0078d7; color: white; }
                QPushButton { background-color: #e1e1e1; border: 1px solid #ccc; padding: 5px; color: #333; border-radius: 3px;}
                QPushButton:hover { background-color: #d1d1d1; }
                QLineEdit { background-color: #ffffff; color: #333; border: 1px solid #ccc; }
                QGroupBox { border: 1px solid #ccc; border-radius: 4px; margin-top: 2ex; font-weight: bold; }
                QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 3px; }
            """)
            
        # Ana butonun stilini her iki modda da koruyalım
        self.buton_duzenle.setStyleSheet("""
            QPushButton {
                background-color: #20c997;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #1ba87e; }
            QPushButton:pressed { background-color: #168a66; }
        """)

    def register_hotkey(self):
        if not HAS_KEYBOARD:
            return
            
        try:
            keyboard.unhook_all()
        except:
            pass
            
        hotkey = self.settings.get("global_hotkey", "")
        if hotkey:
            try:
                # Klavye thread'inden Qt thread'ine sinyal gönderiyoruz
                keyboard.add_hotkey(hotkey, lambda: self.hotkey_listener.pressed.emit())
            except Exception as e:
                print("Kısayol tuşu ayarlanamadı:", e)

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Orta Bölüm (Geçmiş ve Metin Alanı Splitter'ı)
        splitter = QSplitter(Qt.Horizontal)
        
        # Geçmiş Paneli
        history_widget = QWidget()
        history_layout = QVBoxLayout(history_widget)
        history_layout.setContentsMargins(0, 0, 0, 0)
        history_layout.addWidget(QLabel("<b>Geçmiş</b>"))
        
        self.list_history = QListWidget()
        self.list_history.itemClicked.connect(self.history_item_clicked)
        history_layout.addWidget(self.list_history)
        
        history_btn_layout = QHBoxLayout()
        btn_secili_sil = QPushButton("Seçileni Sil")
        btn_secili_sil.clicked.connect(self.sil_secili_gecmis)
        btn_tumunu_sil = QPushButton("Tümünü Sil")
        btn_tumunu_sil.clicked.connect(self.sil_tum_gecmis)
        
        history_btn_layout.addWidget(btn_secili_sil)
        history_btn_layout.addWidget(btn_tumunu_sil)
        history_layout.addLayout(history_btn_layout)
        
        # Metin Paneli
        self.metin_kutusu = QPlainTextEdit()
        self.metin_kutusu.setFont(QFont("Tahoma", 11))
        
        # Sağ Panel
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Karakter Manipülasyonu
        self.group_manipulasyon = QGroupBox("Karakter Manipülasyonu")
        manipulasyon_layout = QVBoxLayout(self.group_manipulasyon)
        
        self.radio_orijinal = QRadioButton("Orijinal")
        self.radio_buyuk = QRadioButton("BÜYÜK HARF")
        self.radio_kucuk = QRadioButton("küçük harf")
        self.radio_ilk = QRadioButton("İlk Harfler Büyük")
        self.radio_cumle = QRadioButton("Cümlelerin İlk Harfleri Büyük")
        
        self.radio_orijinal.setChecked(True)
        
        self.btn_group = QButtonGroup(self)
        self.btn_group.addButton(self.radio_orijinal, 1)
        self.btn_group.addButton(self.radio_buyuk, 2)
        self.btn_group.addButton(self.radio_kucuk, 3)
        self.btn_group.addButton(self.radio_ilk, 4)
        self.btn_group.addButton(self.radio_cumle, 5)
        
        manipulasyon_layout.addWidget(self.radio_orijinal)
        manipulasyon_layout.addWidget(self.radio_buyuk)
        manipulasyon_layout.addWidget(self.radio_kucuk)
        manipulasyon_layout.addWidget(self.radio_ilk)
        manipulasyon_layout.addWidget(self.radio_cumle)
        
        self.btn_group.idToggled.connect(self.on_radio_toggled)
        
        right_layout.addWidget(self.group_manipulasyon)
        
        # Ayarlar
        self.group_ayarlar = QGroupBox("Ayarlar")
        
        ayarlar_layout = QFormLayout(self.group_ayarlar)
        
        self.chk_always_on_top = QCheckBox("Uygulamayı Her Zaman Üstte Tut")
        self.chk_always_on_top.setChecked(self.settings.get("always_on_top", False))
        self.chk_always_on_top.toggled.connect(self.ayarlar_degisti)
        
        self.chk_dark_mode = QCheckBox("Karanlık Mod (Dark Mode)")
        self.chk_dark_mode.setChecked(self.settings.get("dark_mode", False))
        self.chk_dark_mode.toggled.connect(self.ayarlar_degisti)
        
        self.chk_clean_pages = QCheckBox("Sayfa Numaralarını Temizle")
        self.chk_clean_pages.setChecked(self.settings.get("clean_page_numbers", True))
        self.chk_clean_pages.toggled.connect(self.ayarlar_degisti)
        
        self.chk_fix_turkish = QCheckBox("Bozuk Türkçe Karakterleri Düzelt")
        self.chk_fix_turkish.setChecked(self.settings.get("fix_turkish_chars", True))
        self.chk_fix_turkish.toggled.connect(self.ayarlar_degisti)
        
        self.txt_hotkey = QLineEdit()
        self.txt_hotkey.setText(self.settings.get("global_hotkey", "ctrl+shift+e"))
        self.txt_hotkey.setPlaceholderText("Örn: ctrl+shift+e")
        self.txt_hotkey.editingFinished.connect(self.ayarlar_degisti)
        
        ayarlar_layout.addRow(self.chk_always_on_top)
        ayarlar_layout.addRow(self.chk_dark_mode)
        ayarlar_layout.addRow(self.chk_clean_pages)
        ayarlar_layout.addRow(self.chk_fix_turkish)
        ayarlar_layout.addRow("Kısayol Tuşu:", self.txt_hotkey)
        
        if not HAS_KEYBOARD:
            warn_lbl = QLabel("Kısayol tuşunun çalışması için \nsisteminizde 'keyboard' modülü \nyüklü olmalıdır.\n (pip install keyboard)")
            warn_lbl.setStyleSheet("color: #e74c3c; font-size: 11px;")
            ayarlar_layout.addWidget(warn_lbl)
            
        right_layout.addWidget(self.group_ayarlar)
        right_layout.addStretch()
        
        splitter.addWidget(history_widget)
        splitter.addWidget(self.metin_kutusu)
        splitter.addWidget(right_panel)
        splitter.setSizes([200, 650, 300])
        
        main_layout.addWidget(splitter)
        
        # Alt Buton
        bottom_layout = QHBoxLayout()
        
        btn_yardim = QPushButton("Yardım")
        btn_yardim.setMinimumHeight(45)
        btn_yardim.setMaximumWidth(120)
        btn_yardim.clicked.connect(self.goster_yardim)
        
        btn_hakkinda = QPushButton("Hakkında")
        btn_hakkinda.setMinimumHeight(45)
        btn_hakkinda.setMaximumWidth(120)
        btn_hakkinda.clicked.connect(self.goster_hakkinda)
        
        self.buton_duzenle = QPushButton("Kopyalanmış Metni Düzenle ve Panoya Kopyala")
        self.buton_duzenle.setMinimumHeight(45)
        self.buton_duzenle.setFont(QFont("Tahoma", 10, QFont.Bold))
        self.buton_duzenle.setCursor(Qt.PointingHandCursor)
        self.buton_duzenle.clicked.connect(self.duzenle_ve_kopyala)
        
        bottom_layout.addWidget(btn_yardim)
        bottom_layout.addWidget(btn_hakkinda)
        bottom_layout.addWidget(self.buton_duzenle)
        
        main_layout.addLayout(bottom_layout)

    def ayarlar_degisti(self):
        eski_kisayol = self.settings.get("global_hotkey")
        self.settings = {
            "always_on_top": self.chk_always_on_top.isChecked(),
            "dark_mode": self.chk_dark_mode.isChecked(),
            "clean_page_numbers": self.chk_clean_pages.isChecked(),
            "fix_turkish_chars": self.chk_fix_turkish.isChecked(),
            "global_hotkey": self.txt_hotkey.text().strip()
        }
        self.save_settings()
        self.apply_settings()
        
        if eski_kisayol != self.settings.get("global_hotkey"):
            self.register_hotkey()

    def on_radio_toggled(self, id, checked):
        if checked:
            if id == 1: self.metin_donustur("orijinal")
            elif id == 2: self.metin_donustur("buyuk")
            elif id == 3: self.metin_donustur("kucuk")
            elif id == 4: self.metin_donustur("ilk")
            elif id == 5: self.metin_donustur("cumle")

    def goster_hakkinda(self):
        QMessageBox.about(self, "Hakkında", 
            "<b>Metni Düzenle v1.3</b><br><br>"
            "Bu uygulama, PDF dosyası, web sayfası,...vb kaynaklardaki metinleri, "
            "satır ve paragraf yapısını bozmadan kopyalamak ve düzenlemek amacıyla hazırlanmıştır.<br><br>"
            "Geliştirici: Mustafa Halil GÖRENTAŞ<br><br>"
            "<b>Programlama Dili ve Modül Bilgisi:</b><br>"
            "<b>Programlama Dili:</b> Python<br>"
            "<b>Kullanıcı Arayüzü:</b> PySide6<br>"
            "<b>Lisans:</b> MIT Lisansı"
        )

    def goster_yardim(self):
        yardim_metni = (
            """
                <b>Kullanım Rehberi:</b><br>

                <b>1.</b> PDF dosyası, web sayfası veya harici bir kaynaktan sorunlu (satırları kopuk) metni kopyalayın (`Ctrl+C`).<br>
                <b>2.</b> <b>"Kopyalanmış Metni Düzenle ve Panoya Kopyala"</b> butonuna basın veya önceden belirlediğiniz <b>Kısayol Tuşunu</b> (`Ctrl+Shift+E` vb.) kullanın.<br>
                <b>3.</b> Düzenlenmiş metin anında panonuza kopyalanacaktır.<br>
                <b>4.</b> Düzenlenmiş metni istediğiniz yere doğrudan yapıştırın (`Ctrl+V`).<br><br>

                <b>Ayarlar:</b><br>
                Uygulamanın sağ panelindeki <b>Ayarlar</b> bölümünü kullanarak;
                <ul>
                <li> <b>Kısayol tuşunuzu</b> değiştirebilir,</li>
                <li> <b>Karanlık Modu</b> açıp kapatabilir,</li>
                <li> <b>Otomatik sayfa numarası temizleme</b> özelliğini açıp kapatabilirsiniz,</li>
                <li> <b>Türkçe karakter düzelticisini</b> açıp kapatabilirsiniz.</li>
                </ul><br>
            """
            
        )
        QMessageBox.information(self, "Yardım", yardim_metni)

    def metin_donustur(self, mod):
        metin = self.metin_kutusu.toPlainText()
        if not metin:
            return
            
        def turkce_upper(harf):
            if harf == 'i': return 'İ'
            if harf == 'ı': return 'I'
            return harf.upper()
            
        def title_match(m):
            return m.group(1) + turkce_upper(m.group(2))
            
        if mod == "orijinal":
            if self.current_original_text:
                metin = self.current_original_text
            else:
                return
        elif mod == "buyuk":
            metin = metin.replace("i", "İ").replace("ı", "I").upper()
        elif mod == "kucuk":
            metin = metin.replace("İ", "i").replace("I", "ı").lower()
        elif mod == "ilk":
            metin = metin.replace("İ", "i").replace("I", "ı").lower()
            metin = re.sub(r'(^|\s)([^\W\d_])', title_match, metin)
        elif mod == "cumle":
            metin = metin.replace("İ", "i").replace("I", "ı").lower()
            # 1. Metnin en başındaki ilk harfi büyük yap
            metin = re.sub(r'(^\s*)([^\W\d_])', title_match, metin)
            # 2. Nokta, ünlem veya soru işaretinden sonraki ilk harfi büyük yap
            metin = re.sub(r'([.!?]\s+)([^\W\d_])', title_match, metin)
            # 3. Yeni bir satır (başlık veya yeni paragraf) başladığında ilk harfi büyük yap
            metin = re.sub(r'(\n\s*)([^\W\d_])', title_match, metin)
            
        self.metin_kutusu.setPlainText(metin)
        QGuiApplication.clipboard().setText(metin)

    def arka_planda_duzenle(self):
        # Kısayol tuşuna basıldığında tetiklenir
        self.duzenle_ve_kopyala()
        
        # Kullanıcıya ufak bir geri bildirim göstermek için pencereyi parlatabiliriz veya title değiştirebiliriz
        orijinal_title = self.windowTitle()
        self.setWindowTitle("Düzenlendi ve Kopyalandı! ✔")
        QTimer.singleShot(1500, lambda: self.setWindowTitle(orijinal_title))

    def clean_page_numbers(self, satirlar):
        temiz = []
        for satir in satirlar:
            s = satir.strip()
            # Sadece sayılardan oluşuyorsa atla
            if s.isdigit():
                continue
            # "Sayfa 12", "Page 15" formatındaysa atla
            if re.match(r'^(sayfa|page)\s*\d+$', s, re.IGNORECASE):
                continue
            temiz.append(satir)
        return temiz

    def fix_turkish_chars(self, text):
        mapping = {
            'Ý': 'İ', 'ý': 'ı', 'Þ': 'Ş', 'þ': 'ş', 'Ð': 'Ğ', 'ð': 'ğ',
            'Ý': 'İ', 'Ý': 'İ'  # Bazı diğer yaygın pdf hataları buraya eklenebilir
        }
        for bozuk, dogru in mapping.items():
            text = text.replace(bozuk, dogru)
        return text

    def history_item_clicked(self, item):
        index = self.list_history.row(item)
        if 0 <= index < len(self.history_data):
            metin = self.history_data[index]
            self.metin_kutusu.setPlainText(metin)
            self.current_original_text = metin

    def add_to_history(self, text):
        # Eğer en son eklenenle aynıysa ekleme
        if self.history_data and self.history_data[0] == text:
            return
            
        self.history_data.insert(0, text)
        ozet = text[:40].replace('\n', ' ') + "..." if len(text) > 40 else text.replace('\n', ' ')
        
        self.list_history.insertItem(0, ozet)
        
        # Sınırlandırma: En fazla 20 geçmiş kalsın
        if len(self.history_data) > 20:
            self.history_data.pop()
            self.list_history.takeItem(20)
            
        self.save_history()

    def sil_secili_gecmis(self):
        row = self.list_history.currentRow()
        if row >= 0:
            self.list_history.takeItem(row)
            self.history_data.pop(row)
            self.save_history()
            
            if not self.history_data:
                self.metin_kutusu.clear()
                self.current_original_text = ""

    def sil_tum_gecmis(self):
        if not self.history_data:
            return
            
        cevap = QMessageBox.question(self, "Onay", "Tüm geçmişi silmek istediğinize emin misiniz?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if cevap == QMessageBox.Yes:
            self.list_history.clear()
            self.history_data.clear()
            self.save_history()
            self.metin_kutusu.clear()
            self.current_original_text = ""

    def duzenle_ve_kopyala(self):
        clipboard = QGuiApplication.clipboard()
        pano_icerigi = clipboard.text()
        
        if not pano_icerigi:
            return
            
        # 1. Türkçe karakter düzeltmesi
        if self.settings.get("fix_turkish_chars", True):
            pano_icerigi = self.fix_turkish_chars(pano_icerigi)
            
        satirlar = pano_icerigi.splitlines()
        
        # 2. Sayfa numaralarını temizleme
        if self.settings.get("clean_page_numbers", True):
            satirlar = self.clean_page_numbers(satirlar)
            
        satirlar_temiz = [s.rstrip() for s in satirlar]
        
        uzunluklar = [len(s) for s in satirlar_temiz if s]
        if not uzunluklar:
            return
            
        max_uzunluk = max(uzunluklar)
        esik_uzunluk = max_uzunluk * 0.60 if max_uzunluk > 40 else 0
        
        metin = ""
        bitis_isaretleri = (".", "!", "?", ":", '."', '!"', '?"', ".'", "!'", "?'")
        
        for satir_temiz in satirlar_temiz:
            if not satir_temiz:
                metin += "\n\n"
            elif satir_temiz.endswith("-") or satir_temiz.endswith("‐") or satir_temiz.endswith("‑"):
                metin += satir_temiz[:-1]
            elif satir_temiz.endswith(bitis_isaretleri):
                metin += satir_temiz + "\n\n"
            elif len(satir_temiz) < esik_uzunluk:
                metin += satir_temiz + "\n\n"
            else:
                metin += satir_temiz + " "
                
        metin = re.sub(r'\n{3,}', '\n\n', metin)
        metin = metin.strip()
        
        self.metin_kutusu.setPlainText(metin)
        self.current_original_text = metin
        clipboard.setText(metin)
        
        self.add_to_history(metin)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    pencere = MetinDuzenleyici()
    pencere.show()
    sys.exit(app.exec())
