import tkinter as tk
from tkinter import ttk
import pyperclip

pencere = tk.Tk()
pencere.geometry("600x350+500+350")
pencere.title(".:: Metni Düzenle ::. (v0.2 - Mustafa Halil)")

def metin_kutusundan_kopyala():
	duzenli = metin_kutusu.get(1.0, tk.END)
	pyperclip.copy(duzenli)

def metin_kutusuna_yapistir():
	pano_icerigi = pencere.clipboard_get()
	if pano_icerigi:
		metin_kutusu.delete("1.0", tk.END)
		pano_icerigi = pano_icerigi.replace("\n","")
		metin_kutusu.insert(tk.INSERT, pano_icerigi)
	else:
		metin_kutusu.delete("1.0", tk.END)
		metin_kutusu.insert(tk.INSERT, "Panoya kopyalanmış metin bulunmamaktadır.")

yazitipi_ozelligi = ("Calibri", 10)	# ("Tahoma", 10, "bold")

metin_kutusu = tk.Text(
    width=40,
    height=10,
    wrap=tk.WORD
)
metin_kutusu.configure(font = yazitipi_ozelligi)
metin_kutusu.pack(fill=tk.BOTH, expand=True)
    
buton_duzenle = tk.Button(
    pencere,
    text="Düzenle",
    # ~ font=yazitipi_ozelligi,
    height=1,
    width=9,
    cursor="hand2",
    command= metin_kutusuna_yapistir
)
buton_duzenle.pack(side="right", padx=10, pady=10)

buton_duzenlenmis = tk.Button(
    pencere,
    text="Kopyala",
    height=1,
    width=9,
    cursor="hand2",
    command= metin_kutusundan_kopyala
)
# ~ buton_duzenlenmis['font']=yazitipi_ozelligi
buton_duzenlenmis.pack(side="right", padx=10, pady=10)

pencere.mainloop()
